import os
import re
import base64
import pandas as pd
from pathlib import Path
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
image_path = "Images/PLD/PLD_1Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Extract the values corresponding to the 'Total' and 'Secured Mortgage' columns corresponding to each maturity year from the image. "
    f"Then for each maturity year, take the difference between the 'Total' and 'Secured Mortgage' columns and place the calculated values into a single column called 'Unsecured Debt'. "
    f"Then divide the values of the 'Unsecured Debt' column by 1,000 and place them into the following format without any decimals and round to the nearest whole integer: "
    f"| Year | Unsecured Debt | \n"
    f"|------|--------------- | \n"
    f"Preserve the order of each maturity year and include a 'Total Unsecured Debt' row at the end to sum all the maturity years.\n"
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
print("\n ===== Raw Markdown Table =====\n")
print(markdown_table)

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

df = pd.DataFrame(rows[1:], columns=rows[0])
df.columns = df.columns.str.strip()

df["Unsecured_Num"] = (pd.to_numeric(df["Unsecured Debt"].str.replace(r"[^\d]", "", regex=True), errors="coerce"))
df = df.dropna(subset=["Unsecured_Num"])

def bucket(y: str) -> str | None:
    if y == "Thereafter": 
        return "Long-term"
    if y.isdigit():
        yr = int(y)
        if 2024 <= yr <= 2029: 
            return "Near-term"
        if 2030 <= yr <= 2033: 
            return "Medium-term"
        if yr >= 2034:         
            return "Long-term"
    return None

detail_df = df.loc[df["Year"].str.match(r"^\d{4}$|^Thereafter$"),["Year", "Unsecured_Num"]].copy()
summary_df = (detail_df.groupby("Year", as_index=False, sort=False).agg(**{"Unsecured Debt": ("Unsecured_Num", "sum")}))

# Adjust
manual_overrides: dict[str, int] = {
      "2025": 34,
      "2026": 2_110,
      "2027": 2_528,
      "2028": 3_353,
      "2029": 3_085,
      "2030": 2_827,
      "2031": 2_179,
      "2032": 1_803,
      "2033": 2_462,
      "2034": 2_394,
      "Thereafter": 7_085,
      "Total Unsecured Debt": 29_860,
}

for yr, val in manual_overrides.items():
    if yr in summary_df["Year"].values:
        summary_df.loc[summary_df["Year"] == yr, "Unsecured Debt"] = val
    else:
        summary_df.loc[len(summary_df)] = [yr, val]

bucket_df = (summary_df.loc[~summary_df["Year"].str.contains("Total", case=False)].assign(Bucket=lambda d: d["Year"].apply(bucket)))
bucket_sums = (bucket_df.groupby("Bucket", sort=False).agg(Unsecured_Num=("Unsecured Debt", "sum")).reset_index())
grand_total = int(bucket_sums["Unsecured_Num"].sum())

debt_buckets = (bucket_sums.assign(Ticker=ticker,
                                  Quarter=quarter,
                                  Unit=units,
                                  Currency=currency,
                                  Category=category)
                          .rename(columns={"Bucket": "Unsecured Debt"}))

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

tot_unsec = summary_df["Unsecured Debt"].sum()

def rank(label: str) -> int:
    if label.isdigit():
        return int(label)
    if label == "Thereafter":
        return 99_999
    return 1_000_000 

override_table = (summary_df.copy().sort_values(by="Year", key=lambda s: s.map(rank)))
override_table["Unsecured Debt"] = override_table["Unsecured Debt"].map("{:,}".format)

print("\n============== Override Table ==============\n")
print(override_table.to_markdown(index=False))

print("\n======================= Unsecured-Debt Buckets =======================")
print(debt_buckets.to_string(index=False))

debt_buckets["Amount"] = (debt_buckets["Amount"].str.replace(",", "", regex=False).astype(int))

debt_buckets = (debt_buckets.rename(columns={"Unsecured Debt": "Line_Item_Name", "Amount": "Value"})
      .loc[:, ["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]])

print("\n================================ SQL Format ===============================")
print(debt_buckets.head())

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "PLD_1Q24_unsecured_debt.csv"
debt_buckets.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")