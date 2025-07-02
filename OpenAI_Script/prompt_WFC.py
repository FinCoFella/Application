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

# Adjust
image_path = "Images/WFC/WFC_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

# Adjust prompts for 4Q24 only
instruction_text = (
    f"Extract the property type labels below the 'By property:' row and their corresponding 'Loans oustanding balance' values under the 'Total commercial real estate' section from this image. "
    f"Then generate a markdown table with the following columns in this exact order: "
    f"Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category. "
    f"For each row, include:\n"
    f"- Ticker: {ticker}\n"
    f"- Quarter: {quarter}\n"
    f"- Units: {units}\n"
    f"- Currency: {currency}\n"
    f"- Category: {category}\n"
    f"Ensure the final row is labeled 'Total CRE'."
    f"Combine 'Shopping center' with 'Retail (excl shopping)' into a 'Retail' property type row."
    f"Combine 'Other' with 'Storage facility', 'Mobile home park', and 'Instiutional' into a single 'Other' property type row."
    f"Rename 'Apartments' to 'Multi-family', 'Industrial/warehouse' to 'Industrial', 'Hotel/motel' to 'Lodging', and 'Mixed use properties' to 'Mixed-use'."
    f"Format everything as a clean markdown table."
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

lines = [
    ln for ln in markdown_string.splitlines()
    if ln.lstrip().startswith("|") and "---" not in ln
]
rows = [re.split(r"\s*\|\s*", ln.strip())[1:-1] for ln in lines]

cre_df = pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

cre_df["Loan Amount"] = (
    cre_df["Loan Amount"].str.replace(",", "", regex=False).astype(float))

# Adjust
corrections = {
    "Multi-family": 39_758,
    "Office": 27_380,
    "Industrial": 24_038,
    "Retail": 19_458,
    "Lodging": 11_506,
    "Mixed-use": 2_316,
    "Other": 12_049,
    "Total CRE": 136_505
}

cre_df["Loan Amount"] = (cre_df["CRE Property Type"].map(corrections))

cre_df["Loan Amount"] = (cre_df["Loan Amount"].astype(int).map("{:,}".format))

print("\nAdjusted SQL Table\n")
print(cre_df.to_markdown(index=False))