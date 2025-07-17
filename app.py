from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
import os, io, base64, urllib.parse, tempfile
from dotenv import load_dotenv
from openai import OpenAI
from markdown import markdown
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import fitz

load_dotenv()

odbc_reits = os.getenv("AZURE_SQL_DB_REITS")
odbc_banks = os.getenv("AZURE_SQL_DB_BANKS")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

engine_reits = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_reits), fast_executemany=True)
engine_banks = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_banks), fast_executemany=True)

############## Helper Functions ##############

def load_rows_by_ticker(ticker: str, engine) -> pd.DataFrame:

    sql = text("""
        SELECT  Ticker,
                Quarter,
                Line_Item_Name,
                Value,
                Unit,
                Currency,
                Category
        FROM    dbo.Financial_Line_Item
        WHERE   Ticker = :ticker
        ORDER BY Quarter
    """)

    with engine.begin() as conn:
        df = pd.read_sql(sql, conn, params={"ticker": ticker.upper()})

    return df

def unsecured_debt_to_ebitda(df: pd.DataFrame) -> pd.DataFrame:

    filt = df["Line_Item_Name"].isin(["EBITDA", "Total Unsecured Debt"])
    piv = (df.loc[filt].pivot(index="Quarter", columns="Line_Item_Name", values="Value").dropna().sort_index())

    piv["Unsecured_Debt_to_EBITDA"] = piv["Total Unsecured Debt"] / (piv["EBITDA"] * 4)

    return piv.reset_index()[["Quarter", "Unsecured_Debt_to_EBITDA"]]

