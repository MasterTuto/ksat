"""
Script simplificado para criar usuário inicial no sistema
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User
from app.models.user_extension import UserExtension
from uuid import uuid4


def create_initial_user():
    """Cria usuário inicial para testes"""
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Verificar se usuário admin já existe
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("Usuário 'admin' já existe no banco de dados.")
            return existing_user

        # Criar usuário inicial com X=1_000 unidades da moeda
        initial_user = UserExtension(
            username="admin",
            email="admin@dindin.com",
            currency_balance=1000.0,  # 1_000 unidades iniciais
        )
        db.add(initial_user)
        db.commit()
        db.refresh(initial_user)

        print("=== USUÁRIO CRIADO COM SUCESSO ===")
        print("Usuário 'admin' criado com 1_000 unidades da moeda")
        print(f"ID: {initial_user.id}")
        print(f"Username: {initial_user.username}")
        print(f"Email: {initial_user.email}")
        print(f"Saldo: {initial_user.currency_balance:.2f} unidades")

        return initial_user

    except Exception as e:
        print(f"Erro ao criar usuário inicial: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_user()
