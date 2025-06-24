import tabula
import pandas as pd
import re

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/HBAN/HBAN_1Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=19, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df = df.iloc[36:42, 0].reset_index(drop=True)

property_types = []
loan_amounts = []

for row in property_df:
    row = str(row).strip()

    match = re.match(r"(.*?)\s+\$\s*([\d,]+)", row)
    if match:
        property_types.append(match.group(1).strip())
        loan_amounts.append(match.group(2).replace(",", ""))
        continue

    match_alt = re.match(r"(.*\D)\s+([\d,]+)$", row)
    if match_alt:
        property_types.append(match_alt.group(1).strip())
        loan_amounts.append(match_alt.group(2).replace(",", ""))
        continue
    property_types.append(row)
    loan_amounts.append("")

# Adjust
property_df = pd.DataFrame({
    "Ticker": "HBAN",
    "Quarter": "1Q24",
    "CRE Property Type": property_types,
    "Loan Amount": pd.to_numeric(loan_amounts, errors='coerce'),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
})

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({
    "Warehouse/Industrial": "Industrial",
    "Hotel": "Lodging"
})

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "HBAN",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)
property_df["Loan Amount"] = property_df["Loan Amount"].apply(
    lambda x: f"{int(x):,}" if pd.notnull(x) else ""
)

# Adjust
print("\n============== Extracted CRE 1Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '', regex=False).replace('', pd.NA).dropna().astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
