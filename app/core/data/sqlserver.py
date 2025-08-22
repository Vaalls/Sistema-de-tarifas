# app/core/data/sqlserver.py
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def _conn_str() -> str:
    # Prioriza DSN (ODBC) via env SAFRA_SQLSERVER_ODBC
    dsn = os.getenv("SAFRA_SQLSERVER_ODBC")  # ex: "Driver=ODBC Driver 17 for SQL Server;Server=HOST;Database=DB;Trusted_Connection=yes;TrustServerCertificate=yes"
    if dsn:
        from urllib.parse import quote_plus
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(dsn)}"

    server   = os.getenv("SAFRA_SQLSERVER_SERVER", "localhost")
    database = os.getenv("SAFRA_SQLSERVER_DATABASE", "master")
    user     = os.getenv("SAFRA_SQLSERVER_USER")
    pwd      = os.getenv("SAFRA_SQLSERVER_PASSWORD")
    driver   = os.getenv("SAFRA_SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server").replace(" ", "+")
    trust    = os.getenv("SAFRA_SQLSERVER_TRUSTCERT", "yes")

    if user and pwd:  # SQL Auth
        return f"mssql+pyodbc://{user}:{pwd}@{server}/{database}?driver={driver}&TrustServerCertificate={trust}"
    # Windows Auth
    return f"mssql+pyodbc://@{server}/{database}?driver={driver}&Trusted_Connection=yes&TrustServerCertificate={trust}"

def get_engine() -> Engine:
    return create_engine(_conn_str(), fast_executemany=True, future=True)
