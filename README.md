# Dindin - Sistema de Mercado Hierárquico

Uma alternativa a Polymarket baseada em agregação hierárquica de métricas com latência dinâmica e penalização via softmin adaptativo.

## Arquitetura

O sistema implementa uma estrutura hierárquica onde:

- **Mercados** (N ilimitados) contêm múltiplas métricas
- **Métricas** agregam dados de fontes externas verificáveis
- **Dados** são avaliados por votação para determinar confiabilidade
- **Valores** são calculados usando fórmulas matemáticas específicas
- **Penalizações** são aplicadas via softmin adaptativo
- **Consistência** é verificada através de modelo K-SAT

## Principais Componentes

### 1. Modelo de Dados

- **Usuários**: Participantes que votam na confiabilidade dos dados
- **Mercados**: Entidades que produzem valores V_i
- **Métricas**: Componentes dos mercados com pesos w_j
- **Fontes Externas**: Provedores de dados verificáveis
- **Pontos de Dados**: Valores específicos com horizontes temporais
- **Votos**: Avaliações binárias de confiabilidade

### 2. Motor Matemático

Implementa as fórmulas principais:

- `C = média(V_i)` - Valor global da moeda
- `V_i = Σ (w_j * metric_j)` - Valor de mercado
- `metric_j = μ_j * latency_j` - Valor de métrica
- `latency_k = participação_k * T_k` - Latência de dado
- `softmin(x, y) = -log(exp(-βx) + exp(-βy)) / β` - Função de penalização

### 3. Serviços de Negócio

- **VoteService**: Gerencia votações e atualizações dinâmicas
- **CalculationService**: Realiza cálculos de valores
- **AuditService**: Mantém logs de todas as operações

## Instalação e Execução

### Requisitos

- Docker e Docker Compose
- Python 3.11+ (se executar localmente)

### Via Docker Compose (Recomendado)

```bash
# Clonar o repositório
git clone <repositório>
cd dindin

# Iniciar serviços
docker-compose up --build

# A API estará disponível em http://localhost:8000
# O banco de dados em localhost:5432
```

### Via Ambiente Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados PostgreSQL
# Editar .env com suas credenciais

# Aplicar schema
psql -U seu_usuario -d dindin -f schema.sql

# Rodar API
uvicorn main:app --reload
```

## Documentação da API

Com a aplicação rodando, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principais

#### Gerenciamento de Entidades
- `POST /users/` - Criar usuário
- `POST /markets/` - Criar mercado
- `POST /metrics/` - Criar métrica
- `POST /data-points/` - Adicionar ponto de dado
- `POST /votes/` - Votar em confiabilidade

#### Cálculos
- `GET /calculations/metric/{id}` - Valor da métrica
- `GET /calculations/market/{id}` - Valor do mercado
- `GET /calculations/global-currency` - Valor global

#### Operações Avançadas
- `POST /calculations/softmin` - Aplicar penalização softmin
- `POST /calculations/binary-search-beta` - Otimizar parâmetro β
- `GET /calculations/ksat-consistency/{id}` - Verificar consistência

## Fluxo de Trabalho Típico

1. **Criar Entidades**: Usuários criam mercados e métricas
2. **Adicionar Dados**: Fontes externas fornecem pontos de dado
3. **Votar**: Usuários avaliam confiabilidade dos dados
4. **Calcular**: Sistema atualiza valores dinamicamente
5. **Otimizar**: Ajusta parâmetros para minimizar erros
6. **Verificar**: Valida consistência via K-SAT

## Conceitos Matemáticos

### Latência Dinâmica

Cada dado possui uma latência que afeta seu peso nos cálculos:

```
latency_k = participação_k * T_k
```

Onde participação_k é a fração de votos positivos e T_k é o horizonte temporal declarado.

### Softmin Adaptativo

Penaliza valores divergentes do observado:

```
metric_j = softmin(metric_j, erro_j)
```

Com β otimizado via busca binária para minimizar divergências.

### Modelo K-SAT

A consistência final é modelada como problema satisfatibilidade onde:
- Métricas representam cláusulas
- Votos são variáveis booleanas
- Decidibilidade existe apenas no nível agregado

## Auditoria e Versionamento

Todas as operações são registradas em logs auditáveis:
- Criações, atualizações, exclusões
- Votos e mudanças de confiabilidade
- Recálculos de valores
- Modificações de parâmetros

## Licença

[Adicionar informação de licença]