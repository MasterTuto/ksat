from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    DECIMAL,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import SessionLocal, engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    DECIMAL,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    votes = relationship("Vote", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Market(Base):
    __tablename__ = "markets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    metrics = relationship("Metric", back_populates="market")
    market_value = relationship("MarketValue", back_populates="market", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="entity_market")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(
        UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    weight = Column(DECIMAL(10, 6), nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    market = relationship("Market", back_populates="metrics")
    data_points = relationship("DataPoint", back_populates="metric")
    metric_value = relationship("MetricValue", back_populates="metric", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="entity_metric")


class ExternalSource(Base):
    __tablename__ = "external_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(500))
    verification_method = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    data_points = relationship("DataPoint", back_populates="source")


class DataPoint(Base):
    __tablename__ = "data_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(
        UUID(as_uuid=True), ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("external_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    value = Column(DECIMAL(15, 8), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    time_horizon_hours = Column(Integer, nullable=False)
    is_reliable = Column(Boolean, nullable=True)
    reliability_expiration = Column(DateTime(timezone=True), nullable=True)
    participation_rate = Column(DECIMAL(5, 4), default=0.0)
    latency = Column(DECIMAL(10, 6), default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    metric = relationship("Metric", back_populates="data_points")
    source = relationship("ExternalSource", back_populates="data_points")
    votes = relationship("Vote", back_populates="data_point")
    audit_logs = relationship("AuditLog", back_populates="entity_data_point")


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    data_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("data_points.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_reliable = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "data_point_id"),)

    user = relationship("User", back_populates="votes")
    data_point = relationship("DataPoint", back_populates="votes")


class MetricValue(Base):
    __tablename__ = "metric_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(
        UUID(as_uuid=True),
        ForeignKey("metrics.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    mu = Column(DECIMAL(15, 8), nullable=False)
    latency = Column(DECIMAL(10, 6), nullable=False)
    value = Column(DECIMAL(15, 8), nullable=False)
    error = Column(DECIMAL(15, 8), default=0.0)
    beta = Column(DECIMAL(10, 6), default=1.0)
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    metric = relationship("Metric", back_populates="metric_value")


class MarketValue(Base):
    __tablename__ = "market_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(
        UUID(as_uuid=True),
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    value = Column(DECIMAL(15, 8), nullable=False)
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    market = relationship("Market", back_populates="market_value")


class GlobalCurrencyValue(Base):
    __tablename__ = "global_currency_value"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(DECIMAL(15, 8), nullable=False)
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)
    old_values = Column(Text)
    new_values = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
    entity_market = relationship(
        "Market",
        foreign_keys=[entity_id],
        primaryjoin="and_(AuditLog.entity_type=='market', Market.id==AuditLog.entity_id)",
    )
    entity_metric = relationship(
        "Metric",
        foreign_keys=[entity_id],
        primaryjoin="and_(AuditLog.entity_type=='metric', Metric.id==AuditLog.entity_id)",
    )
    entity_data_point = relationship(
        "DataPoint",
        foreign_keys=[entity_id],
        primaryjoin="and_(AuditLog.entity_type=='data_point', DataPoint.id==AuditLog.entity_id)",
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
