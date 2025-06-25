import pandas as pd
from sqlalchemy import create_engine

sql_df = pd.read_csv("cre_loan_data.csv")

server = '10.82.193.77'
port = '1433'
database = 'US_Banks'
username = 'FinCoFella'
password = 'ND24ICL'
driver = 'ODBC Driver 17 for SQL Server'

connection_string = (
    f"mssql+pyodbc://{username}:{password}@{server},{port}/{database}"
    f"?driver={driver.replace(' ', '+')}"
)

engine = create_engine(connection_string)

sql_df.to_sql('Financial_Line_Item', con=engine, if_exists='append', index=False)

print("✅ Data successfully exported to SQL.")
