from SNV_1Q24_10Q_CRE_v1 import extract_cre_main_table
from SNV_1Q24_10Q_CRE_v2 import extract_cre_other_table
import pandas as pd
from pathlib import Path

##### Retrieve DataFrames from both extraction functions #####
df1 = extract_cre_main_table()
df2 = extract_cre_other_table()
##### Remove the 'Total CRE' row from the first DataFrame before merging #####
df1 = df1[df1["CRE Property Type"] != "Total CRE"]
combined_cre_df = pd.concat([df1, df2], ignore_index=True)
##### Convert 'Loan Amount' to float for accurate summation #####
combined_cre_df["Loan Amount"] = combined_cre_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)
##### Group by 'CRE Property Type' and sum the 'Loan Amount' values #####
grouped = (combined_cre_df.groupby("CRE Property Type", as_index=False).agg({"Loan Amount": "sum"}))

##### Add additional columns with constant values to the DataFrame #####
grouped["Ticker"] = "SNV"
grouped["Quarter"] = "1Q24"
grouped["Unit"] = "mn"
grouped["Currency"] = "USD"
grouped["Category"] = "CRE"

#### Reorder the columns of the DataFrame #####
grouped = grouped[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]]
grouped["Loan Amount"] = grouped["Loan Amount"] / 1000

##### Create a 'Total CRE' row and append it to the DataFrame that sums the 'Loan Amount' column #####
total_row = pd.DataFrame([{
    "Ticker": "SNV",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": grouped["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

##### Append the 'Total CRE' row to the DataFrame and format the 'Loan Amount' column with commas #####
final_df = pd.concat([grouped, total_row], ignore_index=True)
final_df["Loan Amount"] = final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,.0f}")

print("\n=============== Merged CRE 1Q24 Loan Portfolio Table ================")
print(final_df, "\n")

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
final_df["Value"] = final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
final_df = final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
final_df = final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(final_df)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "SNV_1Q24_cre.csv"
final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
