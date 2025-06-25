import tabula
import pandas as pd

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/RF/RF_1Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=62, multiple_tables=True, stream=True)

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
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]
# Adjust
total_row = pd.DataFrame([{
    "Ticker": "RF",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")
# Adjust
print("\n============== Extracted CRE 1Q24 Loan Portfolio Table ==============")
print(property_df, "\n")

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
