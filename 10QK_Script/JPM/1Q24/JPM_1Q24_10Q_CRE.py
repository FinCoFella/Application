import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/JPM/JPM_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=86, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns, reset the index, and rename columns #####
property_df = df.iloc[3:10, [0, 4, 6]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Combined Value', 'Percent Drawn']

##### Parse numbers from the 'Combined Value' column into the 'Credit Exposure' column, remove commas, and cast the values as a float data type #####
property_df['Credit Exposure'] = property_df['Combined Value'].str.extract(r'([\d,]+)$')[0].str.replace(",", "", regex=False).astype(float)
property_df.drop(columns=['Combined Value'], inplace=True)

##### Remove non-numeric characters in the 'Percent Drawn' column #####
property_df["Percent Drawn"] = property_df["Percent Drawn"].replace({r"[^\d.]": ""}, regex=True).astype(float)

##### Calculates the values in the 'Loan Amount' column using a mathematical formula applied on numbers in other columns in the DataFrame #####
property_df["Loan Amount"] = (property_df["Percent Drawn"] / 100) * property_df["Credit Exposure"]

##### Rename the original labels in 'CRE Property Type' column to a standardised label #####
row_rename_map = {
  "Multifamily(a)": "Multi-family",
}

##### Apply the renaming map to the DataFrame #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map) 

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "JPM"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

#### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Credit Exposure", "Percent Drawn", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

##### Create a 'Total CRE' row for the DataFrame that sums the 'Credit Exposure' and 'Loan Amount' columns, and calculates the overall percentage drawn value #####
total_row = pd.DataFrame([{
    "Ticker": "JPM",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Credit Exposure": property_df["Credit Exposure"].sum(),
    "Percent Drawn": (property_df["Loan Amount"].sum() / property_df["Credit Exposure"].sum()) * 100,
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the 'Total CRE' row to the DataFrame #####
property_df = pd.concat([property_df, total_row], ignore_index=True)

##### Format the values in the identified columns #####
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,}")
property_df["Percent Drawn"] = property_df["Percent Drawn"].apply(lambda x: f"{int(round(x))}")
property_df["Credit Exposure"] = property_df["Credit Exposure"].apply(lambda x: f"{int(round(x)):,}")

print("\n====================================== Extracted CRE 3Q24 Loan Portfolio Table =======================================")
print(property_df)

##### Create a new DataFrame containing specific columns #####
cre_final_df = property_df[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]].copy()

##### Cast the values in the 'Loan Amount' column to a float data type #####
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].str.replace(",", "").astype(float)

##### Create a Boolean mask to identify which original labels should be standardised into an 'Other' label #####
mask = cre_final_df["CRE Property Type"].isin([
    "Other Income Producing Properties(b)",
    "Services and Non Income Producing"
])

##### Sum the loan amount values in the mask to obtain an aggregated value for the standardised 'Other' label ##### 
other_total = cre_final_df.loc[mask, "Loan Amount"].sum()

##### Construct an 'Other' row with constant values and the agggregated loan amount values of the labels in the mask #####
other_row = {
    "Ticker": "JPM",
    "Quarter": "1Q24",
    "CRE Property Type": "Other",
    "Loan Amount": other_total,
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}

##### Remove the rows containing the original labels in the mask, append the 'Other' row, and format the numbers in the 'Loan Amount' column #####
cre_final_df = cre_final_df[~mask]
cre_final_df = pd.concat([cre_final_df, pd.DataFrame([other_row])], ignore_index=True)
cre_final_df["Loan Amount"] = cre_final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,}")

##### Partition the DataFrame into different sections #####
other_row = cre_final_df[cre_final_df["CRE Property Type"] == "Other"]
total_row = cre_final_df[cre_final_df["CRE Property Type"] == "Total CRE"]
remaining_rows = cre_final_df[~cre_final_df["CRE Property Type"].isin(["Other", "Total CRE"])]
##### Append the partitioned sections into a new DataFrame in a new order #####
cre_final_df = pd.concat([remaining_rows, other_row, total_row], ignore_index=True)

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
cre_final_df["Value"] = cre_final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
cre_final_df = cre_final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
cre_final_df = cre_final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format =========================")
print(cre_final_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "JPM_1Q24_cre.csv"
cre_final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
