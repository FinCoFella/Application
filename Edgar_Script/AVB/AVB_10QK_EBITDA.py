import pandas as pd
import requests
import datetime
from pathlib import Path

CIK = '0000915912' # AVB CIK Number

start_date = datetime.datetime(2015, 12, 31)
end_date = datetime.datetime(2025, 4, 30)

headers = { 'User-Agent': 'Nik (nd24@ic.ac.uk)', }
download = requests.get('https://data.sec.gov/api/xbrl/companyfacts/CIK'+CIK+'.json', stream=True, headers = headers)
fin_statment = download.json()

us_gaap_concepts = list(fin_statment['facts']['us-gaap'].keys())
net_income = fin_statment['facts']['us-gaap']['ProfitLoss']['units']['USD']
interest_exp = fin_statment['facts']['us-gaap']['InterestExpense']['units']['USD']
tax_exp = fin_statment['facts']['us-gaap']['IncomeTaxExpenseBenefit']['units']['USD']
dep_amort_exp = fin_statment['facts']['us-gaap']['Depreciation']['units']['USD']
gain_loss_sale = fin_statment['facts']['us-gaap']['GainsLossesOnSalesOfInvestmentRealEstate']['units']['USD']

def normalize_items(item_list):
    for item in item_list:
        item['fy'] = item.get('fy', None)  # Fiscal Year
        item['filed'] = item.get('filed', None)  # Filed Date
        item['fp'] = item.get('fp', None)  # Fiscal Period
        item['form'] = item.get('form', None)  # Form
        item['start'] = item.get('start', None)  # Fiscal Period
        item['end'] = item.get('end', None)  # Form

normalize_items(net_income)
normalize_items(interest_exp)
normalize_items(tax_exp)
normalize_items(dep_amort_exp)
normalize_items(gain_loss_sale)

net_income_df = pd.DataFrame(net_income)
interest_exp_df = pd.DataFrame(interest_exp)
tax_exp_df = pd.DataFrame(tax_exp)
dep_amort_exp_df = pd.DataFrame(dep_amort_exp)
gain_loss_sale_df = pd.DataFrame(gain_loss_sale)

for df in [net_income_df, interest_exp_df, tax_exp_df, dep_amort_exp_df, gain_loss_sale_df]:
    df['start'] = pd.to_datetime(df['start'], format="%Y-%m-%d")
    df['end'] = pd.to_datetime(df['end'], format="%Y-%m-%d")
    df['days'] = (df['end']-df['start']).dt.days

net_income_df = net_income_df.dropna(subset=['frame'])
net_income_df = net_income_df[net_income_df['frame'].str.contains('CY')]
net_income_df = net_income_df[net_income_df['form'].isin(['10-K', '10-Q'])].copy()

interest_exp_df = interest_exp_df.dropna(subset=['frame'])
interest_exp_df = interest_exp_df[interest_exp_df['frame'].str.contains('CY')]
interest_exp_df = interest_exp_df[interest_exp_df['form'].isin(['10-K', '10-Q'])].copy()

tax_exp_df = tax_exp_df.dropna(subset=['frame'])
tax_exp_df = tax_exp_df[tax_exp_df['frame'].str.contains('CY')]
tax_exp_df = tax_exp_df[tax_exp_df['form'].isin(['10-K', '10-Q'])].copy()

dep_amort_exp_df = dep_amort_exp_df.dropna(subset=['frame'])
dep_amort_exp_df = dep_amort_exp_df[dep_amort_exp_df['frame'].str.contains('CY')]
dep_amort_exp_df = dep_amort_exp_df[dep_amort_exp_df['form'].isin(['10-K', '10-Q'])].copy()

gain_loss_sale_df = gain_loss_sale_df.dropna(subset=['frame'])
gain_loss_sale_df = gain_loss_sale_df[gain_loss_sale_df['frame'].str.contains('CY')]
gain_loss_sale_df = gain_loss_sale_df[gain_loss_sale_df['form'].isin(['10-K', '10-Q'])].copy()

for i in range(3, net_income_df.shape[0]):
    if net_income_df.loc[net_income_df.index[i], 'days'] > 100:
        net_income_df.loc[net_income_df.index[i], 'val'] = (
            net_income_df.loc[net_income_df.index[i], 'val']
            - net_income_df.loc[net_income_df.index[i-1], 'val']
            - net_income_df.loc[net_income_df.index[i-2], 'val']
            - net_income_df.loc[net_income_df.index[i-3], 'val']
        )
        net_income_df.loc[net_income_df.index[i], 'days'] = 99
net_income_df = net_income_df[net_income_df['days'] < 100]

