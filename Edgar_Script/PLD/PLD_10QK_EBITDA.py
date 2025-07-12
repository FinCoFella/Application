import pandas as pd
import numpy as np
import requests
import datetime
from pathlib import Path

CIK = '0001045609' # CCI CIK Number
HEADERS = {"User-Agent": "Nik (nd24@ic.ac.uk)"}
CSV = "CCI_10QK_EBITDA.csv"

RECENT_QUARTERS = 10
RECENT_YEARS = 5  
ABS_SIGN_FACTS = {"InterestExpenseDebt": True}

def get_fact_df(data: dict, fact_key: str) -> pd.DataFrame:
    raw_items = data["facts"]["us-gaap"][fact_key]["units"]["USD"]

    for itm in raw_items:
        itm["fy"] = itm.get("fy")
        itm["fp"] = itm.get("fp")
        itm["filed"] = itm.get("filed")
        itm["form"] = itm.get("form")
        itm["start"] = itm.get("start")
        itm["end"] = itm.get("end")

    df = pd.DataFrame(raw_items)
    df = df[df["form"].isin(["10-K", "10-Q"])]

    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df["days"] = (df["end"] - df["start"]).dt.days

    df["val"] = df["val"].astype("int64")
    if ABS_SIGN_FACTS.get(fact_key):
        df["val"] = df["val"].abs()

    return df

def carve_out_q4(df: pd.DataFrame) -> pd.DataFrame:
    ##### Creates synthetic Q4 rows (one per FY) by subtracting Q1–Q3 from the annual 10‑K value #####
    quarters = df[df["days"] < 100].copy()
    annuals = df[df["days"] >= 100].copy()

    q = (quarters.sort_values(["fy", "fp", "end", "filed"], ascending=[True, True, False, False])
              .drop_duplicates(["fy", "fp"], keep="first"))

    a = (annuals.sort_values(["fy", "end", "filed"], ascending=[True, False, False])
                  .drop_duplicates("fy", keep="first"))

    synth = []
    for fy in a["fy"].dropna().unique():
        q_fy_all = q[q["fy"] == fy]
        q_fy     = q_fy_all[q_fy_all["fp"].str.upper().isin({"Q1", "Q2", "Q3"})]

        if q_fy.shape[0] == 3:
            ann_val = int(a.loc[a["fy"] == fy, "val"].iloc[0])
            q4_val  = ann_val - int(q_fy["val"].sum())
            row = a.loc[a["fy"] == fy].iloc[0].copy()
            row.update({
                "fp"  : "Q4",
                "days": 99,
                "val" : np.int64(q4_val),
                "start": datetime.datetime(int(fy), 10, 1),
                "end"  : datetime.datetime(int(fy), 12, 31),
            })
            synth.append(row)

    return (pd.concat([q, pd.DataFrame(synth)], ignore_index=True)
          .sort_values(["fy", "fp"])
          .reset_index(drop=True))

