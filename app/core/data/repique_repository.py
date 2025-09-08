# app/core/data/repique_repository.py
from __future__ import annotations
from typing import List, Dict, Any, Optional

class RepiqueRepository:
    def __init__(self, engine=None, use_mock: bool = True):
        self.engine = engine
        self.use_mock = use_mock

    def fetch_repiques(self) -> List[Dict[str, Any]]:
        if self.use_mock:
            # Datas em meses diferentes para testar "MesRef"
            return [
                {"CNPJ_CPF":"12.345.678/0001-90","CLIENTE":"Cliente Alfa","GRUPO_ECON":"Alfa Holding","TARIFA":"660","AGENCIA":"1234","CONTA":"567890-1","DT":"20250801","VALOR":120000.00,"Estab_CNPJ":"12.345.678/0001-90","HISTORICO":"Tarifa de repique 660","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
                {"CNPJ_CPF":"98.765.432/0001-10","CLIENTE":"Cliente Beta","GRUPO_ECON":"Beta Group","TARIFA":"662","AGENCIA":"2233","CONTA":"008877-2","DT":"20250802","VALOR":30000.00,"Estab_CNPJ":"98.765.432/0001-10","HISTORICO":"Tarifa de repique 662","LOTE":"0","DESC_STATUS":"Concluído","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Middle"},
                {"CNPJ_CPF":"11.111.111/0001-11","CLIENTE":"Cliente Gama","GRUPO_ECON":"Gama Participações","TARIFA":"665","AGENCIA":"4455","CONTA":"112233-4","DT":"20250803","VALOR":55000.00,"Estab_CNPJ":"11.111.111/0001-11","HISTORICO":"Tarifa de repique 665","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
                {"CNPJ_CPF":"22.222.222/0001-22","CLIENTE":"Cliente Delta","GRUPO_ECON":"Delta S.A.","TARIFA":"671","AGENCIA":"7788","CONTA":"556677-5","DT":"20250803","VALOR":48000.90,"Estab_CNPJ":"22.222.222/0001-22","HISTORICO":"Tarifa de repique 671","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Middle"},
                {"CNPJ_CPF":"55.555.555/0001-55","CLIENTE":"Cliente Ômega","GRUPO_ECON":"Ômega Participações","TARIFA":"665","AGENCIA":"6677","CONTA":"121212-3","DT":"20250804","VALOR":180000.00,"Estab_CNPJ":"55.555.555/0001-55","HISTORICO":"Tarifa de repique 665","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
                {"CNPJ_CPF":"66.666.666/0001-66","CLIENTE":"Cliente Sigma","GRUPO_ECON":"Sigma LTDA","TARIFA":"671","AGENCIA":"6677","CONTA":"454545-1","DT":"20250805","VALOR":20000.00,"Estab_CNPJ":"66.666.666/0001-66","HISTORICO":"Tarifa de repique 671","LOTE":"0","DESC_STATUS":"Concluído","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"SMB"},
                {"CNPJ_CPF":"77.777.777/0001-77","CLIENTE":"Cliente Teta","GRUPO_ECON":"Teta Corp","TARIFA":"672","AGENCIA":"6677","CONTA":"232323-1","DT":"20250806","VALOR":51000.00,"Estab_CNPJ":"77.777.777/0001-77","HISTORICO":"Tarifa de repique 672","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Middle"},
                {"CNPJ_CPF":"88.888.888/0001-88","CLIENTE":"Cliente Iota","GRUPO_ECON":"Iota Inc","TARIFA":"660","AGENCIA":"6677","CONTA":"909090-0","DT":"20250807","VALOR":72000.00,"Estab_CNPJ":"88.888.888/0001-88","HISTORICO":"Tarifa de repique 660","LOTE":"0","DESC_STATUS":"Análise","MODAL":"PJ","DEBC":"N/A","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
                # Meses diferentes:
                {"CNPJ_CPF":"10.000.000/0001-00","CLIENTE":"Cliente Janeiro","GRUPO_ECON":"Jan Group","TARIFA":"660","AGENCIA":"1000","CONTA":"100100-0","DT":"20250128","VALOR":52000.00,"Estab_CNPJ":"10.000.000/0001-00","HISTORICO":"Repique Jan","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"-","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
                {"CNPJ_CPF":"03.000.000/0001-00","CLIENTE":"Cliente Março","GRUPO_ECON":"Mar Group","TARIFA":"662","AGENCIA":"3000","CONTA":"303030-3","DT":"20250302","VALOR":47000.00,"Estab_CNPJ":"03.000.000/0001-00","HISTORICO":"Repique Mar","LOTE":"0","DESC_STATUS":"Concluído","MODAL":"PJ","DEBC":"-","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"SMB"},
                {"CNPJ_CPF":"07.000.000/0001-00","CLIENTE":"Cliente Julho","GRUPO_ECON":"Jul Group","TARIFA":"671","AGENCIA":"7000","CONTA":"707070-7","DT":"20250715","VALOR":510000.00,"Estab_CNPJ":"07.000.000/0001-00","HISTORICO":"Repique Jul","LOTE":"0","DESC_STATUS":"Pendente","MODAL":"PJ","DEBC":"-","RAT":"-","WORKOUT":"-","RESTR_INT":"-","SEGMENTO":"Corporate"},
            ]
        # (ramo sem mock omitido propositalmente neste ambiente)
        return []
