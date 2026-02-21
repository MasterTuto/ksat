#!/usr/bin/env python3
"""
Script para criar 5 mercados com 3 métricas cada e fontes de dados dumb
com as características solicitadas.
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
    MarketValue,
)
from config import N, INITIAL_COIN_VALUE
from app.services.calculation_service import CalculationService
from uuid import uuid4
import math
import random
from datetime import datetime, timedelta

# Configurações dos mercados
MARKETS_CONFIG = [
    {
        "name": "Existem pessoas sem acesso a todos os recursos?",
        "description": "Market measuring global resource accessibility",
        "question": "Existem pessoas sem acesso a todos os recursos?",
        "relevance_question": "Este mercado é útil?",
        "totality_question": "Este mercado é total?",
        "color": "#FF6B6B",  # Laranja
    },
    {
        "name": "Existem pessoas que não decidiram?",
        "description": "Market measuring decision-making patterns in society",
        "question": "Existem pessoas que não decidiram?",
        "relevance_question": "Este mercado é útil?",
        "totality_question": "Este mercado é total?",
        "color": "#4ECDC4",  # Amarelo
    },
    {
        "name": "Existem pessoas com alta inteligência emocional?",
        "description": "Market measuring emotional intelligence levels",
        "question": "Existem pessoas com alta inteligência emocional?",
        "relevance_question": "Este mercado é útil?",
        "totality_question": "Este mercado é total?",
        "color": "#2196F3",  # Azul
    },
    {
        "name": "Existem pessoas sem acesso à educação?",
        "description": "Market measuring educational access inequality",
        "question": "Existem pessoas sem acesso à educação?",
        "relevance_question": "Este mercado é útil?",
        "totality_question": "Este mercado é total?",
        "color": "#9C27B0",  # Laranja escuro
    },
    {
        "name": "Existem pessoas com acesso a água potável?",
        "description": "Market measuring clean water access",
        "question": "Existem pessoas com acesso a água potável?",
        "relevance_question": "Este mercado é relevante?",
        "totality_question": "Este mercado é total?",
        "color": "#00BCD4",  # Ciano
    },
]

# Métricas para cada mercado
METRICS_CONFIG = [
    {
        "name": "Population Percentage",
        "weight": 1.0,
        "description": "Percentage of global population affected",
    },
    {
        "name": "Economic Impact",
        "weight": 1.5,
        "description": "Economic impact on global scale",
    },
    {
        "name": "Social Impact",
        "weight": 0.8,
        "description": "Social and cultural impact",
    },
]

# Fontes de dados dumb
DATA_SOURCES = [
    {
        "name": "World Bank Data",
        "url": "https://data.worldbank.org",
        "verification_method": "Official API",
    },
    {
        "name": "UN Statistics",
        "url": "https://unstats.un.org",
        "verification_method": "Official API",
    },
    {
        "name": "Global Census",
        "url": "https://census.gov",
        "verification_method": "Official API",
    },
    {
        "name": "Mock Research Institute",
        "url": "https://mock-research.edu",
        "verification_method": "Academic Research",
    },
    {
        "name": "Independent Survey",
        "url": "https://independent-survey.org",
        "verification_method": "Survey Data",
    },
    {
        "name": "Government Statistics",
        "url": "https://stats.gov",
        "verification_method": "Official API",
    },
    {
        "name": "Human Rights Watch",
        "url": "https://hrw.org",
        "verification_method": "NGO Data",
    },
    {
        "name": "Economic Forum",
        "url": "https://weforum.org",
        "verification_method": "Economic Reports",
    },
    {
        "name": "Environmental Agency",
        "url": "https://epa.gov",
        "verification_method": "Environmental Data",
    },
]


def create_dumb_data_point(metric_id, source_id, base_value):
    """Cria um data point com valor dumb baseado na latência"""
    # Latência em segundos (será usada para calcular valor)
    latency_seconds = random.randint(30, 300)  # 30s a 5 minutos

    # O job vai atualizar o valor baseado na latência
    # Simulação: valor aumenta com o tempo
    time_factor = latency_seconds / 60.0  # Converter para minutos
    noise = random.uniform(-0.1, 0.1)  # Adicionar ruído

    # Valor final: base + fator de tempo + ruído
    final_value = base_value + (time_factor * 0.01) + noise

    return DataPoint(
        metric_id=metric_id,
        source_id=source_id,
        value=final_value,
        time_horizon_hours=24,
        is_reliable=True,
        participation_rate=1.0,
        latency=latency_seconds,
        reliability_expiration=datetime.utcnow() + timedelta(hours=24),
    )


def create_dumb_job():
    """Cria um job dumb que atualiza valores com base na latência"""
    import time
    import random

    while True:
        # Espera um tempo aleatório entre 10 e 60 segundos
        wait_time = random.randint(10, 60)
        time.sleep(wait_time)

        # Atualiza valores de data points de forma proporcional à latência
        db = SessionLocal()
        try:
            data_points = db.query(DataPoint).all()

            for dp in data_points:
                # Calcular fator de atualização baseado na latência
                time_factor = dp.latency / 60.0 if dp.latency else 1.0
                update_amount = (time_factor * 0.001) + random.uniform(-0.0001, 0.0001)

                # Atualizar valor
                new_value = float(dp.value) + update_amount
                dp.value = new_value
                dp.updated_at = datetime.utcnow()

                print(
                    f"Updated data point {dp.id}: {dp.value} -> {new_value} (latency: {dp.latency}s)"
                )

            db.commit()

        except Exception as e:
            print(f"Error in dumb job: {e}")
        finally:
            db.close()


def create_sample_markets():
    """
    Cria 5 mercados com 3 métricas cada e fontes de dados dumb
    """
    db = SessionLocal()

    try:
        # Criar tabelas se não existirem
        create_tables()

        # Criar usuário mock
        mock_user = db.query(User).filter(User.username == "mock_user").first()
        if not mock_user:
            mock_user = User(username="mock_user", email="mock@example.com")
            db.add(mock_user)
            db.commit()
            db.refresh(mock_user)

        # Criar fontes externas
        created_sources = []
        for source_config in DATA_SOURCES:
            source = (
                db.query(ExternalSource)
                .filter(ExternalSource.name == source_config["name"])
                .first()
            )
            if not source:
                source = ExternalSource(**source_config)
                db.add(source)
                db.commit()
                db.refresh(source)
            created_sources.append(source)

        # Criar mercados e métricas
        for market_config in MARKETS_CONFIG:
            # Criar mercado
            market = Market(
                name=market_config["name"],
                description=market_config["description"],
                is_active=True,
            )
            db.add(market)
            db.commit()
            db.refresh(market)

            print(f"Created market: {market.name}")

            # Criar 3 métricas para este mercado
            market_metrics = []
            metric_values = []

            for i, metric_config in enumerate(METRICS_CONFIG):
                # Criar métrica
                metric = Metric(
                    market_id=market.id,
                    name=metric_config["name"],
                    description=metric_config["description"],
                    weight=metric_config["weight"],
                )
                db.add(metric)
                db.commit()
                db.refresh(metric)
                market_metrics.append(metric)

                # Criar 3 data points para cada métrica (total 9 por mercado)
                metric_data_points = []
                for j in range(3):
                    source = random.choice(created_sources)
                    base_value = (
                        INITIAL_COIN_VALUE if j == 0 else random.uniform(0.5, 2.0)
                    )  # Primeiro data point com 1/N

                    data_point = create_dumb_data_point(
                        metric.id, source.id, base_value
                    )
                    db.add(data_point)
                    db.commit()
                    db.refresh(data_point)
                    metric_data_points.append(data_point)

                # Criar valor inicial da métrica
                initial_values = [dp.value for dp in metric_data_points]
                mu_value = sum(initial_values) / len(initial_values)

                metric_value = MetricValue(
                    metric_id=metric.id,
                    mu=mu_value,
                    latency=sum(dp.latency for dp in metric_data_points)
                    / len(metric_data_points),
                    value=mu_value
                    * (
                        sum(dp.latency for dp in metric_data_points)
                        / len(metric_data_points)
                    ),
                    error=0.0,
                    beta=1.0,
                )
                db.add(metric_value)
                db.commit()
                metric_values.append(metric_value)

            # Criar valor do mercado (média ponderada das métricas)
            total_weighted_value = sum(
                mv.value * float(mv.metric.weight) for mv in metric_values
            )
            total_weight = sum(float(mv.metric.weight) for mv in metric_values)
            market_value = (
                total_weighted_value / total_weight if total_weight > 0 else 0
            )

            market_val = MarketValue(market_id=market.id, value=market_value)
            db.add(market_val)
            db.commit()

            print(f"  Market value: {market_value}")
            print(
                f"  Created {len(market_metrics)} metrics with {len([dp for metric in market_metrics for dp in metric.metric_data_points])} data points each"
            )

        print("\n=== Mercados e dados dumb criados com sucesso! ===")
        print(f"Total markets: {len(MARKETS_CONFIG)}")
        print(f"Total metrics per market: {len(METRICS_CONFIG)} (3 data points each)")
        print(f"Total data sources: {len(DATA_SOURCES)}")
        print(f"\nMercados criados:")
        for i, market in enumerate(MARKETS_CONFIG, 1):
            print(f"  {i}. {market['name']}")
            print(f"     Question: {market['question']}")
            print(f"     Relevance: {market['relevance_question']}")
            print(f"     Totality: {market['totality_question']}")

        print(f"\nFontes de dados criadas:")
        for source in DATA_SOURCES:
            print(f"  - {source['name']} ({source['verification_method']})")

        print(
            f"\nJobs dumb devem ser iniciados separadamente para atualizar os valores com base na latência."
        )
        print("Exemplo: python run_dumb_jobs.py")

    except Exception as e:
        print(f"Erro ao criar mercados: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_markets()
