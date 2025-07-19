import os
import re
import base64
import pandas as pd
import math
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

# Adjust
image_path = "Images/RF/RF_3Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Carefully read and execute the following instructions:\n"
    f"Extract the property type labels and loan amounts from this image, then output a markdown table with columns:\n"
        "Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.\n"
    f"Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'.\n" 
    f"Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type.\n"
    f"Then multiply each percentage by property type by the dollar amount value in the center of the pie chart to determine the loan amount by property type.\n"
    f"Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'.\n"
    f"The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Residential' and 'Other'.\n"
    f"Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.\n"
    f"Truncate the decimal and divide by 1000.\n"
    f"- Ticker: {ticker}\n"
    f"- Quarter: {quarter}\n"
    f"- Units: {units}\n"
    f"- Currency: {currency}\n"
    f"- Category: {category}"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", "text": instruction_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
)

markdown_string = response.choices[0].message.content.strip()
print("\nRaw Markdown Table:\n")
print(markdown_string)

lines = [ln for ln in markdown_string.splitlines() if ln.strip().startswith("|")]
rows = [re.split(r"\s*\|\s*", ln.strip())[1:-1] for ln in lines]
data_lines = [ln for ln in lines if "---" not in ln]
header = [c.strip() for c in data_lines[0].strip("|").split("|")]

rows = [
    [c.strip() for c in ln.strip().strip("|").split("|")]
    for ln in data_lines[1:]
]

df = pd.DataFrame(rows, columns=header)
required_cols = {"Ticker","Quarter","CRE Property Type","Loan Amount","Units","Currency","Category"}

missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing expected columns: {missing}. Got columns: {list(df.columns)}")

def parse_numeric(val):
    if pd.isna(val):
        return float("nan")
    s = str(val).replace(",", " ").strip()
    m = re.search(r"-?\d+(?:\.\d+)?", s.replace(" ", ""))
    return float(m.group()) if m else float("nan")

df["Loan Amount"] = df["Loan Amount"].apply(parse_numeric)

corrections = {
    "Multi-family": 4_235,
    "Office":       1_555,
    "Industrial":  2_233,
    "Retail":       1_371,
    "Lodging":      801,
    "Residential":  1_217,
    "Other":       3_989
}

df.set_index("CRE Property Type", inplace=True)
corrections_df = pd.Series(corrections, name="Loan Amount").to_frame()
df.update(corrections_df) 
df.reset_index(inplace=True)

missing_rows = (
    pd.Series(corrections)
    .drop(index=df["CRE Property Type"], errors="ignore")
    .reset_index()
    .rename(columns={"index": "CRE Property Type", 0: "Loan Amount"})
)

if not missing_rows.empty:
    missing_rows["Ticker"] = ticker
    missing_rows["Quarter"] = quarter
    missing_rows["Units"] = units
    missing_rows["Currency"] = currency
    missing_rows["Category"] = category
    df = pd.concat([df, missing_rows], ignore_index=True)

is_total = df["CRE Property Type"].str.contains("Total", case=False, na=False)

if is_total.any():
    df.loc[is_total, "Loan Amount"] = df.loc[~is_total, "Loan Amount"].sum()
else:
    total_row = {
        "Ticker": ticker,
        "Quarter": quarter,
        "CRE Property Type": "Total CRE",
        "Loan Amount": df["Loan Amount"].sum(),
        "Units": units,
        "Currency": currency,
        "Category": category,
    }
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

final_cols = ["Ticker","Quarter","CRE Property Type","Loan Amount","Units","Currency","Category"]

print("\nAdjusted Table\n")
print(df[final_cols].to_markdown(index=False))