for i in range(3, interest_exp_df.shape[0]):
    if interest_exp_df.loc[interest_exp_df.index[i], 'days'] > 100:
        interest_exp_df.loc[interest_exp_df.index[i], 'val'] = (
            interest_exp_df.loc[interest_exp_df.index[i], 'val']
            - interest_exp_df.loc[interest_exp_df.index[i-1], 'val']
            - interest_exp_df.loc[interest_exp_df.index[i-2], 'val']
            - interest_exp_df.loc[interest_exp_df.index[i-3], 'val']
        )
        interest_exp_df.loc[interest_exp_df.index[i], 'days'] = 99
interest_exp_df = interest_exp_df[interest_exp_df['days'] < 100]

for i in range(3, tax_exp_df.shape[0]):
    if tax_exp_df.loc[tax_exp_df.index[i], 'days'] > 100:
        tax_exp_df.loc[tax_exp_df.index[i], 'val'] = (
            tax_exp_df.loc[tax_exp_df.index[i], 'val']
            - tax_exp_df.loc[tax_exp_df.index[i-1], 'val']
            - tax_exp_df.loc[tax_exp_df.index[i-2], 'val']
            - tax_exp_df.loc[tax_exp_df.index[i-3], 'val']
        )
        tax_exp_df.loc[tax_exp_df.index[i], 'days'] = 99
tax_exp_df = tax_exp_df[tax_exp_df['days'] < 100]

for i in range(3, dep_amort_exp_df.shape[0]):
    if dep_amort_exp_df.loc[dep_amort_exp_df.index[i], 'days'] > 100:
        dep_amort_exp_df.loc[dep_amort_exp_df.index[i], 'val'] = (
            dep_amort_exp_df.loc[dep_amort_exp_df.index[i], 'val']
            - dep_amort_exp_df.loc[dep_amort_exp_df.index[i-1], 'val']
            - dep_amort_exp_df.loc[dep_amort_exp_df.index[i-2], 'val']
            - dep_amort_exp_df.loc[dep_amort_exp_df.index[i-3], 'val']
        )
        dep_amort_exp_df.loc[dep_amort_exp_df.index[i], 'days'] = 99
dep_amort_exp_df = dep_amort_exp_df[dep_amort_exp_df['days'] < 100]

for i in range(3, gain_loss_sale_df.shape[0]):
    if gain_loss_sale_df.loc[gain_loss_sale_df.index[i], 'days'] > 100:
        gain_loss_sale_df.loc[gain_loss_sale_df.index[i], 'val'] = (
            gain_loss_sale_df.loc[gain_loss_sale_df.index[i], 'val']
            - gain_loss_sale_df.loc[gain_loss_sale_df.index[i-1], 'val']
            - gain_loss_sale_df.loc[gain_loss_sale_df.index[i-2], 'val']
            - gain_loss_sale_df.loc[gain_loss_sale_df.index[i-3], 'val']
        )
        gain_loss_sale_df.loc[gain_loss_sale_df.index[i], 'days'] = 99
gain_loss_sale_df = gain_loss_sale_df[gain_loss_sale_df['days'] < 100]

# ========== Net Income DataFrame ========== #
net_income_df = net_income_df[['fy', 'fp', 'form', 'filed', 'start', 'end', 'val']].drop_duplicates()
net_income_df = net_income_df.sort_values(['end']).reset_index(drop=True)
net_income_df.rename(columns={
    'fy': 'FY',
    'fp': 'FP',
    'form': 'Form',
    'filed': 'File Date',
    'start': 'Start Date',
    'end': 'End Date',
    'val': 'Net Income'
}, inplace=True)
net_income_df['FY'] = net_income_df['FY'].astype('Int64')
net_income_df['Quarter'] = net_income_df['End Date'].apply(
    lambda d: (
        f"{(d.month // 3)}Q{str(d.year)[-2:]}" if d.month in [3, 6, 9, 12]
        else None
    ) if pd.notnull(d) else None
)
net_income_df = net_income_df[['FY', 'FP', 'Quarter', 'Form', 'File Date', 'Start Date', 'End Date', 'Net Income']]

