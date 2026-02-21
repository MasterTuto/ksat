# Dindin - Sistema de Mercado Hierárquico

Uma alternativa a Polymarket baseada em agregação hierárquica de métricas com latência dinâmica e penalização via softmin adaptativo.

## Arquitetura

O sistema implementa uma estrutura hierárquica onde:

- **Mercados** (N ilimitados) contêm múltiplas métricas
- **Métricas** agregam dados de fontes externas verificáveis
- **Dados** são avaliados por votação para determinar confiabilidade
- **Valores** são calculados usando o valor desse dado (numero de pessoas com acesso a internet). Note q esse numero precisa estar entre 0 e 1.
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

### 4. Frontend Mínimo

Interface web simples sem styling que permite:
- Visualizar mercado "Is this coin useful?" com valor inicial 1/137
- Votar na confiabilidade dos dados
- Monitorar valores em tempo real

## Instalação e Execução

### Requisitos

- Docker e Docker Compose
- Python 3.11+ (se executar localmente)

### Via Docker Compose (Recomendado)

```bash
# Clonar o repositório
git clone <repositório>
cd dindin

# Iniciar serviços (API + Frontend + Banco)
docker-compose up --build

# A API estará disponível em http://localhost:8002
# O frontend em http://localhost:3002
# O banco de dados em localhost:5433 (porta alterada para evitar conflito)
```

### Resolução de Conflitos de Porta

Se encontrar erros de porta, o sistema inclui um script auxiliar:

```bash
# Verificar portas em uso
./check_ports.sh
```

E permite fácil modificação das portas no arquivo `docker-compose.yml`.

### Portas Configuradas

- **PostgreSQL**: 5433
- **API**: 8002  
- **Frontend**: 3002

### Setup Inicial

```bash
# Criar mercado inicial com valor 1/137
docker-compose exec api python create_coin_market.py

# O frontend já vai mostrar o mercado "Is this coin useful?"
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

# Rodar frontend (em outro terminal)
python frontend_server.py
```

## Documentação da API

Com a aplicação rodando, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:3000

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

1. **Acessar Frontend**: http://localhost:3000
2. **Visualizar Mercado**: "Is this coin useful?" com valor 1/137
3. **Votar**: Usuários votam na confiabilidade dos dados
4. **Monitorar**: Sistema atualiza valores dinamicamente
5. **Observar**: Valor do mercado muda baseado nos votos

## Mercado Inicial

O sistema vem pré-configurado com um mercado de demonstração:

- **Pergunta**: "Is this coin useful?"
- **Valor Inicial**: 1/137 (constante fundamental)
- **Métrica**: "usefulness" com peso 1.0
- **Fonte**: "Initial Value" (sistema)
- **Usuário Mock**: "mock_user" para testes

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