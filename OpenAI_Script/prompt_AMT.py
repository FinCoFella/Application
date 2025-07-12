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
image_path = "Images/AMT/AMT_1Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Extract the values corresponding to the 'Senior Notes' grey label in each bar column corresponding to each maturity year. Then place the values into the following format: "
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

df["Unsecured_Num"] = (pd.to_numeric(
    df["Unsecured Debt"]
        .str.replace(r"[^\d]", "", regex=True),
    errors="coerce")
)

df = df.dropna(subset=["Unsecured_Num"])

def bucket(y: str) -> str | None:
    if y == "Thereafter": return "Long-term"
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
      "2024": 650,
      "2025": 3_189,
      "2026": 3_339,
      "2027": 4_546,
      "2028": 4_259,
      "2029": 3_709,
      "2030": 2_839,
      "2031": 1_939,
      "2032": 1_351,
      "2033": 2_939,
      "2034": 650,
      "2049": 600,
      "2050": 1_050,
      "2051": 1_050,
      "Total Unsecured Debt": 32_110,
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

def _rank(label: str) -> int:
    if label.isdigit():
        return int(label)
    if label == "Thereafter":
        return 99_999
    return 1_000_000 

final_table = (pd.concat([summary_df], ignore_index=True).sort_values(by="Year", key=lambda s: s.map(_rank)))
final_table["Unsecured Debt"] = final_table["Unsecured Debt"].map("{:,}".format)

print("\n============== Override Table ==============\n")
print(final_table.to_markdown(index=False))

print("\n======================= Unsecured-Debt Buckets =======================")
print(debt_buckets.to_string(index=False))