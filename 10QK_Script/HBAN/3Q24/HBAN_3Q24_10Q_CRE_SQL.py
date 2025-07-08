from sqlalchemy import create_engine
from pathlib import Path
import pandas as pd
import urllib
import os
from dotenv import load_dotenv 

load_dotenv()

SQL_SSMS_USER = os.getenv("SQL_SSMS_USER")
SQL_SSMS_PASS = os.getenv("SQL_SSMS_PASS")

sql_df = pd.read_csv(Path(__file__).with_name("HBAN_3Q24_cre.csv"))

odbc = (
    "DRIVER=ODBC Driver 17 for SQL Server;"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_Banks;"
    f"UID={SQL_SSMS_USER};"
    f"PWD={SQL_SSMS_PASS};"
    "TrustServerCertificate=Yes;"
)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",
    fast_executemany=True
)

sql_df.to_sql("Financial_Line_Item", engine, schema="dbo",
          if_exists="append", index=False, method="multi")

print("Data successfully exported to SQL.")
