import tabula
import pandas as pd
from pathlib import Path
import re

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/PLD/PLD_3Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=25, multiple_tables=True, stream=True, pandas_options={"header": None})

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")

debt_maturity_df = tables[0]

debt_maturity_df = (debt_maturity_df.loc[30:36, [0, 6]].reset_index(drop=True))
debt_maturity_df[0] = (debt_maturity_df[0].astype(str).str.extract(r'(\d{4}|Thereafter|Subtotal)')[0]).replace("Subtotal", "Total")

total_col = (debt_maturity_df[6].astype(str).str.replace(r'[\$,()]', '', regex=True).str.strip().str.split(expand=True).iloc[:, :2].apply(pd.to_numeric, errors='coerce'))
total_col.columns = ["Secured Debt", "Total Debt"]

debt_maturity_df = (pd.concat([debt_maturity_df[[0]], total_col], axis=1).rename(columns={0: "Year"}))
debt_maturity_df[["Secured Debt", "Total Debt"]] = (debt_maturity_df[["Secured Debt", "Total Debt"]].div(1_000).round(0).astype(int))

debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Total Debt"] - debt_maturity_df["Secured Debt"])

print("\n============== Debt Maturity Table ($mn) ==============")
print(debt_maturity_df)

unsecured_debt = debt_maturity_df[~debt_maturity_df["Year"].str.contains("Total", case=False)]

yearly = unsecured_debt.copy()

def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    y = int(year)
    if 2024 <= y <= 2029:
        return "Near-term"
    return "Other"

yearly["Bucket"] = yearly["Year"].apply(bucket)

bucket_sums = (yearly.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
total_debt = bucket_sums["Unsecured Debt"].sum() 

# Adjust
debt_buckets_df = pd.DataFrame({
    "Ticker":   "PLD",
    "Quarter":  "3Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

# Adjust
debt_buckets_df.loc[len(debt_buckets_df)] = [
    "PLD",
    "3Q24",
    "Total Unsecured Debt",
    f"{int(total_debt):,}",
    "mn",
    "USD",
    "Unsecured Debt"
]

print("\n======================== Unsecured Debt Buckets =======================")
print(debt_buckets_df.to_string(index=False))

debt_buckets_df["Amount"] = (debt_buckets_df["Amount"].str.replace(",", "", regex=False).astype(int))

debt_buckets_df = (debt_buckets_df.rename(columns={"Unsecured Debt": "Line_Item_Name", "Amount": "Value"})
      .loc[:, ["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]])

print("\n================================ SQL Format ===============================")
print(debt_buckets_df.head())

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "PLD_3Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")