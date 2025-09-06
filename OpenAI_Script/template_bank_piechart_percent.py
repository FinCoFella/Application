import os
import re
import base64
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

ticker = input("Enter the Ticker: ").strip()
quarter = input("Enter the Quarter: ").strip()
units = input("Enter the Units: ").strip()
currency = input("Enter the Currency: ").strip()
category = input("Enter the Category: ").strip()

image_path = "Images/BAC/BAC_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

generic_prompt = f"""
EXTRACTION STAGE
1) Extract the property type labels and loan amount values from the pie chart image. 

STANDARDIZATION STAGE
2) Read the dollar amount in the center of the pie chart and convert it into millions by multiplying it by 1000. 
3) Multiply each slice's percentage value with the dollar amount in millions to calculate the loan amount of each property type label. 
4) Standardize the labels by changing 'Industrial / Warehouse' to 'Industrial', 'Multi-family rental' to 'Multi-family', 'Shopping centers / Retail' to 'Retail', 'Hotel / Motels' to 'Lodging', and 'Multi-use' to 'Mixed-use'. 
5) Aggregate the loan amount values based on the following eight standardized labels: 'Industrial', 'Lodging', 'Multi-family', 'Office', 'Residential', 'Retail', 'Mixed-use', and 'Other'.
6) Create a new label called 'Total CRE' which calculates the sum of all the loan amount values of the eight standardized labels. 

RAW MARKDOWN STAGE
7) Using the standardized labels and aggregated values, return one markdown table in the exact order below with the subsequent constant parameter values from user input: 
    | Ticker | Quarter | CRE Property Type | Loan Amount | Units | Currency | Category | 

- Ticker: {ticker}
- Quarter: {quarter}
- Units: {units}
- Currency: {currency}
- Category: {category}
"""

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": generic_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                },
            ],
        }
    ],
)

markdown_table = completion.choices[0].message.content or ""
print("\n LLM API Raw Markdown Table:\n")
print(markdown_table)

#####################################################################################

lines = [ln for ln in markdown_table.strip().splitlines() if "|" in ln]
lines = [ln for ln in lines if not re.search(r'^\s*\|\s*:?-{3,}', ln)]

if not lines:
    raise ValueError("No markdown table detected.")

rows = [re.split(r'\s*\|\s*', ln.strip())[1:-1] for ln in lines]

header, data_rows = rows[0], rows[1:]
header = [h.strip() for h in header]

df = pd.DataFrame(data_rows, columns=header)
df.columns = [c.strip() for c in df.columns]

df["CRE Property Type"] = df["CRE Property Type"].astype(str).str.strip()
df["Loan Amount"] = df["Loan Amount"].astype(str).str.strip()

manual_corrections = {
    "Office": 15_100,
    "Multi-family": 11_000,
    "Industrial": 13_200,
    "Residential": 900,
    "Retail": 5_600,
    "Lodging": 4_700,
    "Mixed-use": 2_200,
    "Other": 13_200,
}

if manual_corrections:
    non_total_mask = ~df["CRE Property Type"].str.contains("Total", case=False, na=False)
    df.loc[non_total_mask, "Loan Amount"] = (
        df.loc[non_total_mask, "CRE Property Type"].map(manual_corrections).fillna(df.loc[non_total_mask, "Loan Amount"])
    )

    if df["CRE Property Type"].str.contains("Total", case=False, na=False).any():
        total_mask = df["CRE Property Type"].str.contains("Total", case=False, na=False)
        subtotal = (
            df.loc[~total_mask, "Loan Amount"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .astype(float)
            .sum()
        )
        df.loc[total_mask, "Loan Amount"] = subtotal

df["Loan Amount"] = pd.to_numeric(df["Loan Amount"].astype(str).str.replace(",", "", regex=False),errors="coerce")
df["Loan Amount"] = df["Loan Amount"].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "")

print("\nOverride Table:\n")
print(df.to_markdown(index=False))