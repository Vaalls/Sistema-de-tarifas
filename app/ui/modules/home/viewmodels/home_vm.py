# ===============================================
# ui/modules/home/viewmodels/home_vm.py — ViewModel
# ===============================================
from dataclasses import dataclass
from typing import Dict, List
from app.core.i18n.i18n import I18n


@dataclass
class RecentItem:
    tipo: str; 
    id: str; 
    cliente: str; 
    data: str; 
    status: str


class HomeViewModel:
    def __init__(self, i18n: I18n):
        self.i18n = i18n

    def kpis(self) -> Dict[str, int]:
        return {
            self.i18n.tr("kpi.repique"): 7,
            self.i18n.tr("kpi.cgm"): 12,
            self.i18n.tr("kpi.fato"): 35,
        }

    def recentes(self) -> List[RecentItem]:
        return [
            RecentItem("Repique", "R-1023", "ACME Ltda", "2025-08-18", "Pendente"),
            RecentItem("CGM", "C-5581", "Beta SA", "2025-08-18", "Aguardando"),
            RecentItem("Fato", "F-8802", "Gamma Corp", "2025-08-17", "Registrado"),
        ]