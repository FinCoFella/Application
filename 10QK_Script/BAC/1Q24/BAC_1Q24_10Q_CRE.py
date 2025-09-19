import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/BAC/BAC_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=53, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns in the DataFrame and reset the index #####
main_df = df.iloc[14:21, [0, 1]].reset_index(drop=True)
residential_df = df.iloc[[22], [0, 1]]

##### Combine the main DataFrame and the residential DataFrame #####
property_df = pd.concat([main_df, residential_df], ignore_index=True)
##### Rename the columns in the new DataFrame #####
property_df.columns = ['CRE Property Type', 'Loan Amount']

##### Rename the original labels in 'CRE Property Type' column to a set of standardised labels #####
row_rename_map = {
    "Industrial / Warehouse": "Industrial",
    "Multi-family rental": "Multi-family",
    "Shopping centers / Retail": "Retail",
    "Hotel / Motels": "Lodging",
    "Multi-use": "Mixed-use",
}

##### Apply the renaming map to the DataFrame #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "BAC"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

##### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

##### Clean the 'Loan Amount' column by removing dollar signs and commas, converting the values in the column to numeric, and drop NaN rows #####
property_df["Loan Amount"] = (property_df["Loan Amount"].replace({r'\$': '', r',': ''}, regex=True).str.strip())
property_df["Loan Amount"] = pd.to_numeric(property_df["Loan Amount"], errors="coerce")
property_df = property_df.dropna(subset=["Loan Amount"])

##### Create a 'Total CRE' row for the DataFrame that sums the 'Loan Amount' column #####
total_row = pd.DataFrame([{
    "Ticker": "BAC",
    "Quarter": "1Q24", # Adjusted
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

###### Append the 'Total CRE' row to the DataFrame and format the 'Loan Amount' column with commas #####
property_df = pd.concat([property_df, total_row], ignore_index=True)
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

# Adjusted
print("\n============== Extracted CRE 1Q24 Loan Portfolio Table ===============")
print(property_df)

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "BAC_1Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")