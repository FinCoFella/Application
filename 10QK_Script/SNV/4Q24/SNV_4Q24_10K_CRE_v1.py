import tabula
import pandas as pd

def extract_cre_main_table():
    # Adjust
    pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/SNV/SNV_2024_10K.pdf"
    # Adjust
    tables = tabula.read_pdf(pdf_path, pages=86, multiple_tables=True, stream=True)

    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")
    df = tables[0]

    # Adjust
    raw = df.iloc[5:11, 0].dropna().reset_index(drop=True)
    # Adjust
    property_df = pd.DataFrame()
    property_df["CRE Property Type"] = raw.str.extract(r"^([A-Za-z\s\-]+)")[0].str.strip().str.title()
    property_df["Loan Amount"] = raw.str.extract(r"(\$?\s*\d[\d,]*)")[0]
    property_df["Loan Amount"] = property_df["Loan Amount"].str.replace("[\$,]", "", regex=True).astype(float)

    row_rename_map = {
        "Multi-Family": "Multi-family",
        "Warehouses": "Industrial",
        "Office Buildings": "Office",
        "Shopping Centers": "Retail",
        "Other Investment Property": "Other",
        "Hotels": "Lodging",
    }

    property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

    # Adjust
    property_df["Ticker"] = "SNV"
    property_df["Quarter"] = "4Q24"
    property_df["Unit"] = "ths"
    property_df["Currency"] = "USD"
    property_df["Category"] = "CRE"

    column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
    property_df = property_df[column_order]

    # Adjust
    total_row = pd.DataFrame([{
        "Ticker": "SNV",
        "Quarter": "4Q24",
        "CRE Property Type": "Total CRE",
        "Loan Amount": property_df["Loan Amount"].sum(),
        "Unit": "ths",
        "Currency": "USD",
        "Category": "CRE"
    }])

    property_df = pd.concat([property_df, total_row], ignore_index=True)
    # Adjust
    property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else x)

    return property_df

if __name__ == "__main__":
    df = extract_cre_main_table()
    # Adjust
    print("\n================ Extracted 4Q24 CRE Portfolio Table =================")
    print(df,"\n")
