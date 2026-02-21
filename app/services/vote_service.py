from sqlalchemy.orm import Session
from app.models.database import Vote, DataPoint, User, AuditLog
from app.math.engine import MathematicalEngine
from datetime import datetime, timedelta
from typing import Union
from uuid import UUID


class VoteService:
    def __init__(self, db: Session):
        self.db = db
        self.math_engine = MathematicalEngine(db)

    def create_vote(
        self,
        user_id: Union[str, UUID],
        data_point_id: Union[str, UUID],
        is_reliable: bool,
    ) -> Vote:
        """
        Cria um voto e atualiza os valores relacionados

        Cada voto altera participação_k.
        Cada alteração deve:
        - Recalcular latency_k
        - Recalcular latency_j
        - Recalcular metric_j
        - Recalcular V_i
        - Recalcular C
        """
        # Criar o voto
        db_vote = Vote(
            user_id=str(user_id),
            data_point_id=str(data_point_id),
            is_reliable=is_reliable,
        )
        self.db.add(db_vote)

        # Log de auditoria para o voto
        AuditService.log_create(
            self.db,
            "vote",
            db_vote.id,
            {
                "user_id": str(user_id),
                "data_point_id": str(data_point_id),
                "is_reliable": is_reliable,
            },
        )

        # Atualizar participação e latência do ponto de dado
        self._update_data_point_after_vote(str(data_point_id))

        # Atualizar valor da métrica
        data_point = (
            self.db.query(DataPoint).filter(DataPoint.id == str(data_point_id)).first()
        )
        if data_point:
            self._update_metric_after_data_point_change(str(data_point.metric_id))

            # Atualizar valor do mercado
            metric = (
                self.db.query(DataPoint)
                .join(Metric)
                .filter(DataPoint.id == str(data_point_id))
                .first()
            )
            if metric:
                self._update_market_after_metric_change(str(metric.market_id))

        self.db.commit()
        self.db.refresh(db_vote)

        return db_vote

    def _update_data_point_after_vote(self, data_point_id: str):
        """
        Atualiza participação e latência do ponto de dado após um voto
        """
        data_point = (
            self.db.query(DataPoint).filter(DataPoint.id == data_point_id).first()
        )
        if not data_point:
            return

        # Calcular nova participação
        participation_rate = self.math_engine.calculate_data_point_participation(
            data_point_id
        )

        # Calcular nova latência
        latency = self.math_engine.calculate_data_point_latency(
            participation_rate, data_point.time_horizon_hours
        )

        # Atualizar dados
        data_point.participation_rate = participation_rate
        data_point.latency = latency

        # Determinar se o dado é confiável baseado na participação
        # Se participação > 50%, consideramos confiável
        if participation_rate > 0.5:
            data_point.is_reliable = True
            # Define expiração da confiabilidade baseada no horizonte temporal
            data_point.reliability_expiration = datetime.utcnow() + timedelta(
                hours=data_point.time_horizon_hours
            )
        else:
            data_point.is_reliable = False
            data_point.reliability_expiration = None

        # Log de auditoria
        AuditService.log_update(
            self.db,
            "data_point",
            data_point_id,
            {
                "participation_rate": float(data_point.participation_rate),
                "latency": float(data_point.latency),
                "is_reliable": data_point.is_reliable,
            },
            {
                "participation_rate": participation_rate,
                "latency": latency,
                "is_reliable": data_point.is_reliable,
            },
        )

    def _update_metric_after_data_point_change(self, metric_id: str):
        """
        Atualiza o valor da métrica após mudança em um ponto de dado
        """
        from app.models.database import MetricValue

        # Calcular novos valores da métrica
        mu, latency, value, error = self.math_engine.calculate_metric_value(metric_id)

        # Obter ou criar registro de valor da métrica
        metric_value = (
            self.db.query(MetricValue)
            .filter(MetricValue.metric_id == metric_id)
            .first()
        )

        if metric_value:
            # Atualizar valores existentes
            old_values = {
                "mu": float(metric_value.mu),
                "latency": float(metric_value.latency),
                "value": float(metric_value.value),
                "error": float(metric_value.error),
            }

            metric_value.mu = mu
            metric_value.latency = latency
            metric_value.value = value
            metric_value.error = error
            metric_value.calculated_at = datetime.utcnow()

            # Log de auditoria
            AuditService.log_update(
                self.db,
                "metric_value",
                metric_value.id,
                old_values,
                {"mu": mu, "latency": latency, "value": value, "error": error},
            )
        else:
            # Criar novo registro
            metric_value = MetricValue(
                metric_id=metric_id, mu=mu, latency=latency, value=value, error=error
            )
            self.db.add(metric_value)

            # Log de auditoria
            AuditService.log_create(
                self.db,
                "metric_value",
                metric_value.id,
                {
                    "metric_id": metric_id,
                    "mu": mu,
                    "latency": latency,
                    "value": value,
                    "error": error,
                },
            )

    def _update_market_after_metric_change(self, market_id: str):
        """
        Atualiza o valor do mercado após mudança em uma métrica
        """
        from app.models.database import MarketValue

        # Calcular novo valor do mercado
        market_value = self.math_engine.calculate_market_value(market_id)

        # Obter ou criar registro de valor do mercado
        db_market_value = (
            self.db.query(MarketValue)
            .filter(MarketValue.market_id == market_id)
            .first()
        )

        if db_market_value:
            # Atualizar valor existente
            old_value = float(db_market_value.value)
            db_market_value.value = market_value
            db_market_value.calculated_at = datetime.utcnow()

            # Log de auditoria
            AuditService.log_update(
                self.db,
                "market_value",
                db_market_value.id,
                {"value": old_value},
                {"value": market_value},
            )
        else:
            # Criar novo registro
            db_market_value = MarketValue(market_id=market_id, value=market_value)
            self.db.add(db_market_value)

            # Log de auditoria
            AuditService.log_create(
                self.db,
                "market_value",
                db_market_value.id,
                {"market_id": market_id, "value": market_value},
            )

    def _update_global_currency_after_market_change(self):
        """
        Atualiza o valor global da moeda após mudança em um mercado
        """
        from app.models.database import GlobalCurrencyValue

        # Calcular novo valor global
        global_value = self.math_engine.calculate_global_currency_value()

        # Obter ou criar registro de valor global (mantém apenas o mais recente)
        existing_value = (
            self.db.query(GlobalCurrencyValue)
            .order_by(GlobalCurrencyValue.calculated_at.desc())
            .first()
        )

        if existing_value:
            # Atualizar valor existente
            old_value = float(existing_value.value)
            existing_value.value = global_value
            existing_value.calculated_at = datetime.utcnow()

            # Log de auditoria
            AuditService.log_update(
                self.db,
                "global_currency_value",
                existing_value.id,
                {"value": old_value},
                {"value": global_value},
            )
        else:
            # Criar novo registro
            existing_value = GlobalCurrencyValue(value=global_value)
            self.db.add(existing_value)

            # Log de auditoria
            AuditService.log_create(
                self.db,
                "global_currency_value",
                existing_value.id,
                {"value": global_value},
            )


# Importar AuditService aqui para evitar importação circular
from app.services.audit_service import AuditService
