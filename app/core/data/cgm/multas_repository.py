from __future__ import annotations
from typing import Any, Dict, List
from app.core.data.cgm.base_repository import BaseRepository, _parse_date_any

class MultasRepository(BaseRepository):
    """
    Tabela real: Multas
    """
    TABLE = "Multas"

    MAP = {
        "Id": "ID",                   # int IDENTITY PK
        "Segmento": "SEGMENTO",
        "Nome_Ag": "NM_AG",
        "AG": "AGENCIA",
        "CC": "CONTA",
        "CNPJ": "CNPJ",
        "Cliente": "CLIENTE",
        "TAR": "TARIFA",
        "Data_Neg": "DATA_NEG",
        "Vlr_tar": "VALOR_MAJORADO",   # mapeado do front
        "Vlr_Aut": "VALOR_REQUERIDO",
        "Autorização": "AUTORIZAÇÃO",
        "Observacao": "OBSERVACAO",
        "Status": "STATUS",
        "Prazo": "PRAZO",
        "Vencimento": "VENCIMENTO",    # NVARCHAR no schema
        "Usuario": "USUARIO",
        "Atuacao": "ATUACAO",
        "QTDE": "QTDE",
        "Atuado_SCT": "ATUADO_SCT",
        "Prazo_SGN": "PRAZO SGN",      # espaço no nome
        "Neg_Esp": "NEG ESP",          # espaço no nome
        "Motivo": "MOTIVO",
    }

    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)
        if "Data_Neg" in d: d["Data_Neg"] = self.to_date(d["Data_Neg"])
        for k in ("Vlr_tar","Vlr_Aut"):
            if k in d: d[k] = self.to_money(d[k])
        # calcula Vencimento (Data_Neg + Prazo) se não vier
        if not d.get("Vencimento"):
            dias = 0
            try: dias = int(d.get("Prazo") or 0)
            except Exception: pass
            base = d.get("Data_Neg") or ""
            d["Vencimento"] = self.add_days_br(base, dias)
        return self._insert_generic(self.TABLE, self.MAP, d)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT TOP(:limit)
          COALESCE(USUARIO,'') AS usuario,
          CONVERT(VARCHAR(10), ISNULL(DATA_NEG, GETDATE()), 103) AS data,
          COALESCE(CLIENTE,'')  AS cliente,
          COALESCE(SEGMENTO,'') AS segmento,
          COALESCE(CNPJ,'')     AS cnpj
        FROM {self.TABLE}
        ORDER BY ISNULL(DATA_NEG, GETDATE()) DESC
        """
        return self._fetchall(sql, limit=limit)

    def search(self, segmento: str = "", cliente: str = "", cnpj: str = ""):
        sql = f"""
        SELECT
          COALESCE(CLIENTE,'') AS Cliente,
          COALESCE(CNPJ,'')    AS CNPJ,
          COALESCE(SEGMENTO,'') AS Segmento,
          COALESCE(AGENCIA,'')  AS AG,
          COALESCE(CONTA,'')    AS CC,
          COALESCE(TARIFA,'')   AS TAR,
          COALESCE(CAST(VALOR_MAJORADO AS NVARCHAR(50)),'')  AS Vlr_tar,
          COALESCE(CAST(VALOR_REQUERIDO AS NVARCHAR(50)),'') AS Vlr_Aut,
          COALESCE(CAST(QTDE AS NVARCHAR(50)),'')            AS QTDE,
          COALESCE(VENCIMENTO,'') AS Vencimento
        FROM {self.TABLE}
        WHERE 1=1
          AND (:seg='' OR SEGMENTO = :seg)
          AND (:cli='' OR CLIENTE  LIKE '%' + :cli + '%')
          AND (:cnpj='' OR CNPJ LIKE '%' + :cnpj + '%')
        ORDER BY ISNULL(DATA_NEG, GETDATE()) DESC
        """
        return self._fetchall(sql, seg=segmento, cli=cliente, cnpj=cnpj)

    def get_by_id(self, id_: int):
        sql = f"""
        SELECT *
        FROM {self.TABLE}
        WHERE Id = :id
        """
        rows = self._fetchall(sql, id=id_)
        return rows[0] if rows else None
    
    def delete_by_id(self, id_: int) -> bool:
        sql = f"DELETE FROM {self.TABLE} WHERE Id = :id"
        self._exec(sql, id=id_)
        return True

    def delete_many(self, ids: List[int]) -> int:
        ok = 0
        for i in ids:
            try:
                self.delete_by_id(int(i))
                ok += 1
            except Exception:
                pass
        return ok

    def update_by_id(self, id_: int, data: Dict[str, Any]) -> bool:
        sets = []
        params = {"id": id_}
        # 1) via MAP (form keys)
        if hasattr(self, "MAP"):
            for fk, col in self.MAP.items():
                if fk in data:
                    sets.append(f"{col} = :{col}")
                    params[col] = data.get(fk)
        # 2) aceita também colunas DB direto
        for k, v in data.items():
            if k == "id" or k == "Id":
                continue
            if hasattr(self, "MAP") and k in self.MAP:
                # já coberto acima
                continue
            # evita duplicar SET da mesma coluna
            if k not in params and isinstance(k, str):
                sets.append(f"{k} = :{k}")
                params[k] = v
        if not sets:
            return False
        sql = f"UPDATE {self.TABLE} SET " + ", ".join(sets) + " WHERE Id = :id"
        self._exec(sql, **params)
        return True

