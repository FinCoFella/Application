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
image_path = "Images/RF/RF_1Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Extract property type labels and their corresponding percentages from this image. "
    f"Then generate a markdown table with the following columns in this exact order: "
    f"Ticker, Quarter, CRE Property Type, Percentage, Units, Currency, Category. "
    f"For each row, include:\n"
    f"- Ticker: {ticker}\n"
    f"- Quarter: {quarter}\n"
    f"- Units: {units}\n"
    f"- Currency: {currency}\n"
    f"- Category: {category}\n"
    f"Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'." 
    f"Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type."
    f"Ensure the final row is labeled 'Total CRE' and shows the sum of the total percentages."
    f"Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'."
    f"The only labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Residential' and 'Other'."
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

percentage_df = pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

percentage_df["Percentage"] = percentage_df["Percentage"].str.rstrip('%').astype(float)

corrections = {
    "Multi-family": 26.4,
    "Office":       9.8,
    "Industrial":  14.5,
    "Retail":       9.1,
    "Lodging":      5.1,
    "Residential":  7.1,
    "Other":       28.0
}

mask = percentage_df["CRE Property Type"].isin(corrections)
percentage_df.loc[mask, "Percentage"] = percentage_df.loc[mask, "CRE Property Type"].map(corrections)

is_total = percentage_df["CRE Property Type"].str.contains("Total", case=False, na=False)
percentage_df.loc[is_total, "Percentage"] = percentage_df.loc[~is_total, "Percentage"].sum()

percentage_df["Percentage"] = percentage_df["Percentage"].map("{:.1f}%".format)

print("\nAdjusted Percentage Table\n")
print(percentage_df.to_markdown(index=False))

loan_amount_df = percentage_df.copy()

loan_amount_df["Loan Amount"] = (
    loan_amount_df["Percentage"]
        .str.rstrip('%').astype(float)
        .div(100)
        .mul(15.4) # Adjust
        .round(2)
)

loan_amount_df = loan_amount_df.drop(columns=["Percentage"])
loan_amount_df["Units"] = "bn"

cols = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Units", "Currency", "Category"]
loan_amount_df = loan_amount_df[cols]

print("\nConverted Loan Amount Table\n")
print(loan_amount_df.to_markdown(index=False))