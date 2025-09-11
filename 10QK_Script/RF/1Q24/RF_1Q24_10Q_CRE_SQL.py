from sqlalchemy import create_engine
from pathlib import Path
import pandas as pd
import urllib
import os
from dotenv import load_dotenv 

load_dotenv()

##### LOAD ENVIRONMENT VARIABLES #####
SQL_SSMS_USER = os.getenv("SQL_SSMS_USER")
SQL_SSMS_PASS = os.getenv("SQL_SSMS_PASS")

##### CSV CONVERTED INTO PANDAS DATAFRAME #####
sql_df = pd.read_csv(Path(__file__).with_name("RF_1Q24_cre.csv"))

##### BUILD ODBC CONNECTION STRING TO CONNECT TO SQL SERVER DATABASE #####
odbc = (
    "DRIVER=ODBC Driver 17 for SQL Server;"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_Banks;"
    f"UID={SQL_SSMS_USER};"
    f"PWD={SQL_SSMS_PASS};"
    "TrustServerCertificate=Yes;"
)

##### BUILD SQLALCHEMY ENGINE TO CONNECT TO SQL SERVER DATABASE #####
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",fast_executemany=True)

##### EXPORT PANDAS DATAFRAME TO SQL SERVER DATABASE AND SPECIFIC RELATION #####
sql_df.to_sql("Financial_Line_Item", engine, schema="dbo", if_exists="append", index=False, method="multi")

print("Data successfully exported to SQL.")
