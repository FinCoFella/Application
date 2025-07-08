import tabula
import pandas as pd
from pathlib import Path

pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/AMT/AMT_1Q24_10Q.pdf"
ticker   = "AMT"
quarter  = "1Q24"

# Adjust
page_specs = {
    23: {"table_idx": 0, "row_slice": slice(5, 31), "col_idxs": [1, 5]},
    24: {"table_idx": 0, "row_slice": slice(0, 20), "col_idxs": [1, 5]},
}

all_raw = []
for page, spec in page_specs.items():
    tables = tabula.read_pdf(pdf_path, pages=page, lattice=True, guess=False, multiple_tables=True, pandas_options={"header": None},)

    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")

    raw = tables[spec["table_idx"]]
    raw = raw.dropna(how="all").reset_index(drop=True)
    if spec["row_slice"] is not None:
        raw = raw.iloc[spec["row_slice"]]
    raw = raw.iloc[:, spec["col_idxs"]].reset_index(drop=True)
    all_raw.append(raw)

raw_combined = pd.concat(all_raw, ignore_index=True)
raw_combined.columns = ["Unsecured Debt", "Maturity"]
raw_combined["Maturity"] = raw_combined["Maturity"].ffill()

raw_combined["Year"] = (raw_combined["Maturity"]
      .astype(str)
      .str.extract(r"(\d{4}|Thereafter|Various)", expand=False)
      .fillna("Various")
      .replace("Various", "Thereafter"))


raw_combined["Unsecured Debt"] = (
    raw_combined["Unsecured Debt"]
      .astype(str)
      .str.replace(r"[^\d.-]", "", regex=True)
      .pipe(pd.to_numeric, errors="coerce")
)

maturity = (
    raw_combined
      .groupby("Year", as_index=False)["Unsecured Debt"]
      .sum()
)

total = maturity["Unsecured Debt"].sum()
maturity = pd.concat([
    maturity,
    pd.DataFrame([{"Year": "Total", "Unsecured Debt": total}])
], ignore_index=True)

mprint = maturity.copy()
mprint["Unsecured Debt"] = mprint["Unsecured Debt"].astype(int).map("{:,}".format)

print("\n= Debt Maturity Table ($mn) =")
print(mprint)

yearly = maturity[maturity["Year"] != "Total"].copy()
yearly["Year"] = yearly["Year"].replace({"Various": "Thereafter"})
yearly["Unsecured Debt"] = yearly["Unsecured Debt"].astype(float)

def bucket(yr):
    try:
        y = int(yr)
    except:
        return "Long-term"
    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    return "Long-term"

yearly["Bucket"] = yearly["Year"].apply(bucket)
bucket_sums = yearly.groupby("Bucket", as_index=False)["Unsecured Debt"].sum()
bucket_total = bucket_sums["Unsecured Debt"].sum()

debt_buckets = pd.DataFrame({
    "Ticker":      ticker,
    "Quarter":     quarter,
    "Line_Item_Name": bucket_sums["Bucket"],
    "Value":       bucket_sums["Unsecured Debt"].astype(int),
    "Unit":        "mn",
    "Currency":    "USD",
    "Category":    "Unsecured Debt",
})

debt_buckets_df = pd.concat([
    debt_buckets,
    pd.DataFrame([{
        "Ticker":        ticker,
        "Quarter":       quarter,
        "Line_Item_Name": "Total Unsecured Debt",
        "Value":         int(bucket_total),
        "Unit":          "mn",
        "Currency":      "USD",
        "Category":      "Unsecured Debt",
    }])
], ignore_index=True)

order = ["Near-term", "Medium-term", "Long-term", "Total Unsecured Debt"]

debt_buckets_df["Line_Item_Name"] = pd.Categorical(
    debt_buckets_df["Line_Item_Name"],
    categories=order,
    ordered=True
)

debt_buckets_df = debt_buckets_df.sort_values("Line_Item_Name").reset_index(drop=True)

print("\n======================== Unsecured Debt Buckets =======================")
print(debt_buckets_df.to_string(index=False))

debt_buckets_df["Value"] = (
    debt_buckets_df["Value"]
      .astype(str)
      .str.replace(",", "", regex=False)
      .astype(int)
)
sql_df = debt_buckets_df.loc[
    :, ["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]
]

print("\n================================ SQL Format ===============================")
print(sql_df.head())

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "AMT_1Q24_unsecured_debt.csv"
sql_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
