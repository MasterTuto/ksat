#!/usr/bin/env python3
"""
Script simplificado para garantir que o mercado inicial 'Is this coin useful?'
com valor 1/137 seja criado no banco de dados
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import (
    User,
    Market,
    Metric,
    ExternalSource,
    DataPoint,
    Vote,
    MetricValue,
)
from uuid import uuid4
import math


def ensure_coin_market():
    """
    Garante que o mercado inicial 'Is this coin useful?' com valor 1/137 exista no banco
    """
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Verificar se o mercado já existe
        existing_market = (
            db.query(Market).filter(Market.name == "Is this coin useful?").first()
        )
        if existing_market:
            print("Mercado 'Is this coin useful?' já existe no banco.")
            print(f"Market ID: {existing_market.id}")
            return

        # Criar usuário mock para frontend
        mock_user = db.query(User).filter(User.username == "mock_user").first()
        if not mock_user:
            mock_user = User(username="mock_user", email="mock@example.com")
            db.add(mock_user)
            db.commit()
            db.refresh(mock_user)
            print(f"Criado usuário mock: {mock_user.id}")

        # Criar fonte externa mock
        mock_source = (
            db.query(ExternalSource)
            .filter(ExternalSource.name == "Initial Value")
            .first()
        )
        if not mock_source:
            mock_source = ExternalSource(
                name="Initial Value", verification_method="System initialization"
            )
            db.add(mock_source)
            db.commit()
            db.refresh(mock_source)
            print(f"Criada fonte externa: {mock_source.id}")

        # Criar mercado 'Is this coin useful?'
        coin_market = Market(
            name="Is this coin useful?",
            description="Market to determine if this coin has utility",
        )
        db.add(coin_market)
        db.commit()
        db.refresh(coin_market)

        # Criar métrica 'usefulness' com peso 1.0
        usefulness_metric = Metric(
            market_id=coin_market.id,
            name="usefulness",
            description="How useful is this coin",
            weight=1.0,
        )
        db.add(usefulness_metric)
        db.commit()
        db.refresh(usefulness_metric)

        # Criar ponto de dado inicial com valor 1/137
        initial_value = 1 / 137
        data_point = DataPoint(
            metric_id=usefulness_metric.id,
            source_id=mock_source.id,
            value=initial_value,
            time_horizon_hours=168,  # 1 semana
            is_reliable=True,
            participation_rate=1.0,
            latency=168.0,
            reliability_expiration=None,  # Sem expiração inicial
        )
        db.add(data_point)
        db.commit()
        db.refresh(data_point)

        # Criar valor de métrica inicial calculado corretamente
        # metric_j = μ_j * latency_j onde μ_j = 1/137
        mu_value = 1 / 137  # μ_j inicial
        latency = 168.0  # latency_j inicial (1 semana)
        calculated_value = mu_value * latency  # metric_j = μ_j * latency_j

        metric_value = MetricValue(
            metric_id=usefulness_metric.id,
            mu=mu_value,
            latency=latency,
            value=calculated_value,
            error=0.0,
            beta=1.0,
        )
        db.add(metric_value)
        db.commit()
        db.refresh(metric_value)

        print("\n=== Mercado inicial criado com sucesso! ===")
        print(f"Market ID: {coin_market.id}")
        print(f"Market Name: 'Is this coin useful?'")
        print(f"Metric ID: {usefulness_metric.id}")
        print(f"Data Point ID: {data_point.id}")
        print(f"Initial μ_j (value): {mu_value} (1/137)")
        print(f"Initial latency: {latency}")
        print(f"Initial metric_j (calculated value): {calculated_value}")
        print(f"User ID for testing: {mock_user.id}")
        print(
            "\nO valor 1/137 está persistido no banco como μ_j (valor inicial da métrica)"
        )

    except Exception as e:
        print(f"Erro ao criar mercado: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    ensure_coin_market()
