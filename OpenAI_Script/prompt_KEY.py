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

image_path = "Images/KEY/KEY_3Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Extract property type labels and loan amounts from the total column in this image. "
    f"Revise the table by adding 'Medical Office' into the single 'Office' property type label."
    f"Revise the table by adding 'Diversified' into 'Other', add 'Data Center' into 'Other', add 'Land & Residential' into 'Other', add 'Self Storage' into 'Other', add 'Senior Housing' into 'Other', add 'Skilled Nursing' into 'Other', and add 'Student Housing' into 'Other'."
    f"Include a final row and label it 'Total CRE' and shows the total loan amount."
    f"Then generate a markdown table with the following columns in this exact order: "
    f"Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category. "
    f"For each row, include:\n"
    f"- Ticker: {ticker}\n"
    f"- Quarter: {quarter}\n"
    f"- Units: {units}\n"
    f"- Currency: {currency}\n"
    f"- Category: {category}\n"
    f"Rename 'Multifamily' to 'Multi-family'."
    f"Format everything as a clean markdown table."
)

completion = client.chat.completions.create(
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

markdown_table = completion.choices[0].message.content
print("\nRaw Markdown Table:\n")
print(markdown_table)

lines = markdown_table.strip().split('\n')
rows = [re.split(r'\s*\|\s*', row.strip())[1:-1] for row in lines if "|" in row and "---" not in row]
df = pd.DataFrame(rows[1:], columns=rows[0])

corrections = {
    "Multi-family": "8010",    
    "Office": "1009",
    "Industrial": "733",
    "Retail": "880",
    "Lodging": "234",
    "Other": "2138"
}

df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"] = (
    df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "CRE Property Type"]
    .map(corrections)
)

df.loc[df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"] = (
    df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"]
    .astype(float).sum()
)

df["Loan Amount"] = df["Loan Amount"].astype(float).apply(lambda x: f"{x:,.0f}")

print("\nAdjusted Table:\n")
print(df.to_markdown(index=False))