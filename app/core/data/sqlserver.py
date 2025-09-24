# app/core/data/sqlserver.py
from __future__ import annotations
import os
from typing import Any
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def _detect_driver(preferred: str | None = None) -> str:
    """Retorna o nome exato de um driver ODBC instalado."""
    available = set()
    try:
        import pyodbc
        available = set(pyodbc.drivers())
    except Exception:
        pass

    candidates = [
        preferred or os.getenv("MSSQL_DRIVER", None),
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ]
    for name in filter(None, candidates):
        if name in available:
            return name

    # fallback: usa o preferido/18 mesmo que não detecte (útil em ambientes sem pyodbc.drivers())
    return preferred or os.getenv("MSSQL_DRIVER") or "ODBC Driver 18 for SQL Server"


def get_engine() -> Any:
    """
    Cria engine do SQL Server com pyodbc + SQLAlchemy.
    .env suportado:
        MSSQL_SERVER=GABRIELVALLS
        MSSQL_DATABASE=BancoCGM
        MSSQL_TRUSTED=true            # autenticação do Windows
        # ou, se usar SQL auth:
        MSSQL_USER=sa
        MSSQL_PASSWORD=...
        MSSQL_DRIVER=ODBC Driver 18 for SQL Server
    """
    server   = os.getenv("MSSQL_SERVER",   "GABRIELVALLS")
    database = os.getenv("MSSQL_DATABASE", "BancoCGM")
    trusted  = os.getenv("MSSQL_TRUSTED",  "true").lower() in ("1", "true", "yes")
    user     = os.getenv("MSSQL_USER",     "")
    password = os.getenv("MSSQL_PASSWORD", "")

    driver   = _detect_driver()
    driver_q = driver.replace(" ", "+")

    # Parâmetros extras (Driver 18 exige Encrypt, senão dá erro de certificado)
    params = f"driver={driver_q}"
    if "18+for+SQL+Server" in driver_q:
        params += "&Encrypt=yes&TrustServerCertificate=yes"
    else:
        params += "&TrustServerCertificate=yes"

    if trusted:
        # Autenticação integrada do Windows
        url = f"mssql+pyodbc://@{server}/{database}?{params}&trusted_connection=yes"
    else:
        # Usuário/senha SQL
        url = f"mssql+pyodbc://{user}:{password}@{server}/{database}?{params}"

    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        fast_executemany=True,
    )


# Opcional: teste rápido que você pode chamar no boot se quiser
def quick_test() -> None:
    eng = get_engine()
    with eng.connect() as con:
        con.execute(text("SELECT 1"))
