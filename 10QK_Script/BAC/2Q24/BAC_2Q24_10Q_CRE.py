import tabula
import pandas as pd

# Adjusted
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/BAC/BAC_2Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=56, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[1] # Adjusted

main_df = df.iloc[14:21, [0, 2]].reset_index(drop=True)
residential_df = df.iloc[[22], [0, 2]]

property_df = pd.concat([main_df, residential_df], ignore_index=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

row_rename_map = {
    "Industrial / Warehouse": "Industrial",
    "Multi-family rental": "Multi-family",
    "Shopping centers / Retail": "Retail",
    "Hotel / Motels": "Lodging",
    "Multi-use": "Mixed-use",
}

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)
# Adjusted
property_df["Ticker"] = "BAC"
property_df["Quarter"] = "2Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

# Adjusted
property_df["Loan Amount"] = (property_df["Loan Amount"].replace({r'\$': '', r',': ''}, regex=True).str.strip())
property_df["Loan Amount"] = pd.to_numeric(property_df["Loan Amount"], errors="coerce")
property_df = property_df.dropna(subset=["Loan Amount"])

total_row = pd.DataFrame([{
    "Ticker": "BAC",
    "Quarter": "2Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

# Adjusted
print("\n================ Extracted CRE 2Q24 Loan Portfolio Table =================")
print(property_df)

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)