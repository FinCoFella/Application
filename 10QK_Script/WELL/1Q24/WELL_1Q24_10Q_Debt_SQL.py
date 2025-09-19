from sqlalchemy import create_engine
from pathlib import Path
import pandas as pd
import urllib
import os
from dotenv import load_dotenv 

load_dotenv()
##### Load environment variables to grab SQL Server credentials #####
SQL_SSMS_USER = os.getenv("SQL_SSMS_USER")
SQL_SSMS_PASS = os.getenv("SQL_SSMS_PASS")

##### Read the CSV file created by the corresponding script file into a Pandas DataFrame #####
sql_df = pd.read_csv(Path(__file__).with_name("WELL_1Q24_unsecured_debt.csv"))

##### Build the ODBC connection string to connect to the SQL Server database #####
odbc = (
    "DRIVER=ODBC Driver 17 for SQL Server;"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_REITs;"
    f"UID={SQL_SSMS_USER};"
    f"PWD={SQL_SSMS_PASS};"
    "TrustServerCertificate=Yes;"
)

##### Build a SQLAlchemy engine using the ODBC connection string #####
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}", fast_executemany=True)
##### Export Pandas DataFrame to SQL Server table 'Financial_Line_Item' #####
sql_df.to_sql("Financial_Line_Item", engine, schema="dbo", if_exists="append", index=False, method="multi")

print("Data successfully exported to SQL.")
