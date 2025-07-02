import os
import re
import base64
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

ticker = input("Enter the Ticker: ").strip()
quarter = input("Enter the Quarter: ").strip()
units = input("Enter the Units: ").strip()
currency = input("Enter the Currency: ").strip()
category = input("Enter the Category: ").strip()

# Adjust
image_path = "Images/AVB/AVB_1Q24_Debt.png"
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

instruction_text = (
    f"Extract the tabular data from this image in the following format: ."
    f"| Year |  Secured Debt | Unsecured Debt | \n"
    f"|------|---------------|--------------- | \n"
    f"- Preserve the order of rows and include a final 'Total' row.\n"
    f"Return only the markdown table."
)

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", "text": instruction_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
)

markdown_table = completion.choices[0].message.content
print("\nRaw Markdown Table:\n")
print(markdown_table)

lines = markdown_table.strip().split('\n')
rows = [re.split(r'\s*\|\s*', row.strip())[1:-1] for row in lines if "|" in row and "---" not in row]
df = pd.DataFrame(rows[1:], columns=rows[0])

### Corrections ###
df.loc[df["Year"] == "", "Secured Debt"] = ""
df.loc[df["Year"] == "", "Unsecured Debt"] = ""

df["Secured Debt Clean"] = (df["Secured Debt"].str.replace(r"[\$,]", "", regex=True).str.strip().astype(float))
df["Unsecured Debt Clean"] = (df["Unsecured Debt"].str.replace(r"[\$,]", "", regex=True).str.strip().astype(float))
df = df[["Year", "Secured Debt", "Unsecured Debt"]]

print("\nFinal Adjusted Table:\n")
print(df.to_markdown(index=False))

Unsecured_debt_df = df.copy()
Unsecured_debt_df["Unsecured_Num"] = (
    Unsecured_debt_df["Unsecured Debt"]
    .str.replace(r"[\$,]", "", regex=True)
    .astype(float)
    .div(1_000)
)
Unsecured_debt_df = Unsecured_debt_df[~Unsecured_debt_df["Year"].str.contains("Total", case=False)]

def bucket(year):
    if year == "Thereafter":
        return "Long-term"
    if year.isdigit():                 
        yr = int(year)
        if 2024 <= yr <= 2029:
            return "Near-term"
        if 2030 <= yr <= 2033:
            return "Medium-term"
        if yr == 2034: # Adjust
            return "Long-term"
    return "Other"

Unsecured_debt_df["Bucket"] = Unsecured_debt_df["Year"].apply(bucket)
df_work = Unsecured_debt_df.dropna(subset=["Bucket"])
bucket_sums = (df_work.groupby("Bucket", sort=False, as_index=False).agg({"Unsecured_Num": "sum"}))

grand_total = bucket_sums["Unsecured_Num"].sum()

total_row = {
    "Ticker":   ticker,
    "Quarter":  quarter,
    "Unsecured Debt": "Total Unsecured Debt",
    "Amount":   f"{int(grand_total):,}",
    "Unit":     units,
    "Currency": currency,
    "Category": category
}

debt_buckets_df = pd.DataFrame({
    "Ticker":         ticker,
    "Quarter":        quarter,
    "Unsecured Debt": bucket_sums["Bucket"],
    "Amount":         bucket_sums["Unsecured_Num"].astype(int).map("{:,}".format),
    "Unit":           units,
    "Currency":       currency,
    "Category":       category 
})

debt_buckets_df.loc[len(debt_buckets_df)] = total_row 

print("\n====================== Unsecured Debt Buckets =========================")
print(debt_buckets_df.to_string(index=False))
