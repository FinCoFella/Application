import tabula
import pandas as pd
from pathlib import Path

pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/JPM/JPM_3Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=107, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

cre_final_df = df.iloc[3:10, [0, 3, 5]].reset_index(drop=True)
cre_final_df.columns = ['CRE Property Type', 'Combined Value', 'Percent Drawn']

cre_final_df['Credit Exposure'] = cre_final_df['Combined Value'].str.extract(r'([\d,]+)$')[0].str.replace(",", "", regex=False).astype(float)
cre_final_df.drop(columns=['Combined Value'], inplace=True)

cre_final_df["Percent Drawn"] = cre_final_df["Percent Drawn"].replace({r"[^\d.]": ""}, regex=True).astype(float)
cre_final_df["Loan Amount"] = (cre_final_df["Percent Drawn"] / 100) * cre_final_df["Credit Exposure"]

row_rename_map = {
  "Multifamily(a)": "Multi-family",
}

cre_final_df["CRE Property Type"] = cre_final_df["CRE Property Type"].replace(row_rename_map) 

cre_final_df["Ticker"] = "JPM"
cre_final_df["Quarter"] = "3Q24"
cre_final_df["Unit"] = "mn"
cre_final_df["Currency"] = "USD"
cre_final_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Credit Exposure", "Percent Drawn", "Loan Amount", "Unit", "Currency", "Category"]
cre_final_df = cre_final_df[column_order]

total_row = pd.DataFrame([{
    "Ticker": "JPM",
    "Quarter": "3Q24",
    "CRE Property Type": "Total CRE",
    "Credit Exposure": cre_final_df["Credit Exposure"].sum(),
    "Percent Drawn": (cre_final_df["Loan Amount"].sum() / cre_final_df["Credit Exposure"].sum()) * 100,
    "Loan Amount": cre_final_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

cre_final_df = pd.concat([cre_final_df, total_row], ignore_index=True)
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,}")
cre_final_df["Percent Drawn"] = cre_final_df["Percent Drawn"].apply(lambda x: f"{int(round(x))}")
cre_final_df["Credit Exposure"] = cre_final_df["Credit Exposure"].apply(lambda x: f"{int(x):,}")

print("\n====================================== Extracted CRE 3Q24 Loan Portfolio Table =======================================")
print(cre_final_df)

cre_final_df = cre_final_df[[
    "Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"
]].copy()

cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(",", "").astype(float)

mask = cre_final_df["CRE Property Type"].isin([
    "Other Income Producing Properties(b)",
    "Services and Non Income Producing"
])

other_total = cre_final_df.loc[mask, "Loan Amount"].sum()

other_row = {
    "Ticker": "JPM",
    "Quarter": "3Q24",
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
CSV = SCRIPT_DIR / "JPM_3Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
