# app/core/data/sqlserver.py
from __future__ import annotations
import os
from functools import lru_cache
from typing import Any, Optional
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def _build_conn_str() -> str:
    """
    Monta a connection string mssql+pyodbc.
    Prioriza variáveis HOST/DB/USER/PASSWORD; se existir DSN, usa DSN.
    """
    dsn = os.getenv("MSSQL_DSN")
    driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
    trust = os.getenv("MSSQL_TRUST_CERT", "yes")
    timeout = int(os.getenv("MSSQL_TIMEOUT", "5"))

    if dsn:
        # DSN já criado no ODBC do Windows
        return f"mssql+pyodbc:///?odbc_connect=DSN={dsn};TrustServerCertificate={trust};LoginTimeout={timeout}"

    host = os.getenv("MSSQL_HOST", "localhost")
    db   = os.getenv("MSSQL_DB", "BancoCGM")
    user = os.getenv("MSSQL_USER", "")
    pwd  = os.getenv("MSSQL_PASSWORD", "")

    # pyodbc connection string URL-encoded (deixamos simples, pois o SQLAlchemy faz o encoding)
    return (
        "mssql+pyodbc://"
        f"{user}:{pwd}@{host}/{db}"
        f"?driver={driver.replace(' ', '+')}"
        f"&TrustServerCertificate={trust}"
        f"&LoginTimeout={timeout}"
    )

@lru_cache(maxsize=1)
def get_engine() -> Any:
    """
    Retorna um engine SQLAlchemy conectado ao SQL Server.
    Usa pool de conexões e echo desativado.
    """
    conn_str = _build_conn_str()
    engine = create_engine(
        conn_str,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
        future=True,
        fast_executemany=True,   # acelera inserts em lote
    )
    # ping leve (opcional)
    try:
        with engine.connect() as con:
            con.execute(text("SELECT 1"))
    except Exception as e:
        # Logue o erro e deixe subir (para ficar visível no app)
        print("[MSSQL] Falha na conexão:", e)
        raise
    return engine
