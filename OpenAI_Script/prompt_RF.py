import os
import re
import base64
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

##### Loads environment variables to grab an OpenAI key value to create an OpenAI authenticated client #####
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

ticker = input("Enter the Ticker: ").strip()
quarter = input("Enter the Quarter: ").strip()
units = input("Enter the Units: ").strip()
currency = input("Enter the Currency: ").strip()
category = input("Enter the Category: ").strip()


image_path = "Images/RF/RF_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

prompt = (f"""
    Carefully read and execute the following instructions:
    Extract the property type labels and loan amounts from this image, then output a markdown table with columns:
        Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'.
    Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type.
    Then multiply each percentage by property type by the dollar amount value in the center of the pie chart to determine the loan amount by property type.
    Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'.
    The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Residential' and 'Other'.
    Ensure that the final row is labeled 'Total CRE' in 'Property Type' column and shows the total loan amount.
    Truncate the decimal and divide by 1000.
    - Ticker: {ticker}
    - Quarter: {quarter}
    - Units: {units}
    - Currency: {currency}
    - Category: {category}"""
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", "text": prompt},
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

# Adjust
corrections = {
    "Multi-family": 4_376,
    "Office":       1_469,
    "Industrial":  2_295,
    "Retail":       1_454,
    "Lodging":      780,
    "Residential":  1_148,
    "Other":       3_779
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

print("\nOverride Table\n")
print(df[final_cols].to_markdown(index=False))