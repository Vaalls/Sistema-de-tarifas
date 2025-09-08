from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from datetime import date, datetime

@dataclass
class RepiqueRow:
    cnpj_cpf: Optional[str]
    cliente: Optional[str]
    grupo_econ: Optional[str]
    tarifa: Optional[str]
    agencia: Optional[str]
    conta: Optional[str]
    dt: Optional[date]
    valor: float
    estab_cnpj: Optional[str]
    historico: Optional[str]
    lote: Optional[str]
    desc_status: Optional[str]
    modal: Optional[str]
    debc: Optional[str]
    rat: Optional[str]
    workout: Optional[str]
    restr_int: Optional[str]
    segmento: Optional[str]

class RepiqueViewModel:
    LIMITE = 50000.0

    def __init__(self):
        self.rows: List[RepiqueRow] = []

    def carregar_db(self, repo) -> None:
        raw: List[Dict[str, Any]] = repo.fetch_repiques()
        parsed: List[RepiqueRow] = []
        for d in raw:
            dt_val = d.get("DT")
            if isinstance(dt_val, str):
                try:
                    dt_val = datetime.fromisoformat(dt_val[:10]).date()
                except Exception:
                    dt_val = None
            elif isinstance(dt_val, datetime):
                dt_val = dt_val.date()
            elif not isinstance(dt_val, date):
                dt_val = None

            try:
                valor = float(d.get("VALOR") or 0.0)
            except Exception:
                valor = 0.0

            parsed.append(RepiqueRow(
                cnpj_cpf=d.get("CNPJ_CPF"),
                cliente=d.get("CLIENTE"),
                grupo_econ=d.get("GRUPO_ECON"),
                tarifa=str(d.get("TARIFA")) if d.get("TARIFA") is not None else None,
                agencia=str(d.get("AGENCIA")) if d.get("AGENCIA") is not None else None,
                conta=str(d.get("CONTA")) if d.get("CONTA") is not None else None,
                dt=dt_val,
                valor=valor,
                estab_cnpj=d.get("Estab_CNPJ"),
                historico=d.get("HISTORICO"),
                lote=str(d.get("LOTE")) if d.get("LOTE") is not None else None,
                desc_status=d.get("DESC_STATUS"),
                modal=d.get("MODAL"),
                debc=d.get("DEBC"),
                rat=d.get("RAT"),
                workout=d.get("WORKOUT"),
                restr_int=d.get("RESTR_INT"),
                segmento=d.get("SEGMENTO"),
            ))
        self.rows = parsed

    def selecionar_acima_limite(self) -> List[RepiqueRow]:
        return [r for r in self.rows if (r.valor or 0.0) >= self.LIMITE]
