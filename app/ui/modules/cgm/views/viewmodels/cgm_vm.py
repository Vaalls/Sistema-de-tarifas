from dataclasses import dataclass
from typing import List

@dataclass
class CadastroCGM:
    id: str
    usuario: str
    tipo: str
    cliente: str

class CgmViewModel:
    def __init__(self, dias_alerta: int = 30):
        self._dias_alerta = dias_alerta

    # KPIs (mocks por enquanto)
    def negociacoes_ativas(self) -> int:
        return 42

    def dias_alerta(self) -> int:
        return self._dias_alerta

    def vencendo_em(self) -> int:
        return 7

    # Últimos cadastros (mock)
    def ultimos_cadastros(self) -> List[CadastroCGM]:
        return [
            CadastroCGM("CGM-10231", "maria.souza", "Estorno", "ACME Ltda"),
            CadastroCGM("CGM-10218", "joao.silva", "Pacote de Tarifas", "Beta SA"),
            CadastroCGM("CGM-10197", "ana.pereira", "Multas e Comissões", "Gamma Corp"),
        ]
