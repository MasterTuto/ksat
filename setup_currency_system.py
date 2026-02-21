#!/usr/bin/env python3
"""
Script para configurar o sistema de moeda global e população dinâmica
Cada usuário recebe 1_000 unidades iniciais
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User, Market, MetricValue, MarketValue
from uuid import uuid4


def setup_currency_system():
    """Configura o sistema de moeda global e população"""
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Buscar usuário mock ou criar se não existir
        mock_user = db.query(User).filter(User.username == "mock_user").first()
        if not mock_user:
            mock_user = User(
                username="mock_user",
                email="mock@example.com",
                currency_balance=1000.0,  # 1_000 unidades iniciais
            )
            db.add(mock_user)
            db.commit()
            db.refresh(mock_user)
            print(
                f"Usuário mock criado com {mock_user.currency_balance} unidades da moeda"
            )

        # Atualizar todos os usuários existentes para ter 1_000 unidades
        users = db.query(User).all()
        for user in users:
            user.currency_balance = 1000.0
            print(
                f"Atualizando usuário {user.username}: {user.currency_balance} unidades"
            )

        db.commit()

        print("=== Sistema de Moeda Configurado ===")
        print("Cada usuário inicia com 1_000 unidades")
        print("Total de usuários no sistema: calculado dinamicamente")
        print("Jobs dumb vão atualizar valores com base na latência")
        print("Use a API para gerenciar mais usuários ou verificar saldos")

    except Exception as e:
        print(f"Erro ao configurar sistema de moeda: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    setup_currency_system()
