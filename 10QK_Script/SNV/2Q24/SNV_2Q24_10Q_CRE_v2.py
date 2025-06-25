import tabula
import pandas as pd

def extract_cre_other_table():
    # Adjust
    pdf_path = "/mnt/c/Users/finco/OneDrive/Documents/Filings/Financials/10QK/SNV/SNV_2Q24_10Q.pdf"
    # Adjust
    tables = tabula.read_pdf(pdf_path, pages=50, multiple_tables=True, stream=True)

    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")
    df = tables[0]

    # Adjust
    property_df = df.iloc[3:5, [0, 2]].reset_index(drop=True)
    property_df.columns = ['CRE Property Type', 'Loan Amount']

    row_rename_map = {
        "1-4 family properties": "Residential",
        "Land and development": "Other",
    }

    property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

    # Adjust
    property_df["Ticker"] = "SNV"
    property_df["Quarter"] = "2Q24"
    property_df["Unit"] = "ths"
    property_df["Currency"] = "USD"
    property_df["Category"] = "CRE"

    column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
    property_df = property_df[column_order]

    property_df = property_df[property_df["Loan Amount"].notna()]
    property_df = property_df[property_df["Loan Amount"].astype(str).str.strip() != ""]
    property_df["Loan Amount"] = property_df["Loan Amount"].astype(str).str.replace(",", "").astype(float)
    property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

    return property_df

if __name__ == "__main__":
    df = extract_cre_other_table()
    # Adjust
    print("\n================ Extracted 2Q24 CRE Portfolio Table =================")
    print(df,"\n")
