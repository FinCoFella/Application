import tabula
import pandas as pd

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/KEY/KEY_2024_10K.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=109, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table)
df = tables[0]

# Adjust
property_df = df.iloc[2:17, [0, -2, -1]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Construction', 'Mortgage']

for col in ['Construction', 'Mortgage']:
    property_df[col] = property_df[col].astype(str).replace(r"[^\d.\-]", "", regex=True).replace("", "0").astype(float)

property_df["Loan Amount"] = property_df["Construction"] + property_df["Mortgage"]

# Adjust
property_df["Ticker"] = "KEY"
property_df["Quarter"] = "4Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Construction", "Mortgage", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "KEY",
    "Quarter": "4Q24",
    "CRE Property Type": "Total CRE",
    "Construction": property_df["Construction"].sum(),
    "Mortgage": property_df["Mortgage"].sum(),
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

for col in ["Construction", "Mortgage", "Loan Amount"]:
    property_df[col] = property_df[col].apply(lambda x: f"{int(x):,}")

# Adjust
property_df = property_df[property_df["CRE Property Type"] != "Nonowner-occupied:"]

# Adjust
print("\n========================== Extracted CRE 4Q24 Loan Portfolio Table ===========================")
print(property_df)

cre_final_df = property_df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]].copy()
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(',', '').astype(int)

consolidation_map = {
    "Diversified": "Other",
    "Land & Residential": "Other",
    "Medical Office": "Office",
    "Self Storage": "Other",
    "Senior Housing": "Other",
    "Skilled Nursing": "Other",
    "Data Center": "Other",
    "Student Housing": "Other"
}

cre_final_df["CRE Property Type"] = cre_final_df["CRE Property Type"].replace(consolidation_map)

cre_final_df = cre_final_df.groupby(
    ["Ticker", "Quarter", "CRE Property Type", "Unit", "Currency", "Category"],
    as_index=False
).agg({"Loan Amount": "sum"})

cre_final_df = cre_final_df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]]

cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n============================ SQL DataFrame =============================")
print(cre_final_df,"\n")

sql_df = cre_final_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
