from SNV_1Q24_10Q_CRE_v1 import extract_cre_main_table
from SNV_1Q24_10Q_CRE_v2 import extract_cre_other_table
import pandas as pd
from pathlib import Path

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
grouped["Quarter"] = "1Q24"
grouped["Unit"] = "mn"
grouped["Currency"] = "USD"
grouped["Category"] = "CRE"

grouped = grouped[["Ticker", "Quarter", "CRE Property Type", "Loan Amount", "Unit", "Currency", "Category"]]
grouped["Loan Amount"] = grouped["Loan Amount"] / 1000

# Adjust
total_row = pd.DataFrame([{
    "Ticker": "SNV",
    "Quarter": "1Q24",
    "CRE Property Type": "Total CRE",
    "Loan Amount": grouped["Loan Amount"].sum(),
    "Unit": "mn",
    "Currency": "USD",
    "Category": "CRE"
}])

final_df = pd.concat([grouped, total_row], ignore_index=True)
final_df["Loan Amount"] = final_df["Loan Amount"].apply(lambda x: f"{int(round(x)):,.0f}")

# Adjust
print("\n=============== Merged CRE 1Q24 Loan Portfolio Table ================")
print(final_df, "\n")

final_df["Value"] = final_df["Loan Amount"].str.replace(",", "", regex=False).astype(int)
final_df = final_df.rename(columns={"CRE Property Type": "Line_Item_Name"})
final_df = final_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

print("\n========================= SQL Format ========================")
print(final_df)

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "SNV_1Q24_cre.csv"
final_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")
