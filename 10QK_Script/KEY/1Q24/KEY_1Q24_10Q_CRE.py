import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/KEY/KEY_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=39, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table)
df = tables[0]

##### Select specific rows and columns, reset the index, and rename columns #####
property_df = df.iloc[2:15, [0, -3, -1]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Construction', 'Mortgage']

##### Remove commas, dashes, dollar signs, and convert to float #####
for col in ['Construction', 'Mortgage']:
    property_df[col] = property_df[col].replace({",": "", "—": "0", "$": ""}, regex=True).fillna("0").astype(float)

##### Create 'Loan Amount' column containing the sum of 'Construction' and 'Mortgage' loan amount values #####
property_df["Loan Amount"] = property_df["Construction"] + property_df["Mortgage"]

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "KEY"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

#### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Construction", "Mortgage", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]
##### Convert 'Loan Amount' to float after removing commas #####
property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

##### Create a 'Total CRE' row and append it to the DataFrame that sums the 'Construction', 'Mortgage', and 'Loan Amount' columns #####
total_row = pd.DataFrame([{
    "Ticker": "KEY",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Construction": property_df["Construction"].sum(),
    "Mortgage": property_df["Mortgage"].sum(),
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

#### Append the 'Total CRE' row to the DataFrame #####
property_df = pd.concat([property_df, total_row], ignore_index=True)
##### Format the 'Construction', 'Mortgage', and 'Loan Amount' columns with commas #####
for col in ["Construction", "Mortgage", "Loan Amount"]:
    property_df[col] = property_df[col].apply(lambda x: f"{int(x):,}")

print("\n========================== Extracted CRE 1Q24 Loan Portfolio Table ===========================")
print(property_df)

##### Create a new DataFrame, include certain columns in the DataFrame, cast the 'Loan Amount' values as integers, and remove commas #####
cre_final_df = property_df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]].copy()
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(',', '').astype(int)

##### Rename the original labels in 'CRE Property Type' column to a set of standardised labels #####
consolidation_map = {
    "Diversified": "Other",
    "Land & Residential": "Other",
    "Medical Office": "Office",
    "Self Storage": "Other",
    "Multifamily": "Multi-family",
    "Senior Housing": "Other",
    "Skilled Nursing": "Other",
    "Student Housing": "Other"
}

##### Apply the renaming map to the DataFrame #####
cre_final_df["CRE Property Type"] = cre_final_df["CRE Property Type"].replace(consolidation_map)

#### Collapses duplicate labels in the 'CRE Property Type' column and sums the corresponding 'Loan Amount' values ##### 
cre_final_df = cre_final_df.groupby(
    ["Ticker", "Quarter", "CRE Property Type", "Unit", "Currency", "Category"],
    as_index=False).agg({"Loan Amount": "sum"})

##### Reorder the columns of the DataFrame and format the values in the 'Loan Amount' column with commas #####
cre_final_df = cre_final_df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]]
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n=========================== SQL DataFrame ============================")
print(cre_final_df,"\n")

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
cre_final_df["Value"] = cre_final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
cre_final_df = cre_final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
cre_final_df = cre_final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(cre_final_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "KEY_1Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
