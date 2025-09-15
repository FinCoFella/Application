import os
import base64
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
image_path = "Images/SNV/SNV_4Q24_CRE.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    Extract property type labels and loan amounts from this image.
    Then generate a markdown table with the following columns in this exact order:
    Ticker, Quarter, CRE Property Type, Loan Amount, Units, Currency, Category.
    For each row, include:
    - Ticker: {ticker}
    - Quarter: {quarter}
    - Units: {units}
    - Currency: {currency}
    - Category: {category}
    Ensure the final row is labeled 'Total CRE' and shows the total loan amount.
    Rename 'Other Investment Properties' into 'Other' and add 'Development & Land' into the single 'Other' property type row.
    Rename 'Office Building' to 'Office', 'Shopping Centers' to 'Retail', 'Hotels' to 'Lodging', 'Warehouse' to 'Industrial', and 'Residential Properties' to 'Residential'.
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

print(completion.choices[0].message.content)