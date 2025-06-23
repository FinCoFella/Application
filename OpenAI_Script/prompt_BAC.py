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

instruction_text = (
    f"Extract property type labels and loan amounts from this image. "
    f"Then generate a markdown table with the following columns in this exact order: "
    f"Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category. "
    f"For each row, include:\n"
    f"- Ticker: {ticker}\n"
    f"- Quarter: {quarter}\n"
    f"- Units: {units}\n"
    f"- Currency: {currency}\n"
    f"- Category: {category}\n"
    f"Ensure the final row is labeled 'Total CRE' and shows the total loan amount. "
    f"Rename 'Industrial / Warehouse' to 'Industrial', 'Multi-family rental' to 'Multi-family', 'Shopping centers / Retail' to 'Retail', 'Hotel / Motels' to 'Lodging', and 'Multi-use' to 'Mixed-use'. "
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
    "Office": "15.1",
    "Multi-family": "11.0",
    "Industrial": "13.2",
    "Residential": "0.9",
    "Retail": "5.6",
    "Lodging": "4.7",
    "Mixed-use": "2.2",
    "Other": "13.2"
}

df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"] = (
    df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "CRE Property Type"]
    .map(corrections)
)

df.loc[df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"] = (
    df.loc[~df["CRE Property Type"].str.contains("Total", case=False), "Loan Amount"]
    .astype(float).sum()
)

print("\nAdjusted Table:\n")
print(df.to_markdown(index=False))