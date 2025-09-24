from __future__ import annotations
from typing import Any, Dict, List
from app.core.data.cgm.base_repository import BaseRepository

class AlcadaRepository(BaseRepository):
        TABLE = "alcada_sup"

        # Mapa: chave enviada pela VIEW -> coluna real no DB (nomes EXATOS)
        MAP = {
            "DATA_NEG":        "DATA_NEG",
            "SEGMENTO":        "SEGMENTO",
            "CLIENTE":         "CLIENTE",
            "CNPJ":            "CNPJ",
            "AGENCIA":         "AGENCIA",
            "CONTA":           "CONTA",
            "TARIFA":          "TARIFA",
            "VALOR_MAJORADO":     "VALOR_MAJORADO",
            "VALOR_REQUERIDO":  "VALOR_REQUERIDO",
            "AUTORIZACAO":     "AUTORIZACAO",   
            "QTDE":   "QTDE",
            "PRAZO":           "PRAZO",
            "VENCIMENTO":      "VENCIMENTO",
            "OBSERVACAO":      "OBSERVACAO",
        }

        # ---------- INSERT ----------
        def insert(self, d: Dict[str, Any]) -> bool:
            d = dict(d)
            # coerção de tipos p/ colunas numéricas/datas dessa tabela
            if "DATA_NEG" in d: d["DATA_NEG"] = self.to_date(d["DATA_NEG"])
            if "VENCIMENTO" in d: d["VENCIMENTO"] = self.to_date(d["VENCIMENTO"])
            if "PRAZO" in d: d["PRAZO"] = self._to_float(d["PRAZO"])
            if "QTDE" in d: d["QTDE"] = self._to_float(d["QTDE"])
            return self._insert_generic(self.TABLE, self.MAP, d)

        # ---------- LISTAGENS ----------
        def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
            sql = f"""
            SELECT TOP(:limit)
            COALESCE(AUTORIZACAO, '') AS responsavel,
            CONVERT(VARCHAR(10), ISNULL(DATA_NEG, GETDATE()), 103) AS data,
            COALESCE(CLIENTE,  '') AS cliente,
            COALESCE(CNPJ,     '') AS cnpj,
            COALESCE(AGENCIA,  '') AS ag,
            COALESCE(TARIFA,   '') AS tarifa
            FROM {self.TABLE}
            ORDER BY DATA_NEG DESC
            """
            return self._fetchall(sql, limit=limit)

        def search(self, ag: str = "", cc: str = "", cliente: str = "", tarifa: str = "") -> List[Dict[str, Any]]:
            sql = f"""
            SELECT
            COALESCE(CLIENTE, '') AS cliente,
            COALESCE(CNPJ,    '') AS cnpj,
            COALESCE(AGENCIA, '') AS ag,
            COALESCE(CONTA,   '') AS conta,
            COALESCE(TARIFA,  '') AS tarifa,
            COALESCE(STATUS,  '') AS situacao
            FROM {self.TABLE}
            WHERE 1=1
            AND (:ag  = '' OR AGENCIA = :ag)
            AND (:cc  = '' OR CONTA   = :cc)
            AND (:cli = '' OR CLIENTE LIKE '%' + :cli + '%')
            AND (:tar = '' OR TARIFA  = :tar)
            ORDER BY DATA_NEG DESC
            """
            return self._fetchall(sql, ag=ag, cc=cc, cli=cliente, tar=tarifa)

        def search_cadastro(self, ag: str = "", cc: str = "", nome: str = "", tarifa: str = "") -> List[Dict[str, Any]]:
            sql = f"""
            SELECT
            Id                           AS id,
            DATA_NEG        AS Data_Neg,
            SEGMENTO        AS SEGMENTO,
            CLIENTE         AS CLIENTE,
            CNPJ            AS CNPJ,
            AGENCIA         AS AGENCIA,
            CONTA           AS CONTA,
            TARIFA          AS TARIFA,
            VALOR_MAJORADO  AS VALOR_MAJORADO,
            VALOR_REQUERIDO AS VALOR_REQUERIDO,
            AUTORIZACAO     AS AUTORIZACAO,
            QTDE            AS QTDE,
            PRAZO           AS PRAZO,
            VENCIMENTO      AS VENCIMENTO,
            OBSERVACAO      AS OBSERVACAO
            FROM {self.TABLE}
            WHERE 1=1
            AND (:ag  = '' OR AGENCIA = :ag)
            AND (:cc  = '' OR CONTA   = :cc)
            AND (:nm  = '' OR CLIENTE LIKE '%' + :nm + '%')
            AND (:tar = '' OR TARIFA  = :tar)
            ORDER BY DATA_NEG DESC
            """
            return self._fetchall(sql, ag=ag, cc=cc, nm=nome, tar=tarifa)

        # ---------- CRUD de linha única ----------
        def get_by_id(self, id_: int):
            sql = f"""
            SELECT * 
            FROM {self.TABLE} 
            WHERE Id = :id
            """
            rows = self._fetchall(sql, id=id_)
            return rows[0] if rows else None

        def update_by_id(self, id_: int, changes: Dict[str, Any]) -> bool:
            if not changes:
                return True
            # normalizações
            d = dict(changes)
            for k in ("DATA_NEG", "VENCIMENTO"):
                if k in d: d[k] = self.to_date(d[k])
                
            if ("VALOR_MAJORADO", "VALOR_REQUERIDO")  in d:
                d["VALOR_REQUERIDO"] = self.to_money(d["VALOR_REQUERIDO"])
                d["VALOR_MAJORADO"] = self.to_money(d["VALOR_MAJORADO"])

            sets = []
            params = {"id": id_}
            for k, v in d.items():
                col = self.MAP.get(k, k)  # aceita tanto chave do form qto coluna direta
                sets.append(f"{col} = :{col}")
                params[col] = v

            sql = f"UPDATE {self.TABLE} SET {', '.join(sets)} WHERE Id = :id"
            self._exec(sql, **params)
            return True

        def delete_by_id(self, id_: int) -> bool:
            sql = f"DELETE FROM {self.TABLE} WHERE Id = :id"
            self._exec(sql, id=id_)
            return True

        def delete_many(self, ids: list[int]) -> int:
            ok = 0
            for i in ids:
                try:
                    self.delete_by_id(int(i))
                    ok += 1
                except Exception:
                    pass
            return ok

        # ---------- Busca para a tela de consulta ----------
        def search_consulta(self, segmento: str = "", cliente: str = "", cnpj: str = "", ag: str = ""):
            sql = f"""
            SELECT
            Id                           AS id,
            DATA_NEG        AS DATA_NEG,
            SEGMENTO        AS SEGMENTO,
            CLIENTE         AS CLIENTE,
            CNPJ            AS CNPJ,
            AGENCIA         AS AGENCIA,
            CONTA           AS CONTA,
            TARIFA          AS TARIFA,
            VALOR_MAJORADO  AS VALOR_MAJORADO,
            VALOR_REQUERIDO AS VALOR_REQUERIDO,
            AUTORIZACAO     AS AUTORIZACAO,
            QTDE            AS QTDE,
            PRAZO           AS PRAZO,
            VENCIMENTO      AS VENCIMENTO,
            OBSERVACAO      AS OBSERVACAO
            FROM {self.TABLE}
            WHERE 1=1
            AND (:seg = '' OR UPPER(SEGMENTO) LIKE UPPER('%' + :seg + '%'))
            AND (:cli = '' OR UPPER(CLIENTE)  LIKE UPPER('%' + :cli + '%'))
            AND (:cnp = '' OR CNPJ = :cnp)
            AND (:ag  = '' OR AGENCIA LIKE :ag + '%')
            ORDER BY DATA_NEG DESC
            """
            cnpj_digits = "".join(ch for ch in (cnpj or "") if ch.isdigit())
            return self._fetchall(sql, seg=segmento or "", cli=cliente or "", cnp=cnpj_digits, ag=ag or "")

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
