import tabula
import pandas as pd
from pathlib import Path
from pprint import pprint

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/WELL/WELL_1Q24_10Q.pdf"
##### Define the area and columns to accurately capture the debt maturity table #####
area = [300, 20, 480, 560]
columns = [330, 435, 520]
tables = tabula.read_pdf(pdf_path, pages=21, stream=True, guess=False, area=area, columns=columns, multiple_tables=False, pandas_options={"header": None})

##### Print all extracted tables and place the first table into a DataFrame #####
for i, df in enumerate(tables):
    pprint(df)
debt_maturity_df = tables[0].dropna(how="all")

##### Select specific rows and columns, reset the index, and rename columns #####
debt_maturity_df = (debt_maturity_df.loc[3:7, [0, 1]].reset_index(drop=True))

##### Renames columns, converts the 'Year' column into strings, and extracts the year digits or 'Thereafter' word from the column#####
debt_maturity_df.columns = ["Year", "Unsecured Debt"]
debt_maturity_df["Year"] = (debt_maturity_df["Year"].astype(str).str.extract(r"(\d{4}|Thereafter)")[0])

##### Normalize the data in the 'Unsecured Debt' column, cast the values as integers, and convert the values into millions #####
debt_maturity_df["Unsecured Debt"] = (debt_maturity_df["Unsecured Debt"].astype(str).replace("—", "0", regex=False).str.replace(r"[\$,()]", "", regex=True).astype(int).div(1_000).round(0).astype(int))

##### Create a 'Total' row for the DataFrame and sum the 'Unsecured Debt' amount column
total_row = pd.DataFrame({"Year": ["Total"], "Unsecured Debt": [debt_maturity_df["Unsecured Debt"].sum()]})
##### Append the 'Total' row to the DataFrame #####
debt_maturity_df = pd.concat([debt_maturity_df, total_row], ignore_index=True)

print("\n===== Debt Maturity Table ($mn) =====")
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

#### Apply the function to assing the 'Year' values into a bucket label #####
yearly["Bucket"] = yearly["Year"].apply(bucket)

#### Aggregate the values in the 'Unsecured Debt' column for each standardised bucket label #####
bucket_sums = (yearly.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))

#### Compute the total value in the 'Unsecured Debt' column across all standardised bucket labels #####
total_debt = bucket_sums["Unsecured Debt"].sum() 

#### Build a DataFrame with user input constant values, along with the standardised bucket labels and the corresponding aggregated unsecured debt values ##### 
debt_buckets_df = pd.DataFrame({
    "Ticker":   "WELL",
    "Quarter":  "1Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

##### Create a 'Total' row with the same user input constant values and the total amount of all unsecured debt values, and append it to the DataFrame #####
debt_buckets_df.loc[len(debt_buckets_df)] = ["WELL", "1Q24", "Total Unsecured Debt", f"{int(total_debt):,}", "mn", "USD", "Unsecured Debt"]

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
CSV = SCRIPT_DIR / "WELL_1Q24_unsecured_debt.csv"
debt_buckets_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")