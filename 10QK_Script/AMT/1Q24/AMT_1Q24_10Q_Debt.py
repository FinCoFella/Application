import tabula
import pandas as pd
from pathlib import Path

##### Store a string file path into a variable to a PDF document stored in the repository #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/AMT/AMT_1Q24_10Q.pdf"
##### Store user input constant values into variables to reflect additional columns to be appended to a relation #####
ticker  = "AMT"
quarter = "1Q24"
unit = "mn"
currency = "USD"
category = "Unsecured Debt"

##### Extraction details for specific tables on certain pages for particular rows and columns #####
target_tables = {
    23: {"table_index": 0, "row_slice": slice(5, 31), "col_idxs": [1, 5]},
    24: {"table_index": 0, "row_slice": slice(0, 20), "col_idxs": [1, 5]},
}
all_raw = []


for page, spec in target_tables.items():
    ##### Apply the Tabula module to return a list of Pandas DataFrames ######
    tables = tabula.read_pdf(pdf_path, pages=page, lattice=True, guess=False, multiple_tables=True, pandas_options={"header": None},)
    ##### Print all tables detected on each page #####
    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")

    ##### Select the extracted target table and drop  empty rows #####
    raw_df = tables[spec["table_index"]]
    raw_df = raw_df.dropna(how="all").reset_index(drop=True)

    ##### Retain the rows that contain the target data #####
    if spec["row_slice"] is not None:
        raw_df = raw_df.iloc[spec["row_slice"]]

    #### Retain the columns that contain the target data ####
    raw_df = raw_df.iloc[:, spec["col_idxs"]].reset_index(drop=True)
    all_raw.append(raw_df)

##### Combine the adjusted tables into a DataFrame #####
raw_combined_df = pd.concat(all_raw, ignore_index=True)
##### Rename extracted columns with meaningful names #####
raw_combined_df.columns = ["Unsecured Debt", "Maturity"]
##### Fill in maturity year labels for empty rows using the prior row maturity year label #####
raw_combined_df["Maturity"] = raw_combined_df["Maturity"].ffill()

##### Extracts the year digits, 'Thereafter' or 'Various' word in the first column and replace 'Various' to 'Thereafter' #####
raw_combined_df["Year"] = (raw_combined_df["Maturity"].astype(str).str.extract(r"(\d{4}|Thereafter|Various)", expand=False).fillna("Various").replace("Various", "Thereafter"))
##### Convert values in 'Unsecured Debt' column to numeric characters and coerce errors to NaN #####
raw_combined_df["Unsecured Debt"] = (raw_combined_df["Unsecured Debt"].astype(str).str.replace(r"[^\d.-]", "", regex=True).pipe(pd.to_numeric, errors="coerce"))
##### Aggregate numeric values in the 'Unsecured Debt' column by unique maturity year labels in the 'Year' column #####
maturity_df = (raw_combined_df.groupby("Year", as_index=False)["Unsecured Debt"].sum())

##### Compute the total amount value in the 'Unsecured Debt' column across all rows #####
total = maturity_df["Unsecured Debt"].sum()
#### Apppend a 'Total' row in the 'Year' column with the variable containing the total amount value in the 'Unsecured Debt' column #####
maturity_df = pd.concat([maturity_df, pd.DataFrame([{"Year": "Total", "Unsecured Debt": total}])], ignore_index=True)
print_df = maturity_df.copy()
#### Casts the values in the 'Unsecured Debt' column to integers before formatting the values as strings with comma thousands separators #####
print_df["Unsecured Debt"] = print_df["Unsecured Debt"].astype(int).map("{:,}".format)

print("\n===== Debt Maturity Table ($mn) =====")
print(print_df)

##### Remove the total row from the DataFrame and make a copy of it #####
yearly_df = maturity_df[maturity_df["Year"] != "Total"].copy()
##### Rename the 'Various' maturity label to 'Thereafter' #####
yearly_df["Year"] = yearly_df["Year"].replace({"Various": "Thereafter"})
##### Convert the values in the 'Unsecured Debt' column into a float data type #####
yearly_df["Unsecured Debt"] = yearly_df["Unsecured Debt"].astype(float)

##### A function that maps a year label into a maturity bucket #####
def bucket(yr):
    try:
        y = int(yr)
    except:
        return "Long-term"
    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    return "Long-term"

#### Apply the function to categorize the maturity years in the 'Year' column into a bucket label #####
yearly_df["Bucket"] = yearly_df["Year"].apply(bucket)
#### Aggregate the values in the 'Unsecured Debt' column for each standardised bucket label #####
bucket_sums = yearly_df.groupby("Bucket", as_index=False)["Unsecured Debt"].sum()
#### Compute the total value in the 'Unsecured Debt' column across all standardised bucket labels #####
bucket_total = bucket_sums["Unsecured Debt"].sum()

##### Build a DataFrame with user input constant values, along with the standardised bucket labels and the corresponding aggregated unsecured debt values #####
debt_buckets = pd.DataFrame({
    "Ticker": ticker,
    "Quarter": quarter,
    "Line_Item_Name": bucket_sums["Bucket"],
    "Value": bucket_sums["Unsecured Debt"].astype(int),
    "Unit": unit,
    "Currency": currency,
    "Category": category,
})

##### Append the total value of all rows in the 'Unsecured Debt' column in the 'Total Unsecured Debt' row ##### 
debt_buckets_df = pd.concat([
    debt_buckets,
    pd.DataFrame([{
        "Ticker": ticker,
        "Quarter": quarter,
        "Line_Item_Name": "Total Unsecured Debt",
        "Value": int(bucket_total),
        "Unit": unit,
        "Currency": currency,
        "Category": category,
    }])], ignore_index=True)

##### Create a categorical order for the standardised bucket labels and sort them in the DataFrame #####
bucket_order = ["Near-term", "Medium-term", "Long-term", "Total Unsecured Debt"]
debt_buckets_df["Line_Item_Name"] = pd.Categorical(debt_buckets_df["Line_Item_Name"], categories=bucket_order, ordered=True)
debt_buckets_df = debt_buckets_df.sort_values("Line_Item_Name").reset_index(drop=True)

print("\n======================== Unsecured Debt Buckets =======================")
print(debt_buckets_df.to_string(index=False))

##### Convert the 'Value' column to integer values and remove commas, and reorder the columns in the final DataFrame #####
debt_buckets_df["Value"] = (debt_buckets_df["Value"].astype(str).str.replace(",", "", regex=False).astype(int))
sql_df = debt_buckets_df.loc[:, ["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n================================ SQL Format ===============================")
print(sql_df.head())

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "AMT_1Q24_unsecured_debt.csv"
sql_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
