import pands as pd

def unsecured_debt_to_ebitda(df: pd.DataFrame) -> pd.DataFrame:

    filt = df["Line_Item_Name"].isin(["EBITDA", "Total Unsecured Debt"])
    piv = (df.loc[filt].pivot(index="Quarter", columns="Line_Item_Name", values="Value").dropna().sort_index())

    piv["Unsecured_Debt_to_EBITDA"] = piv["Total Unsecured Debt"] / (piv["EBITDA"] * 4)

    return piv.reset_index()[["Quarter", "Unsecured_Debt_to_EBITDA"]]