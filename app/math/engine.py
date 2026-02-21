import numpy as np
from typing import List, Tuple, Union
from app.models.database import MetricValue, DataPoint, Metric
from sqlalchemy.orm import Session
import math
from datetime import datetime
from uuid import UUID


class MathematicalEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_softmin(self, x: float, y: float, beta: float = 1.0) -> float:
        """
        Calcula o softmin de dois valores com parâmetro beta

        softmin(x, y) = -log(exp(-βx) + exp(-βy)) / β
        """
        return -math.log(math.exp(-beta * x) + math.exp(-beta * y)) / beta

    def calculate_data_point_participation(
        self, data_point_id: Union[str, UUID]
    ) -> float:
        """
        Calcula a taxa de participação para um dado específico

        participação_k = (# votos 1) / (total de votos)
        """
        from app.models.database import Vote

        votes = (
            self.db.query(Vote).filter(Vote.data_point_id == str(data_point_id)).all()
        )
        if not votes:
            return 0.0

        positive_votes = sum(1 for vote in votes if vote.is_reliable)
        return positive_votes / len(votes)

    def calculate_data_point_latency(
        self, participation_rate: float, time_horizon: int
    ) -> float:
        """
        Calcula a latência de um dado

        latency_k = participação_k * T_k
        """
        return participation_rate * time_horizon

    def calculate_metric_latency(self, metric_id: Union[str, UUID]) -> float:
        """
        Calcula a latência de uma métrica como média ponderada das latências dos dados

        latency_j = Σ (peso_k * latency_k)
        """
        data_points = (
            self.db.query(DataPoint)
            .filter(
                DataPoint.metric_id == str(metric_id), DataPoint.is_reliable == True
            )
            .all()
        )

        if not data_points:
            return 0.0

        total_size = sum(abs(float(dp.value)) for dp in data_points)
        if total_size == 0:
            return 0.0

        weighted_latency = 0.0
        for dp in data_points:
            weight = abs(float(dp.value)) / total_size
            weighted_latency += weight * float(dp.latency)

        return weighted_latency

    def calculate_metric_mu(self, metric_id: Union[str, UUID]) -> float:
        """
        Calcula o valor μ_j como a média dos dados confiáveis

        μ_j = média(D_k confiáveis)
        """
        data_points = (
            self.db.query(DataPoint)
            .filter(
                DataPoint.metric_id == str(metric_id), DataPoint.is_reliable == True
            )
            .all()
        )

        if not data_points:
            return 0.0

        return sum(float(dp.value) for dp in data_points) / len(data_points)

    def calculate_metric_value(
        self, metric_id: Union[str, UUID]
    ) -> Tuple[float, float, float, float]:
        """
        Calcula o valor completo de uma métrica

        metric_j = μ_j * latency_j

        Retorna: (mu, latency, value, error)
        """
        mu = self.calculate_metric_mu(metric_id)
        latency = self.calculate_metric_latency(metric_id)
        value = mu * latency

        # Calcular erro comparando com valores observados reais
        error = self.calculate_metric_error(metric_id, mu)

        return mu, latency, value, error

    def calculate_metric_error(self, metric_id: Union[str, UUID], mu: float) -> float:
        """
        Calcula o erro da métrica

        erro_j = |μ_j - valor_real_observado_j|

        O valor real observado é derivado de dados que permaneceram confiáveis até T
        """
        data_points = (
            self.db.query(DataPoint)
            .filter(
                DataPoint.metric_id == str(metric_id), DataPoint.is_reliable == True
            )
            .all()
        )

        # Filtrar dados que ainda são confiáveis (não expiraram)
        current_time = datetime.utcnow()
        reliable_data_points = []
        for dp in data_points:
            if (
                dp.reliability_expiration is None
                or dp.reliability_expiration > current_time
            ):
                reliable_data_points.append(dp)

        if not reliable_data_points:
            return 0.0

        observed_real_value = sum(float(dp.value) for dp in reliable_data_points) / len(
            reliable_data_points
        )
        return abs(mu - observed_real_value)

    def apply_softmin_penalty(
        self, metric_id: Union[str, UUID], beta: float = 1.0
    ) -> float:
        """
        Aplica penalização por divergência usando softmin adaptativo

        metric_j = softmin(metric_j, erro_j)
        """
        mu, latency, value, error = self.calculate_metric_value(metric_id)

        # Aplicar softmin entre o valor atual e o erro
        penalized_value = self.calculate_softmin(value, error, beta)

        return penalized_value

    def binary_search_beta(
        self, metric_id: Union[str, UUID], epsilon: float = 0.01, delta: float = 0.001
    ) -> float:
        """
        Executa busca binária sobre β para minimizar divergência

        Objetivo: minimizar divergência entre expectativa agregada e valor real observado
        Critério de parada: erro residual < δ
        """
        low, high = 0.1, 10.0
        best_beta = 1.0
        min_error = float("inf")

        while high - low > delta:
            mid = (low + high) / 2
            penalized_value = self.apply_softmin_penalty(metric_id, mid)

            mu, latency, _, error = self.calculate_metric_value(metric_id)
            residual_error = abs(penalized_value - mu)  # Simplificação do erro residual

            if residual_error < min_error:
                min_error = residual_error
                best_beta = mid

            if residual_error > epsilon:
                # Se erro ainda grande, ajustar beta
                if penalized_value > mu:
                    high = mid
                else:
                    low = mid
            else:
                break

        return best_beta

    def calculate_market_value(self, market_id: Union[str, UUID]) -> float:
        """
        Calcula o valor de um mercado como média ponderada das métricas

        V_i = Σ (w_j * metric_j)
        """
        metrics = self.db.query(Metric).filter(Metric.market_id == str(market_id)).all()
        if not metrics:
            return 0.0

        total_value = 0.0
        total_weight = 0.0

        for metric in metrics:
            metric_value = self.apply_softmin_penalty(metric.id)
            total_value += float(metric.weight) * metric_value
            total_weight += float(metric.weight)

        if total_weight == 0:
            return 0.0

        return total_value / total_weight

    def calculate_global_currency_value(self) -> float:
        """
        Calcula o valor global da moeda como média dos valores dos mercados ativos

        C = média(V_i) para todos i ∈ mercados ativos
        """
        from app.models.database import Market, MarketValue

        active_markets = self.db.query(Market).filter(Market.is_active == True).all()
        if not active_markets:
            return 0.0

        total_value = 0.0
        count = 0

        for market in active_markets:
            market_value = self.calculate_market_value(market.id)
            total_value += market_value
            count += 1

        if count == 0:
            return 0.0

        return total_value / count

    def check_ksat_consistency(self, market_id: Union[str, UUID]) -> bool:
        """
        Verifica consistência final como problema k-SAT

        Cada métrica representa cláusula
        Votos são variáveis booleanas
        Existe decidibilidade apenas no nível agregado final
        """
        from app.models.database import Metric, DataPoint, Vote

        metrics = self.db.query(Metric).filter(Metric.market_id == str(market_id)).all()
        if not metrics:
            return False

        # Simplificação: verificamos se todas as métricas têm dados confiáveis
        # Em um sistema real, isso seria um solver SAT completo
        for metric in metrics:
            reliable_data_points = (
                self.db.query(DataPoint)
                .filter(DataPoint.metric_id == metric.id, DataPoint.is_reliable == True)
                .count()
            )

            if reliable_data_points == 0:
                return False

        return True
