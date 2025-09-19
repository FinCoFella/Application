import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/FCNCA/FCNCA_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=136, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns, reset the index, and rename columns #####

property_df = df.iloc[1:8, [0, 2]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

##### Rename the original labels in 'CRE Property Type' column to a set of standardised labels #####
row_rename_map = {
    "Multi-Family": "Multi-family",
    "Industrial / Warehouse": "Industrial",
    "Hotel/Motel": "Lodging",
}

##### Apply the renaming map to the 'CRE Property Type' column #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "FCNCA"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

##### Reorder the columns in the DataFrame for better readability #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

##### Collapse 'Medical Office' and 'General Office' labels into a single standardised 'Office' label  and calculate the total loan amount value #####
office_mask = property_df["CRE Property Type"].isin(["Medical Office", "General Office"])
office_total = property_df.loc[office_mask, "Loan Amount"].sum()
property_df = property_df[~office_mask]

##### Create a new row for 'Office' with the aggregated loan amount value #####
office_row = pd.DataFrame([{
    "Ticker": "FCNCA",
    "Quarter": "1Q24",
    "CRE Property Type": "Office",
    "Loan Amount": office_total,
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the new 'Office' row to the main DataFrame #####
property_df = pd.concat([property_df, office_row], ignore_index=True)

##### Create a 'Total CRE' row that calculates the total 'Loan Amount' value for all property types in the DataFrame #####
total_row = pd.DataFrame([{
    "Ticker": "FCNCA",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

#### Append the 'Total CRE' row to the DataFrame #####
property_df = pd.concat([property_df, total_row], ignore_index=True)
##### Format the 'Loan Amount' column with commas as thousands separators #####
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

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
CSV = SCRIPT_DIR / "FCNCA_1Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
