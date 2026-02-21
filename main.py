from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.database import (
    get_db,
    DataPoint,
    User,
    Market,
    Metric,
    ExternalSource,
    Vote,
    AuditLog,
)
from app.schemas.schemas import (
    DataPoint as DataPointSchema,
    UserCreate,
    UserUpdate,
    UserSchema,
    MarketCreate,
    MarketUpdate,
    MarketSchema,
    MarketWithMetrics,
    MetricCreate,
    MetricSchema,
    MetricWithDataPoints,
    ExternalSourceCreate,
    ExternalSourceSchema,
    VoteCreate,
    VoteSchema,
    MetricValueResponse,
    MarketValueResponse,
    GlobalCurrencyValueResponse,
    SoftminRequest,
    SoftminResponse,
    BinarySearchRequest,
    BinarySearchResponse,
    KSatConsistencyResponse,
    AuditLogResponse,
)
from app.services.calculation_service import CalculationService
from app.services.vote_service import VoteService
from app.math.engine import MathematicalEngine
from app.services.audit_service import AuditService
from config import N

# Simple API for data points with filtering

app = FastAPI(
    title="Dindin API",
    description="Sistema de Mercado Hierárquico com Agregação de Métricas",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rotas para Usuários
@app.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=UserSchema)
def read_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_user


@app.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: UUID, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


# Rotas para Mercados
@app.post("/markets/", response_model=MarketSchema, status_code=status.HTTP_201_CREATED)
def create_market(market: MarketCreate, db: Session = Depends(get_db)):
    # Verificar se o número máximo de mercados foi atingido
    existing_markets = db.query(Market).count()
    if existing_markets >= N:
        raise HTTPException(
            status_code=400, detail=f"Número máximo de mercados atingido. Limite: {N}"
        )

    db_market = Market(**market.dict())
    db.add(db_market)
    db.commit()
    db.refresh(db_market)

    # Criar log de auditoria
    AuditService.log_create(db, "market", db_market.id, db_market.dict())

    return db_market


@app.get("/markets/", response_model=List[MarketSchema])
def read_markets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    markets = db.query(Market).offset(skip).limit(limit).all()
    return markets


@app.get("/markets/{market_id}", response_model=MarketWithMetrics)
def read_market(market_id: UUID, db: Session = Depends(get_db)):
    db_market = db.query(Market).filter(Market.id == market_id).first()
    if db_market is None:
        raise HTTPException(status_code=404, detail="Mercado não encontrado")

    # Obter métricas do mercado
    metrics = db.query(Metric).filter(Metric.market_id == market_id).all()

    # Calcular valor do mercado
    math_engine = MathematicalEngine(db)
    market_value = math_engine.calculate_market_value(market_id)

    return MarketWithMetrics(**db_market.__dict__, metrics=metrics, value=market_value)


@app.put("/markets/{market_id}", response_model=MarketSchema)
def update_market(market_id: UUID, market: MarketUpdate, db: Session = Depends(get_db)):
    db_market = db.query(Market).filter(Market.id == market_id).first()
    if db_market is None:
        raise HTTPException(status_code=404, detail="Mercado não encontrado")

    old_values = db_market.__dict__.copy()

    update_data = market.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_market, key, value)

    db.commit()
    db.refresh(db_market)

    # Criar log de auditoria
    AuditService.log_update(db, "market", market_id, old_values, db_market.__dict__)

    return db_market


