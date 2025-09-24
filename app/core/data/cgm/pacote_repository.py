# app/core/data/cgm/pacote_repository.py
from __future__ import annotations
from typing import Any, Dict, List
from app.core.data.cgm.base_repository import BaseRepository

class PacoteRepository(BaseRepository):
    TABLE = "Pacotes"

    MAP = {
        "DATA_NEG": "DATA_NEG",
        "SEGMENTO": "SEGMENTO",
        "CLIENTE": "CLIENTE",
        "CNPJ": "CNPJ",
        "PACOTE": "PACOTE",
        "AGENCIA": "AGENCIA",
        "CONTA": "CONTA",
        "PRAZO": "PRAZO",
        "DATA_REV": "DATA_REV",
        "MOTIVO": "MOTIVO",
        "OBS": "OBS"
    }

    # ... (insert/recent/search/get_by_id/delete/update_by_id inalterados)
    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)  # cópia
        # converte datas para objetos date (evita erro nvarchar→datetime)
        if "Data_Neg" in d: d["DATA_NEG"] = self.to_date(d["Data_Neg"])
        if "DT_Atuacao" in d: d["DT_ATUACAO"] = self.to_date(d["DT_Atuacao"])
        if "Data_Rev" in d: d["DATA_REV"] = self.to_date(d["Data_Rev"])
        if "PRAZO" in d: d["PRAZO"] = self._to_float(d["PRAZO"])
        # faz o insert
        return self._insert_generic(self.TABLE, self.MAP, d)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT TOP(:limit)
          CONVERT(VARCHAR(10), ISNULL(DATA_NEG, GETDATE()), 103) AS data,
          COALESCE(CLIENTE,'') AS cliente,
          COALESCE(SEGMENTO,'') AS segmento,
          COALESCE(CNPJ,'') AS cnpj,
          COALESCE(AGENCIA,'') AS ag,
          COALESCE(CONTA,'') AS conta
        FROM {self.TABLE}
        ORDER BY DT_ATUACAO DESC
        """
        return self._fetchall(sql, limit=limit)

    def search(self, ag: str = "", cc: str = "", cliente: str = "", segment: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
          COALESCE(CLIENTE,'') AS cliente,
          COALESCE(CNPJ,'')      AS cnpj,
          COALESCE(AGENCIA,'')        AS ag,
          COALESCE(CONTA,'')        AS conta,
          COALESCE(SEGMENTO,'')       AS segmento
        FROM {self.TABLE}
        WHERE 1=1
          AND (:ag = '' OR AGENCIA = :ag)
          AND (:cc = '' OR CONTA = :cc)
          AND (:cli = '' OR CLIENTE LIKE '%' + :cli + '%')
          AND (:seg = '' OR SEGMENTO = :seg)
        ORDER BY DATA_NEG DESC
        """
        return self._fetchall(sql, ag=ag, cc=cc, cli=cliente, seg=segment)
    
    def search_cadastro(self, ag: str = "", cc: str = "", nome: str = "", pacote: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
        Id                           AS id,
        DATA_NEG        AS DATA_NEG,
        SEGMENTO        AS SEGMENTO,
        CLIENTE         AS CLIENTE,
        CNPJ            AS CNPJ,
        PACOTE          AS PACOTE,
        AGENCIA         AS AGENCIA,
        CONTA           AS CONTA,
        PRAZO           AS PRAZO,       
        DATA_REV        AS Data_Rev,
        MOTIVO          AS MOTIVO,
        OBS             AS OBS
        FROM {self.TABLE}
        WHERE 1=1
        AND (:ag  = '' OR AGENCIA = :ag)
        AND (:cc  = '' OR CONTA   = :cc)
        AND (:nm  = '' OR CLIENTE LIKE '%' + :nm + '%')
        AND (:pac = '' OR PACOTE  = :pac)
        ORDER BY DATA_NEG DESC
        """
        return self._fetchall(sql, ag=ag, cc=cc, nm=nome, pac=pacote)
      
      # ---------- CRUD de linha única ----------
    def get_by_id(self, id_: int):
      sql = f"""
      SELECT *
      FROM {self.TABLE}
      WHERE Id = :id
      """
      rows = self._fetchall(sql, id=id_)
      return rows[0] if rows else None

    def update_by_id(self, id_: int, data: dict) -> bool:
        if not data:
            return False
        sets, params, i = [], {"id": id_}, 0
        for key_view, value in data.items():
            k = str(key_view).upper() if key_view is not None else ""
            dbcol = self.MAP.get(k)
            if not dbcol:
                continue

            # coerção igual ao insert
            up = dbcol.upper()
            if up == "DATA_NEG":
                value = self.to_date(value)
            elif up == "DATA_REV":
                value = self.to_date(value)
            elif up == "DT_ATUACAO":
                value = self.to_date(value)
            else:
                value = None if value is None else str(value)

            p = f"p{i}"; i += 1
            sets.append(f"{dbcol} = :{p}")
            params[p] = value

        if not sets:
            return False

        sql = f"UPDATE {self.TABLE} SET " + ", ".join(sets) + f" WHERE Id = :id"
        self._exec(sql, **params)
        return True


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

    def search_consulta(self, segmento: str = "", cliente: str = "", cnpj: str = "", ag: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
        Id                      AS id,
        DATA_NEG                AS DATA_NEG,
        SEGMENTO                AS SEGMENTO,
        CLIENTE                 AS CLIENTE,
        CNPJ                    AS CNPJ,
        PACOTE                  AS PACOTE,
        AGENCIA                 AS AGENCIA,
        CONTA                   AS CONTA,
        PRAZO                   AS PRAZO,
        DATA_REV                AS DATA_REV,
        MOTIVO                  AS MOTIVO,
        OBS                     AS OBS       
        FROM {self.TABLE}
        WHERE 1=1
        AND (:seg  = '' OR SEGMENTO = :seg)
        AND (:cli  = '' OR CLIENTE  LIKE '%' + :cli + '%')
        AND (:cnpj = '' OR CNPJ     = :cnpj)
        AND (:ag   = '' OR AGENCIA  = :ag)
        ORDER BY DATA_NEG DESC
        """
        return self._fetchall(sql, seg=segmento or "", cli=cliente or "", cnpj=cnpj or "", ag=ag or "")

    
    def _to_float(self, v) -> float | None:
            if v is None: return None
            s = str(v).strip()
            if not s: return None
            if "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s:
                s = s.replace(",", ".")
            return float(s)
    
    