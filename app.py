from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
import os, urllib.parse, json
from dotenv import load_dotenv
from openai import OpenAI

from llm_extract_cre import extract_cre_table, md_table_to_rows
from charts import line_chart_png, pie_chart_png
from calc import unsecured_debt_to_ebitda
from load_reit_db import load_ticker_reit
from load_bank_db import load_ticker_bank
from llm_analyze_chart import analyze_ratio as run_ratio_analysis
from llm_analyze_doc import analyze_quarter_doc
from bank_stnd_cre import override_values, build_rows_from_llm

load_dotenv()

odbc_reits = os.getenv("AZURE_SQL_DB_REITS")
odbc_banks = os.getenv("AZURE_SQL_DB_BANKS")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

engine_reits = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_reits), fast_executemany=True)
engine_banks = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_banks), fast_executemany=True)

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
        df = load_ticker_reit(ticker, engine_reits)
        rows = df.to_dict("records") if not df.empty else []
        ratio_df = unsecured_debt_to_ebitda(df)
        ratio_png = line_chart_png(ratio_df)

    return render_template("reits.html", ticker=ticker, rows=rows, ratio_png=ratio_png)

@app.route("/banks")
def banks():                         
    ticker = request.args.get("ticker", "").strip().upper()
    quarter = request.args.get("quarter", "").strip()
    action = request.args.get("action", "")
    rows, pie_png = None, ""

    if ticker and quarter:
        df = load_ticker_bank(ticker, quarter, engine_banks)
        rows = df.to_dict("records") if not df.empty else []

        if action == "pie" and not df.empty:
            pie_png = pie_chart_png(df)

    return render_template("banks.html", ticker=ticker, quarter=quarter, rows=rows, pie_png=pie_png)

@app.route("/analyze_ratio", methods=["POST"])
def analyze_ratio_route():
    try:
        ticker = request.json.get("ticker", "").strip().upper()

        if not ticker:
            return {"error": "Missing ticker"}, 400
        
        result = run_ratio_analysis(ticker, engine_reits, unsecured_debt_to_ebitda, client)

        return jsonify({
                "analysis": result["analysis"],
                "table": result["ratio_df"],
            })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/analyze_ebitda_pdf", methods=["POST"])
def analyze_quarter_pdf_route():
    try:
        file = request.files.get("pdf")
        ticker = request.form.get("ticker", "").strip().upper()

        if not file or not ticker:
            return jsonify({"error": "Missing PDF or ticker."}), 400

        result = analyze_quarter_doc(file.read(), ticker, client)
        return jsonify(result)

    except ValueError as verror:
        return jsonify({"error": str(verror)}), 400
    
    except Exception as e:
        print("Error in analyzing PDF:", e, flush=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/standardize_cre", methods=["GET", "POST"])
def standardize_cre():

    ##### User CRE Values Override Route #####
    if request.method == "POST" and request.form.get("override") == "1":
        ticker   = request.form["ticker"]
        quarter  = request.form["quarter"]
        units    = request.form["units"]
        currency = request.form["currency"]
        category = request.form["category"]

        orig_rows = json.loads(request.form["orig_rows_json"])
        override_rows = override_values(orig_rows, request.form)

        return render_template(
            "standardize_cre.html",
            rows=orig_rows,
            override_rows=override_rows,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
            explanation=None,
        )
    
    ##### User PNG Upload Route for LLM Analysis #####
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

        rows, explanation = build_rows_from_llm(md_table_to_rows, extract_cre_table, image, ticker, quarter, units, currency, category)

        return render_template(
            "standardize_cre.html",
            rows=rows,
            override_rows=None,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
            orig_rows_json=rows,
            explanation=explanation,
        )
    
    return render_template("standardize_cre.html")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)