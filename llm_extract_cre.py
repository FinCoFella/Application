import base64, tempfile, os, re
from typing import Dict, Callable
from collections import defaultdict
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cfg_prompt(ticker, quarter, units, currency, category) -> str: 
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n" 
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Merge 'Other general office' and 'Credit tenant lease and life sciences' into 'Office'.\n"
        f"Merge 'Other', 'Co‑op', and 'Data Center' into 'Other'.\n"
        f"Rename 'Hospitality' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def bac_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Industrial / Warehouse' to 'Industrial', 'Multi-family rental' to 'Multi-family', 'Shopping centers / Retail' to 'Retail', 'Hotel / Motels' to 'Lodging', and 'Multi-use' to 'Mixed-use'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def jpm_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels, their corresponding values in the 'Credit Exposure' column, and the '% Drawn' column from this image.\n"
        f"Then multiply the values in '% Drawn' column with the values in th 'Credit Exposure' column and place the product in a 'Loan Amount' column.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Other Income Producing Properties' and 'Services and Non Income Producing' into a single 'Other' property type row.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def wfc_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels below the 'By property:' column and their corresponding 'Loans oustanding balance' values under the 'Total commercial real estate' section from this image.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Shopping center' with 'Retail (excl shopping)' into a 'Retail' property type row.\n"
        f"Combine 'Other' with 'Storage facility', 'Mobile home park', and 'Instiutional' into a single 'Other' property type row.\n"
        f"Rename 'Apartments' to 'Multi-family', 'Industrial/warehouse' to 'Industrial', 'Hotel/motel' to 'Lodging', and 'Mixed use properties' to 'Mixed-use'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def key_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels below the 'Nonowner-occupied' column and their corresponding values in the 'Total' column from this image.\n"
        f"Generate a markdown table with the following columns in this exact order:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine the 'Medical Office' value with the 'Office' value into a single 'Office' property type.\n"
        f"Combine 'Diversified' into 'Other', add 'Data Center' into 'Other', add 'Land & Residential' into 'Other', add 'Self Storage' into 'Other', add 'Senior Housing' into 'Other', add 'Skilled Nursing' into 'Other', and add 'Student Housing' into 'Other'.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"        
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def hban_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Multifamily' to 'Multi-family'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def snv_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Rename 'Other Investment Properties' into 'Other' and add 'Development & Land' into the single 'Other' property type row.\n"
        f"Rename 'Office Building' to 'Office', 'Shopping Centers' to 'Retail', 'Hotels' to 'Lodging', 'Warehouse' to 'Industrial', and 'Residential Properties' to 'Residential'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def fcnca_prompt(ticker, quarter, units, currency, category) -> str:
       return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Medical Office' and 'General Office' values into a single 'Office' property type row.\n"
        f"Rename 'Hotel/Motel' to 'Lodging' and 'Industrial / Warehouse' to 'Industrial'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def pnc_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Combine 'Seniors Housing' into the 'Other' property type row.'\n"
        f"Rename 'Industrial / Warehouse' to 'Industrial', 'Multifamily' to 'Multi-family', 'Mixed Use' to 'Mixed-use', and 'Hotel / Motel' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def rf_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        f"Carefully read and execute the following instructions:\n"
        f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        f"Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'.\n" 
        f"Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type.\n"
        f"Then multiply each percentage by property type by the dollar amount value in the center of the pie chart to determine the loan amount by property type.\n"
        f"Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'.\n"
        f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Mixed-use', 'Residential' and 'Other'.\n"
        f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
        f"Divide the values by 1000.\n"
        f"Truncate the trailing decimal value.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

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

    return f""" Extract CRE exposure from the image and exactly follow the rules below:

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
    - The `percent_sum` must be **100**. Re-read ambiguous or small slices and minimally correct to reach 100.

    EXTRACT
    1) Read the total dollar amount in the center of the pie chart, which is the total loan amount for all property types.
    2) Then read all property type labels and their corresponding loan amounts from the image, and if the values are percentages: 
        - If a slice shows a percentage, multiply *each* one by the total dollar amount given in center of the pie chart.
    3) If the values are in a table, follow these rules:
        - If the table contains a 'Credit exposure' and '% Drawn' column, multiply the values from the 'Credit exposure' and '% Drawn" to calculate the loan amount.
        - If the table contains a 'Loans outstanding balance' column, use those values as the loan amounts for each property type label.
        - If the table contains a 'Total' column of amounts by type, use those values as the loan amounts for each property type label.

    CONVERT UNITS
    4) If the values are in billions (e.g., '0.0'), multiply the value by 1000 to convert it into millions.

    NORMALIZE LABELS
    5) USe the following case-insensitive mapping to normalize the labels {syn_labels} and keep only these final labels: {stnd_labels}.

    AGGREGATE
    6) After normalizing the property type lables, **sum the amounts that map to the same final label within {stnd_labels}**. 

    FORMAT 
    7) After aggregating the loan amount values, **truncate the trailing decimal values** in the 'Loan Amount' column to an integer to remove decimals.

    APPLY USER INPUT
    8) Produce only one markdown table that uses the following constant values:
        - Ticker: {ticker}\n"
        - Quarter: {quarter}\n"
        - Units: {units}\n"
        - Currency: {currency}\n"
        - Category: {category}\n"

    AUDIT
    9) In the '### Explanation', describe how the labels were normalized and how the total loan amount was calculated.
    It should include an equation used to calculate the 'Other' property type. The explanation should be less than 200 words."""

PROMPT_MAP: Dict[str, Callable[[str, str, str, str, str],str]] = {
    # "CFG": cfg_prompt,
    # "BAC": bac_prompt,
    # "JPM": jpm_prompt,
    # "WFC": wfc_prompt,
    # "KEY": key_prompt,
    # "HBAN": hban_prompt,
    # "SNV": snv_prompt,
    # "FCNCA": fcnca_prompt,
    # "PNC": pnc_prompt,
    # "RF": rf_prompt,
}

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
    prompt_builder = PROMPT_MAP.get(ticker_up, generic_prompt)
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