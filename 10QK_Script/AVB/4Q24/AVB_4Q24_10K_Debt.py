import tabula
import pandas as pd

# Adjust
pdf_path = "/home/fincofella/dev/Application/10QK_PDFs/AVB/AVB_2024_10K.pdf"
# Adjust
tables = tabula.read_pdf(pdf_path, pages=84, multiple_tables=True, stream=True, pandas_options={"header": None})

for i, table in enumerate(tables):
    print(f"Table {i}:\n", table, "\n")

debt_maturity_df = tables[0]

debt_maturity_df = debt_maturity_df.drop(columns=debt_maturity_df.columns[[1, 3, 5]])
debt_maturity_df = debt_maturity_df.drop(index=debt_maturity_df.index[-1])

debt_maturity_df.columns = ["Year", "Secured Debt", "Unsecured Debt"]
debt_maturity_df["Year"] = debt_maturity_df["Year"].ffill()

for col in ["Secured Debt", "Unsecured Debt"]:
    debt_maturity_df[col] = (
        debt_maturity_df[col]
        .replace({r"," : ""}, regex=True)
        .astype(float)
        .div(1_000)
        .fillna(0)
    )

debt_final_df = (debt_maturity_df.groupby("Year", as_index=False, sort=False).sum(numeric_only=True))

total_amount = debt_final_df[["Secured Debt", "Unsecured Debt"]].sum()
debt_final_df.loc[len(debt_final_df)] = ["Total", total_amount["Secured Debt"], total_amount["Unsecured Debt"]]

for col in ["Secured Debt", "Unsecured Debt"]:
    debt_final_df[col] = debt_final_df[col].astype(int).map("{:,}".format)

print("\n======== Debt Maturity Table ($mn) ========")
print(debt_final_df)

unsecured_debt = debt_final_df[~debt_final_df["Year"].str.contains("Total", case=False)]

yearly = unsecured_debt.copy()
yearly["Unsecured Debt"] = (yearly["Unsecured Debt"].str.replace(",", "", regex=False).astype(float))

# Adjust
def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    y = int(year)
    if 2024 <= y <= 2029:
        return "Near-term"
    if 2030 <= y <= 2033:
        return "Medium-term"
    if year == "2034":
        return "Long-term"
    return "Other"

yearly["Bucket"] = yearly["Year"].apply(bucket)

bucket_sums = (yearly.groupby("Bucket", as_index=False, sort=False).agg({"Unsecured Debt": "sum"}))
total_debt = bucket_sums["Unsecured Debt"].sum() 

# Adjust
debt_buckets_df = pd.DataFrame({
    "Ticker":   "AVB",
    "Quarter":  "4Q24",
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":   bucket_sums["Unsecured Debt"].astype(int).map("{:,}".format),
    "Unit":     "mn",
    "Currency": "USD",
    "Category": "Unsecured Debt",
})

debt_buckets_df.loc[len(debt_buckets_df)] = [
    "AVB",
    "4Q24",
    "Total Unsecured Debt",
    f"{int(total_debt):,}",
    "mn",
    "USD",
    "Unsecured Debt"
]

print("\n======================== Unsecured Debt Buckets =======================")
print(debt_buckets_df.to_string(index=False))
