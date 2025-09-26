from __future__ import annotations
from typing import Any, Dict, List
from app.core.data.cgm.base_repository import BaseRepository, _parse_date_any

class MultasRepository(BaseRepository):

    TABLE = "Multas"

    MAP = {
        "DATA_NEG": "DATA_NEG",
        "SEGMENTO": "SEGMENTO",
        "CLIENTE": "CLIENTE",
        "CNPJ": "CNPJ",
        "AGENCIA": "AGENCIA",
        "CONTA": "CONTA",
        "TARIFA": "TARIFA",
        "VALOR_TARIFA": "VALOR_TARIFA",   
        "VALOR_AUTORIZADO": "VALOR_AUTORIZADO",
        "AUTORIZAÇÃO": "AUTORIZACAO",
        "QTDE": "QTDE",
        "PRAZO": "PRAZO",
        "NEG_ESP": "NEG_ESP",
        "PRAZO_SGN": "PRAZO_SGN",
        "VENCIMENTO": "VENCIMENTO",    
        "OBSERVAÇÃO": "OBSERVACAO",
        "ATUADO_SCT": "ATUADO_SCT",
        "MOTIVO": "MOTIVO",
        "ATUACAO": "ATUACAO",
        "USUARIO": "USUARIO",
        "STATUS": "STATUS",
        "NM_AG": "NM_AG"
    }

    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)
        # coerção de tipos p/ colunas numéricas/datas dessa tabela
        if "DATA_NEG" in d: d["DATA_NEG"] = self.to_date(d["DATA_NEG"])
        if "VENCIMENTO" in d: d["VENCIMENTO"] = self.to_date(d["VENCIMENTO"])
        if "PRAZO" in d: d["PRAZO"] = self._to_float(d["PRAZO"])
        if "QTDE" in d: d["QTDE"] = self._to_float(d["QTDE"])
        if "VALOR_TARIFA" in d: d["VALOR_TARIFA"] = self.to_money(d["VALOR_TARIFA"])
        if "VALOR_AUTORIZADO" in d: d["VALOR_AUTORIZADO"] = self.to_money(d["VALOR_AUTORIZADO"])
        if "ATUADO_SCT" in d: d["ATUADO_SCT"] = self._to_bit(d["ATUADO_SCT"])
        if "NEG_ESP" in d: d["NEG_ESP"] = self._to_bit(d["NEG_ESP"])
        # inserir
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
        ORDER BY DATA_NEG DESC
        """
        return self._fetchall(sql, limit=limit)

    def search(self, segmento: str = "", cliente: str = "", cnpj: str = ""):
        sql = f"""
        SELECT
        COALESCE(CLIENTE,'') AS Cliente,
        COALESCE(CNPJ,'')    AS CNPJ,
        COALESCE(SEGMENTO,'') AS Segmento
        FROM {self.TABLE}
        WHERE 1=1
        AND (:seg='' OR SEGMENTO = :seg)
        AND (:cli='' OR CLIENTE  LIKE '%' + :cli + '%')
        AND (:cnpj='' OR CNPJ LIKE '%' + :cnpj + '%')
        ORDER BY ISNULL(DATA_NEG, GETDATE()) DESC
        """
        return self._fetchall(sql, seg=segmento, cli=cliente, cnpj=cnpj)
    
    def search_cadastro(self, ag: str = "", cc: str = "", nome: str = "", tarifa: str = "") -> List[Dict[str, Any]]:
            sql = f"""
            SELECT
            Id              AS id,
            DATA_NEG        AS Data_Neg,
            SEGMENTO        AS SEGMENTO,
            CLIENTE         AS CLIENTE,
            CNPJ            AS CNPJ,
            AGENCIA         AS AGENCIA,
            CONTA           AS CONTA,
            TARIFA          AS TARIFA,
            VALOR_TARIFA    AS VALOR_TARIFA,
            VALOR_AUTORIZADO AS VALOR_REQUERIDO,
            AUTORIZACAO     AS AUTORIZACAO,
            QTDE            AS QTDE,
            PRAZO           AS PRAZO,
            NEG_ESP        AS NEG_ESP,
            PRAZO_SGN      AS PRAZO_SGN,
            VENCIMENTO      AS VENCIMENTO,
            OBSERVACAO      AS OBSERVACAO,
            ATUADO_SCT     AS ATUADO_SCT,
            MOTIVO          AS MOTIVO
            FROM {self.TABLE}
            WHERE 1=1
            AND (:ag  = '' OR AGENCIA = :ag)
            AND (:cc  = '' OR CONTA   = :cc)
            AND (:nm  = '' OR CLIENTE LIKE '%' + :nm + '%')
            AND (:tar = '' OR TARIFA  = :tar)
            ORDER BY DATA_NEG DESC
            """
            return self._fetchall(sql, ag=ag, cc=cc, nm=nome, tar=tarifa)

    # ---------- CRUD BÁSICO ----------
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
            return False

        d = dict(changes)

        # aliases vindos da UI (com acento/caixa)
        ui_alias = {
            "AUTORIZAÇÃO": "AUTORIZACAO",
            "OBSERVAÇÃO": "OBSERVACAO",
        }
        d = {ui_alias.get(k, k): v for k, v in d.items()}

        # --- coerções seguras ---
        from app.core.data.cgm.base_repository import _parse_date_any

        for k in ("DATA_NEG", "VENCIMENTO"):
            if k in d:
                val = (d.get(k) or "").strip()
                if val:
                    try:
                        d[k] = _parse_date_any(val)  # aceita “dd/MM/yyyy”, “yyyy-MM-dd HH:mm:ss”, etc.
                    except Exception:
                        d.pop(k)  # não grava NULL se não conseguir converter

        if "PRAZO" in d:
            d["PRAZO"] = self._to_float(d["PRAZO"])
        if "VALOR_TARIFA" in d:
            d["VALOR_TARIFA"] = self.to_money(d["VALOR_TARIFA"])
        if "VALOR_AUTORIZADO" in d:
            d["VALOR_AUTORIZADO"] = self.to_money(d["VALOR_AUTORIZADO"])

        # monta o UPDATE usando o MAP (ou coluna direta)
        sets, params = [], {"id": id_}
        for k, v in d.items():
            col = self.MAP.get(k, k)
            sets.append(f"{col} = :{col}")
            params[col] = v

        if not sets:
            return False

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
    def search_consulta(self, segmento: str = "", cliente: str = "", cnpj: str = ""):
            sql = f"""
            SELECT
            Id              AS id,
            DATA_NEG        AS DATA_NEG,
            SEGMENTO        AS SEGMENTO,
            CLIENTE         AS CLIENTE,
            CNPJ            AS CNPJ,
            AGENCIA         AS AGENCIA,
            CONTA           AS CONTA,
            TARIFA          AS TARIFA,
            VALOR_TARIFA  AS VALOR_TARIFA,
            VALOR_AUTORIZADO AS VALOR_AUTORIZADO,
            AUTORIZACAO     AS AUTORIZACAO,
            QTDE            AS QTDE,
            PRAZO           AS PRAZO,
            NEG_ESP        AS NEG_ESP,
            PRAZO_SGN      AS PRAZO_SGN,
            VENCIMENTO      AS VENCIMENTO,
            OBSERVACAO      AS OBSERVACAO,
            ATUADO_SCT     AS ATUADO_SCT,
            MOTIVO          AS MOTIVO
            FROM {self.TABLE}
            WHERE 1=1
            AND (:seg = '' OR UPPER(SEGMENTO) LIKE UPPER('%' + :seg + '%'))
            AND (:cli = '' OR UPPER(CLIENTE)  LIKE UPPER('%' + :cli + '%'))
            AND (:cnp = '' OR CNPJ = :cnp)
            ORDER BY DATA_NEG DESC
            """
            return self._fetchall(sql, seg=segmento or "", cli=cliente or "", cnp=cnpj)

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
        
    def _to_bit(self, v) -> int | None:
        if v is None: return None
        s = str(v).strip().lower()
        if not s: return None
        if s in ("s", "sim", "y", "yes", "1", "true"):  return 1
        if s in ("n", "nao", "não", "no", "0", "false"): return 0
        # se vier 0/1 direto
        try: return 1 if int(s) != 0 else 0
        except Exception: return None