# ========== Interest Expense DataFrame ========== #
interest_exp_df = interest_exp_df[['fy', 'fp', 'form', 'filed', 'start', 'end', 'val']].drop_duplicates()
interest_exp_df = interest_exp_df.sort_values(['end']).reset_index(drop=True)
interest_exp_df.rename(columns={
    'fy': 'FY',
    'fp': 'FP',
    'form': 'Form',
    'filed': 'File Date',
    'start': 'Start Date',
    'end': 'End Date',
    'val': 'Interest Expense'
}, inplace=True)
interest_exp_df['FY'] = interest_exp_df['FY'].astype('Int64')
interest_exp_df['Quarter'] = interest_exp_df.apply(
    lambda row: (
        '4Q' + str(row['End Date'].year)[-2:]
        if pd.notnull(row['End Date']) and row['End Date'].month == 12 and row['End Date'].day == 31
        else (
            row['FP'].replace('Q', '') + 'Q' + str(row['FY'])[-2:]
            if pd.notnull(row['FP']) and pd.notnull(row['FY']) else None
        )
    ),
    axis=1
)
interest_exp_df = interest_exp_df[['FY', 'FP', 'Quarter', 'Form', 'File Date', 'Start Date', 'End Date', 'Interest Expense']]

# ========== Tax Expense DataFrame ========== #
tax_exp_df = tax_exp_df[['fy', 'fp', 'form', 'filed', 'start', 'end', 'val']].drop_duplicates()
tax_exp_df = tax_exp_df.sort_values(['end']).reset_index(drop=True)
tax_exp_df.rename(columns={
        'fy': 'FY',
    'fp': 'FP',
    'form': 'Form',
    'filed': 'File Date',
    'start': 'Start Date',
    'end': 'End Date',
    'val': 'Tax Expense'
}, inplace=True)

tax_exp_df['FY'] = tax_exp_df['FY'].astype('Int64')
tax_exp_df['Quarter'] = tax_exp_df.apply(
    lambda row: (
        '4Q' + str(row['End Date'].year)[-2:]
        if pd.notnull(row['End Date']) and row['End Date'].month == 12 and row['End Date'].day == 31
        else (
            row['FP'].replace('Q', '') + 'Q' + str(row['FY'])[-2:]
            if pd.notnull(row['FP']) and pd.notnull(row['FY']) else None
        )
    ),
    axis=1
)
tax_exp_df = tax_exp_df[['FY', 'FP', 'Quarter', 'Form', 'File Date', 'Start Date', 'End Date', 'Tax Expense']]

# ========== Depreciation & Amortization Expense DataFrame ========== #
dep_amort_exp_df = dep_amort_exp_df[['fy', 'fp', 'form', 'filed', 'start', 'end', 'val']].drop_duplicates()
dep_amort_exp_df = dep_amort_exp_df.sort_values(['end']).reset_index(drop=True)
dep_amort_exp_df.rename(columns={
    'fy': 'FY',
    'fp': 'FP',
    'form': 'Form',
    'filed': 'File Date',
    'start': 'Start Date',
    'end': 'End Date',
    'val': 'D&A Expense'
}, inplace=True)

dep_amort_exp_df['FY'] = dep_amort_exp_df['FY'].astype('Int64')
dep_amort_exp_df['Quarter'] = dep_amort_exp_df.apply(
    lambda row: (
        '4Q' + str(row['End Date'].year)[-2:]
        if pd.notnull(row['End Date']) and row['End Date'].month == 12 and row['End Date'].day == 31
        else (
            row['FP'].replace('Q', '') + 'Q' + str(row['FY'])[-2:]
            if pd.notnull(row['FP']) and pd.notnull(row['FY']) else None
        )
    ),
    axis=1
)
dep_amort_exp_df = dep_amort_exp_df[['FY', 'FP', 'Quarter', 'Form', 'File Date', 'Start Date', 'End Date', 'D&A Expense']]

# ========== Gain/Loss on Sale DataFrame ========== #
gain_loss_sale_df = gain_loss_sale_df[['fy', 'fp', 'form', 'filed', 'start', 'end', 'val']].drop_duplicates()
gain_loss_sale_df = gain_loss_sale_df.sort_values(['end']).reset_index(drop=True)
gain_loss_sale_df.rename(columns={
    'fy': 'FY',
    'fp': 'FP',
    'form': 'Form',
    'filed': 'File Date',
    'start': 'Start Date',
    'end': 'End Date',
    'val': 'Gain Loss on Sale'
}, inplace=True)

gain_loss_sale_df['FY'] = gain_loss_sale_df['FY'].astype('Int64')
gain_loss_sale_df['Quarter'] = gain_loss_sale_df.apply(
    lambda row: (
        '4Q' + str(row['End Date'].year)[-2:]
        if pd.notnull(row['End Date']) and row['End Date'].month == 12 and row['End Date'].day == 31
        else (
            row['FP'].replace('Q', '') + 'Q' + str(row['FY'])[-2:]
            if pd.notnull(row['FP']) and pd.notnull(row['FY']) else None
        )
    ),
    axis=1
)
gain_loss_sale_df = gain_loss_sale_df[['FY', 'FP', 'Quarter', 'Form', 'File Date', 'Start Date', 'End Date', 'Gain Loss on Sale']]

