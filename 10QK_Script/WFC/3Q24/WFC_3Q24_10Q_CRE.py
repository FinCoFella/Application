import tabula
import pandas as pd

pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/WFC/WFC_3Q24_10Q.pdf"
tables = tabula.read_pdf(pdf_path, pages=36, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")

df = tables[0]

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
df_total = df_total[df_total['Property Type'] != 'By property:']

print("\n========== DataFrame 3: Total CRE Loans Outstanding ==========")
print(format_numeric_columns(df_total))

df_total.to_csv("WFC_3Q24_CRE_Totals.csv", index=False)

with open("Load_WFC_3Q24_CRE_Totals.py", "w") as f:
    f.write("import pandas as pd\n\n")
    f.write("def load_data():\n")
    f.write("    return pd.read_csv('WFC_3Q24_CRE_Totals.csv')\n")
