import tabula
import pandas as pd
from pathlib import Path
import re

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/HBAN/HBAN_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=19, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns from the DataFrame to isolate the desired CRE property types and loan amounts #####
property_df = df.iloc[36:42, 0].reset_index(drop=True)

##### Instantiates empty lists to hold property types and loan amounts #####
property_types = []
loan_amounts = []

##### Parse each row in the DataFrame to extract property types and loan amounts using regular expressions #####
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

##### Create a new DataFrame with the extracted property types and loan amounts, along with additional metadata #####
property_df = pd.DataFrame({
    "Ticker": "HBAN",
    "Quarter": "1Q24",
    "CRE Property Type": property_types,
    "Loan Amount": pd.to_numeric(loan_amounts, errors='coerce'),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
})

##### Renames certain property type labels into a standardised labels for consistency #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({"Warehouse/Industrial": "Industrial", "Hotel": "Lodging"})

##### Create a 'Total CRE' row that calculates the total 'Loan Amount' value for all property types in the DataFrame #####
total_row = pd.DataFrame([{
    "Ticker": "HBAN",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the 'Total CRE' row to the DataFrame #####
property_df = pd.concat([property_df, total_row], ignore_index=True)
##### Format the 'Loan Amount' column with commas as thousands separators #####
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")

print("\n============== Extracted CRE 1Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "HBAN_1Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
