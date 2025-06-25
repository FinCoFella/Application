import tabula
import pandas as pd

# Adjust
pdf_path = "/mnt/c/Users/finco/OneDrive/Documents/Filings/Financials/10QK/FCNCA/FCNCA_2Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=138, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df = df.iloc[1:8, [0, 2]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

row_rename_map = {
    "Multi-Family": "Multi-family",
    "Industrial / Warehouse": "Industrial",
    "Hotel / Motel": "Lodging",
}

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

# Adjust
property_df["Ticker"] = "FCNCA"
property_df["Quarter"] = "2Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

office_mask = property_df["CRE Property Type"].isin(["Medical Office", "General Office"])
office_total = property_df.loc[office_mask, "Loan Amount"].sum()
property_df = property_df[~office_mask]

# Adjust
office_row = pd.DataFrame([{
    "Ticker": "FCNCA",
    "Quarter": "2Q24",
    "CRE Property Type": "Office",
    "Loan Amount": office_total,
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, office_row], ignore_index=True)

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "FCNCA",
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
print("\n============== Extracted CRE 2Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
