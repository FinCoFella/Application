import tabula
import pandas as pd

def extract_cre_main_table():
    pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/SNV/SNV_3Q24_10Q.pdf"
    tables = tabula.read_pdf(pdf_path, pages=54, multiple_tables=True, stream=True)

    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")
    df = tables[0]

    property_df = df.iloc[3:9, [0, 2]].reset_index(drop=True)
    property_df.columns = ['CRE Property Type', 'Loan Amount']

    row_rename_map = {
        "Multi-Family": "Multi-family",
        "Warehouses": "Industrial",
        "Office Buildings": "Office",
        "Shopping Centers": "Retail",
        "Other investment property": "Other",
        "Hotels": "Lodging",
    }

    property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)

    property_df["Ticker"] = "SNV"
    property_df["Quarter"] = "3Q24"
    property_df["Unit"] = "ths"
    property_df["Currency"] = "USD"
    property_df["Category"] = "CRE"

    column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
    property_df = property_df[column_order]

    property_df["Loan Amount"] = property_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

    total_row = pd.DataFrame([{
        "Ticker": "SNV",
        "Quarter": "3Q24",
        "CRE Property Type": "Total CRE",
        "Loan Amount": property_df["Loan Amount"].sum(),
        "Unit": "ths",
        "Currency": "USD",
        "Category": "CRE"
    }])

    property_df = pd.concat([property_df, total_row], ignore_index=True)
    property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}")

    return property_df

if __name__ == "__main__":
    df = extract_cre_main_table()
    print("\n================ Extracted 3Q24 CRE Portfolio Table =================")
    print(df,"\n")
