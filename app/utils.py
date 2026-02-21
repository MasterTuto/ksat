#!/usr/bin/env python3
"""
Script simplificado para criar usuário padrão no sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import get_db, create_tables
from app.models.database import User
from app.models.user_password_mixin import UserPasswordMixin
from uuid import uuid4

def create_standard_user():
    """
    Cria usuário padrão no sistema
    """
    db = SessionLocal()
    try:
        # Verificar se já existe usuário padrão
        existing_user = db.query(User).filter(User.username == "admin").first()
        
        if existing_user:
            print(f"Usuário 'admin' já existe no banco de dados!")
            return existing_user
        
        print("=== CRIANDO USUÁRIO DE USUÁRIO ===")
        
        print("Criando usuário padrão 'admin' no banco de dados...")
        admin_user = User(
            username="admin",
            email="admin@dindin.com",
            currency_balance=1000.0,  # 1_000 unidades iniciais
        )
        admin_user.password_hash = UserPasswordMixin.set_password("admin123")
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"Usuário 'admin' criado com sucesso!")
        print(f"Username: admin")
        print(f"Email: admin@dindin.com")
        print(f"Moeda: 1000.00 unidades")
        print("\n=== USUÁRIO CRIADO COM SUCESSO ===")
        
    except Exception as e:
        print(f"Erro ao criar usuário padrão: {e}")
        import traceback
        return None

def create_standard_user_interactive():
    """
    Cria usuário padrão se não houver admin
    """
    db = SessionLocal()
    
    # Verificar se já existe usuário padrão
    existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Usuário 'admin' já existe no banco de dados!")
            return existing_admin
        
        print("=== CRIANDO USUÁRIO ===")
        print("Criando usuário padrão...")
        
        standard_user = User(
            username="standard_user",
            email="standard@example.com",
            currency_balance=1000.0  # 1_000 unidades iniciais
        )
        standard_user.password_hash = UserPasswordMixin.set_password("standard123")
        
        db.add(standard_user)
        db.commit()
        db.refresh(standard_user)
        
        print(f"Usuário 'standard_user' criado com sucesso!")
        print(f"Username: standard_user")
        print(f"Email: standard@example.com")
        print(f"Moeda: 1000.00 unidades")
        print("\n=== USUÁRIO CRIADO COM SUCESSO ===")
        
    except Exception as e:
        print(f"Erro ao criar usuário padrão: {e}")
        import traceback
        return None

if __name__ == "__main__":
    print("=== SISTEMA DE LOGIN - DINDIN ===")
    
    create_standard_user()