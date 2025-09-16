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
image_path = "Images/CCI/CCI_3Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

##### LLM prompt instructions to extract financial data and produce a Markdown table #####
prompt = (f"""
    For every row between 'Total secured debt' and 'Total unsecured debt', extract the year from the 'Maturity' column and the number from the 'Unsecured Debt' column in the image in following format:
    | Year | Unsecured Debt |
    |------|--------------- |
    Preserve the order of rows and include a final 'Total Unsecured Debt' row.
    Append the 'Total Secured Debt' row and its Unsecured Debt number after the 'Total Unsecured Debt' row.
    If there is a 'Various' in the 'Maturity' column, rename it to 'Thereafter' and move it before the'Total Unsecured Debt' row.
    Create a 'Total Debt' row at the end to be the sum of the 'Total Secured Debt' and 'Total Unsecured Debt' rows.
    Then create and return a second markdown table that groups the unsecured debt numbers by each unique maturity year, followed by 'Total Secured Debt', 'Total Unsecured Debt' and 'Total Debt'."""
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

###### Extracts and stores a markdown table from the LLM response #####
markdown_table = completion.choices[0].message.content
print("\n ===== Raw Markdown Table =====\n")
print(markdown_table)

##### Parses the markdown table into a DataFrame #####
lines = markdown_table.splitlines()
start = next(i for i,l in enumerate(lines) if re.match(r"^\s*\|\s*Year\s*\|", l))
first_table = []

for line in lines[start:]:
    if not line.strip():
        break
    first_table.append(line)

rows = [re.split(r"\s*\|\s*", l.strip())[1:-1] 
        for l in first_table 
        if "|" in l and "---" not in l]

###### Converts the parsed markdown table into a DataFrame and removes non-digit characters, removes non-numeric rows, and converts the data into numbers #####
df = pd.DataFrame(rows[1:], columns=rows[0])
df["Unsecured_Num"] = (pd.to_numeric(df["Unsecured Debt"].str.replace(r"[^\d]", "", regex=True), errors="coerce"))
df = df.dropna(subset=["Unsecured_Num"])

##### A function that maps a year label into a maturity bucket #####
def bucket(year: str) -> str | None:
    if year == "Thereafter": return "Long-term"
    if year.isdigit():
        yr = int(year)
        if 2024 <= yr <= 2029: 
            return "Near-term"
        if 2030 <= yr <= 2033: 
            return "Medium-term"
        if yr >= 2034:         
            return "Long-term"
    return None

##### Keeps rows with valid years or a 'Thereafter' label #####
detail_df = df.loc[df["Year"].str.match(r"^\d{4}$|^Thereafter$"),["Year", "Unsecured_Num"]].copy()
##### Groups the 'detail' DataFrame by each unique year and sums the values of any duplicate year label into a 'summary' DataFrame #####
summary_df = (detail_df.groupby("Year", as_index=False, sort=False).agg(**{"Unsecured Debt": ("Unsecured_Num", "sum")}))

##### Manually insert override values for specific years #####
manual_overrides: dict[str, int] = {
      "2025": 500,
      "2026": 2_650,
      "2027": 3_382,
      "2028": 2_600,
      "2029": 2_450,
      "2030": 750,
      "2031": 2_850,
      "2033": 750,
      "2034": 1_450,
      "2041": 1_250,
      "2047": 350,
      "2049": 750,
      "2050": 500,
      "2051": 900,
      "Thereafter": 1_312,
      "Total Secured Debt": 1_785,
      "Total Unsecured Debt": 22_444, 
      "Total Debt": 24_229 
}

##### Applies the manual override values to the 'summary' DataFrame #####
for yr, value in manual_overrides.items():
    if yr in summary_df["Year"].values:
        summary_df.loc[summary_df["Year"] == yr, "Unsecured Debt"] = value
    else:
        summary_df.loc[len(summary_df)] = [yr, value]

##### Creates a 'bucket' DataFrame by applying the 'bucket' function to each year label in the 'summary' DataFrame #####
bucket_df = (summary_df.loc[~summary_df["Year"].str.contains("Total", case=False)].assign(Bucket=lambda d: d["Year"].apply(bucket)))
#### Sums the values in the 'bucket' DataFrame by each unique bucket label #####
bucket_sums = (bucket_df.groupby("Bucket", sort=False).agg(Unsecured_Num=("Unsecured Debt", "sum")).reset_index())
#### Sums the values in the 'bucket_sums' DataFrame to calculate a total value and casts it as an integer #####
grand_total = int(bucket_sums["Unsecured_Num"].sum())

##### Creates a new 'debt_buckets' DataFrame by assigning the constant user input values to each row of the 'bucket_sums' DataFrame in new columns #####
debt_buckets = (bucket_sums.assign(Ticker=ticker,
                                  Quarter=quarter,
                                  Unit=units,
                                  Currency=currency,
                                  Category=category).rename(columns={"Bucket": "Unsecured Debt"}))

##### Renames and reorders the columns of the 'debt_buckets' DataFrame and appends a final row to the DataFrame with the total value #####
debt_buckets["Amount"] = debt_buckets["Unsecured_Num"].map("{:,}".format)
debt_buckets = debt_buckets[["Ticker","Quarter","Unsecured Debt","Amount", "Unit","Currency","Category"]]

debt_buckets.loc[len(debt_buckets)] = {
    "Ticker":         ticker,
    "Quarter":        quarter,
    "Unsecured Debt": "Total Unsecured Debt",
    "Amount":         f"{grand_total:,}",
    "Unit":           units,
    "Currency":       currency,
    "Category":       category
}

##### A function that ranks year labels to sort the rows in the DataFrame #####
def rank(label: str) -> int:
    if label.isdigit():
        return int(label)
    if label == "Thereafter":
        return 99_999
    return 1_000_000 

##### Sorts the 'summary' DataFrame by the year rank #####
final_table = summary_df.sort_values(by="Year", key=lambda s: s.map(rank))
final_table["Unsecured Debt"] = final_table["Unsecured Debt"].map("{:,}".format)

print("\n============== Override Table ==============\n")
print(final_table.to_markdown(index=False))

print("\n======================= Unsecured-Debt Buckets =======================")
print(debt_buckets.to_string(index=False))