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

##### Collects user input and stores the entered data into variables #####
ticker = input("Enter the Ticker: ").strip()
quarter = input("Enter the Quarter: ").strip()
units = input("Enter the Units: ").strip()
currency = input("Enter the Currency: ").strip()
category = input("Enter the Category: ").strip()

##### Establishes a file path to the image in the repository and encodes the raw bytes of the image into a Base64 text string #####
image_path = "Images/KEY/KEY_3Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    Extract property type labels and loan amounts from the total column in this image.
    Revise the table by adding 'Medical Office' into the single 'Office' property type label.
    Revise the table by adding 'Diversified' into 'Other', add 'Data Center' into 'Other', add 'Land & Residential' into 'Other', add 'Self Storage' into 'Other', add 'Senior Housing' into 'Other', add 'Skilled Nursing' into 'Other', and add 'Student Housing' into 'Other'.
    Include a final row and label it 'Total CRE' and shows the total loan amount.
    Then generate a markdown table with the following columns in this exact order:
    Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    For each row, include:\n
    - Ticker: {ticker}\n
    - Quarter: {quarter}\n
    - Units: {units}\n
    - Currency: {currency}\n
    - Category: {category}\n
    Rename 'Multifamily' to 'Multi-family'.
    Format everything as a clean markdown table."""
)

##### Sends the prompt and Base64 image URL to the LLM, which decodes the text string into pixels and processes the image and prompt #####
completion = client.chat.completions.create(
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

markdown_table = completion.choices[0].message.content
print("\n ===== Raw Markdown Table ===== \n")
print(markdown_table)

lines = markdown_table.strip().split('\n')
rows = [re.split(r'\s*\|\s*', row.strip())[1:-1] for row in lines if "|" in row and "---" not in row]
df = pd.DataFrame(rows[1:], columns=rows[0])

corrections = {
    "Multi-family": 8_010,    
    "Office": 1_009,
    "Industrial": 733,
    "Retail": 880,
    "Lodging": 234,
    "Other": 2_138
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

print("\n ===== Override Table ===== \n")
print(df.to_markdown(index=False))