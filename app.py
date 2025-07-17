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
import json
from llm_cre_extract import extract_cre_table, md_table_to_rows
from charts import line_chart_png, pie_chart_png
from calc import unsecured_debt_to_ebitda

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
            pie_png = pie_chart_png(df)

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
    if request.method == "POST" and request.form.get("override") == "1":
        ticker   = request.form["ticker"]
        quarter  = request.form["quarter"]
        units    = request.form["units"]
        currency = request.form["currency"]
        category = request.form["category"]

        orig_rows = json.loads(request.form["orig_rows_json"])

        override_rows = []
        total_override = 0.0

        for r in orig_rows:
            r2 = r.copy()
            if r["Line_Item_Name"] != "Total CRE":
                field_name = f"ov_{r['Line_Item_Name'].replace(' ', '_')}"
                try:
                    new_val = float(request.form.get(field_name, "") or r["Value"])
                except ValueError:
                    new_val = r["Value"]
                r2["Value"] = new_val
                total_override += new_val
            override_rows.append(r2)

        for r2 in override_rows:
            if r2["Line_Item_Name"] == "Total CRE":
                r2["Value"] = total_override
                break

        return render_template(
            "standardize_cre.html",
            rows=orig_rows,
            override_rows=override_rows,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
        )
    
    elif request.method == "POST":
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
            override_rows=None,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
            orig_rows_json=json.dumps(rows),
        )
    
    return render_template("standardize_cre.html")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)