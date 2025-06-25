from SNV_4Q24_10Q_CRE_v1 import extract_cre_main_table
from SNV_4Q24_10Q_CRE_v2 import extract_cre_other_table
import pandas as pd

df1 = extract_cre_main_table()
df2 = extract_cre_other_table()

df1 = df1[df1["CRE Property Type"] != "Total CRE"]
combined_cre_df = pd.concat([df1, df2], ignore_index=True)

combined_cre_df["Loan Amount"] = combined_cre_df["Loan Amount"].replace({",": ""}, regex=True).astype(float)

grouped = (
    combined_cre_df
    .groupby("CRE Property Type", as_index=False)
    .agg({"Loan Amount": "sum"})
)

# Adjust
grouped["Ticker"] = "SNV"
grouped["Quarter"] = "4Q24"
grouped["Unit"] = "mn"
grouped["Currency"] = "USD"
grouped["Category"] = "CRE"

grouped = grouped[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]]
grouped["Loan Amount"] = grouped["Loan Amount"] / 1000

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "SNV",
    "Quarter": "4Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": grouped["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

final_df = pd.concat([grouped, total_row], ignore_index=True)
final_df["Loan Amount"] = final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,.0f}")

# Adjust
print("\n=============== Merged CRE 4Q24 Loan Portfolio Table ================")
print(final_df, "\n")

sql_df = final_df.copy()
sql_df['Loan Amount'] = sql_df['Loan Amount'].str.replace(',', '').astype(float).round(0).astype(int)
sql_df.rename(columns={"CRE Property Type": "Line_Item_Name", "Loan Amount": "Value"}, inplace=True)
sql_df.to_csv("cre_loan_data_merged.csv", index=False)
combined_cre_df.to_csv("cre_loan_data_merged.csv", index=False)
