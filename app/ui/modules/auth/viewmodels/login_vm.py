# ==================================================
# ui/modules/auth/viewmodels/login_vm.py — ViewModel
# ==================================================
class LoginViewModel:
    def __init__(self):
        self.user = ""
        self.password = ""
        self.env = "prod"


    def validate(self) -> bool:
        # Mock simples: qualquer coisa não vazia passa
        return bool(self.user.strip()) and bool(self.password.strip())