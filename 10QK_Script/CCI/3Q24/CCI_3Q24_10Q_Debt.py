import tabula
import pandas as pd
from pathlib import Path

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/CCI/CCI_3Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=12, multiple_tables=True, stream=True, pandas_options={"header": None})

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")

raw = tables[0]
# Adjust
debt_maturity_df = raw.iloc[6:37, [3, 6]].copy()
debt_maturity_df.columns = ["Maturity", "Unsecured Debt"]
debt_maturity_df["Maturity"] = debt_maturity_df["Maturity"].ffill()

debt_maturity_df["Year"] = (debt_maturity_df["Maturity"].astype(str).str.extract(r"(\d{4}|Thereafter|Various)", expand=False)
                            .fillna("Various").replace("Various", "Thereafter"))

debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Unsecured Debt"]
                    .astype(str).str.replace(r"[^\d.\-]", "", regex=True).pipe(pd.to_numeric, errors="coerce"))

debt_maturity_df = debt_maturity_df.groupby("Year", as_index=False)["Unsecured Debt"].sum()


debt_maturity_df = pd.concat([debt_maturity_df, pd.DataFrame(
    {"Year": ["Total"], "Unsecured Debt": [debt_maturity_df["Unsecured Debt"].sum()]},),],ignore_index=True,)

debt_final_clean_df = debt_maturity_df.copy()
debt_final_clean_df["Unsecured Debt"] = debt_final_clean_df["Unsecured Debt"].astype(int).map("{:,}".format)

print("\n= Debt Maturity Table ($mn) =")
print(debt_final_clean_df)

unsecured_debt_df = debt_final_clean_df.copy()  

yearly = unsecured_debt_df[unsecured_debt_df["Year"] != "Total"].copy()
yearly["Unsecured Debt"] = yearly["Unsecured Debt"].str.replace(",", "", regex=False).astype(float)
yearly["Year"] = yearly["Year"].replace({"Various": "Thereafter"})

def bucket(yr):
    try:
        y = int(yr)
    except (ValueError, TypeError):
        return "Long-term"

    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    
    return "Long-term"

yearly["Bucket"] = yearly["Year"].apply(bucket)
bucket_sums = (yearly.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
total_debt = bucket_sums["Unsecured Debt"].sum()

# Adjust
debt_buckets_df = pd.DataFrame({
    "Ticker":   "CCI",
    "Quarter":  "3Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

# Adjust
debt_buckets_df.loc[len(debt_buckets_df)] = [
    "CCI",
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
CSV = SCRIPT_DIR / "CCI_3Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
