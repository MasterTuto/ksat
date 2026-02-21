#!/usr/bin/env python3
"""
Script para criar o mercado inicial 'Is this coin useful?' com valor 1/N
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
from app.services.calculation_service import CalculationService
from app.services.vote_service import VoteService
from uuid import uuid4
import math
from config import N, INITIAL_COIN_VALUE


def create_coin_market():
    """
    Cria o mercado inicial 'Is this coin useful?' com valor 1/N
    """
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Criar usuário mock para frontend
        user = User(username="mock_user", email="mock@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Criar fonte externa mock
        source = ExternalSource(
            name="Initial Value", verification_method="System initialization"
        )
        db.add(source)
        db.commit()
        db.refresh(source)

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

        # Criar ponto de dado inicial com valor 1/N
        initial_value = INITIAL_COIN_VALUE
        data_point = DataPoint(
            metric_id=usefulness_metric.id,
            source_id=source.id,
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
        # metric_j = μ_j * latency_j
        # Onde latency_j vem dos dados confiáveis
        initial_value = INITIAL_COIN_VALUE  # μ_j inicial
        latency = 168.0  # latency_j inicial (1 semana)
        calculated_value = initial_value * latency  # metric_j = μ_j * latency_j

        metric_value = MetricValue(
            metric_id=usefulness_metric.id,
            mu=initial_value,
            latency=latency,
            value=calculated_value,
            error=0.0,
            beta=1.0,
        )
        db.add(metric_value)
        db.commit()

        print("Mercado inicial criado com sucesso!")
        print(f"Market ID: {coin_market.id}")
        print(f"Metric ID: {usefulness_metric.id}")
        print(f"Data Point ID: {data_point.id}")
        print(f"Initial Value: {initial_value} (1/N, N={N})")
        print(f"User ID for testing: {user.id}")

    except Exception as e:
        print(f"Erro ao criar mercado: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_coin_market()
