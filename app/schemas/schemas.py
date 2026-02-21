from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


# Schemas para Usuários
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Mercados
class MarketBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class MarketCreate(MarketBase):
    pass


class MarketUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Market(MarketBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Métricas
class MetricBase(BaseModel):
    name: str
    description: Optional[str] = None
    weight: float = 1.0


class MetricCreate(MetricBase):
    market_id: UUID


class MetricUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = None


class Metric(MetricBase):
    id: UUID
    market_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Fontes Externas
class ExternalSourceBase(BaseModel):
    name: str
    url: Optional[str] = None
    verification_method: Optional[str] = None
    is_active: bool = True


class ExternalSourceCreate(ExternalSourceBase):
    pass


class ExternalSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    verification_method: Optional[str] = None
    is_active: Optional[bool] = None


class ExternalSource(ExternalSourceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Pontos de Dados
class DataPointBase(BaseModel):
    value: float
    time_horizon_hours: int


class DataPointCreate(DataPointBase):
    metric_id: UUID
    source_id: UUID


class DataPointUpdate(BaseModel):
    value: Optional[float] = None
    time_horizon_hours: Optional[int] = None


class DataPoint(DataPointBase):
    id: UUID
    metric_id: UUID
    source_id: UUID
    timestamp: datetime
    is_reliable: Optional[bool] = None
    reliability_expiration: Optional[datetime] = None
    participation_rate: float = 0.0
    latency: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Votos
class VoteBase(BaseModel):
    is_reliable: bool


class VoteCreate(VoteBase):
    data_point_id: UUID


class Vote(VoteBase):
    id: UUID
    user_id: UUID
    data_point_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Schemas para Valores Calculados
class MetricValueResponse(BaseModel):
    metric_id: UUID
    mu: float
    latency: float
    value: float
    error: float
    beta: float
    calculated_at: datetime

    class Config:
        from_attributes = True


class MarketValueResponse(BaseModel):
    market_id: UUID
    value: float
    calculated_at: datetime

    class Config:
        from_attributes = True


class GlobalCurrencyValueResponse(BaseModel):
    value: float
    calculated_at: datetime

    class Config:
        from_attributes = True


# Schemas para Logs de Auditoria
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    action: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Schemas para respostas complexas
class MarketWithMetrics(Market):
    metrics: List[Metric] = []
    value: Optional[float] = None


class MetricWithDataPoints(Metric):
    data_points: List[DataPoint] = []
    calculated_value: Optional[MetricValueResponse] = None


class DataPointWithVotes(DataPoint):
    votes: List[Vote] = []
    source: Optional[ExternalSource] = None


# Schemas para operações matemáticas
class SoftminRequest(BaseModel):
    metric_id: UUID
    beta: Optional[float] = 1.0


class SoftminResponse(BaseModel):
    metric_id: UUID
    original_value: float
    penalized_value: float
    beta_used: float


class BinarySearchRequest(BaseModel):
    metric_id: UUID
    epsilon: float = 0.01
    delta: float = 0.001


class BinarySearchResponse(BaseModel):
    metric_id: UUID
    optimal_beta: float
    min_error: float


class KSatConsistencyResponse(BaseModel):
    market_id: UUID
    is_consistent: bool
    details: Dict[str, Any] = {}
