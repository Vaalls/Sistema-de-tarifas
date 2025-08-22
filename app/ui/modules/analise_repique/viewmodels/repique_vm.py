# app/ui/modules/analise_repique/viewmodels/repique_vm.py
from dataclasses import dataclass
from typing import List


@dataclass
class RepiqueRow:
    cliente: str
    conta: str
    valor: float


class RepiqueViewModel:
    LIMITE = 50000.0

    def __init__(self):
        self.rows: List[RepiqueRow] = []

    def selecionar_acima_limite(self) -> List[RepiqueRow]:
        """Retorna as linhas com valor >= LIMITE."""
        return [r for r in self.rows if r.valor >= self.LIMITE]

    def clear(self) -> None:
        """Limpa as linhas carregadas."""
        self.rows.clear()

    def carregar_db(self, repo) -> None:
        self.rows = [RepiqueRow(cli, conta, valor) for cli, conta, valor in repo.fetch_repiques()]

