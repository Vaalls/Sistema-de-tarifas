from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.data.cgm.base_repository import BaseRepository

class EstornoRepository(BaseRepository):
    TABLE = "Estorno"

    # chaves do formulário → colunas reais da tabela
    MAP = {
        "Data_Ent":   "DATA_ENT",
        "DT_Est":     "DT_EST",
        "Status":     "STATUS",
        "Area":       "AREA",
        "Segmento":   "SEGMENTO",
        "Resp":       "RESP",
        "Agencia":    "AG",                # UI "Agencia" → DB "AG"
        "Conta":      "CC",                # UI "Conta"   → DB "CC"
        "Nome_Ag":    "NOME_AG",
        "Nome_Cli":   "NOME_CLIENTE",      # alinhei com o que apareceu no seu erro
        "CNPJ":       "CNPJ",
        "Tar":        "Tar",
        "Vlr_Est":    "VLR_EST",
        "Class":      "CLASS",
        "Parecer_OP": "PARECER_OP",
        "de_acordo":  "DE_ACORDO",
        "Vlr_Cred":   "VLR_CRED",
        "Solicitante":"SOLICITANTE"       # <--- Linha adicionada
    }

    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)  # cópia
        # converte datas para objetos date (evita erro nvarchar→datetime)
        if "Data_Ent" in d: d["Data_Ent"] = self.to_date(d["Data_Ent"])
        if "DT_Est"   in d: d["DT_Est"]   = self.to_date(d["DT_Est"])
        # dinheiro
        if "Vlr_Est" in d: d["Vlr_Est"] = self.to_money(d["Vlr_Est"])
        # faz o insert
        return self._insert_generic(self.TABLE, self.MAP, d)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT TOP(:limit)
          COALESCE(RESP,'') AS responsavel,
          CONVERT(VARCHAR(10), ISNULL(DT_EST, GETDATE()), 103) AS data,
          COALESCE(NOME_CLIENTE,'') AS cliente,
          COALESCE(CNPJ,'') AS cnpj,
          COALESCE(AG,'') AS ag,
          COALESCE(CC,'') AS conta
        FROM {self.TABLE}
        ORDER BY DATA_ENT DESC
        """
        return self._fetchall(sql, limit=limit)

    def search(self, ag: str = "", cc: str = "", cliente: str = "", tarifa: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
          COALESCE(NOME_CLIENTE,'') AS cliente,
          COALESCE(CNPJ,'')      AS cnpj,
          COALESCE(AG,'')        AS ag,
          COALESCE(CC,'')        AS conta,
          COALESCE(Tar,'')       AS tarifa,
          COALESCE(STATUS,'')    AS situacao
        FROM {self.TABLE}
        WHERE 1=1
          AND (:ag = '' OR AG = :ag)
          AND (:cc = '' OR CC = :cc)
          AND (:cli = '' OR NOME_CLIENTE LIKE '%' + :cli + '%')
          AND (:tar = '' OR Tar = :tar)
        ORDER BY DATA_ENT DESC
        """
        return self._fetchall(sql, ag=ag, cc=cc, cli=cliente, tar=tarifa)
      
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
        for k in ("Data_Ent","DT_Est"):
            if k in d: d[k] = self.to_date(d[k])
        if "Vlr_Est" in d:
            d["Vlr_Est"] = self.to_money(d["Vlr_Est"])

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

    def delete_many(self, ids: List[int]) -> int:
        ok = 0
        for i in ids:
            try:
                self.delete_by_id(int(i))
                ok += 1
            except Exception:
                pass
        return ok
    
    def search_cadastro(self, ag: str = "", cc: str = "", nome: str = "", tarifa: str = "") -> List[Dict[str, Any]]:
      sql = f"""
      SELECT
        Id AS id,
        DATA_ENT     AS Data_Ent,
        AREA         AS AREA,
        AG           AS AG,
        CC           AS CC,
        VLR_EST      AS Vlr_EST,
        Tar          AS TAR,
        VLR_CRED     AS Vlr_CRED,
        STATUS       AS Status,
        RESP         AS RESP,
        SEGMENTO     AS SEGMENTO,
        NOME_CLIENTE AS NOME
      FROM {self.TABLE}
      WHERE 1=1
        AND (:ag = ''  OR AG = :ag)
        AND (:cc = ''  OR CC = :cc)
        AND (:nm = ''  OR NOME_CLIENTE LIKE '%' + :nm + '%')
        AND (:tar = '' OR Tar = :tar)
      ORDER BY DATA_ENT DESC
      """
      return self._fetchall(sql, ag=ag, cc=cc, nm=nome, tar=tarifa)

