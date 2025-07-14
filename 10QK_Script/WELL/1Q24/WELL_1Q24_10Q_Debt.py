import tabula
import pandas as pd
from pathlib import Path
from pprint import pprint

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/WELL/WELL_1Q24_10Q.pdf"

area = [300, 20, 480, 560]
columns = [330, 435, 520]

tables = tabula.read_pdf(pdf_path, pages=21, stream=True, guess=False, area=area, columns=columns, multiple_tables=False, pandas_options={"header": None})

for i, df in enumerate(tables):
    pprint(df)

debt_maturity_df = tables[0].dropna(how="all")

debt_maturity_df = (debt_maturity_df.loc[3:7, [0, 1]].reset_index(drop=True))

debt_maturity_df.columns = ["Year", "Unsecured Debt"]
debt_maturity_df["Year"] = (debt_maturity_df["Year"].astype(str).str.extract(r"(\d{4}|Thereafter)")[0])

debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Unsecured Debt"].astype(str).replace("—", "0", regex=False)
                                      .str.replace(r"[\$,()]", "", regex=True)
                                      .astype(int).div(1_000).round(0).astype(int))

total_row = pd.DataFrame({"Year": ["Total"], "Unsecured Debt": [debt_maturity_df["Unsecured Debt"].sum()]})

debt_maturity_df = pd.concat([debt_maturity_df, total_row], ignore_index=True)

print("\n= Debt Maturity Table ($mn) =")
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
    "Ticker":   "WELL",
    "Quarter":  "1Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

# Adjust
debt_buckets_df.loc[len(debt_buckets_df)] = [
    "WELL",
    "1Q24",
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
CSV = SCRIPT_DIR / "WELL_1Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")