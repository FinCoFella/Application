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
image_path = "Images/WFC/WFC_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    Extract the property type labels below the 'By property:' row and their corresponding 'Loans oustanding balance' values under the 'Total commercial real estate' section from this image.
    Then generate a markdown table with the following columns in this exact order:
    Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    For each row, include:
    - Ticker: {ticker}
    - Quarter: {quarter}
    - Units: {units}
    - Currency: {currency}
    - Category: {category}
    Ensure the final row is labeled 'Total CRE'.
    Combine 'Shopping center' with 'Retail (excl shopping)' into a 'Retail' property type row.
    Combine 'Other' with 'Storage facility', 'Mobile home park', and 'Instiutional' into a single 'Other' property type row.
    Rename 'Apartments' to 'Multi-family', 'Industrial/warehouse' to 'Industrial', 'Hotel/motel' to 'Lodging', and 'Mixed use properties' to 'Mixed-use'.
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
print("\n ===== Raw Markdown Table ===== \n")
print(markdown_string)

##### Parses the markdown table into a DataFrame #####
lines = [
    ln for ln in markdown_string.splitlines()
    if ln.lstrip().startswith("|") and "---" not in ln
]
rows = [re.split(r"\s*\|\s*", ln.strip())[1:-1] for ln in lines]

##### Converts the list of rows into a pandas DataFrame and assigns column headers #####
df = pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

##### Formats the 'Loan Amount' column by removing commas and converting the values to floats #####
df["Loan Amount"] = (df["Loan Amount"].str.replace(",", "", regex=False).astype(float))

##### Manually insert override values for specific CRE property type labels #####
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

##### Applies the manual override values to the 'Loan Amount' column in the DataFrame #####
df["Loan Amount"] = (df["CRE Property Type"].map(corrections))
##### Format the 'Loan Amount' column with commas for thousands separators #####
df["Loan Amount"] = (df["Loan Amount"].astype(int).map("{:,}".format))

print("\n ===== Override Table ===== \n")
print(df.to_markdown(index=False))