import base64, tempfile, json, os, re
from typing import Dict, Callable
from collections import defaultdict
from decimal import Decimal, ROUND_DOWN, getcontext
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

from ticker_prompts_cre import PROMPT_MAP as TICKER_PROMPT_MAP

getcontext().prec = 28

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

Standardized_Labels = ["Multi-family", "Industrial", "Lodging", "Office", "Retail", "Mixed-use", "Residential", "Other"]

Synonyms = { 
    "Multifamily": "Multi-family", 
    "Apartments": "Multi-family",
    "Apartments & Residential": "Multi-family",
    "Multi Family": "Multi-family",
    "Multi-family rental": 'Multi-family',

    "Industrial / Warehouse": "Industrial",
    "Industrial/warehouse": "Industrial",
    "Industrial/Warehouse": "Industrial",
    "Warehouse/Industrial": "Industrial",
    "Warehouse": "Industrial",

    "Hotel": "Lodging",
    "Hotels": "Lodging",
    "Hotel/Motel": "Lodging",
    "Hotel/motel": "Lodging",
    "Hospitality": "Lodging",

    "Mixed use": "Mixed-use",
    "Mixed use properties": "Mixed-use",
    "Multi use": "Mixed-use",

    "Shopping Centers": "Retail",
    "Shopping center": "Retail",
    "Retail (excl shopping center)": "Retail",

    "Medical Office": "Office",
    "General Office": "Office",
    "Office Building": "Office",
    "Healthcare Office": "Office",
    "Other general office": "Office",
    "Credit tenant lease and life sciences": "Office",

    "Single Family / Land Development": "Residential",
    "Residential Land": "Residential",
    "Residential Properties": "Residential",
    "Residential for Sale": "Residential",
    "Residential (Housing)": "Residential",
    "Res. Homebuilders": "Residential",

    "Land Carry": "Other",
    "Other Income Producing Properties": "Other",
    "Services and Non Income Producing": "Other",
    "Land & Residential": "Other",
    "Senior Housing": "Other",
    "Seniors Housing": "Other",
    "Diversified": "Other",
    "Healthcare": "Other",
    "Healthcare ": "Other",
    "Health care": "Other",
    "Health Care": "Other",
    "Health-care": "Other",
    "Commercial Land": "Other",
    "Construction and Land": "Other",
    "Data Center": "Other",
    "Institutional": "Other",
    "Self Storage": "Other",
    "Mobile home park": "Other",
    "Skilled Nursing": "Other",
    "Specialty & Other": "Other",
    "Student Housing": "Other",
    "Self-Storage": "Other",
    "Storage facility": "Other",
    "Development & Land": "Other",
    "Other Investment Properties": "Other",
    "Co-op": "Other"
}

def generic_prompt(ticker, quarter, units, currency, category) -> str:
    syn_labels = "\n".join(f" - '{k}' → '{v}'" for k, v in Synonyms.items())
    stnd_labels = ", ".join(Standardized_Labels)

    return f""" 
    Extract CRE exposure from one image.

    OUTPUT TABLE:
    - Return one markdown table with the following columns in this exact order:
        | Ticker | Quarter | CRE Property Type | Loan Amount | Units | Currency | Category |
    - The last row in the 'CRE Property Type' column should say 'Total CRE'. 
    - The last row in the 'Loan Amount' column should be the sum of all rows.

    OUTPUT AUDIT
    - After the table, add an '### Explanation' section that begins with a JSON code block:
    ```json
            {{ "total_mn": <number>,
            "slices": [ {{ "label":"...", "percent": <number>, "amount_mn": <number> }}, ... ],
            "percent_sum": <number>
            }}

    ```
    - The JSON must list every slice printed next to the chart.
    - Compute percent_sum as the sum of the listed percentages. Do not round it up to 100.
    - If the sum does not equal 100 by more than ± 0.5, re-read ambiguous labels and minimally correct to reach 100.

    EXTRACT
    1) Read the total dollar amount in the center of the pie chart, and convert it into millions (e.g.'0.0' to 0,000).
    2) Then read all property type labels and their corresponding loan amounts from the image, and if the values are percentages, apply the formula below: 
        - Total dollar amount in millions * (% Slice / 100) = slice amount in millions.
    3) If the values are in a table, follow these rules:
        - If the table contains a 'Credit exposure' and '% Drawn' column, multiply the values from the 'Credit exposure' and '% Drawn" to calculate the loan amount.
        - If the table contains a 'Loans outstanding balance' column, use those values as the loan amounts for each property type label.
        - If the table contains a 'Total' column of amounts by type, use those values as the loan amounts for each property type label.

    CONVERT UNITS
    4) If the values are in billions (e.g., '0.0'), multiply the value by 1000 to convert it into millions.

    NORMALIZE LABELS
    5) USe the following case-insensitive mapping to normalize the labels {syn_labels} and keep only these final labels: {stnd_labels}.
    6) Check to make sure 'Other' = sum of *all* slices that map to 'Other' in {syn_labels}.

    AGGREGATE
    7) After normalizing the property type lables, **sum the amounts that map to the same final label within {stnd_labels}**. 

    FORMAT 
    8) After aggregating the loan amount values, **truncate the trailing decimal values** in the 'Loan Amount' column to an integer to remove decimals.

    APPLY USER INPUT
    9) Produce only one markdown table that uses the following constant values:
        - Ticker: {ticker}\n"
        - Quarter: {quarter}\n"
        - Units: {units}\n"
        - Currency: {currency}\n"
        - Category: {category}\n"

    AUDIT
    10) In the '### Explanation', describe how the labels were normalized and how the total loan amount was calculated.
    It should include an equation used to calculate the 'Other' property type. The explanation should be less than 200 words."""

