import tabula
import pandas as pd
from pathlib import Path

##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/WFC/WFC_1Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=36, multiple_tables=True, stream=True)

##### Print all extracted tables and place the first table into a DataFrame #####
for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

##### Function to merge 'Retail (excl shopping center)' label shown into two rows into one row #####
def fix_split_rows(table):
    rows = table['Unnamed: 0'].astype(str).tolist()
    for i in range(len(rows) - 1):
        if 'Retail (excl shopping' in rows[i] and 'center)' in rows[i + 1]:
            table.at[i, 'Unnamed: 0'] = 'Retail'
            for col in table.columns[1:]:
                if pd.isna(table.at[i, col]):
                    table.at[i, col] = ''
                if pd.notna(table.at[i + 1, col]):
                    table.at[i, col] += ' ' + str(table.at[i + 1, col])
            table.drop(index=i + 1, inplace=True)
            table.reset_index(drop=True, inplace=True)
            break
    return table

##### Apply 'fix_split_rows' function to merge labels that appear into separate rows #####
tables = [fix_split_rows(tbl) for tbl in tables]

##### Function to format numeric data in a DataFrame as integers or return an empty string if values are NaN #####
def format_numeric_columns(df):
    df_formatted = df.copy()
    for col in df_formatted.select_dtypes(include='number').columns:
        df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    return df_formatted

##### Normalize values in columns into a string data type in both DataFrames #####
df['Unnamed: 1'] = df['Unnamed: 1'].astype(str)
df['Unnamed: 2'] = df['Unnamed: 2'].astype(str)

##### Extract two sets of numbers from the 'Unnamed: 1' column and write the numbers into two columns with meaningful header names #####
##### The regular expression pattern attempts to capture currency like integers separated by a space #####
df1 = df[['Unnamed: 0', 'Unnamed: 1']].copy()
df1[['RE Mortgage Nonaccruals', 'RE Mortgage Outstanding']] = df1['Unnamed: 1'].str.extract(r'(?:[-–]?\s*)?([$]?\d[\d,]*)?\s+([$]?\d[\d,]*)')
df1.drop(columns='Unnamed: 1', inplace=True)

##### Extract two sets of numbers from the 'Unnamed: 2' column and write the numbers into two columns with meaningful header names #####
##### The regular expression pattern attempts to capture currency like integers separated by a space #####
df2 = df[['Unnamed: 0', 'Unnamed: 2']].copy()
df2[['RE Construction Nonaccruals', 'RE Construction Outstanding']] = df2['Unnamed: 2'].str.extract(r'(?:[-–]?\s*)?([$]?\d[\d,]*)?\s+([$]?\d[\d,]*)')
df2.drop(columns='Unnamed: 2', inplace=True)

##### Remove currency symbols and comma thousands separators from each column in both DataFrames #####
for dframe in [df1, df2]:
    for col in dframe.columns:
        dframe[col] = dframe[col].replace('[\$,]', '', regex=True)
        dframe[col] = pd.to_numeric(dframe[col], errors='ignore')

##### Drop irrelevant columns from both DataFrames #####
df1.drop(columns='RE Mortgage Nonaccruals', inplace=True)
df2.drop(columns='RE Construction Nonaccruals', inplace=True)

##### Drop the 'By property' row and first 18 rows from both DataFrames and reset the index #####
df1 = df1[df1['Unnamed: 0'] != 'By property:']
df2 = df2[df2['Unnamed: 0'] != 'By property:']
df1 = df1.iloc[18:].reset_index(drop=True)
df2 = df2.iloc[18:].reset_index(drop=True)

print("\n============ DataFrame 1: CRE Mortgage Loans) ============")
print(format_numeric_columns(df1))

print("\n============ DataFrame 2: CRE Construction Loans) ============")
print(format_numeric_columns(df2))

