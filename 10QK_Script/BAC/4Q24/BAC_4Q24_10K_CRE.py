import tabula
import pandas as pd

# Adjusted
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/BAC/BAC_2024_10K.pdf"
tables = tabula.read_pdf(pdf_path, pages=112, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

# Adjusted
main_df = df.iloc[17:24, [0, 3]].reset_index(drop=True)
residential_df = df.iloc[[25], [0, 3]]

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

property_df["Ticker"] = "BAC"
property_df["Quarter"] = "4Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

# Adjusted
property_df["Loan Amount"] = (property_df["Loan Amount"].astype(str).str.extract(r"([\d,]+)").iloc[:, 0].replace({",": ""}, regex=True).astype(float))

total_row = pd.DataFrame([{
    "Ticker": "BAC",
    "Quarter": "4Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

# Adjusted
print("\n================ Extracted CRE 4Q24 Loan Portfolio Table =================")
print(property_df)

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)