import tabula
import pandas as pd
from pathlib import Path

pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/PNC/PNC_3Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=44, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df = df.iloc[15:23, [0, 2]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

property_df["Ticker"] = "PNC"
property_df["Quarter"] = "3Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

property_df["Loan Amount"] = property_df["Loan Amount"].str.extract(r"([\d,]+)")[0]
property_df["Loan Amount"] = property_df["Loan Amount"].str.replace(",", "").astype(float)

row_rename_map = {
  "Industrial/warehouse": "Industrial",
  "Hotel/motel": "Lodging",
  "Multifamily": "Multi-family",
  "Mixed use": "Mixed-use",
}

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map) 


total_row = pd.DataFrame([{
    "Ticker": "PNC",
    "Quarter": "3Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n=============== Extracted CRE 3Q24 Loan Portfolio Table ================")
print(property_df)

cre_final_df = property_df.copy()
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(",", "").astype(float)
senior_housing_val = cre_final_df.loc[cre_final_df["CRE Property Type"] == "Seniors housing", "Loan Amount"].values[0]
other_val = cre_final_df.loc[cre_final_df["CRE Property Type"] == "Other", "Loan Amount"].values[0]

cre_final_df.loc[cre_final_df["CRE Property Type"] == "Other", "Loan Amount"] = other_val + senior_housing_val
cre_final_df = cre_final_df[cre_final_df["CRE Property Type"] != "Seniors housing"].reset_index(drop=True)

combined_total = pd.DataFrame([{
    "Ticker": "PNC",
    "Quarter": "3Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": cre_final_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

cre_final_df = pd.concat([cre_final_df, combined_total], ignore_index=True)
cre_final_df = cre_final_df[~((cre_final_df["CRE Property Type"] == "Total CRE") & (cre_final_df.duplicated(["CRE Property Type"], keep='first')))]
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(x):,}")


print("\n=============== Extracted CRE 3Q24 Loan Portfolio Table ================")
print(cre_final_df,"\n")

cre_final_df["Value"] = cre_final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
cre_final_df = cre_final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
cre_final_df = cre_final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(cre_final_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "PNC_3Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
