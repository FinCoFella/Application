from pathlib import Path
import pandas as pd
import urllib
from sqlalchemy import create_engine

sql_df = pd.read_csv(Path(__file__).with_name("AVB_3Q24_unsecured_debt.csv"))

odbc = (
    "DRIVER=ODBC Driver 17 for SQL Server;"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_REITs;"
    "UID=FinCoFella;"
    "PWD=ND24ICL;"
    "TrustServerCertificate=Yes;"
)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",
    fast_executemany=True
)

sql_df.to_sql("Financial_Line_Item", engine, schema="dbo",
          if_exists="append", index=False, method="multi")

print("Data successfully exported to SQL.")
