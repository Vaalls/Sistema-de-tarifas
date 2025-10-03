from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.core.data.cgm.base_repository import BaseRepository

class EstornoRepository(BaseRepository):
    TABLE = "Estorno"

    # chaves do formulário → colunas reais da tabela
    MAP = {
        "DATA_ENT":   "DATA_ENT",
        "ÁREA":       "AREA",
        "AGÊNCIA":    "AG",
        "CONTA":      "CC",
        "CLIENTE":   "NOME_CLIENTE",      # alinhei com o que apareceu no seu erro
        "CNPJ":       "CNPJ",
        "VLR_ESTORNO":    "VLR_EST",
        "TARIFA":        "Tar",
        "DT_ESTORNO":     "DT_EST",
        "VLR_CREDITO":   "VLR_CRED",
        "STATUS":     "STATUS",
        "RESPONSAVEL":       "RESP",
        "SEGMENTO":   "SEGMENTO",
        "NM_AGÊNCIA":    "NOME_AG",
        "CLASS":      "CLASS",
        "PARECER": "PARECER_OP",
        "GRUPO": "GRUPO"
    }

    def insert(self, d: Dict[str, Any]) -> bool:
        d = dict(d)  # cópia
        # converte datas para objetos date (evita erro nvarchar→datetime)
        if "DATA_ENT" in d: d["DATA_ENT"] = self.to_date(d["DATA_ENT"])
        if "DT_ESTORNO"   in d: d["DT_ESTORNO"]   = self.to_date(d["DT_ESTORNO"])

        # dinheiro
        if "VLR_ESTORNO" in d: d["VLR_ESTORNO"] = self.to_money(d["VLR_ESTORNO"])
        if "VLR_CREDITO" in d: d["VLR_CREDITO"] = self.to_money(d["VLR_CREDITO"])

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

    def search(self, ag: str = "", cc: str = "", cli: str = "", tar: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
          COALESCE(NOME_CLIENTE,'') AS cliente,
          COALESCE(CNPJ,'')      AS cnpj,
          COALESCE(AG,'')        AS ag,
          COALESCE(CC,'')        AS conta,
          COALESCE(Tar,'')       AS tarifa
        FROM {self.TABLE}
        WHERE 1=1
          AND (:ag = '' OR AG = :ag)
          AND (:cc = '' OR CC = :cc)
          AND (:cli = '' OR NOME_CLIENTE LIKE '%' + :cli + '%')
          AND (:tar = '' OR Tar = :tar)
        ORDER BY DATA_ENT DESC
        """
        return self._fetchall(sql, ag=ag, cc=cc, cli=cli, tar=tar)
    
    def search_cadastro(self, ag: str = "", cc: str = "", cli: str = "", tar: str = "") -> List[Dict[str, Any]]:
      sql = f"""
      SELECT
        Id AS id,
          DATA_ENT       AS DATA_ENT,
          AREA           AS AREA,
          AG             AS AG,
          CC             AS CC,  
          NOME_CLIENTE   AS CLIENTE,
          CNPJ AS CNPJ,
          VLR_EST        AS VLR_EST,
          TAR            AS TAR,
          DT_EST        AS DT_EST,
          VLR_CRED       AS VLR_CRED,
          STATUS         AS STATUS,
          RESP           AS RESP,
          SEGMENTO       AS SEGMENTO,
          NOME_AG AS NM_AGÊNCIA,
          CLASS AS CLASS,
          PARECER_OP AS PARECER
      FROM {self.TABLE}
      WHERE 1=1
        AND (:ag = ''  OR AG = :ag)
        AND (:cc = ''  OR CC = :cc)
        AND (:nm = ''  OR NOME_CLIENTE LIKE '%' + :nm + '%')
        AND (:tar = '' OR Tar = :tar)
      ORDER BY DATA_ENT DESC
      """
      return self._fetchall(sql, ag=ag, cc=cc, nm=cli, tar=tar)
    
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
            if col == "DATA_ENT":
                v = self.to_date(v)            # DATA_NEG é datetime
            elif col in ("VLR_EST", "VLR_CRED"):
                v = self.to_money(v)
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
            if col == "DATA_ENT":
                v = self.to_date(v)
            elif col in ("VLR_EST", "VLR_CRED"):
                v = self.to_money(v)
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
    
    # ---------- Busca para a tela de consulta ----------
    def search_consulta(self, ag: str = "", cc: str = "", cli: str = "", tar: str = "") -> List[Dict[str, Any]]:
        sql = f"""
        SELECT
        Id            AS id,
        DATA_ENT      AS DATA_ENT,
        AREA          AS AREA,
        AG            AS AG,
        CC            AS CC,
        NOME_CLIENTE  AS CLIENTE,
        CNPJ          AS CNPJ,
        VLR_EST       AS VLR_EST,
        TAR           AS TAR,
        DT_EST        AS DT_EST,
        VLR_CRED      AS VLR_CRED,
        STATUS        AS STATUS,
        RESP          AS RESP,
        SEGMENTO      AS SEGMENTO,
        NOME_AG       AS NM_AGÊNCIA,
        CLASS         AS CLASS,
        PARECER_OP    AS PARECER
        FROM {self.TABLE}
        WHERE 1=1
        AND (:ag  = '' OR AG  = :ag)
        AND (:cc  = '' OR CC  = :cc)
        AND (:cli = '' OR NOME_CLIENTE LIKE '%' + :cli + '%')
        AND (:tar = '' OR TAR = :tar)      -- <<< FALTAVA ESTE FILTRO
        ORDER BY DATA_ENT DESC
        """
        return self._fetchall(sql, ag=ag or "", cc=cc or "", cli=cli or "", tar=tar or "")

    