def line_chart_png(ratio_df: pd.DataFrame) -> str:

    if ratio_df.empty:
        return ""
    
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(ratio_df["Quarter"], ratio_df["Unsecured_Debt_to_EBITDA"],
            marker="o", linewidth=2, color="#00aeef")
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Total Unsecured Debt / EBITDA (Annualized)")
    ax.set_title("Unsecured Leverage Trend")
    ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def pie_chart(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(6, 6))

    df = df[df["Value"] > 0].copy()
    total_cre_row = df[df["Line_Item_Name"] == "Total CRE"]

    if total_cre_row.empty:
        plt.close(fig)
        return ""

    total_cre_value = total_cre_row["Value"].values[0]
    df = df[df["Line_Item_Name"] != "Total CRE"].copy()
    df = df.sort_values(by="Value", ascending=False)

    colors = [
        "#003f5c", "#29487d", "#87bdd8", "#AEDEF4", "#012F42",
        "#51A0AC", "#3B6565", "#409ac7", "#0f9a93", "#59C9BA"
    ]

    color_cycle = (colors * ((len(df) // len(colors)) + 1))[:len(df)]

    values = df["Value"]
    raw_labels = df["Line_Item_Name"]
    percentages = values / total_cre_value * 100
    labels = [f"{label}, {pct:.1f}%" for label, pct in zip(raw_labels, percentages)]

    ax.pie(values, labels=labels, startangle=140, colors=color_cycle)
    ax.set_title("CRE Loan Portfolio Distribution")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def extract_cre_table(
    image_file,
    ticker: str,
    quarter: str,
    units: str,
    currency: str,
    category: str,
    ) -> str:
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image_file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

    instruction = (
        "Extract the property type labels and loan amounts from this image, then output a markdown table with columns: " 
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        "Merge 'Other general office' and 'Credit tenant lease and life sciences' into 'Office'.\n"
        "Merge 'Other', 'Co‑op', and 'Data Center' into 'Other'.\n"
        "Rename 'Hospitality' to 'Lodging'.\n"
        "Add a final row 'Total CRE' containing the sum of the loan amounts.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )
    return resp.choices[0].message.content

def md_table_to_rows(md_table: str):
    rows = []
    lines = [l for l in md_table.splitlines() if l.startswith("|")]
    if len(lines) < 3:
        return rows
    for line in lines[2:]:
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) != 7:
            continue
        try:
            value = float(parts[3].replace(",", ""))
        except ValueError:
            value = None
        rows.append(
            {
                "Ticker": parts[0],
                "Quarter": parts[1],
                "Line_Item_Name": parts[2],
                "Value": value,
                "Unit": parts[4],
                "Currency": parts[5],
                "Category": parts[6],
            }
        )
    return rows

############## Flask App Endpoints ##############

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reits")
def reits():                         
    ticker = request.args.get("ticker", "").strip().upper()
    rows = None
    ratio_png = ""

    if ticker:
        df = load_rows_by_ticker(ticker, engine_reits)
        rows = df.to_dict("records") if not df.empty else []

        ratio_df = unsecured_debt_to_ebitda(df)
        ratio_png = line_chart_png(ratio_df)

    return render_template("reits.html", ticker=ticker, rows=rows, ratio_png=ratio_png)

@app.route("/banks")
def banks():                         
    ticker = request.args.get("ticker", "").strip().upper()
    quarter = request.args.get("quarter", "").strip()
    action = request.args.get("action", "")

    rows = None
    pie_png = ""

    if ticker and quarter:
        sql = text("""
            SELECT  Ticker,
                    Quarter,
                    Line_Item_Name,
                    Value,
                    Unit,
                    Currency,
                    Category
            FROM    dbo.Financial_Line_Item
            WHERE   Ticker = :ticker AND Quarter = :quarter
            ORDER BY Line_Item_Name
        """)
    
        with engine_banks.begin() as conn:
            df = pd.read_sql(sql, conn, params={"ticker": ticker, "quarter": quarter})

        rows = df.to_dict("records") if not df.empty else []

        if action == "pie" and not df.empty:
            pie_png = pie_chart(df)

    return render_template("banks.html", ticker=ticker, quarter=quarter, rows=rows, pie_png=pie_png)

@app.route("/analyze_ratio", methods=["POST"])
def analyze_ratio():
    try:
        ticker = request.json.get("ticker", "").strip().upper()

        if not ticker:
            return {"error": "Missing ticker"}, 400

        df = load_rows_by_ticker(ticker, engine_reits)

        if df.empty:
            return {"error": "No financial data found for this ticker."}, 400

        ratio_df = unsecured_debt_to_ebitda(df)

        if ratio_df.empty:
            return {"error": "Not enough data to analyze."}, 400

        trend_str = "\n".join([
            f"{row['Quarter']}: {row['Unsecured_Debt_to_EBITDA']:.2f}"
            for _, row in ratio_df.iterrows()
        ])

        prompt = f"""
        The following data is a quarterly trend of an unsecured debt-to-EBITDA ratio for the REIT ticker {ticker}: {trend_str}
        Analyze how this ratio has changed over time and provide exactly 3 concise bullet point that explain possible reasons for why the financial ratio has increased or decreased materially in certain quarters.
        Use financial reasoning and trends in the REIT industry to explain changes in this company's EBITDA financial metric and unsecured debt levels. 
        Avoid giving generic statements in the explanation and keep each bullet under 3 sentences."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400
        )
        result = response.choices[0].message.content

        return jsonify({"analysis": result, "table": ratio_df.to_dict(orient="records")})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/analyze_ebitda_pdf", methods=["POST"])
def analyze_quarter_pdf():
    try:
        file = request.files.get("pdf")
        ticker = request.form.get("ticker", "").strip().upper()

        if not file or not ticker:
            return jsonify({"error": "Missing PDF or ticker."}), 400

        doc = fitz.open(stream=file.read(), filetype="pdf")

        target_text = ""
        for i, page in enumerate(doc):
            text = page.get_text()
            if "CONDENSED CONSOLIDATED STATEMENT OF OPERATIONS" in text.upper():

                target_text = text
                if i + 1 < len(doc):
                    target_text += "\n" + doc[i + 1].get_text()
                break
        
        if not target_text:
            return jsonify({"error": "Could not find the Income Statement section in the PDF."}), 400
        
        normalized_text = " ".join(target_text.split())
        doc_excerpt = normalized_text[:4000]

        prompt = f"""
        The following data is extracted text from {ticker}'s financial filing, which contains the company's income statement for a given quarter in the column "Three Months Ended". 
        In 1 concise bullet point, identify the quarter being analyzed and explain why EBITDA may be negative, unusually high, or low in the most recent quarter (typically the left-most column under "Three Months Ended"). 
        Look for mentions of impairment charges, operating losses, debt changes, or other one-time items.
        Note that EBITDA is defined as the sum of net income, interest expense, depreciation and amortization, and provision for income taxes.
        Document Text: {doc_excerpt[:4000]}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )

        result = response.choices[0].message.content
        return jsonify({"analysis": result})

    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/standardize_cre", methods=["GET", "POST"])
def standardize_cre():
    if request.method == "POST":
        image    = request.files.get("image")
        ticker   = request.form.get("ticker", "").strip().upper()
        quarter  = request.form.get("quarter", "").strip()
        units    = request.form.get("units", "").strip()
        currency = request.form.get("currency", "").strip()
        category = request.form.get("category", "").strip()

        if not image or image.filename == "" or not image.filename.lower().endswith(".png"):
            error_msg = "Please upload a valid PNG file."
            return render_template("standardize_cre.html", error_msg=error_msg)

        md_table  = extract_cre_table(image, ticker, quarter, units, currency, category)
        clean_table = "\n".join(line for line in md_table.splitlines() if line.lstrip().startswith("|"))
        rows = md_table_to_rows(clean_table)

        return render_template(
            "standardize_cre.html",
            rows=rows,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
        )
    
    return render_template("standardize_cre.html")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)