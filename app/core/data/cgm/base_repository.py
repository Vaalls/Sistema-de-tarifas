# app/core/data/cgm/base_repository.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from sqlalchemy import text
from app.core.data.sqlserver import get_engine

def _parse_date_any(x) -> Optional[date]:
    if not x:
        return None
    if isinstance(x, date):
        return x
    if isinstance(x, datetime):
        return x.date()
    s = str(x).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def _parse_money_br(s) -> Optional[float]:
    if s is None or s == "":
        return None
    s = str(s).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

class BaseRepository:
    TABLE = ""
    PK = "Id"

    def __init__(self):
        self.engine = get_engine()

    def _exec(self, sql: str, **params):
        with self.engine.begin() as con:
            return con.execute(text(sql), params)

    def _fetchall(self, sql: str, **params) -> List[Dict[str, Any]]:
        with self.engine.connect() as con:
            rows = con.execute(text(sql), params).mappings().all()
            return [dict(r) for r in rows]

    # conversões reutilizáveis
    @staticmethod
    def to_date(v) -> Optional[date]:
        return _parse_date_any(v)

    @staticmethod
    def to_money(v) -> Optional[float]:
        return _parse_money_br(v)

    # insert genérico
    def _insert_generic(self, table: str, mapping: Dict[str, str], data: Dict[str, Any]):
        cols, vals, params = [], [], {}
        for form_key, col in mapping.items():
            cols.append(col)
            vals.append(f":{col}")
            params[col] = data.get(form_key)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)})"
        self._exec(sql, **params)
        return True
    
        
