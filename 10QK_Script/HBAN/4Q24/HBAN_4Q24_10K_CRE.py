import tabula
import pandas as pd
import re

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/HBAN/HBAN_2024_10K.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=82, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

# Adjust
property_rows = df.iloc[1:7, [0, 2]].dropna().reset_index(drop=True)

property_types = []
loan_amounts = []

# Adjust
for _, row in property_rows.iterrows():
    prop = str(row.iloc[0]).strip()
    value_str = str(row.iloc[1]).strip()

    match = re.match(r"([\d,]+)\s+\d+\s*%?", value_str)
    if match:
        amount = match.group(1).replace(",", "")
    else:
        amount = ""

    property_types.append(prop)
    loan_amounts.append(pd.to_numeric(amount, errors='coerce'))

# Adjust
property_df = pd.DataFrame({
    "Ticker": "HBAN",
    "Quarter": "4Q24",
    "CRE Property Type": property_types,
    "Loan Amount": loan_amounts,
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
})

# Adjust
property_df["CRE Property Type"] = property_df["CRE Property Type"].str.replace(r"\s*\$", "", regex=True)

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({
    "Warehouse/industrial": "Industrial",
    "Hotel": "Lodging"
})

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "HBAN",
    "Quarter": "4Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")

# Adjust
print("\n============== Extracted CRE 4Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '', regex=False).replace('', pd.NA).dropna().astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
