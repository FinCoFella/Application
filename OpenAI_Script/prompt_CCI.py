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
image_path = "Images/CCI/CCI_1Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"For every row between 'Total secured debt' and 'Total unsecured debt', extract the year from the 'Maturity' column and the number from the 'Unsecured Debt' column in the image in following format: "
    f"| Year | Unsecured Debt | \n"
    f"|------|--------------- | \n"
    f"Preserve the order of rows and include a final 'Total Unsecured Debt' row.\n"
    f"Append the 'Total Secured Debt' row and its Unsecured Debt number after the 'Total Unsecured Debt' row.\n"
    f"If there is a 'Various' in the 'Maturity' column, rename it to 'Thereafter' and move it before the'Total Unsecured Debt' row.\n"
    f"Create a 'Total Unsecured Debt' row at the end to be the sume of the 'Total Secured Debt' and 'Total Unsecured Debt' rows.\n"
    f"Then create and return a second markdown table that groups the Unsecured Debt numbers by each unique maturity year, followed by 'Total Secured Debt', 'Total Unsecured Debt' and 'Total Debt'."
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
tot_secured = int(df.loc[df["Year"].str.contains("Total Secured", case=False),"Unsecured_Num"].iloc[0])
tot_debt = tot_unsec + tot_secured

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