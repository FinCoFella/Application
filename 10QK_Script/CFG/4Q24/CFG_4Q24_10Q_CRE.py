import tabula
import pandas as pd

# Adjust
pdf_path = "/mnt/c/Users/finco/OneDrive/Documents/Filings/Financials/10QK/CFG/CFG_2024_10K.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=71, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df= df.iloc[3:13, [0, 1]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

# Adjust
property_df["Ticker"] = "CFG"
property_df["Quarter"] = "4Q24"
property_df["Unit"] = "mn"
property_df["Currency"] = "USD"
property_df["Category"] = "CRE"

column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
property_df = property_df[column_order]

property_df = property_df.dropna(subset=["Loan Amount"])
property_df["Loan Amount"] = property_df["Loan Amount"].replace({r"[\$,]": ""}, regex=True).astype(float)

office_total = property_df.loc[
    property_df["CRE Property Type"].isin([
        "Credit tenant lease and life sciences(1)", "Other general office"
    ]), "Loan Amount"
].sum()

other_total = property_df.loc[
    property_df["CRE Property Type"].isin(["Other", "Co-op", "Data center"]),
    "Loan Amount"
].sum()

property_df = property_df[
    ~property_df["CRE Property Type"].isin([
        "Credit tenant lease and life sciences(1)",
        "Other general office",
        "Co-op",
        "Data center",
        "Other",
        "Total CRE"
    ])
]

new_rows = pd.DataFrame([
    {
        "Ticker": "CFG", "Quarter": "4Q24", "CRE Property Type": "Office",
        "Loan Amount": office_total, "Unit": "mn", "Currency": "USD", "Category": "CRE"
    },
    {
        "Ticker": "CFG", "Quarter": "4Q24", "CRE Property Type": "Other",
        "Loan Amount": other_total, "Unit": "mn", "Currency": "USD", "Category": "CRE"
    }
])

property_df = pd.concat([property_df, new_rows], ignore_index=True)

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({
    "Hospitality": "Lodging"
})

total_row = pd.DataFrame([{
    "Ticker": "CFG",
    "Quarter": "4Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

print("\n============== Extracted CRE 4Q24 Loan Portfolio Table ===============")
print(property_df, "\n")

sql_df = property_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(int)
sql_df.rename(columns={
    "CRE Property Type": "Line_Item_Name",
    "Loan Amount": "Value"
}, inplace=True)

sql_df.to_csv("cre_loan_data.csv", index=False)
