# Run "WFC_CRE_3Q24_10Q.py" to generate the data before running this script.
from Load_WFC_4Q24_CRE_Totals import load_data
from sqlalchemy import create_engine
import pandas as pd

df = load_data()

df['Total CRE Loans Outstanding'] = df['Total CRE Loans Outstanding'].apply(
    lambda x: f"{int(x):,}" if pd.notnull(x) else ""
)

df = df[~df['Property Type'].isin(['By property:', 'Total'])].reset_index(drop=True)
# Adjust
rename_map = {
    '1-4 family structure': 'Residential',
    'Apartments': 'Multi-family',
    'Hotel/motel': 'Lodging',
    'Industrial/warehouse': 'Industrial',
    'Institutional': 'Other',
    'Mixed use properties': 'Mixed-use',
    'Mobile home park': 'Other',
    'Storage facility': 'Other'
}

df['Property Type'] = df['Property Type'].replace(rename_map)
df['Total CRE Loans Outstanding'] = df['Total CRE Loans Outstanding'].replace(r'[\$,]', '', regex=True).astype(float)

df['Property Type'] = df['Property Type'].replace({
    'Retail (excl shopping center)': 'Retail',
    'Shopping center': 'Retail'
})

df = df.groupby('Property Type', as_index=False)['Total CRE Loans Outstanding'].sum()

df['Total CRE Loans Outstanding'] = df['Total CRE Loans Outstanding'].apply(lambda x: f"{int(x):,}")

total = df['Total CRE Loans Outstanding'].replace('[,]', '', regex=True).astype(int).sum()
df.loc[len(df.index)] = ['Total CRE', f"{total:,}"]

df.rename(columns={
    "Property Type": "CRE Property Type",
    "Total CRE Loans Outstanding": "Loan Amount"
}, inplace=True)
# Adjust
df["Ticker"] = "WFC"
df["Quarter"] = "4Q24"
df["Unit"] = "mn"
df["Currency"] = "USD"
df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
final_CRE_df = df[column_order]
# Adjust
print("\n============== Extracted CRE 4Q24 Loan Portfolio Table ===============")
print(final_CRE_df)

sql_df = final_CRE_df.copy()

sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)

sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

print("\n======================= SQL DataFrame ========================")
print(sql_df)

server = '10.82.193.77'
port = '1433'
database = 'US_Banks'
username = 'FinCoFella'
password = 'ND24ICL'
driver = 'ODBC Driver 17 for SQL Server'

connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server},{port}/{database}"
    f"?driver={driver.replace(' ', '+')}"
)

engine = create_engine(connection_string)

sql_df.to_sql('Financial_Line_Item', con=engine, if_exists='append', index=False)