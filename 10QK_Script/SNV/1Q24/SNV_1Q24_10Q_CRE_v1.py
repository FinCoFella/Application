import tabula
import pandas as pd

def extract_cre_main_table():
    
    ##### Extract tables from a specific page of the 10-Q PDF using tabula-py #####
    pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/SNV/SNV_1Q24_10Q.pdf"
    tables = tabula.read_pdf(pdf_path, pages=62, multiple_tables=True, stream=True)

    ##### Print all extracted tables and place the first table into a DataFrame #####
    for i, table in enumerate(tables):
        print(f"Table {i}:\n", table, "\n")
    df = tables[0]

    ##### Select specific rows and columns, reset the index #####
    raw = df.iloc[4:10, 0].dropna().reset_index(drop=True)
    property_df = pd.DataFrame()

    ##### Extract a 'CRE Property Type' label and 'Loan Amount' value using regular expressions and convert 'Loan Amount' to float #####
    property_df["CRE Property Type"] = raw.str.extract(r"^([A-Za-z\s\-]+)")[0].str.strip().str.title()
    property_df["Loan Amount"] = raw.str.extract(r"(\$?\s*\d[\d,]*)")[0]
    property_df["Loan Amount"] = property_df["Loan Amount"].str.replace("[\$,]", "", regex=True).astype(float)

    ##### Rename the original labels in 'CRE Property Type' column to a set of standardised labels #####
    row_rename_map = {
        "Multi-Family": "Multi-family",
        "Warehouses": "Industrial",
        "Office Buildings": "Office",
        "Shopping Centers": "Retail",
        "Other Investment Property": "Other",
        "Hotels": "Lodging",
    }

    ##### Apply the renaming map to the DataFrame #####
    property_df["CRE Property Type"] = property_df["CRE Property Type"].replace(row_rename_map)
    
    ##### Add additional columns with constant values to the DataFrame #####
    property_df["Ticker"] = "SNV"
    property_df["Quarter"] = "1Q24"
    property_df["Unit"] = "ths"
    property_df["Currency"] = "USD"
    property_df["Category"] = "CRE"

    ##### Reorder the columns of the DataFrame #####
    column_order = ["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]
    property_df = property_df[column_order]

    ##### Create a 'Total CRE' row and append it to the DataFrame that sums the 'Loan Amount' column #####
    total_row = pd.DataFrame([{
        "Ticker": "SNV",
        "Quarter": "1Q24",
        "CRE Property Type": "Total CRE",
        "Loan Amount": property_df["Loan Amount"].sum(),
        "Unit": "ths",
        "Currency": "USD",
        "Category": "CRE"
    }])

    ##### Append the 'Total CRE' row to the DataFrame #####
    property_df = pd.concat([property_df, total_row], ignore_index=True)
    
    ##### Format the 'Loan Amount' column with commas #####
    property_df["Loan Amount"] = property_df["Loan Amount"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else x)

    return property_df

if __name__ == "__main__":
    df = extract_cre_main_table()
    
    print("\n================ Extracted 1Q24 CRE Portfolio Table =================")
    print(df,"\n")
