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
image_path = "Images/JPM/JPM_1Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
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

##### Sends the prompt and Base64 image URL to the LLM, which decodes the text string into pixels and processes the image and prompt #####
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

###### Extracts and stores a markdown table from the LLM response #####
markdown_string = response.choices[0].message.content.strip()
print("\n ====== Raw Markdown Table ===== \n")
print(markdown_string)

##### Parses the markdown table into a DataFrame #####
lines = [
    ln for ln in markdown_string.splitlines()
    if ln.lstrip().startswith("|") and "---" not in ln
]
rows = [re.split(r"\s*\|\s*", ln.strip())[1:-1] for ln in lines]
df = pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

##### Manually insert override values for specific CRE property type labels #####
corrections = {
    "Multi-family": 110_530,
    "Office": 13_366,
    "Industrial": 14_241,
    "Other": 17_320,
    "Retail": 9_058,
    "Lodging": 2_406,
    "Total CRE": 166_920
}

##### Removes commas in the 'Loan Amount' column and converts the column to a float data type #####
df["Loan Amount"] = (df["Loan Amount"].str.replace(",", "", regex=False).astype(float))
##### Applies the manual override values to the 'CRE Property Type' rows in the DataFrame #####
df["Loan Amount"] = (df["CRE Property Type"].map(corrections).fillna(df["Loan Amount"]))

##### Recalculates the total loan amount value for the 'Total CRE' row in the DataFrame #####
total = df["CRE Property Type"].str.contains("Total", case=False, na=False)
df.loc[total, "Loan Amount"] = df.loc[~total, "Loan Amount"].sum()

##### Formats the 'Loan Amount' column to have commas to separate thousands but no decimals, and keeps only the specified columns in the specified order #####
df["Loan Amount"] = df["Loan Amount"].round().astype(int).map("{:,}".format)
df = df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Units", "Currency", "Category"]]

print("\n ===== Override Table ===== \n")
print(df.to_markdown(index=False))