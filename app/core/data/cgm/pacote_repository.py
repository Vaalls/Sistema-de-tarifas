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

    def update_by_id(self, id_: int, data: Dict[str, Any], only: List[str]) -> bool:
        """
        Atualiza o registro Id. Se `only` for informado, atualiza apenas essas colunas.
        Em `only` você pode passar chaves do formulário (MAP) ou nomes de colunas do BD.
        - DATA_NEG: normaliza como data (datetime)
        - VENCIMENTO: mantém como texto (NVARCHAR no schema)
        - Valores vazios/None são ignorados (não sobrescrevem no BD)
        """
        if not data:
            return False

        # Se 'only' veio, convertemos para nomes de colunas do BD
        allowed_cols: set[str] | None = None
        if only:
            allowed_cols = set(self.MAP.get(k, k) for k in only)

        def _allowed(col: str) -> bool:
            return (allowed_cols is None) or (col in allowed_cols)

        db_vals: Dict[str, Any] = {}

        # 1) chaves do formulário (via MAP)
        for form_key, col in self.MAP.items():
            if form_key not in data or not _allowed(col):
                continue
            v = data.get(form_key)

            # Ignora None ou string vazia (não atualiza a coluna)
            if v is None or (isinstance(v, str) and not v.strip()):
                continue

            # Normalizações por coluna
            if col == ("DATA_NEG", "DATA_REV"):
                v = self.to_date(v)            # DATA_NEG é datetime
            elif col in ("VALOR_TARIFA", "VALOR_AUTORIZADO"):
                v = self.to_money(v)
            elif col == "PRAZO":
                v = self._to_float(v)
            # VENCIMENTO: não converter (é NVARCHAR)

            db_vals[col] = v

        # 2) aceita também nomes de coluna do BD diretamente
        for col, v in data.items():
            if col in self.MAP:  # já tratado acima
                continue
            if not _allowed(col):
                continue
            if v is None or (isinstance(v, str) and not v.strip()):
                continue

            # Normalizações quando já vier nome da coluna do BD
            if col == "DATA_NEG":
                v = self.to_date(v)
            elif col in ("VALOR_TARIFA", "VALOR_AUTORIZADO"):
                v = self.to_money(v)
            elif col == "PRAZO":
                v = self._to_float(v)
            elif col == ("ATUADO_SCT", "NEG_ESP"):
                v = self._to_bit(v)
            # VENCIMENTO: manter texto

            db_vals[col] = v

        if not db_vals:
            return False

        sets = [f"{c} = :{c}" for c in db_vals]
        db_vals["id"] = id_
        sql = f"UPDATE {self.TABLE} SET {', '.join(sets)} WHERE Id = :id"
        self._exec(sql, **db_vals)
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
    
    