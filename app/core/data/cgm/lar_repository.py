from __future__ import annotations
from typing import Any, Dict, List
from app.core.data.cgm.base_repository import BaseRepository
from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

class LarRepository(BaseRepository):

    TABLE = "Lar"

    MAP = {
        "DATA_NEG": "DATA_NEG",
        "SEGMENTO": "SEGMENTO",
        "CNPJ": "CNPJ",
        "AGÊNCIA": "AGENCIA",
        "TARIFA": "TARIFA",
        "VALOR_TARIFA": "VALOR_MAJORADO",
        "VALOR_AUTORIZADO": "VALOR_REQUERIDO",
        "VALOR_DA_LAR": "VALOR_LAR",
        "PRAZO": "PRAZO",
        "VENCIMENTO": "VENCIMENTO",     # NVARCHAR
        "AUTORIZAÇÃO": "AUTORIZACAO",
        "CLIENTE": "CLIENTE",
        "ATUADO_SCT": "ATUADO_SCT",
        "OBSERVAÇÃO": "OBSERVACAO",
        "MOTIVO": "MOTIVO",
        "ATUAÇÃO": "USUARIO",
        "TIPO_CLIENTE": "ATUACAO",
        "STATUS_CLIENTE": "STATUS_CLIENTE"
    }

    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)
        if "DATA_NEG" in d: d["DATA_NEG"] = self.to_date(d["DATA_NEG"])
        if "VENCIMENTO" in d: d["VENCIMENTO"] = self.to_date(d["VENCIMENTO"])
        if "PRAZO" in d: d["PRAZO"] = self._to_float(d["PRAZO"])
        if "VALOR_TARIFA" in d: d["VALOR_TARIFA"] = self.to_money(d["VALOR_TARIFA"])
        if "VALOR_AUTORIZADO" in d: d["VALOR_AUTORIZADO"] = self.to_money(d["VALOR_AUTORIZADO"])
        if "VALOR_DA_LAR" in d: d["VALOR_DA_LAR"] = self.to_money(d["VALOR_DA_LAR"])
        if "ATUADO_SCT" in d: d["ATUADO_SCT"] = self._to_bit(d["ATUADO_SCT"])
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
          COALESCE(CLIENTE,'')  AS Cliente,
          COALESCE(CNPJ,'')     AS CNPJ,
          COALESCE(SEGMENTO,'') AS Segmento,
          COALESCE(AGENCIA,'')  AS AG
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
            VALOR_MAJORADO    AS VALOR_TARIFA,
            VALOR_REQUERIDO AS VALOR_REQUERIDO,
            AUTORIZACAO     AS AUTORIZACAO,
            PRAZO           AS PRAZO,
            ATUACAO         AS ATUACAO,
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

    def get_by_id(self, id_: int):
      sql = f"""
      SELECT *
      FROM {self.TABLE}
      WHERE Id = :id
      """
      rows = self._fetchall(sql, id=id_)
      return rows[0] if rows else None
    
    def update_by_id(self, id_: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False

        d = dict(data)  # cópia para não mutar o chamador
        db: Dict[str, Any] = {}  # colunas do BD -> valor normalizado

        def _put(col: str, val: Any):
            # ignora None ou string vazia (não atualiza a coluna)
            if val is None: 
                return
            if isinstance(val, str) and not val.strip():
                return
            db[col] = val

        # --- 1) chaves do formulário (usa MAP) ---
        for form_key, col in self.MAP.items():
            if form_key in d:
                v = d[form_key]
                # normalização por coluna de destino
                if col in ("DATA_NEG", "VENCIMENTO"):
                    v = self.to_date(v)
                elif col in ("PRAZO",):
                    v = self._to_float(v)
                elif col in ("VALOR_MAJORADO", "VALOR_REQUERIDO", "VALOR_LAR"):
                    v = self.to_money(v)
                elif col == "ATUADO_SCT":
                    v = self._to_bit(v)
                _put(col, v)

        # --- 2) também aceita nomes de coluna do BD direto ---
        for col, v in d.items():
            if col in db:        # já coberto via MAP
                continue
            if col in ("DATA_NEG", "VENCIMENTO"):
                v = self.to_date(v)
            elif col in ("PRAZO",):
                v = self._to_float(v)
            elif col in ("VALOR_MAJORADO", "VALOR_REQUERIDO", "VALOR_LAR"):
                v = self.to_money(v)
            elif col == "ATUADO_SCT":
                v = self._to_bit(v)
            _put(col, v)

        if not db:
            return False

        sets = [f"{col} = :{col}" for col in db.keys()]
        db["id"] = id_
        sql = f"UPDATE {self.TABLE} SET {', '.join(sets)} WHERE Id = :id"
        self._exec(sql, **db)
        return True

    
    def delete_by_id(self, id_: int) -> bool:
      sql = f"DELETE FROM {self.TABLE} WHERE Id = :id"
      self._exec(sql, id=id_)
      return True
    
         # ---------- Busca para a tela de consulta ----------
    def search_consulta(self, segmento: str = "", cliente: str = "", cnpj: str = ""):
        sql = f"""
        SELECT
        Id               ,
        DATA_NEG         ,
        SEGMENTO         ,
        CLIENTE          ,
        CNPJ             ,
        AGENCIA          ,
        TARIFA           ,
        VALOR_MAJORADO   ,
        VALOR_REQUERIDO  ,
        VALOR_LAR        ,
        AUTORIZACAO      ,
        STATUS_CLIENTE   ,
        PRAZO            ,
        VENCIMENTO    ,
        OBSERVACAO       ,
        ATUADO_SCT       ,
        MOTIVO,
        USUARIO           
        FROM {self.TABLE}
        WHERE 1=1
        AND (:seg = '' OR UPPER(SEGMENTO) LIKE UPPER('%' + :seg + '%'))
        AND (:cli = '' OR UPPER(CLIENTE)  LIKE UPPER('%' + :cli + '%'))
        AND (:cnp = '' OR CNPJ = :cnp)
        ORDER BY DATA_NEG DESC
        """
        return self._fetchall(sql, seg=segmento or "", cli=cliente or "", cnp=cnpj)

    def delete_many(self, ids: List[int]) -> int:
        ok = 0
        for i in ids:
            try:
                self.delete_by_id(int(i))
                ok += 1
            except Exception:
                pass
        return ok
    
    def _to_bit(self, v) -> int | None:
        if v is None: return None
        s = str(v).strip().lower()
        if not s: return None
        if s in ("s", "sim", "y", "yes", "1", "true"):  return 1
        if s in ("n", "nao", "não", "no", "0", "false"): return 0
        # se vier 0/1 direto
        try: return 1 if int(s) != 0 else 0
        except Exception: return None

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