print("\n=========================== Net Income Table ============================")
print(net_income_df.tail(15))

print("\n=========================== Interest Expense Table ============================")
print(interest_exp_df.tail(15))

print("\n=========================== Tax Expense Table ============================")
print(tax_exp_df.tail(15))

print("\n=========================== D&A Expense Table ============================")
print(dep_amort_exp_df.tail(15))

print("\n=========================== Gain/Loss on Sale Table ============================")
print(gain_loss_sale_df.tail(15))

# ========== Merged Table ========== #
net_income_df = net_income_df.sort_values(by=['Quarter', 'End Date', 'File Date'], ascending=[True, False, False])
net_income_df = net_income_df.drop_duplicates(subset=['Quarter'], keep='first')

interest_exp_df = interest_exp_df.sort_values(by=['Quarter', 'End Date', 'File Date'], ascending=[True, False, False])
interest_exp_df = interest_exp_df.drop_duplicates(subset=['Quarter'], keep='first')

tax_exp_df = tax_exp_df.sort_values(by=['Quarter', 'End Date', 'File Date'], ascending=[True, False, False])
tax_exp_df = tax_exp_df.drop_duplicates(subset=['Quarter'], keep='first')

dep_amort_exp_df = dep_amort_exp_df.sort_values(by=['Quarter', 'End Date', 'File Date'], ascending=[True, False, False])
dep_amort_exp_df = dep_amort_exp_df.drop_duplicates(subset=['Quarter'], keep='first')

gain_loss_sale_df = gain_loss_sale_df.sort_values(by=['Quarter', 'End Date', 'File Date'], ascending=[True, False, False])
gain_loss_sale_df = gain_loss_sale_df.drop_duplicates(subset=['Quarter'], keep='first')

merged_quarter_df = (
    net_income_df[['Quarter','End Date','Net Income']]
        .merge(interest_exp_df[['Quarter','Interest Expense']], on='Quarter', how='left')
        .merge(tax_exp_df[['Quarter','Tax Expense']], on='Quarter', how='left')
        .merge(dep_amort_exp_df[['Quarter','D&A Expense']], on='Quarter', how='left')
        .merge(gain_loss_sale_df[['Quarter','Gain Loss on Sale']], on='Quarter', how='left')
        .sort_values('End Date')
)

merged_quarter_df = merged_quarter_df.sort_values(by='End Date', ascending=True)

merged_quarter_df['EBITDARe'] = (
      merged_quarter_df['Net Income']
    + merged_quarter_df['Interest Expense']
    + merged_quarter_df['Tax Expense']
    + merged_quarter_df['D&A Expense']
    - merged_quarter_df['Gain Loss on Sale']
)

merged_quarter_df['EBITDA'] = (
      merged_quarter_df['Net Income']
    + merged_quarter_df['Interest Expense']
    + merged_quarter_df['Tax Expense']
    + merged_quarter_df['D&A Expense']
)

merged_quarter_df['Ticker'] = 'AVB'
merged_quarter_df = merged_quarter_df[['Ticker', 'Quarter', 'End Date', 'Net Income', 'Interest Expense', 'Tax Expense', 'D&A Expense', 'Gain Loss on Sale', 'EBITDARe', 'EBITDA']]

int_cols = ['Net Income', 'Interest Expense', 'Tax Expense', 'D&A Expense', 'Gain Loss on Sale', 'EBITDARe', 'EBITDA']
merged_quarter_df[int_cols] = (merged_quarter_df[int_cols].apply(pd.to_numeric, errors='coerce').round().astype('Int64'))

recent_10_entries = merged_quarter_df.tail(15)
print("\n================================================= Merged EBITDA Table ==================================================")
print(recent_10_entries.to_string(index=False, justify='center'))

recent_10_entries = merged_quarter_df.tail(10).copy()
sql_df = (recent_10_entries.melt(id_vars = ["Ticker", "Quarter"], value_vars = ["EBITDA"], var_name="Line_Item_Name", value_name="Value"))

sql_df["Unit"]     = "mn"
sql_df["Currency"] = "USD"            
sql_df["Category"] = "Profitability"

sql_df = sql_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

sql_df["Value"] = sql_df["Value"].astype(float) / 1_000_000 
sql_df["Value"] = sql_df["Value"].round(0).astype("Int64")

print("\n====================== SQL Database Format =====================")
print(sql_df.to_string(index=False))

SCRIPT_DIR = Path(__file__).resolve().parent
CSV = SCRIPT_DIR / "AVB_10QK_EBITDA.csv"
sql_df.to_csv(CSV, index=False)

print(f"\n Saved SQL Unsecured Debt Table to {CSV}")