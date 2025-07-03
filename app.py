from flask import Flask, render_template, request
import pandas as pd
from sqlalchemy import create_engine, text
import os, urllib.parse
from dotenv import load_dotenv 

load_dotenv()

SQL_USER = os.getenv("SQL_USER")
SQL_PASS = os.getenv("SQL_PASS")

odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_REITs;"
    f"UID={SQL_USER};"
    f"PWD={SQL_PASS};"
    "TrustServerCertificate=Yes;"
)

connection_uri = (
    "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_str)
)

engine = create_engine(connection_uri, fast_executemany=True)

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

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reits")
def reits():                         
    ticker = request.args.get("ticker", "").strip().upper()
    rows = None

    if ticker:
        df = load_rows_by_ticker(ticker)
        rows = df.to_dict("records") if not df.empty else []

    return render_template("reits.html", ticker=ticker, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)