from sqlalchemy import create_engine, text
from pathlib import Path
import pandas as pd
import urllib
import os
from dotenv import load_dotenv  

load_dotenv()

SQL_SSMS_USER = os.getenv("SQL_SSMS_USER")
SQL_SSMS_PASS = os.getenv("SQL_SSMS_PASS")

odbc = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.24.112.1,1433;"
    "DATABASE=US_Banks;"
    f"UID={SQL_SSMS_USER};"
    f"PWD={SQL_SSMS_PASS};"
    "Encrypt=Yes;"
    "TrustServerCertificate=Yes;"
    "Connection Timeout=5;"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}",fast_executemany=True)

with engine.connect() as conn:
    row1 = conn.execute(text("SELECT @@SERVERNAME AS server_name, DB_NAME() AS db_name")).fetchone()
    row2 = conn.execute(text("""
        SELECT
            CAST(CONNECTIONPROPERTY('local_net_address')  AS varchar(64)) AS ip,
            CAST(CONNECTIONPROPERTY('local_tcp_port')     AS int)         AS port,
            CAST(CONNECTIONPROPERTY('client_net_address') AS varchar(64)) AS client_ip,
            CAST(CONNECTIONPROPERTY('net_transport')      AS varchar(20)) AS transport
    """)).fetchone()
    print(row1) 
    print(row2)
