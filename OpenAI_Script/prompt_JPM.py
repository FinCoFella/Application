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


image_path = "Images/JPM/JPM_1Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

prompt = (f"""
    Extract the property type labels, their corresponding values in the 'Credit Exposure' column, and the '% Drawn' column from this image.
    Then multiply the values in '% Drawn' column with the values in th 'Credit Exposure' column and place the product in a 'Loan Amount' column. 
    Generate a markdown table with the following columns in this exact order:
    Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    For each row, include:\n
    - Ticker: {ticker}\n
    - Quarter: {quarter}\n
    - Units: {units}\n
    - Currency: {currency}\n
    - Category: {category}\n
    Combine 'Other Income Producing Properties' and 'Services and Non Income Producing' into a single 'Other' property type row
    Ensure the final row is labeled 'Total CRE' and format the numbers in the 'Loan Amount' column to have commas to separate thousands but no decimals.
    Rename 'Multifamily' to 'Multi-family'.
    Format everything as a clean markdown table."""
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

lines = [
    ln for ln in markdown_string.splitlines()
    if ln.lstrip().startswith("|") and "---" not in ln
]

rows = [re.split(r"\s*\|\s*", ln.strip())[1:-1] for ln in lines]
df = pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

corrections = {
    "Multi-family": 110_530,
    "Office":       13_366,
    "Industrial":  14_241,
    "Other": 17_320,
    "Retail": 9_058,
    "Lodging": 2_406,
    "Total CRE": 166_920
}

df["Loan Amount"] = (df["Loan Amount"].str.replace(",", "", regex=False).astype(float))
df["Loan Amount"] = (df["CRE Property Type"].map(corrections).fillna(df["Loan Amount"]))

total = df["CRE Property Type"].str.contains("Total", case=False, na=False)
df.loc[total, "Loan Amount"] = df.loc[~total, "Loan Amount"].sum()

df["Loan Amount"] = df["Loan Amount"].round().astype(int).map("{:,}".format)
df = df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Units", "Currency", "Category"]]

print("\nOverride Table\n")
print(df.to_markdown(index=False))