# Rotas para Métricas
@app.post("/metrics/", response_model=MetricSchema, status_code=status.HTTP_201_CREATED)
def create_metric(metric: MetricCreate, db: Session = Depends(get_db)):
    # Verificar se o mercado existe
    market = db.query(Market).filter(Market.id == metric.market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Mercado não encontrado")

    db_metric = Metric(**metric.dict())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    # Criar log de auditoria
    AuditService.log_create(db, "metric", db_metric.id, db_metric.dict())

    return db_metric


@app.get("/metrics/{metric_id}", response_model=MetricWithDataPoints)
def read_metric(metric_id: UUID, db: Session = Depends(get_db)):
    db_metric = db.query(Metric).filter(Metric.id == metric_id).first()
    if db_metric is None:
        raise HTTPException(status_code=404, detail="Métrica não encontrada")

    # Obter pontos de dados da métrica
    data_points = db.query(DataPoint).filter(DataPoint.metric_id == metric_id).all()

    # Calcular valor da métrica
    calculation_service = CalculationService(db)
    metric_value = calculation_service.calculate_metric_value(metric_id)

    return MetricWithDataPoints(
        **db_metric.__dict__, data_points=data_points, calculated_value=metric_value
    )


# Rotas para Fontes Externas
@app.post(
    "/external-sources/",
    response_model=ExternalSourceSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_external_source(source: ExternalSourceCreate, db: Session = Depends(get_db)):
    db_source = ExternalSource(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@app.get("/external-sources/", response_model=List[ExternalSourceSchema])
def read_external_sources(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    sources = db.query(ExternalSource).offset(skip).limit(limit).all()
    return sources


# Rotas para Pontos de Dados
@app.post(
    "/data-points/", response_model=DataPointSchema, status_code=status.HTTP_201_CREATED
)
def create_data_point(data_point: DataPointCreate, db: Session = Depends(get_db)):
    # Verificar se a métrica e a fonte existem
    metric = db.query(Metric).filter(Metric.id == data_point.metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Métrica não encontrada")

    source = (
        db.query(ExternalSource)
        .filter(ExternalSource.id == data_point.source_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Fonte externa não encontrada")

    db_data_point = DataPoint(**data_point.dict())
    db.add(db_data_point)
    db.commit()
    db.refresh(db_data_point)

    # Criar log de auditoria
    AuditService.log_create(
        db, "data_point", str(db_data_point.id), db_data_point.dict()
    )

    return db_data_point


@app.get("/data-points/", response_model=List[DataPointSchema])
def read_data_points(
    metric_id: Optional[str] = Query(None, description="Filter by metric ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(DataPoint)

    if metric_id:
        query = query.filter(DataPoint.metric_id == metric_id)

    data_points = query.offset(skip).limit(limit).all()
    return data_points


@app.get("/data-points/{data_point_id}", response_model=DataPointWithVotes)
def read_data_point(data_point_id: UUID, db: Session = Depends(get_db)):
    db_data_point = db.query(DataPoint).filter(DataPoint.id == data_point_id).first()
    if db_data_point is None:
        raise HTTPException(status_code=404, detail="Ponto de dado não encontrado")

    # Obter votos
    votes = db.query(Vote).filter(Vote.data_point_id == data_point_id).all()

    # Obter fonte
    source = (
        db.query(ExternalSource)
        .filter(ExternalSource.id == db_data_point.source_id)
        .first()
    )

    return DataPointWithVotes(**db_data_point.__dict__, votes=votes, source=source)


# Rotas para Votos
@app.post("/votes/", response_model=VoteSchema, status_code=status.HTTP_201_CREATED)
def create_vote(vote: VoteCreate, user_id: UUID, db: Session = Depends(get_db)):
    # Verificar se o usuário e o ponto de dado existem
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    data_point = db.query(DataPoint).filter(DataPoint.id == vote.data_point_id).first()
    if not data_point:
        raise HTTPException(status_code=404, detail="Ponto de dado não encontrado")

    # Verificar se o usuário já votou neste ponto de dado
    existing_vote = (
        db.query(Vote)
        .filter(Vote.user_id == user_id, Vote.data_point_id == vote.data_point_id)
        .first()
    )

    if existing_vote:
        raise HTTPException(
            status_code=400, detail="Usuário já votou neste ponto de dado"
        )

    # Criar voto usando serviço de votos
    vote_service = VoteService(db)
    db_vote = vote_service.create_vote(user_id, vote.data_point_id, vote.is_reliable)

    return db_vote


# Rotas para Cálculos
@app.get("/calculations/metric/{metric_id}", response_model=MetricValueResponse)
def calculate_metric_value(metric_id: UUID, db: Session = Depends(get_db)):
    calculation_service = CalculationService(db)
    metric_value = calculation_service.calculate_metric_value(metric_id)
    if not metric_value:
        raise HTTPException(
            status_code=404, detail="Métrica não encontrada ou sem dados confiáveis"
        )
    return metric_value


@app.get("/calculations/market/{market_id}", response_model=MarketValueResponse)
def calculate_market_value(market_id: UUID, db: Session = Depends(get_db)):
    calculation_service = CalculationService(db)
    market_value = calculation_service.calculate_market_value(market_id)
    if market_value is None:
        raise HTTPException(
            status_code=404, detail="Mercado não encontrado ou sem métricas"
        )
    return market_value


@app.get("/calculations/global-currency", response_model=GlobalCurrencyValueResponse)
def calculate_global_currency_value(db: Session = Depends(get_db)):
    calculation_service = CalculationService(db)
    global_value = calculation_service.calculate_global_currency_value()
    return global_value


# Rotas para Operações Matemáticas Avançadas
@app.post("/calculations/softmin", response_model=SoftminResponse)
def apply_softmin_penalty(request: SoftminRequest, db: Session = Depends(get_db)):
    math_engine = MathematicalEngine(db)
    original_value = math_engine.calculate_metric_value(request.metric_id)[
        2
    ]  # Pegar o valor (terceiro elemento)
    penalized_value = math_engine.apply_softmin_penalty(request.metric_id, request.beta)

    return SoftminResponse(
        metric_id=request.metric_id,
        original_value=original_value,
        penalized_value=penalized_value,
        beta_used=request.beta,
    )


@app.post("/calculations/binary-search-beta", response_model=BinarySearchResponse)
def binary_search_beta(request: BinarySearchRequest, db: Session = Depends(get_db)):
    math_engine = MathematicalEngine(db)
    optimal_beta = math_engine.binary_search_beta(
        request.metric_id, request.epsilon, request.delta
    )

    # Calcular o erro mínimo com o beta ótimo
    mu, _, _, error = math_engine.calculate_metric_value(request.metric_id)
    penalized_value = math_engine.apply_softmin_penalty(request.metric_id, optimal_beta)
    min_error = abs(penalized_value - mu)

    return BinarySearchResponse(
        metric_id=request.metric_id, optimal_beta=optimal_beta, min_error=min_error
    )


@app.get(
    "/calculations/ksat-consistency/{market_id}", response_model=KSatConsistencyResponse
)
def check_ksat_consistency(market_id: UUID, db: Session = Depends(get_db)):
    math_engine = MathematicalEngine(db)
    is_consistent = math_engine.check_ksat_consistency(market_id)

    return KSatConsistencyResponse(
        market_id=market_id,
        is_consistent=is_consistent,
        details={"message": "Verificação de consistência K-SAT concluída"},
    )


# Rotas para Logs de Auditoria
@app.get("/audit-logs/", response_model=List[AuditLogResponse])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs


@app.get(
    "/audit-logs/entity/{entity_type}/{entity_id}",
    response_model=List[AuditLogResponse],
)
def read_entity_audit_logs(
    entity_type: str, entity_id: UUID, db: Session = Depends(get_db)
):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    return logs


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
