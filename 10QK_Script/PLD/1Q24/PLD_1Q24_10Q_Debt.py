import tabula
import pandas as pd
from pathlib import Path
import re

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/PLD/PLD_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=27, multiple_tables=True, stream=True, pandas_options={"header": None})

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
debt_maturity_df = tables[0]

##### Select specific rows and columns, reset the index #####
debt_maturity_df = (debt_maturity_df.loc[2:9, [0, 7, 9]].reset_index(drop=True))

##### Extracts the year digits or 'Thereafter' word in the first column and rename 'Subtotal' to 'Total' #####
debt_maturity_df[0] = (debt_maturity_df[0].astype(str).str.extract(r'(\d{4}|Thereafter|Subtotal)')[0]).replace("Subtotal", "Total")

##### Rename columns and remove empty rows in the 'Year' column #####
debt_maturity_df = debt_maturity_df.rename(columns={0: "Year", 7: "Secured Debt", 9: "Total Debt"})
debt_maturity_df = debt_maturity_df.dropna(subset=["Year"])

##### Clean characters in both columns, convert the values into millions and cast the values as integers #####
for col in ["Secured Debt", "Total Debt"]:
    debt_maturity_df[col] = (pd.to_numeric(debt_maturity_df[col].astype(str).str.replace(r'[\$,()\s]', '', regex=True), errors="coerce").div(1_000).round(0).astype("int"))

##### Calculation for 'Unsecured Debt' which is the difference between the values in the 'Total Debt' and 'Secured Debt' columns #####
debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Total Debt"] - debt_maturity_df["Secured Debt"])

##### Sum values across all rows in the identified columns excluding a 'Total' row and cast the values as integers #####
totals = (debt_maturity_df.loc[debt_maturity_df["Year"] != "Total", ["Secured Debt", "Total Debt", "Unsecured Debt"]].sum().astype("int"))

##### Populate the 'Total' row with the calculated total amount values for the identified columns #####
debt_maturity_df.loc[debt_maturity_df["Year"] == "Total", ["Secured Debt", "Total Debt", "Unsecured Debt"]] = totals.values

print("\n============== Debt Maturity Table ($mn) ==============")
print(debt_maturity_df)

##### Keep all the rows that do not contain the 'Total' row #####
unsecured_debt = debt_maturity_df[~debt_maturity_df["Year"].str.contains("Total", case=False)]
yearly = unsecured_debt.copy()

##### A function that maps a year label into a maturity bucket #####
def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    y = int(year)
    if 2024 <= y <= 2029:
        return "Near-term"
    return "Other"

#### Apply the function to categorize the maturity years in the 'Year' column into a bucket label #####
yearly["Bucket"] = yearly["Year"].apply(bucket)
#### Aggregate the values in the 'Unsecured Debt' column for each standardised bucket label #####
bucket_sums = (yearly.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
#### Compute the total value in the 'Unsecured Debt' column across all standardised bucket labels #####
total_debt = bucket_sums["Unsecured Debt"].sum() 

#### Build a DataFrame with user input constant values, along with the standardised bucket labels and the corresponding aggregated unsecured debt values ##### 
debt_buckets_df = pd.DataFrame({
    "Ticker":   "PLD",
    "Quarter":  "1Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

##### Create a 'Total' row with the same user input constant values and the total amount of all unsecured debt values, and append it to the DataFrame #####
debt_buckets_df.loc[len(debt_buckets_df)] = ["PLD", "1Q24", "Total Unsecured Debt", f"{int(total_debt):,}", "mn", "USD", "Unsecured Debt"]

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
CSV = SCRIPT_DIR / "PLD_1Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")