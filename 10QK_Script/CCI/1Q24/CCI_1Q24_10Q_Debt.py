import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/CCI/CCI_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=14, multiple_tables=True, stream=True, pandas_options={"header": None})

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
raw = tables[0]

##### Select specific rows and columns, reset the index #####
debt_maturity_df = raw.iloc[5:34, [3, 6]].copy()

##### Rename columns and forward-fill blank cells in the 'Maturity' column using values in the prior row #####
debt_maturity_df.columns = ["Maturity", "Unsecured Debt"]
debt_maturity_df["Maturity"] = debt_maturity_df["Maturity"].ffill()

##### Extracts the year digits, 'Thereafter' or 'Various' word in the first column and replace 'Various' to 'Thereafter' #####
debt_maturity_df["Year"] = (debt_maturity_df["Maturity"].astype(str).str.extract(r"(\d{4}|Thereafter|Various)", expand=False).fillna("Various").replace("Various", "Thereafter"))

##### Convert values in 'Unsecured Debt' column to numeric characters and coerce errors to NaN #####
debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Unsecured Debt"].astype(str).str.replace(r"[^\d.\-]", "", regex=True).pipe(pd.to_numeric, errors="coerce"))
##### Aggregate numeric values in the 'Unsecured Debt' column by unique maturity year labels in the 'Year' column #####
debt_maturity_df = debt_maturity_df.groupby("Year", as_index=False)["Unsecured Debt"].sum()

##### Create a 'Total' row to sum the values in the 'Unsecured Debt' column across all maturity year labels in the DataFrame #####
debt_maturity_df = pd.concat([debt_maturity_df, pd.DataFrame({"Year": ["Total"], "Unsecured Debt": [debt_maturity_df["Unsecured Debt"].sum()]},),],ignore_index=True,)
debt_final_clean_df = debt_maturity_df.copy()

##### Clean the values in the 'Unsecured Debt' column to include thousand comma separators #####
debt_final_clean_df["Unsecured Debt"] = debt_final_clean_df["Unsecured Debt"].astype(int).map("{:,}".format)

print("\n===== Debt Maturity Table ($mn) =====")
print(debt_final_clean_df)

unsecured_debt_df = debt_final_clean_df.copy()  

##### Create a new DataFrame that excludes the 'Total' row ##### 
yearly_df = unsecured_debt_df[unsecured_debt_df["Year"] != "Total"].copy()

##### Transform the values in the 'Unsecured Debt' column into a float data type and remove commas #####
yearly_df["Unsecured Debt"] = yearly_df["Unsecured Debt"].str.replace(",", "", regex=False).astype(float)

##### Standardise the 'Various' label to 'Thereafter' #####
yearly_df["Year"] = yearly_df["Year"].replace({"Various": "Thereafter"})

##### A function that maps a year label into a maturity bucket #####
def bucket(yr):
    try:
        y = int(yr)
    except (ValueError, TypeError):
        return "Long-term"

    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    return "Long-term"

#### Apply the function to categorize the maturity years in the 'Year' column into a bucket label #####
yearly_df["Bucket"] = yearly_df["Year"].apply(bucket)
#### Aggregate the values in the 'Unsecured Debt' column for each standardised bucket label #####
bucket_sums = (yearly_df.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
#### Compute the total value in the 'Unsecured Debt' column across all standardised bucket labels #####
total_debt = bucket_sums["Unsecured Debt"].sum()

#### Build a DataFrame with user input constant values, along with the standardised bucket labels and the corresponding aggregated unsecured debt values #####
debt_buckets_df = pd.DataFrame({
    "Ticker":   "CCI",
    "Quarter":  "1Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

##### Create a 'Total' row with the same user input constant values and the total amount of all unsecured debt values, and append it to the DataFrame #####
debt_buckets_df.loc[len(debt_buckets_df)] = ["CCI", "1Q24", "Total Unsecured Debt", f"{int(total_debt):,}", "mn", "USD", "Unsecured Debt"]

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
CSV = SCRIPT_DIR / "CCI_1Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
