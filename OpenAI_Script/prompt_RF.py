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
image_path = "Images/RF/RF_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    Carefully read and execute the following instructions:
    Extract the property type labels and loan amounts from this image, then output a markdown table with columns:
        Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    Add the percentages from 'Residential homebuilders' and 'Residential land' into 'Residential'.
    Add the percentages of 'Data center', 'Diversified', 'Healthcare', 'Commercial land', 'Other', and 'Self storage' into the single 'Other' property type.
    Then multiply each percentage by property type by the dollar amount value in the center of the pie chart to determine the loan amount by property type.
    Rename 'Apartments' to 'Multi-family' and 'Hotel' to 'Lodging'.
    The only property type labels in the table should be 'Multi-family', 'Industrial', 'Lodging', 'Office', 'Retail', 'Residential' and 'Other'.
    Ensure that the final row is labeled 'Total CRE' in 'CRE Property Type' column and shows the total loan amount.
    Truncate the decimal and divide by 1000.
    - Ticker: {ticker}
    - Quarter: {quarter}
    - Units: {units}
    - Currency: {currency}
    - Category: {category}"""
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

##### Parses the markdown table string into a pandas DataFrame #####
lines = [line for line in markdown_string.splitlines() if line.strip().startswith("|")]
rows = [re.split(r"\s*\|\s*", line.strip())[1:-1] for line in lines]
data_lines = [line for line in lines if "---" not in line]
header = [cell.strip() for cell in data_lines[0].strip("|").split("|")]
rows = [
    [cell.strip() for cell in line.strip().strip("|").split("|")]
    for line in data_lines[1:]
]
df = pd.DataFrame(rows, columns=header)

##### Manually insert override values for specific CRE property type labels #####
corrections = {
    "Multi-family": 4_376,
    "Office": 1_469,
    "Industrial": 2_295,
    "Retail": 1_454,
    "Lodging": 780,
    "Residential": 1_148,
    "Other": 3_779
}

##### Applies the manual override values to the corresponding 'CRE Property Type' rows and adds a new 'Loan Amount' column in the DataFrame #####
df.set_index("CRE Property Type", inplace=True)
corrections_df = pd.Series(corrections, name="Loan Amount").to_frame()
df = df.drop(columns=['Loan Amount'], errors='ignore').join(corrections_df, how='left')
df.update(corrections_df)
df.reset_index(inplace=True)

##### Boolean mask to identify a 'Total CRE' row #####
is_total = df["CRE Property Type"].str.contains("Total", case=False, na=False)

##### If a 'Total CRE' row exists, update its 'Loan Amount' with the sum of other rows; otherwise, append a new 'Total CRE' row #####
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

##### Reorder the columns in the DataFrame #####
final_cols = ["Ticker","Quarter","CRE Property Type","Loan Amount","Units","Currency","Category"]

print("\n ===== Override Table ===== \n")
print(df[final_cols].to_markdown(index=False))