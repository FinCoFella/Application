import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/PNC/PNC_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=42, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns in the DataFrame, reset the index, and rename columns #####
property_df = df.iloc[15:23, [0, 2]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "PNC"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

##### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

##### Clean the 'Loan Amount' column by extracting numeric values, removing commas, and converting to float #####
property_df["Loan Amount"] = property_df["Loan Amount"].str.extract(r"([\d,]+)")[0]
property_df["Loan Amount"] = property_df["Loan Amount"].str.replace(",", "").astype(float)

##### Rename the original labels in 'CRE Property Type' column to a set of standardised labels #####
row_rename_map = {
  "Industrial/warehouse": "Industrial",
  "Hotel/motel": "Lodging",
  "Multifamily": "Multi-family",
  "Mixed use": "Mixed-use",
}

##### Apply the renamed labels in the 'CRE Property Type' column in the DataFrame #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map) 

##### Create a 'Total CRE' row for the DataFrame that sums the 'Loan Amount' column #####
total_row = pd.DataFrame([{
    "Ticker": "PNC",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the 'Total CRE' row to the DataFrame and format the 'Loan Amount' column with commas #####
property_df = pd.concat([property_df, total_row], ignore_index=True)
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n=============== Extracted CRE 1Q24 Loan Portfolio Table ================")
print(property_df)


cre_final_df = property_df.copy()
##### Combine the "Seniors housing" loan amount value into the "Other" category and remove the "Seniors housing" row #####
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(",", "").astype(float)
senior_housing_val = cre_final_df.loc[cre_final_df["CRE Property Type"] == "Seniors housing", "Loan Amount"].values[0]
other_val = cre_final_df.loc[cre_final_df["CRE Property Type"] == "Other", "Loan Amount"].values[0]
cre_final_df.loc[cre_final_df["CRE Property Type"] == "Other", "Loan Amount"] = other_val + senior_housing_val
cre_final_df = cre_final_df[cre_final_df["CRE Property Type"] != "Seniors housing"].reset_index(drop=True)

##### Create a combined 'Total CRE' row for the DataFrame that sums the 'Loan Amount' column #####
combined_total = pd.DataFrame([{
    "Ticker": "PNC",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": cre_final_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the combined 'Total CRE' row to the DataFrame, remove duplicate 'Total CRE' rows, and format the 'Loan Amount' column with commas #####
cre_final_df = pd.concat([cre_final_df, combined_total], ignore_index=True)
cre_final_df = cre_final_df[~((cre_final_df["CRE Property Type"] == "Total CRE") & (cre_final_df.duplicated(["CRE Property Type"], keep='first')))]
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n=============== Extracted CRE 1Q24 Loan Portfolio Table ================")
print(cre_final_df,"\n")

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
cre_final_df["Value"] = cre_final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
cre_final_df = cre_final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
cre_final_df = cre_final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(cre_final_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "PNC_1Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
