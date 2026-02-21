#!/usr/bin/env python3
"""
Script para implementar sistema de login mínimo com usuário e senha em texto plano
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User
from app.models.user_extension import UserExtension
from uuid import uuid4
import hashlib
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash de senha simples (em produção usar bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_login_system():
    """
    Cria sistema de login com usuário/senha em texto plano
    """
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        print("=== SISTEMA DE LOGIN ===")
        print("Usuários existentes:")
        users = db.query(User).all()

        if not users:
            print("  Nenhum usuário encontrado.")
            print("Criando usuário admin padrão...")

            # Criar usuário admin
            admin_user = User(
                username="admin", email="admin@dindin.com", currency_balance=1000.0
            )
            admin_user.password_hash = hash_password("admin123")
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            print(f"Usuário admin criado:")
            print(f"  Username: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            print("  Senha: admin123")
            print(f"  Moeda: {admin_user.currency_balance:.2f}")
            print()
            print("Use essas credenciais para fazer login.")
        else:
            print(f"  {len(users)} usuário(s) encontrados:")
            for user in users:
                status = "Habilitado" if hasattr(user, "password_hash") else "Sem senha"
                moeda = (
                    f"{user.currency_balance:.2f}"
                    if hasattr(user, "currency_balance")
                    else "N/A"
                )
                print(
                    f"  Username: {user.username} | Email: {user.email} | Status: {status} | Moeda: {moeda}"
                )

        print("\n=== INSTRUÇÕES ===")
        print("1. Use o frontend para criar nova conta")
        print("2. Use: python create_user.py para criar usuários via linha de comando")
        print("3. Use: python list_users.py para listar usuários existentes")

    except Exception as e:
        print(f"Erro ao configurar sistema de login: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def create_user_interactive():
    """
    Cria um novo usuário de forma interativa
    """
    db = SessionLocal()

    try:
        print("=== CRIAÇÃO DE USUÁRIO ===")

        username = input("Username: ").strip()
        if not username:
            print("Username não pode ser vazio!")
            return

        email = input("Email: ").strip()
        if not email:
            print("Email não pode ser vazio!")
            return

        password = input("Senha: ").strip()
        if not password:
            print("Senha não pode ser vazia!")
            return

        # Verificar se usuário já existe
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Usuário '{username}' já existe!")
            return

        # Criar novo usuário
        new_user = User(
            username=username,
            email=email,
            currency_balance=1000.0,  # 1_000 unidades iniciais
        )
        new_user.password_hash = hash_password(password)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"\nUsuário criado com sucesso!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Moeda: 1000.00 unidades")
        print(f"\nFaça login para acessar o sistema.")

    except KeyboardInterrupt:
        print("\nOperação cancelada.")
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def list_users():
    """
    Lista todos os usuários existentes
    """
    db = SessionLocal()

    try:
        users = db.query(User).all()

        if not users:
            print("Nenhum usuário encontrado.")
            return

        print(f"=== USUÁRIOS ({len(users)}) ===")
        print(f"{'Username':<15} | {'Moeda':<15} | {'Email':<30} | {'Criado em':<20}")
        print("-" * 70)

        for user in users:
            created_date = user.created_at.strftime("%d/%m/%Y %H:%M")
            moeda = (
                f"{user.currency_balance:.2f}"
                if hasattr(user, "currency_balance")
                else "N/A"
            )

            print(
                f"{user.username:<15} | {moeda:<10} | {user.email:<30} | {created_date}"
            )

        print("-" * 70)

    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def verify_login(username: str, password: str) -> tuple:
    """
    Verifica credenciais de usuário
    Retorna (sucesso, usuário_obj ou erro, None)
    """
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return (False, "Usuário não encontrado", None)

        if not hasattr(user, "password_hash"):
            return (False, "Usuário não tem senha definida", None)

        # Verificar senha
        input_hash = hash_password(password)

        if input_hash == user.password_hash:
            return (True, user, None)
        else:
            return (False, "Senha incorreta", None)

    except Exception as e:
        return (False, f"Erro na verificação: {e}", None)
    finally:
        db.close()


def main():
    """Menu principal do sistema de login"""
    print("=== SISTEMA DE LOGIN - DINDIN ===")
    print("1. Verificar sistema")
    print("2. Criar usuário")
    print("3. Listar usuários")
    print("4. Sair")

    try:
        choice = input("\nEscolha uma opção: ").strip()

        if choice == "1":
            create_login_system()
        elif choice == "2":
            create_user_interactive()
        elif choice == "3":
            list_users()
        elif choice == "4":
            print("Saindo...")
            return
        else:
            print("Opção inválida!")

    except KeyboardInterrupt:
        print("\nSaindo...")
    except EOFError:
        print("\nExecutando verificação padrão do sistema...")
        create_login_system()


if __name__ == "__main__":
    main()
