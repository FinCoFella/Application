from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
import os, re, urllib.parse, json
from dotenv import load_dotenv
from openai import OpenAI
from markupsafe import Markup, escape

from llm_extract_cre import extract_cre_table, md_table_to_rows, aggregate_standardized, rows_from_slices_json_precise, rows_from_table_json_precise
from charts import line_chart_png, pie_chart_png
from calc import unsecured_debt_to_ebitda
from load_reit_db import load_ticker_reit
from load_bank_db import load_ticker_bank
from llm_analyze_chart import analyze_ratio as run_ratio_analysis
from llm_analyze_doc import analyze_quarter_doc
from bank_stnd_cre import override_values

load_dotenv()

odbc_reits = os.getenv("AZURE_SQL_DB_REITS")
odbc_banks = os.getenv("AZURE_SQL_DB_BANKS")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

engine_reits = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_reits), fast_executemany=True)
engine_banks = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc_banks), fast_executemany=True)

JSON_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S | re.I)

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

    ##### Override Route #####
    if request.method == "POST" and request.form.get("override") == "1":
        ticker   = request.form["ticker"]
        quarter  = request.form["quarter"]
        units    = request.form["units"]
        currency = request.form["currency"]
        category = request.form["category"]
        chart_type = request.form.get("chart_type", "percentage_pie")

        raw = request.form.get("orig_rows_json", "")

        try:
            orig_rows = json.loads(raw)
            if isinstance(orig_rows, str):
                orig_rows = json.loads(orig_rows)
            if not isinstance(orig_rows, list):
                raise ValueError("orig_rows_json must be a JSON array")
        except Exception:
            return render_template(
                "standardize_cre.html",
                error_msg="Invalid original rows payload.",
                ticker=ticker, 
                quarter=quarter, 
                units=units,
                currency=currency, 
                category=category,
                chart_type=chart_type, 
            )

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
            chart_type=chart_type, 
            orig_rows_json=json.dumps(orig_rows),
            explanation=None,
        )
    
    ##### PNG Upload for LLM Analysis Route #####
    elif request.method == "POST":
        image    = request.files.get("image")
        ticker   = request.form.get("ticker", "").strip().upper()
        quarter  = request.form.get("quarter", "").strip()
        units    = request.form.get("units", "").strip()
        currency = request.form.get("currency", "").strip()
        category = request.form.get("category", "").strip()
        chart_type = request.form.get("chart_type", "percentage_pie")

        if not image or image.filename == "" or not image.filename.lower().endswith(".png"):
            error_msg = "Please upload a valid PNG file."
            return render_template("standardize_cre.html", error_msg=error_msg, chart_type=chart_type)

        md_table, explanation = extract_cre_table(image, ticker, quarter, units, currency, category, chart_type=chart_type)
        explanation_html = format_exp_for_html(explanation)

        if chart_type == "value_table":
            rows = rows_from_table_json_precise(explanation, ticker, quarter, units, currency, category)
        elif chart_type == "percentage_pie":
            rows = rows_from_slices_json_precise(explanation, ticker, quarter, units, currency, category)

        if not rows:
            rows = md_table_to_rows(md_table)
        
        if not rows:
            return render_template(
                "standardize_cre.html",
                error_msg="Could not extract any rows from the image.",
                ticker=ticker, 
                quarter=quarter, 
                units=units,
                currency=currency, 
                category=category, 
                chart_type=chart_type,
                explanation=explanation_html,
            )
        
        rows = aggregate_standardized(rows)

        return render_template(
            "standardize_cre.html",
            rows=rows,
            override_rows=None,
            ticker=ticker,
            quarter=quarter,
            units=units,
            currency=currency,
            category=category,
            chart_type=chart_type,
            orig_rows_json=json.dumps(rows),
            explanation=explanation_html,
        )
    
    return render_template("standardize_cre.html", chart_type="percentage_pie")

def format_exp_for_html(md_text: str) -> Markup:

    if not md_text:
        return Markup("")

    m = JSON_FENCE.search(md_text)
    if not m:
        return Markup(f"<div class='explanation-text'>{escape(md_text)}</div>")

    raw_json = m.group(1)
    pretty = raw_json
    try:
        pretty = json.dumps(json.loads(raw_json), indent=2, ensure_ascii=False)
    except Exception:
        pretty = raw_json

    before = escape(md_text[:m.start()])
    after  = escape(md_text[m.end():]).lstrip()

    html = (
        f"{before}"
        f"<pre class='code-block'><code>{escape(pretty)}</code></pre>"
        f"<div class='explanation-text'>{after}</div>"
    )
    return Markup(html)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)