import tabula
import pandas as pd
from pathlib import Path

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/JPM/JPM_1Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=86, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

# Adjust
property_df = df.iloc[3:10, [0, 4, 6]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Combined Value', 'Percent Drawn']

property_df['Credit Exposure'] = property_df['Combined Value'].str.extract(r'([\d,]+)$')[0].str.replace(",", "", regex=False).astype(float)
property_df.drop(columns=['Combined Value'], inplace=True)

property_df["Percent Drawn"] = property_df["Percent Drawn"].replace({r"[^\d.]": ""}, regex=True).astype(float)
property_df["Loan Amount"] = (property_df["Percent Drawn"] / 100) * property_df["Credit Exposure"]

row_rename_map = {
  "Multifamily(a)": "Multi-family",
}

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map) 

# Adjust
property_df["Ticker"] = "JPM"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Credit Exposure", "Percent Drawn", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "JPM",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Credit Exposure": property_df["Credit Exposure"].sum(),
    "Percent Drawn": (property_df["Loan Amount"].sum() / property_df["Credit Exposure"].sum()) * 100,
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,}")
property_df["Percent Drawn"] = property_df["Percent Drawn"].apply(lambda x: f"{int(round(x))}")
property_df["Credit Exposure"] = property_df["Credit Exposure"].apply(lambda x: f"{int(x):,}")

print("\n====================================== Extracted CRE 3Q24 Loan Portfolio Table =======================================")
print(property_df)

cre_final_df = property_df[[
    "Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"
]].copy()

cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(",", "").astype(float)

mask = cre_final_df["CRE Property Type"].isin([
    "Other Income Producing Properties(b)",
    "Services and Non Income Producing"
])

other_total = cre_final_df.loc[mask, "Loan Amount"].sum()

# Adjust
other_row = {
    "Ticker": "JPM",
    "Quarter": "1Q24",
    "CRE Property Type": "Other",
    "Loan Amount": other_total,
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}

cre_final_df = cre_final_df[~mask]
cre_final_df = pd.concat([cre_final_df, pd.DataFrame([other_row])], ignore_index=True)
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,}")

other_row = cre_final_df[cre_final_df["CRE Property Type"] == "Other"]
total_row = cre_final_df[cre_final_df["CRE Property Type"] == "Total CRE"]
remaining_rows = cre_final_df[
    ~cre_final_df["CRE Property Type"].isin(["Other", "Total CRE"])
]

cre_final_df = pd.concat([remaining_rows, other_row, total_row], ignore_index=True)

cre_final_df["Value"] = cre_final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
cre_final_df = cre_final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
cre_final_df = cre_final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format =========================")
print(cre_final_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "JPM_1Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
