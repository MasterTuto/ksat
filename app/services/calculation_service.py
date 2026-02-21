from sqlalchemy.orm import Session
from app.models.database import (
    MetricValue,
    MarketValue,
    GlobalCurrencyValue,
    DataPoint,
    Metric,
    Market,
)
from app.math.engine import MathematicalEngine
from app.schemas.schemas import (
    MetricValueResponse,
    MarketValueResponse,
    GlobalCurrencyValueResponse,
)
from typing import Union, Optional
from uuid import UUID
from datetime import datetime


class CalculationService:
    def __init__(self, db: Session):
        self.db = db
        self.math_engine = MathematicalEngine(db)

    def calculate_metric_value(
        self, metric_id: Union[str, UUID]
    ) -> Optional[MetricValueResponse]:
        """
        Calcula e retorna o valor de uma métrica
        """
        metric_id_str = str(metric_id)

        # Verificar se a métrica existe
        metric = self.db.query(Metric).filter(Metric.id == metric_id_str).first()
        if not metric:
            return None

        # Calcular valores
        mu, latency, value, error = self.math_engine.calculate_metric_value(
            metric_id_str
        )

        # Obter ou criar registro de valor da métrica
        metric_value = (
            self.db.query(MetricValue)
            .filter(MetricValue.metric_id == metric_id_str)
            .first()
        )

        if metric_value:
            # Atualizar valores existentes
            metric_value.mu = mu
            metric_value.latency = latency
            metric_value.value = value
            metric_value.error = error
            metric_value.calculated_at = datetime.utcnow()
            self.db.commit()
        else:
            # Criar novo registro
            metric_value = MetricValue(
                metric_id=metric_id_str,
                mu=mu,
                latency=latency,
                value=value,
                error=error,
            )
            self.db.add(metric_value)
            self.db.commit()
            self.db.refresh(metric_value)

        return MetricValueResponse(
            metric_id=UUID(metric_id_str),
            mu=mu,
            latency=latency,
            value=value,
            error=error,
            beta=float(metric_value.beta),
            calculated_at=metric_value.calculated_at,
        )

    def calculate_market_value(
        self, market_id: Union[str, UUID]
    ) -> Optional[MarketValueResponse]:
        """
        Calcula e retorna o valor de um mercado
        """
        market_id_str = str(market_id)

        # Verificar se o mercado existe
        market = self.db.query(Market).filter(Market.id == market_id_str).first()
        if not market:
            return None

        # Calcular valor do mercado
        value = self.math_engine.calculate_market_value(market_id_str)

        # Obter ou criar registro de valor do mercado
        market_value = (
            self.db.query(MarketValue)
            .filter(MarketValue.market_id == market_id_str)
            .first()
        )

        if market_value:
            # Atualizar valor existente
            market_value.value = value
            market_value.calculated_at = datetime.utcnow()
            self.db.commit()
        else:
            # Criar novo registro
            market_value = MarketValue(market_id=market_id_str, value=value)
            self.db.add(market_value)
            self.db.commit()
            self.db.refresh(market_value)

        return MarketValueResponse(
            market_id=UUID(market_id_str),
            value=value,
            calculated_at=market_value.calculated_at,
        )

    def calculate_global_currency_value(self) -> GlobalCurrencyValueResponse:
        """
        Calcula e retorna o valor global da moeda
        """
        # Calcular valor global
        value = self.math_engine.calculate_global_currency_value()

        # Obter ou criar registro de valor global
        global_value = (
            self.db.query(GlobalCurrencyValue)
            .order_by(GlobalCurrencyValue.calculated_at.desc())
            .first()
        )

        if global_value:
            # Atualizar valor existente
            global_value.value = value
            global_value.calculated_at = datetime.utcnow()
            self.db.commit()
        else:
            # Criar novo registro
            global_value = GlobalCurrencyValue(value=value)
            self.db.add(global_value)
            self.db.commit()
            self.db.refresh(global_value)

        return GlobalCurrencyValueResponse(
            value=value, calculated_at=global_value.calculated_at
        )

    def calculate_all_metrics_for_market(self, market_id: Union[str, UUID]) -> list:
        """
        Calcula todos os valores de métricas para um mercado específico
        """
        market_id_str = str(market_id)

        # Obter todas as métricas do mercado
        metrics = self.db.query(Metric).filter(Metric.market_id == market_id_str).all()

        results = []
        for metric in metrics:
            metric_value = self.calculate_metric_value(metric.id)
            if metric_value:
                results.append(metric_value)

        return results

    def calculate_all_markets(self) -> list:
        """
        Calcula valores para todos os mercados ativos
        """
        # Obter todos os mercados ativos
        markets = self.db.query(Market).filter(Market.is_active == True).all()

        results = []
        for market in markets:
            market_value = self.calculate_market_value(market.id)
            if market_value:
                results.append(market_value)

        return results

    def recalculate_all_values(self):
        """
        Recalcula todos os valores do sistema (reprocessamento determinístico)
        """
        # Calcular todas as métricas
        metrics = self.db.query(Metric).all()
        for metric in metrics:
            self.calculate_metric_value(metric.id)

        # Calcular todos os mercados
        markets = self.db.query(Market).all()
        for market in markets:
            self.calculate_market_value(market.id)

        # Calcular valor global
        self.calculate_global_currency_value()

    def apply_softmin_to_metric(
        self, metric_id: Union[str, UUID], beta: float = 1.0
    ) -> float:
        """
        Aplica penalização softmin a uma métrica
        """
        return self.math_engine.apply_softmin_penalty(metric_id, beta)

    def optimize_beta_for_metric(
        self, metric_id: Union[str, UUID], epsilon: float = 0.01, delta: float = 0.001
    ) -> float:
        """
        Otimiza beta para uma métrica usando busca binária
        """
        return self.math_engine.binary_search_beta(metric_id, epsilon, delta)

    def check_market_consistency(self, market_id: Union[str, UUID]) -> bool:
        """
        Verifica consistência K-SAT de um mercado
        """
        return self.math_engine.check_ksat_consistency(market_id)

    def get_reliable_data_points_for_metric(self, metric_id: Union[str, UUID]) -> list:
        """
        Retorna todos os pontos de dados confiáveis para uma métrica
        """
        metric_id_str = str(metric_id)
        data_points = (
            self.db.query(DataPoint)
            .filter(DataPoint.metric_id == metric_id_str, DataPoint.is_reliable == True)
            .all()
        )

        return data_points