def finalise_quarters(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    df = (
        df[["fy", "fp", "form", "filed", "start", "end", "val"]]
        .drop_duplicates()
        .sort_values("end")
        .reset_index(drop=True)
    )

    df = df.rename(
        columns={
            "fy": "FY",
            "fp": "FP",
            "form": "Form",
            "filed": "File Date",
            "start": "Start Date",
            "end": "End Date",
            "val": value_name,
        }
    )

    df["FY"] = df["FY"].astype("Int64")

    def _quarter(row):
        if pd.isna(row["End Date"]):
            return None
        if row["End Date"].month == 12 and row["End Date"].day == 31:
            return f"4Q{str(row['End Date'].year)[-2:]}"
        if pd.notnull(row["FP"]) and pd.notnull(row["FY"]):
            return row["FP"].replace("Q", "") + "Q" + str(row["FY"])[-2:]
        return None

    df["Quarter"] = df.apply(_quarter, axis=1)

    return df[["FY", "FP", "Quarter", "Form", "File Date", "Start Date", "End Date", value_name]]

def extract_annual(raw_df: pd.DataFrame, value_col: str, value_name: str) -> pd.DataFrame:
    annuals = raw_df[raw_df["days"] >= 100].copy()
    if annuals.empty:
        return pd.DataFrame(columns=["FY", "End Date", value_name])

    latest = (
        annuals.sort_values(["fy", "end", "filed"], ascending=[True, False, False])
        .drop_duplicates("fy", keep="first")
    )
    latest = latest.rename(
        columns={
            "fy": "FY",
            "end": "End Date",
            "val": value_name,
        }
    )
    latest["FY"] = latest["FY"].astype("Int64")
    return latest[["FY", "End Date", value_name]].sort_values("End Date")

def most_recent(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(["Quarter", "End Date", "File Date"], ascending=[True, False, False])
          .drop_duplicates("Quarter", keep="first"))

def show_recent(df: pd.DataFrame, cols: list[str], n: int):
    recent_df = df.sort_values(cols[1]).tail(n)
    print(recent_df[cols].to_string(index=False))

def main():
    json_data = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json", headers=HEADERS
    ).json()

    ni_raw = get_fact_df(json_data, "NetIncomeLoss")
    if "ProfitLoss" in json_data["facts"]["us-gaap"]:
        ni_raw = pd.concat([ni_raw, get_fact_df(json_data, "ProfitLoss")], ignore_index=True)

    ie_raw = get_fact_df(json_data, "InterestExpenseDebt")
    te_raw = get_fact_df(json_data, "IncomeTaxExpenseBenefit")
    da_raw = get_fact_df(json_data, "DepreciationAndAmortization")

    ni_q   = finalise_quarters(carve_out_q4(ni_raw), "Net Income")
    ie_q   = finalise_quarters(carve_out_q4(ie_raw), "Interest Expense")
    te_q   = finalise_quarters(carve_out_q4(te_raw), "Tax Expense")
    da_q   = finalise_quarters(carve_out_q4(da_raw), "D&A Expense")

    ni_a   = extract_annual(ni_raw, "val", "Net Income")
    ie_a   = extract_annual(ie_raw, "val", "Interest Expense")
    te_a   = extract_annual(te_raw, "val", "Tax Expense")
    da_a   = extract_annual(da_raw, "val", "D&A Expense")

    print(f"\n==== Quarterly Net Income ====")
    show_recent(ni_q, ["Quarter", "End Date", "Net Income"], RECENT_QUARTERS)

    print(f"\n==== Annual Net Income ====")
    show_recent(ni_a, ["FY", "End Date", "Net Income"], RECENT_YEARS)

    print(f"\n==== Quarterly Interest Expense ====")
    show_recent(ie_q, ["Quarter", "End Date", "Interest Expense"], RECENT_QUARTERS)

    print(f"\n==== Annual Interest Expense ====")
    show_recent(ie_a, ["FY", "End Date", "Interest Expense"], RECENT_YEARS)

    print(f"\n==== Quarterly Tax Expense  ====")
    show_recent(te_q, ["Quarter", "End Date", "Tax Expense"], RECENT_QUARTERS)

    print(f"\n==== Annual Tax Expense ====")
    show_recent(te_a, ["FY", "End Date", "Tax Expense"], RECENT_YEARS)

    print(f"\n==== Quarterly D&A Expense ====")
    show_recent(da_q, ["Quarter", "End Date", "D&A Expense"], RECENT_QUARTERS)

    print(f"\n==== Annual D&A Expense ====")
    show_recent(da_a, ["FY", "End Date", "D&A Expense"], RECENT_YEARS)

    ###### Merge ######
    ni = most_recent(ni_q)
    ie = most_recent(ie_q)
    te = most_recent(te_q)
    da = most_recent(da_q)

    merged = (
        ni[["Quarter", "End Date", "Net Income"]]
        .merge(ie[["Quarter", "Interest Expense"]], on="Quarter", how="left")
        .merge(te[["Quarter", "Tax Expense"]], on="Quarter", how="left")
        .merge(da[["Quarter", "D&A Expense"]], on="Quarter", how="left")
        .sort_values("End Date")
    )

    merged["Ticker"] = "PLD"
    merged["EBITDA"] = merged[
        ["Net Income", "Interest Expense", "Tax Expense", "D&A Expense"]
    ].sum(axis=1)

    num_cols = [
        "Net Income",
        "Interest Expense",
        "Tax Expense",
        "D&A Expense",
        "EBITDA",
    ]

    merged[num_cols] = merged[num_cols].apply(pd.to_numeric, errors="coerce").astype("Int64")

    recent = merged.tail(10).copy()
    sql_df = recent.melt(
        id_vars=["Ticker", "Quarter"],
        value_vars=["EBITDA"],
        var_name="Line_Item_Name",
        value_name="Value",
    )

    sql_df["Unit"] = "mn"
    sql_df["Currency"] = "USD"
    sql_df["Category"] = "Profitability"

    sql_df["Value"] = (sql_df["Value"].astype(float) / 1_000_000).round(0).astype("Int64")
    sql_df = sql_df[["Ticker", "Quarter", "Line_Item_Name", "Value", "Unit", "Currency", "Category"]]

    ##### CSV Format #####
    export_path = Path(__file__).with_name(CSV)
    sql_df.to_csv(export_path, index=False)

    print("\n====================== SQL Database Format =====================")
    print(sql_df.to_string(index=False))
    print(f"\nSaved SQL EBITDA table to {export_path.resolve()}")

if __name__ == "__main__":
    main()