############ Extract Data into Markdown Table ############
def extract_cre_table(image_file, ticker: str, quarter: str, units: str, currency: str, category: str) -> tuple[str, str]:
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image_file.save(tmp.name)

        try:
            with Image.open(tmp.name) as img:
                w, h = img.size

                if w > 0 and h > 0:
                    try:
                        resample = Image.Resampling.LANCZOS
                    except AttributeError:
                        resample = Image.LANCZOS

                    img = img.resize((int(w*2), int(h*2)), resample=resample)
                    img.save(tmp.name, format="PNG", optimize=True)

        except Exception:
            pass 

        with open(tmp.name, "rb") as f:
            data = f.read()

        image_b64 = base64.b64encode(data).decode("utf-8")
    
    try:
        os.unlink(tmp.name)
    except Exception:
        pass

    ticker_up = ticker.upper()
    prompt_builder = TICKER_PROMPT_MAP.get(ticker_up, generic_prompt)
    instruction = prompt_builder(ticker_up, quarter, units, currency, category)

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                    },
                ],
            }
        ],
    )

    raw = resp.choices[0].message.content

    parts = re.split(r'^#+\s*Explanation\b', raw, flags=re.I|re.M) 
    
    if len(parts) == 1:
        parts.append("LLM does not have an explanation.")

    md_table = parts[0].strip()
    explanation = parts[1].strip()

    return md_table, explanation

############ Convert Markdown Table into Python Dictionary List ############
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

def normalize_label(label: str) -> str:
    k = re.sub(r"\s+", " ", label.strip()).casefold()

    if not hasattr(normalize_label, "_syn"):
        normalize_label._syn = {k.casefold(): v for k, v in Synonyms.items()}
    mapped = normalize_label._syn.get(k, label)

    return mapped

def aggregate_standardized(rows):
    if not rows:
        return rows

    agg = defaultdict(float)
    meta = {k: v for k, v in rows[0].items() if k not in ("Line_Item_Name", "Value")}

    for r in rows:
        name = str(r.get("Line_Item_Name", "")).strip()
        if not name or name.lower() == "total cre":
            continue
        normalized = normalize_label(name)

        if normalized not in Standardized_Labels:
            continue
        val = r.get("Value") or 0
        try:
            val = float(val)
        except Exception:
            val = 0
        agg[normalized] += val

    out = []
    for label, val in agg.items():
        out.append({**meta, "Line_Item_Name": label, "Value": int(val)})  # truncate

    total = int(sum(r["Value"] for r in out))
    out.append({**meta, "Line_Item_Name": "Total CRE", "Value": total})

    return out

def rows_from_slices_json_precise(explanation_text, ticker, quarter, units, currency, category):
    m = re.search(r"```json\s*(\{.*?\})\s*```", explanation_text, flags=re.S|re.I)

    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None

    total = Decimal(str(data.get("total_mn", 0)))
    slices = data.get("slices", []) or []

    agg = defaultdict(Decimal)

    for s in slices:
        raw_label = str(s.get("label", "")).strip()
        pct = s.get("percent")

        if pct is None:
            continue

        amt_exact = (total * Decimal(str(pct))) / Decimal(100)
        amt_trunc = amt_exact.quantize(Decimal("1"), rounding=ROUND_DOWN)

        norm = normalize_label(raw_label)
        if norm in Standardized_Labels:
            agg[norm] += amt_trunc

    meta = {"Ticker": ticker, "Quarter": quarter, "Unit": units, "Currency": currency, "Category": category}
    rows = [{**meta, "Line_Item_Name": k, "Value": int(v)} for k, v in agg.items()]
    total_row = int(sum(r["Value"] for r in rows))
    rows.append({**meta, "Line_Item_Name": "Total CRE", "Value": total_row})

    return rows