import tabula
import pandas as pd
from pathlib import Path

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/RF/RF_2Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=69, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]
# Adjust
property_df = df.iloc[1:13, [0, 3]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

row_rename_map = {
    "Residential homebuilders": "Residential",
    "Residential land": "Residential",
    "Apartments": "Multi-family",
    "Data center": "Other",
    "Diversified": "Other",
    "Healthcare": "Other",
    "Commercial land": "Other",
    "Business offices": "Office",
    "Self Storage": "Other",
    "Hotel": "Lodging",
}

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)
property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)
property_df = property_df.groupby("CRE Property Type", as_index=False)["Loan Amount"].sum()
# Adjust
property_df["Ticker"] = "RF"
property_df["Quarter"] = "2Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]
# Adjust
total_row = pd.DataFrame([{
    "Ticker": "RF",
    "Quarter": "2Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")
# Adjust
print("\n============== Extracted CRE 2Q24 Loan Portfolio Table ==============")
print(property_df, "\n")

property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "RF_2Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
