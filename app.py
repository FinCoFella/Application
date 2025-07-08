from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
import os, io, base64, urllib.parse
from dotenv import load_dotenv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

load_dotenv()

odbc_reits = os.getenv("AZURE_SQL_DB_REITS")
odbc_banks = os.getenv("AZURE_SQL_DB_BANKS")

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

def chart_png(ratio_df: pd.DataFrame) -> str:

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
        ratio_png = chart_png(ratio_df)

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

if __name__ == '__main__':
    app.run(debug=True)