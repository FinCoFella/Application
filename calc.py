import pandas as pd

##### Annualize the EBIITDA financial metric and calculate the Unsecured-debt-to-EBITDA financial ratio #####
def unsecured_debt_to_ebitda(df: pd.DataFrame, periods_per_year: int = 4,) -> pd.DataFrame:

    mask = df["Line_Item_Name"].isin(["EBITDA", "Total Unsecured Debt"])
    pivot = (df.loc[mask].pivot(index="Quarter", columns="Line_Item_Name", values="Value").dropna().sort_index())

    ratio = (pivot["Total Unsecured Debt"] / (pivot["EBITDA"] * periods_per_year)).rename("Unsecured_Debt_to_EBITDA")

    return ratio.reset_index()