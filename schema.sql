-- Modelo de Dados para Sistema de Mercado Hierárquico

-- Tabela de Usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Mercados
CREATE TABLE markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Métricas (associadas a mercados)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    weight DECIMAL(10, 6) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Fontes Externas
CREATE TABLE external_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    verification_method VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Dados (valores específicos de métricas de fontes externas)
CREATE TABLE data_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id UUID NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES external_sources(id) ON DELETE CASCADE,
    value DECIMAL(15, 8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    time_horizon_hours INTEGER NOT NULL, -- T_k
    is_reliable BOOLEAN NULL, -- Será definido pelos votos
    reliability_expiration TIMESTAMP WITH TIME ZONE, -- Quando a confiabilidade expira
    participation_rate DECIMAL(5, 4) DEFAULT 0.0, -- participação_k
    latency DECIMAL(10, 6) DEFAULT 0.0, -- latency_k
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Votos
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data_point_id UUID NOT NULL REFERENCES data_points(id) ON DELETE CASCADE,
    is_reliable BOOLEAN NOT NULL, -- 1 = sim, 0 = não
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, data_point_id)
);

-- Tabela de Valores Calculados de Métricas (cache)
CREATE TABLE metric_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id UUID NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    mu DECIMAL(15, 8) NOT NULL, -- μ_j
    latency DECIMAL(10, 6) NOT NULL, -- latency_j
    value DECIMAL(15, 8) NOT NULL, -- metric_j = μ_j * latency_j
    error DECIMAL(15, 8) DEFAULT 0.0, -- erro_j
    beta DECIMAL(10, 6) DEFAULT 1.0, -- β para softmin
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(metric_id)
);

-- Tabela de Valores Calculados de Mercados (cache)
CREATE TABLE market_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
    value DECIMAL(15, 8) NOT NULL, -- V_i
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(market_id)
);

-- Tabela de Valor Global da Moeda (cache)
CREATE TABLE global_currency_value (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    value DECIMAL(15, 8) NOT NULL, -- C
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Logs de Auditoria
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    entity_type VARCHAR(50) NOT NULL, -- 'market', 'metric', 'data_point', 'vote'
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'vote'
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_metrics_market_id ON metrics(market_id);
CREATE INDEX idx_data_points_metric_id ON data_points(metric_id);
CREATE INDEX idx_data_points_source_id ON data_points(source_id);
CREATE INDEX idx_votes_user_id ON votes(user_id);
CREATE INDEX idx_votes_data_point_id ON votes(data_point_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_data_points_timestamp ON data_points(timestamp);

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_markets_updated_at BEFORE UPDATE ON markets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metrics_updated_at BEFORE UPDATE ON metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_external_sources_updated_at BEFORE UPDATE ON external_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_points_updated_at BEFORE UPDATE ON data_points FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();