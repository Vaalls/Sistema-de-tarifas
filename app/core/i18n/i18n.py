# ======================================
# core/i18n/i18n.py — Tradução simples
# ======================================
from ast import Dict
from typing import Dict

class I18n:
    PT = "pt"
    EN = "en"


    def __init__(self):
        self.current = I18n.PT
        self.dicts: Dict[str, Dict[str, str]] = {
            I18n.PT: {
                "app.title": "Sistema de Tarifa",
                "login.title": "Acessar",
                "login.user": "Usuário",
                "login.pass": "Senha",
                "login.env": "Ambiente",
                "login.remember": "Lembrar-me",
                "login.button": "Entrar",
                "login.forgot": "Esqueci minha senha",
                "env.prod": "Produção",
                "env.hml": "Homologação",
                "home.title": "Home",
                "search.placeholder": "Buscar clientes, contratos, repiques…",
                "quick.new.repique": "Nova Análise de Repique",
                "quick.new.cgm": "Novo Cadastro no CGM",
                "quick.new.fato": "Registrar Fato Gerador",
                "kpi.repique": "Repique pendente (hoje)",
                "kpi.cgm": "Cadastros CGM pendentes",
                "kpi.fato": "Fatos geradores (semana)",
                "recent": "Recentes",
                "view.all": "Ver todos",
                "menu.home": "Início",
                "menu.dashboard": "Dashboard",
                "menu.repique": "Análise de Repique",
                "menu.cgm": "Cadastro no CGM",
                "menu.fato": "Fato Gerador",
                "menu.cockpit": "Relatório Cockpit",
                "menu.docs": "Documentação",
                "menu.cancel": "Cancelamento de Repique",
                "toast.error.credentials": "Usuário ou senha inválidos",
                "help": "Ajuda",
            },
            I18n.EN: {
                "app.title": "Tariffs System",
                "login.title": "Sign in",
                "login.user": "User",
                "login.pass": "Password",
                "login.env": "Environment",
                "login.remember": "Remember me",
                "login.button": "Sign in",
                "login.forgot": "Forgot password",
                "env.prod": "Production",
                "env.hml": "Staging",
                "home.title": "Home",
                "search.placeholder": "Search customers, contracts, charges…",
                "quick.new.repique": "New Repique Analysis",
                "quick.new.cgm": "New CGM Registration",
                "quick.new.fato": "Register Fato Gerador",
                "kpi.repique": "Pending repique (today)",
                "kpi.cgm": "CGM registrations pending",
                "kpi.fato": "Fatos geradores (week)",
                "recent": "Recent",
                "view.all": "View all",
                "menu.home": "Home",
                "menu.dashboard": "Dashboard",
                "menu.repique": "Repique Analysis",
                "menu.cgm": "CGM Registration",
                "menu.fato": "Fato Gerador",
                "menu.docs": "Documentação",
                "menu.cockpit": "Cockpit Report",
                "menu.cancel": "Repique Cancellation",
                "toast.error.credentials": "Invalid credentials",
                "help": "Help",
            }
        }

    def tr(self, key: str) -> str:
        return self.dicts.get(self.current, {}).get(key, key)

    def toggle(self):
        self.current = I18n.EN if self.current == I18n.PT else I18n.PT