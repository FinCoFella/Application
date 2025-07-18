import base64, tempfile, os
from typing import Dict, Callable
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cfg_prompt(ticker, quarter, units, currency, category) -> str: 
    return (
        "Extract the property type labels and loan amounts from this image, then output a markdown table with columns: " 
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        "Merge 'Other general office' and 'Credit tenant lease and life sciences' into 'Office'.\n"
        "Merge 'Other', 'Co‑op', and 'Data Center' into 'Other'.\n"
        "Rename 'Hospitality' to 'Lodging'.\n"
        "Ensure the final row is labeled 'Total CRE' and shows the total loan amount.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

def bac_prompt(ticker, quarter, units, currency, category) -> str:
    return (
        "Extract the property type labels and loan amounts from this image, then output a markdown table with columns: "
            "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
        "Rename 'Industrial / Warehouse' to 'Industrial', "
        "'Multi-family rental' to 'Multi-family', "
        "'Shopping centers / Retail' to 'Retail', "
        "'Hotel / Motels' to 'Lodging', "
        "and 'Multi-use' to 'Mixed-use'. "
        "Ensure the final row is labeled 'Total CRE' and shows the total loan amount.\n"
        f"- Ticker: {ticker}\n"
        f"- Quarter: {quarter}\n"
        f"- Units: {units}\n"
        f"- Currency: {currency}\n"
        f"- Category: {category}"
    )

PROMPT_MAP: Dict[str, Callable[[str, str, str, str, str],str]] = {
    "CFG": cfg_prompt,
    "BAC": bac_prompt,
}

############ Extract Data into Markdown Table ############
def extract_cre_table(image_file, ticker: str, quarter: str, units: str, currency: str, category: str) -> str:
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image_file.save(tmp.name)
        with open(tmp.name, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

    ticker_up = ticker.upper()
    prompt_builder = PROMPT_MAP.get(ticker_up, cfg_prompt)
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
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )

    return resp.choices[0].message.content

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