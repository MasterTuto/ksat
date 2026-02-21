import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User, Market, Metric
from app.services.calculation_service import CalculationService
from app.services.audit_service import AuditService
from app.math.engine import MathematicalEngine
from uuid import uuid4
from datetime import datetime
from config import N, INITIAL_COIN_VALUE


def create_initial_data():
    """
    Cria dados iniciais para o sistema
    """
    db = SessionLocal()
    try:
        print("=== CRIANDO DADOS INICIAIS ===")

        # Criar usuário admin
        admin_user = User(username="admin", email="admin@dindin.com")
        # Senha hash (em produção usar bcrypt)
        admin_user.password_hash = "sha256$加盐"
        db.add(admin_user)
        db.commit()
        print(f"Usuário admin criado: {admin_user.username} - {admin_user.email}")

        # Criar mercado "Is this coin useful?"
        coin_market = Market(
            name="Is this coin useful?",
            description="Market to determine if this coin has utility",
            is_active=True,
        )
        db.add(coin_market)
        db.commit()
        print(f"Mercado criado: {coin_market.name} - {coin_market.description}")

        # Criar métrica "usefulness" com peso 1.0
        usefulness_metric = Metric(
            market_id=coin_market.id,
            name="usefulness",
            description="How useful is this coin?",
            weight=1.0,
        )
        db.add(usefulness_metric)
        db.commit()
        print(
            f"Métrica criada: {usefulness_metric.name} - {usefulness_metric.description}"
        )

        # Criar fonte externa "Initial Value"
        initial_source = {
            "name": "Initial Value",
            "url": "https://dindin.com",
            "verification_method": "Manual setup",
        }

        # Criar ponto de dado inicial (1/N)
        from app.models.database import DataPoint, ExternalSource

        # Fonte externa mock inicial para o primeiro ponto
        from app.models.database import DataPoint, ExternalSource

        # Criar fonte externa Initial Value
        initial_source = (
            db.query(ExternalSource).filter_by(name="Initial Value").first()
        )
        if not initial_source:
            initial_source = ExternalSource(
                name="Initial Value",
                url="https://dindin.com",
                verification_method="Manual setup",
            )
            db.add(initial_source)
            db.commit()
            print(f"Fonte externa criada: {initial_source.name}")

        initial_source_id = initial_source.id

        # Criar ponto de dado inicial com valor 1/N
        initial_data_point = DataPoint(
            metric_id=usefulness_metric.id,
            source_id=initial_source_id,
            value=INITIAL_COIN_VALUE,
            time_horizon_hours=168,  # 1 semana
            is_reliable=True,
            participation_rate=1.0,
            latency=168.0,  # Latência máxima (1 semana)
            reliability_expiration=None,  # Sem expiração inicial
            created_at=datetime.utcnow(),
        )
        db.add(initial_data_point)
        db.commit()
        print(f"Ponto de dado inicial criado: {initial_data_point.id}")

        # Criar valor inicial da métrica
        from app.models.database import MetricValue

        initial_metric_value = MetricValue(
            metric_id=usefulness_metric.id,
            mu=INITIAL_COIN_VALUE,
            latency=168.0,
            value=INITIAL_COIN_VALUE * 168.0,  # μ_j * latency_j
            error=0.0,
            beta=1.0,
            calculated_at=datetime.utcnow(),
        )
        db.add(initial_metric_value)
        db.commit()
        print(f"Valor inicial da métrica criado: {initial_metric_value.value}")

        # Criar valor inicial do mercado
        from app.models.database import MarketValue

        initial_market_value = MarketValue(
            market_id=coin_market.id,
            value=INITIAL_COIN_VALUE,  # valor inicial da moeda (1/N)
            calculated_at=datetime.utcnow(),
        )
        db.add(initial_market_value)
        db.commit()
        print(f"Valor inicial do mercado criado: {initial_market_value.value}")

        print("\n=== DADOS INICIAIS CRIADOS COM SUCESSO ===")
        print(f"Mercado criado:")
        print(f"  Mercado: {coin_market.name}")
        print(f"  Métrica: {usefulness_metric.name}")
        print(f"  Valor inicial da moeda: 1/N (N={N})")
        print(f"  Valor do mercado: {initial_market_value.value}")
        print("Sistema pronto para uso.")

    except Exception as e:
        print(f"Erro ao criar dados iniciais: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_data()
