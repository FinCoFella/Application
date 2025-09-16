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
image_path = "Images/AVB/AVB_4Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    Extract the tabular data from this image in the following format: .
    | Year | Unsecured Debt |
    |------|--------------- |
    Divide the extracted values by 1000 and place the adjusted values into the markdown table.
    Preserve the order of rows and include a final 'Total Unsecured Debt' row."""
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
print("\nRaw Markdown Table:\n")
print(markdown_table)

lines = markdown_table.strip().split('\n')
rows = [re.split(r'\s*\|\s*', row.strip())[1:-1] for row in lines if "|" in row and "---" not in row]
df = pd.DataFrame(rows[1:], columns=rows[0])

# Adjust
manual_overrides: dict[str, int] = {
    "2025": 825,
    "2026": 775,
    "2027": 400,
    "2028": 850,
    "2029": 450,
    "2030": 700,
    "2031": 600,
    "2032": 700,
    "2033": 750,
    "2034": 400,
    "Thereafter": 950,
    "Total Unsecured Debt": 7_400,
}

df["Unsecured Debt"] = df["Year"].map(manual_overrides)

unsecured_debt_df = df.copy()
unsecured_debt_df = unsecured_debt_df[~unsecured_debt_df["Year"].str.contains("Total", case=False, na=False)]
unsecured_debt_df["Unsecured_Num"] = unsecured_debt_df["Year"].map(manual_overrides).astype(float)

df = df[["Year", "Unsecured Debt"]]

print("\nFinal Adjusted Table:\n")
print(df.to_markdown(index=False))

def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    if year.isdigit():                 
        yr = int(year)
        if 2024 <= yr <= 2029:
            return "Near-term"
        if 2030 <= yr <= 2033:
            return "Medium-term"
        if yr == 2034:
            return "Long-term"
    return "Other"

unsecured_debt_df["Bucket"] = unsecured_debt_df["Year"].apply(bucket)
df_work = unsecured_debt_df.dropna(subset=["Bucket"])
bucket_sums = (df_work.groupby("Bucket", sort=False, as_index=False).agg({"Unsecured_Num": "sum"}))

grand_total = bucket_sums["Unsecured_Num"].sum()

total_row = {
    "Ticker":   ticker,
    "Quarter":  quarter,
    "Unsecured Debt": "Total Unsecured Debt",
    "Amount":   f"{int(grand_total):,}",
    "Unit":     units,
    "Currency": currency,
    "Category": category
}

debt_buckets_df = pd.DataFrame({
    "Ticker":         ticker,
    "Quarter":        quarter,
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":         bucket_sums["Unsecured_Num"].astype(int).map("{:,}".format),
    "Unit":           units,
    "Currency":       currency,
    "Category":       category 
})

debt_buckets_df.loc[len(debt_buckets_df)] = total_row 

print("\n====================== Unsecured Debt Buckets =========================")
print(debt_buckets_df.to_string(index=False))
