#!/usr/bin/env python3
"""
Script de inicialização para criar dados de exemplo no sistema
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User, Market, Metric, ExternalSource, DataPoint, Vote
from app.services.calculation_service import CalculationService
from app.services.vote_service import VoteService
from uuid import uuid4
import random
from datetime import datetime, timedelta


def create_sample_data():
    """
    Cria dados de exemplo para demonstração do sistema
    """
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Criar usuários de exemplo
        users = []
        for i in range(5):
            user = User(username=f"user_{i + 1}", email=f"user{i + 1}@example.com")
            db.add(user)
            users.append(user)

        db.commit()

        # Criar mercados
        markets = []
        market_data = [
            {
                "name": "Mercado de Criptomoedas",
                "description": "Preços e volumes de criptomoedas",
            },
            {
                "name": "Mercado de Ações",
                "description": "Índices e ações do mercado tradicional",
            },
            {
                "name": "Mercado de Commodities",
                "description": "Preços de commodities e matérias-primas",
            },
        ]

        for data in market_data:
            market = Market(**data)
            db.add(market)
            markets.append(market)

        db.commit()

        # Criar métricas para cada mercado
        metrics = []

        # Métricas para mercado de criptomoedas
        crypto_metrics = [
            {"name": "Bitcoin Price", "weight": 1.5},
            {"name": "Ethereum Price", "weight": 1.2},
            {"name": "Total Market Cap", "weight": 0.8},
        ]

        for i, metric_data in enumerate(crypto_metrics):
            metric = Metric(market_id=markets[0].id, **metric_data)
            db.add(metric)
            metrics.append(metric)

        # Métricas para mercado de ações
        stock_metrics = [
            {"name": "S&P 500", "weight": 1.0},
            {"name": "NASDAQ", "weight": 0.9},
            {"name": "Dow Jones", "weight": 0.8},
        ]

        for metric_data in stock_metrics:
            metric = Metric(market_id=markets[1].id, **metric_data)
            db.add(metric)
            metrics.append(metric)

        db.commit()

        # Criar fontes externas
        sources = []
        source_data = [
            {"name": "CoinGecko", "verification_method": "API verification"},
            {"name": "CoinMarketCap", "verification_method": "API verification"},
            {"name": "Yahoo Finance", "verification_method": "Official feed"},
            {"name": "Bloomberg", "verification_method": "Official feed"},
            {"name": "Reuters", "verification_method": "Official feed"},
        ]

        for data in source_data:
            source = ExternalSource(**data)
            db.add(source)
            sources.append(source)

        db.commit()

        # Criar pontos de dados
        data_points = []
        for metric in metrics:
            # 3-5 pontos de dado por métrica
            for i in range(random.randint(3, 5)):
                # Valor aleatório baseado no tipo de métrica
                if (
                    "Price" in metric.name
                    or "S&P" in metric.name
                    or "NASDAQ" in metric.name
                ):
                    # Preços de mercado
                    if "Bitcoin" in metric.name:
                        base_value = random.uniform(30000, 70000)
                    elif "Ethereum" in metric.name:
                        base_value = random.uniform(1500, 4000)
                    elif "S&P" in metric.name:
                        base_value = random.uniform(4000, 5000)
                    elif "NASDAQ" in metric.name:
                        base_value = random.uniform(12000, 16000)
                    else:
                        base_value = random.uniform(100, 1000)
                else:
                    # Outros indicadores
                    base_value = random.uniform(1000000, 5000000000)

                data_point = DataPoint(
                    metric_id=metric.id,
                    source_id=random.choice(sources).id,
                    value=base_value,
                    time_horizon_hours=random.choice([24, 48, 72, 168]),
                    is_reliable=True,  # Inicialmente confiável
                    reliability_expiration=datetime.utcnow()
                    + timedelta(days=random.randint(1, 7)),
                )
                db.add(data_point)
                data_points.append(data_point)

        db.commit()

        # Criar votos (aleatórios)
        vote_service = VoteService(db)
        for data_point in data_points:
            # 3-5 votos por ponto de dado
            for user in random.sample(users, random.randint(3, min(5, len(users)))):
                try:
                    # Maioria dos votos positiva (70%)
                    is_reliable = random.random() < 0.7
                    vote_service.create_vote(user.id, data_point.id, is_reliable)
                except Exception as e:
                    print(f"Erro ao criar voto: {e}")

        # Recalcular todos os valores
        calc_service = CalculationService(db)
        calc_service.recalculate_all_values()

        print("Dados de exemplo criados com sucesso!")
        print(f"- {len(users)} usuários")
        print(f"- {len(markets)} mercados")
        print(f"- {len(metrics)} métricas")
        print(f"- {len(sources)} fontes externas")
        print(f"- {len(data_points)} pontos de dado")

    except Exception as e:
        print(f"Erro ao criar dados: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
