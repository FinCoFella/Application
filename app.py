from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
import os, io, base64, urllib.parse
from dotenv import load_dotenv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

load_dotenv()

server = os.getenv("SQL_SERVER")
db = os.getenv("SQL_DATABASE")
user = os.getenv("SQL_USER")
pwd = os.getenv("SQL_PASS")
driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

odbc_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER=tcp:{server},1433;"
    f"DATABASE={db};"
    f"UID={user};PWD={pwd};"
    "Encrypt=yes;TrustServerCertificate=no;"
)

connection_uri = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str)
engine = create_engine(connection_uri, fast_executemany=True)

############## Helper Functions ##############

def load_rows_by_ticker(ticker: str) -> pd.DataFrame:

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
        df = load_rows_by_ticker(ticker)
        rows = df.to_dict("records") if not df.empty else []

        ratio_df = unsecured_debt_to_ebitda(df)
        ratio_png = chart_png(ratio_df)

    return render_template("reits.html", ticker=ticker, rows=rows, ratio_png=ratio_png)

if __name__ == '__main__':
    app.run(debug=True)