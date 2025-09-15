from sqlalchemy import text
import pandas as pd

#### FUNCTION TO LOAD BANK DATA FOR A SPECIFIC TICKER AND QUARTER ####
def load_ticker_bank(ticker: str, quarter: str, engine) -> pd.DataFrame:

    sql = text( """
        SELECT  Ticker, Quarter, Line_Item_Name, Value, Unit, Currency, Category
        FROM    dbo.Financial_Line_Item
        WHERE   Ticker = :ticker AND Quarter = :quarter
        ORDER BY Line_Item_Name
    """)
    
    with engine.begin() as conn:
        return pd.read_sql(sql, conn, params={"ticker": ticker.upper(), "quarter": quarter})