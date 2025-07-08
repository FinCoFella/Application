import tabula
import pandas as pd
from pathlib import Path

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/CFG/CFG_2Q24_10Q.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=26, multiple_tables=True, stream=True)

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")
df = tables[0]

property_df= df.iloc[3:13, [0, 1]].reset_index(drop=True)
property_df.columns = ['CRE Property Type', 'Loan Amount']

# Adjust
property_df["Ticker"] = "CFG"
property_df["Quarter"] = "2Q24"
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

# Adjust
new_rows = pd.DataFrame([
    {
        "Ticker": "CFG", "Quarter": "2Q24", "CRE Property Type": "Office",
        "Loan Amount": office_total, "Unit": "mn", "Currency": "USD", "Category": "CRE"
    },
    {
        "Ticker": "CFG", "Quarter": "2Q24", "CRE Property Type": "Other",
        "Loan Amount": other_total, "Unit": "mn", "Currency": "USD", "Category": "CRE"
    }
])

property_df = pd.concat([property_df, new_rows], ignore_index=True)

property_df["CRE Property Type"] = property_df["CRE Property Type"].replace({
    "Hospitality": "Lodging"
})

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "CFG",
    "Quarter": "2Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": property_df["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

property_df = pd.concat([property_df, total_row], ignore_index=True)

property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

# Adjust
print("\n============== Extracted CRE 2Q24 Loan Portfolio Table ===============")
print(property_df,"\n")

property_df["Value"] = property_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
property_df = property_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
property_df = property_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(property_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "CFG_2Q24_cre.csv"
property_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
