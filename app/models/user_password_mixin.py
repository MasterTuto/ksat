# Extensão do modelo User para suporte a senha hash
class UserPasswordMixin:
    """Mixin para adicionar suporte a senha hash ao modelo User"""

    password_hash = Column(String(255), nullable=False, default="")

    def set_password(self, password: str):
        """Define a senha (hash)"""
        import hashlib

        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        import hashlib

        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
