import tabula
import pandas as pd
from pathlib import Path
import re

pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/HBAN/HBAN_3Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=24, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df = df.iloc[36:42, 0].reset_index(drop=True)

property_types = []
loan_amounts = []

for row in property_df:
    row = str(row).strip()

    match = re.match(r"(.*?)\s+\$\s*([\d,]+)", row)
    if match:
        property_types.append(match.group(1).strip())
        loan_amounts.append(match.group(2).replace(",", ""))
        continue

    match_alt = re.match(r"(.*\D)\s+([\d,]+)$", row)
    if match_alt:
        property_types.append(match_alt.group(1).strip())
        loan_amounts.append(match_alt.group(2).replace(",", ""))
        continue
    property_types.append(row)
    loan_amounts.append("")

property_df = pd.DataFrame({
    "Ticker": "HBAN",
    "Quarter": "3Q24",
    "CRE Property Type": property_types,
    "Loan Amount": pd.to_numeric(loan_amounts, errors='coerce'),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
})

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({
    "Warehouse/Industrial": "Industrial",
    "Hotel": "Lodging"
})


total_row = pd.DataFrame([{
    "Ticker": "HBAN",
    "Quarter": "3Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)
property_df["Loan Amount"] = property_df["Loan Amount"].apply(
    lambda x: f"{int(x):,}" if pd.notnull(x) else ""
)

print("\n============== Extracted CRE 3Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "HBAN_3Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