##### Create a new DataFrame that merges both DataFrames on the shared label column #####
df_total = pd.merge(df1, df2, on='Unnamed: 0', how='outer')
##### Fill in missing values with zeros before applying arithmetic to prevent NaN values #####
df_total.fillna(0, inplace=True)
##### Create a column in the new DataFrame that is the sum of the loan amount values from columns in the original DataFrames along each row #####
df_total['Total CRE Loans Outstanding'] = (df_total['RE Mortgage Outstanding'] + df_total['RE Construction Outstanding'])

##### Keep the first column and the 'Total' column in the new DataFrame #####
df_total = df_total[['Unnamed: 0', 'Total CRE Loans Outstanding']]
##### Rename the first column to 'Property Type' #####
df_total.rename(columns={'Unnamed: 0': 'Property Type'}, inplace=True)
##### Remove rows that do not contain numeric data from the DataFrame#####
df_total = df_total.loc[lambda d: ~d['Property Type'].isin(['By property:', 'Total'])].reset_index(drop=True)

print("\n========== DataFrame 3: Total CRE Loans Outstanding ==========")
print(format_numeric_columns(df_total))

df_cre_final = df_total.copy()

##### Cast the values in the column to integers and applies comma thousands separators before rendering the values into a string data type #####
df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")

##### Rename the original labels in 'Property Type' column to a set of standardised labels #####
rename_map = {
    '1-4 family structure': 'Residential',
    'Apartments': 'Multi-family',
    'Hotel/motel': 'Lodging',
    'Industrial/warehouse': 'Industrial',
    'Institutional': 'Other',
    'Mixed use properties': 'Mixed-use',
    'Storage facility': 'Other'
}

##### Apply the renamed labels in the 'CRE Property Type' column in the DataFrame #####
df_cre_final['Property Type'] = df_cre_final['Property Type'].replace(rename_map)

##### Formta the values in the column to remove currency symbols and comma thousands separators and converts the string values into a float data type #####
df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].replace(r'[\$,]', '', regex=True).astype(float)

##### Transform the original category labels in the DataFrame into a standardised label #####
df_cre_final['Property Type'] = df_cre_final['Property Type'].replace({
    'Retail (excl shopping center)': 'Retail',
    'Shopping center': 'Retail'
})

##### Aggregate the loan amount values according to each standardised label #####
df_cre_final = df_cre_final.groupby('Property Type', as_index=False)['Total CRE Loans Outstanding'].sum()

##### Format the values in the column as integers, includes comma thousands separators before rendering the values into a string data type #####
df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].apply(lambda x: f"{int(x):,}")

##### Remove commas from values in the column, casts the values as integers, and sum all the values in the column to arrive at a total #####
total_cre_amt = df_total['Total CRE Loans Outstanding'].replace('[,]', '', regex=True).astype(int).sum()

##### Append a 'Total CRE' row with the total value amount to the DataFrame formatted with comma thousand separators #####
df_cre_final.loc[len(df_cre_final.index)] = ['Total CRE', f"{total_cre_amt:,}"]

##### Rename the header columns #####
df_cre_final.rename(columns={
    "Property Type": "CRE Property Type",
    "Total CRE Loans Outstanding": "Loan Amount"
}, inplace=True)

##### Add additional columns with constant values to the DataFrame #####
df_cre_final["Ticker"] = "WFC"
df_cre_final["Quarter"] = "1Q24"
df_cre_final["Unit"] = "mn"
df_cre_final["Currency"] = "USD"
df_cre_final["Category"] = "CRE"

##### Reorder the columns of the DataFrame #####
column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
df_cre_final = df_cre_final[column_order]

print("\n====================== Standardized CRE Table =======================")
print(df_cre_final)

##### Convert the 'Loan Amount' column to integer values and remove commas, rename 'CRE Property Type' to 'Line_Item_Name', and reorder the columns in the final DataFrame #####
df_cre_final["Value"] = df_cre_final["Loan Amount"].str.replace(",", "", regex=False).astype(int)
df_cre_final = df_cre_final.rename(columns={"CRE Property Type": "Line_Item_Name"})
df_cre_final = df_cre_final[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format =========================")
print(df_cre_final)

##### Save the final DataFrame to a CSV file in the same directory as the script #####
SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "WFC_1Q24_cre.csv"
df_cre_final.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
