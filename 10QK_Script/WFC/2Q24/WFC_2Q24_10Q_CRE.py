import tabula
import pandas as pd
from pathlib import Path

# Adjust 
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/WFC/WFC_2Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=39, multiple_tables=True, stream=True) 

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")

df = tables[0]

# Adjust
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

tables = [fix_split_rows(tbl) for tbl in tables]

def format_numeric_columns(df):
    df_formatted = df.copy()
    for col in df_formatted.select_dtypes(include='number').columns:
        df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    return df_formatted

df['Unnamed: 1'] = df['Unnamed: 1'].astype(str)
df['Unnamed: 2'] = df['Unnamed: 2'].astype(str)


df1 = df[['Unnamed: 0', 'Unnamed: 1']].copy()
df1[['RE Mortgage Nonaccruals', 'RE Mortgage Outstanding']] = df1['Unnamed: 1'].str.extract(r'(?:[-–]?\s*)?([$]?\d[\d,]*)?\s+([$]?\d[\d,]*)')
df1.drop(columns='Unnamed: 1', inplace=True)


df2 = df[['Unnamed: 0', 'Unnamed: 2']].copy()
df2[['RE Construction Nonaccruals', 'RE Construction Outstanding']] = df2['Unnamed: 2'].str.extract(r'(?:[-–]?\s*)?([$]?\d[\d,]*)?\s+([$]?\d[\d,]*)')
df2.drop(columns='Unnamed: 2', inplace=True)


for dframe in [df1, df2]:
    for col in dframe.columns:
        dframe[col] = dframe[col].replace('[\$,]', '', regex=True)
        dframe[col] = pd.to_numeric(dframe[col], errors='ignore')

df1.drop(columns='RE Mortgage Nonaccruals', inplace=True)
df2.drop(columns='RE Construction Nonaccruals', inplace=True)

df1 = df1[df1['Unnamed: 0'] != 'By property:']
df2 = df2[df2['Unnamed: 0'] != 'By property:']

df1 = df1.iloc[18:].reset_index(drop=True)
df2 = df2.iloc[18:].reset_index(drop=True)

print("\n============ DataFrame 1: CRE Mortgage Loans) ============")
print(format_numeric_columns(df1))

print("\n============ DataFrame 2: CRE Construction Loans) ============")
print(format_numeric_columns(df2))

df_total = pd.merge(
    df1, df2,
    on='Unnamed: 0',
    how='outer'
)

df_total.fillna(0, inplace=True)

df_total['Total CRE Loans Outstanding'] = (
    df_total['RE Mortgage Outstanding'] + df_total['RE Construction Outstanding']
)

df_total = df_total[['Unnamed: 0', 'Total CRE Loans Outstanding']]
df_total.rename(columns={'Unnamed: 0': 'Property Type'}, inplace=True)
df_total = df_total.loc[lambda d: ~d['Property Type'].isin(['By property:', 'Total'])].reset_index(drop=True)
df_total = df_total[df_total['Property Type'] != 'By property:']

print("\n========== DataFrame 3: Total CRE Loans Outstanding ==========")
print(format_numeric_columns(df_total))

df_cre_final = df_total.copy()
df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].apply(
    lambda x: f"{int(x):,}" if pd.notnull(x) else ""
)

df_cre_final = df_cre_final[~df_cre_final['Property Type'].isin(['By property:', 'Total'])].reset_index(drop=True)

rename_map = {
    '1-4 family structure': 'Residential',
    'Apartments': 'Multi-family',
    'Hotel/motel': 'Lodging',
    'Industrial/warehouse': 'Industrial',
    'Institutional': 'Other',
    'Mixed use properties': 'Mixed-use',
    'Storage facility': 'Other'
}

df_cre_final['Property Type'] = df_cre_final['Property Type'].replace(rename_map)
df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].replace(r'[\$,]', '', regex=True).astype(float)

df_cre_final['Property Type'] = df_cre_final['Property Type'].replace({
    'Retail (excl shopping center)': 'Retail',
    'Shopping center': 'Retail'
})

df_cre_final = df_cre_final.groupby('Property Type', as_index=False)['Total CRE Loans Outstanding'].sum()

df_cre_final['Total CRE Loans Outstanding'] = df_cre_final['Total CRE Loans Outstanding'].apply(lambda x: f"{int(x):,}")

total = df_total['Total CRE Loans Outstanding'].replace('[,]', '', regex=True).astype(int).sum()
df_cre_final.loc[len(df_cre_final.index)] = ['Total CRE', f"{total:,}"]

df_cre_final.rename(columns={
    "Property Type": "CRE Property Type",
    "Total CRE Loans Outstanding": "Loan Amount"
}, inplace=True)

df_cre_final["Ticker"] = "WFC"
df_cre_final["Quarter"] = "2Q24"
df_cre_final["Unit"] = "mn"
df_cre_final["Currency"] = "USD"
df_cre_final["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
df_cre_final = df_cre_final[column_order]

print("\n====================== Standardized CRE Table =======================")
print(df_cre_final)

df_cre_final["Value"] = df_cre_final["Loan Amount"].str.replace(",", "", regex=False).astype(int)
df_cre_final = df_cre_final.rename(columns={"CRE Property Type": "Line_Item_Name"})
df_cre_final = df_cre_final[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format =========================")
print(df_cre_final)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "WFC_2Q24_cre.csv"
df_cre_final.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
