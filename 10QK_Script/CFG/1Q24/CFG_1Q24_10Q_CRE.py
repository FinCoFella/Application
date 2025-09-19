import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/CFG/CFG_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=25, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Select specific rows and columns in the DataFrame, reset the index, and rename columns #####
property_df= df.iloc[3:13, [0, 1]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

##### Add additional columns with constant values to the DataFrame #####
property_df["Ticker"] = "CFG"
property_df["Quarter"] = "1Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

#### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

##### Remove empty rows and cast 'Loan Amount' to float after removing dollar signs and commas #####
property_df = property_df.dropna(subset=["Loan Amount"])
property_df["Loan Amount"] = property_df["Loan Amount"].replace({r"[\$,]": ""}, regex=True).astype(float)

##### Combine specific property types into an 'Office' DataFrame and sum their 'Loan Amount' values #####
office_total = property_df.loc[
    property_df["CRE Property Type"].isin(["Credit tenant lease and life sciences(1)", "Other general office"]), "Loan Amount"].sum()

##### Combine specific property types into an 'Other' DataFrame and sum their 'Loan Amount' values #####
other_total = property_df.loc[
    property_df["CRE Property Type"].isin(["Other", "Co-op", "Data center"]), "Loan Amount"].sum()

##### Remove the original labels in the DataFrame that were combined into 'Office' and 'Other' #####
property_df = property_df[
    ~property_df["CRE Property Type"].isin([
        "Credit tenant lease and life sciences(1)",
        "Other general office",
        "Co-op",
        "Data center",
        "Other",
        "Total CRE"
    ])
]

##### Create new rows for 'Office' and 'Other' with their respective total 'Loan Amount' values #####
new_rows = pd.DataFrame([
    {
        "Ticker": "CFG", 
        "Quarter": "1Q24", 
        "CRE Property Type": "Office",
        "Loan Amount": office_total, 
        "Unit": "mn", 
        "Currency": "USD", 
        "Category": "CRE"
    },
    {
        "Ticker": "CFG", 
        "Quarter": "1Q24", 
        "CRE Property Type": "Other",
        "Loan Amount": other_total, 
        "Unit": "mn", 
        "Currency": "USD", 
        "Category": "CRE"
    }
])

##### Append the new rows to the original DataFrame #####
property_df = pd.concat([property_df, new_rows], ignore_index=True)
##### Rename 'Hospitality' with 'Lodging' in the 'CRE Property Type' column #####
property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({"Hospitality": "Lodging"})

##### Create a 'Total CRE' row that aggregates the total 'Loan Amount' for all property types in the DataFrame #####
total_row = pd.DataFrame([{
    "Ticker": "CFG",
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
property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n============== Extracted CRE 1Q24 Loan Portfolio Table ===============")
print(property_df,"\n")

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "CFG_1Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
