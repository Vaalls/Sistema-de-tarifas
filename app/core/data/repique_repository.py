# app/data/repique_repository.py
from typing import List, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Engine

class RepiqueRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def fetch_repiques(self, limit: int = 1000) -> List[Tuple[str, str, float]]:
        # Ajuste o FROM/colunas p/ a sua base (placeholder)
        sql = text("""
            SELECT TOP 1000
                cliente, conta, valor
            FROM dbo.Repique
            ORDER BY data DESC
        """)
        with self.engine.connect() as conn:
            rs = conn.execute(sql)
            rows = rs.fetchall()
        out: List[Tuple[str, str, float]] = []
        for r in rows[:limit]:
            cliente, conta, valor = r[0], r[1], float(r[2] or 0)
            out.append((cliente, conta, valor))
        return out
