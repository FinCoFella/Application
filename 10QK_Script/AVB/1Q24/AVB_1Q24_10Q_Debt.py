import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/AVB/AVB_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=18, multiple_tables=True, stream=True, pandas_options={"header": None})

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
debt_maturity_df = tables[0]

##### Select specific rows and columns, reset the index #####
debt_maturity_df = debt_maturity_df.drop(columns=debt_maturity_df.columns[[1, 3, 5]])
debt_maturity_df = debt_maturity_df.drop(index=debt_maturity_df.index[-1])

##### Rename columns and forward-fill blank cells in the 'Year' column using values in the prior row #####
debt_maturity_df.columns = ["Year", "Secured Debt", "Unsecured Debt"]
debt_maturity_df["Year"] = debt_maturity_df["Year"].ffill()

##### Clean characters in both columns, convert the values into millions and cast the values as integers #####
for col in ["Secured Debt", "Unsecured Debt"]:
    debt_maturity_df[col] = (debt_maturity_df[col].replace({r"," : ""}, regex=True).astype(float).div(1_000).fillna(0))

##### Collapses duplicate maturity years in the 'Year' column and aggregates the values in each group #####
debt_final_df = (debt_maturity_df.groupby("Year", as_index=False, sort=False).sum(numeric_only=True))
##### Calculates total debt values for both columns #####
total_amount = debt_final_df[["Secured Debt", "Unsecured Debt"]].sum()
##### Appends the 'Total' row to the DataFrame #####
debt_final_df.loc[len(debt_final_df)] = ["Total", total_amount["Secured Debt"], total_amount["Unsecured Debt"]]

##### Cast the values in both columns as integers and include comma separators #####
for col in ["Secured Debt", "Unsecured Debt"]:
    debt_final_df[col] = debt_final_df[col].astype(int).map("{:,}".format)

print("\n======== Debt Maturity Table ($mn) ========")
print(debt_final_df)

##### Create a new DataFrame that excludes the 'Total' row in the original DataFrame #####
unsecured_debt = debt_final_df[~debt_final_df["Year"].str.contains("Total", case=False)]
yearly_df = unsecured_debt.copy()

##### Cast the values in the 'Unsecured Debt' column into a float data type and remove thousands comma separators #####
yearly_df["Unsecured Debt"] = (yearly_df["Unsecured Debt"].str.replace(",", "", regex=False).astype(float))

##### A function that maps a year label into a maturity bucket #####
def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    y = int(year)
    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    return "Other"

#### Apply the function to categorize the maturity years in the 'Year' column into a bucket label #####
yearly_df["Bucket"] = yearly_df["Year"].apply(bucket)
#### Aggregate the values in the 'Unsecured Debt' column for each standardised bucket label #####
bucket_sums = (yearly_df.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
#### Compute the total value in the 'Unsecured Debt' column across all standardised bucket labels #####
total_debt = bucket_sums["Unsecured Debt"].sum() 

#### Build a DataFrame with user input constant values, along with the standardised bucket labels and the corresponding aggregated unsecured debt values #####
debt_buckets_df = pd.DataFrame({
    "Ticker":   "AVB",
    "Quarter":  "1Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

##### Create a 'Total' row with the same user input constant values and the total amount of all unsecured debt values, and append it to the DataFrame #####
debt_buckets_df.loc[len(debt_buckets_df)] = ["AVB", "1Q24", "Total Unsecured Debt", f"{int(total_debt):,}", "mn", "USD", "Unsecured Debt"]

print("\n======================== Unsecured Debt Buckets =======================")
print(debt_buckets_df.to_string(index=False))

##### Convert the 'Amount' column to integer values and remove commas, rename the 'Unsecured Debt' and 'Amount' columns, and reorder the columns in the final DataFrame #####
debt_buckets_df["Amount"] = (debt_buckets_df["Amount"].str.replace(",", "", regex=False).astype(int))
debt_buckets_df = (debt_buckets_df.rename(columns={"Unsecured Debt": "Line_Item_Name", "Amount": "Value"})
      .loc[:, ["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]])

print("\n================================ SQL Format ===============================")
print(debt_buckets_df.head())

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "AVB_1Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")