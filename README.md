# Cellus Framework

Agente de IA para plantas industriais que raciocina sobre **Knowledge Graph de ativos** e **dados operacionais em tempo real** de qualquer historiador.

Engenheiros de processo fazem perguntas em linguagem natural. O Cellus consulta o Neo4j (contexto, hierarquia, POPs) e o historiador via MCP (telemetria, alarmes, status) — e entrega a resposta consolidada, com rastreabilidade de fonte e memória de conversação entre turnos.

Trocar de historiador é mudar uma linha no `.env`. Nenhum código muda.

## Arquitetura

```
cellus/
├── core/          ← AgentState, Planner, Nodes, Workflow, CellusAgent
├── connectors/    ← ToolConnector (base), Neo4jConnector, MCPConnector, SQLConnector
├── memory/        ← ConversationMemory (histórico por session_id)
├── api/           ← create_app() + rotas REST
├── utils/         ← build_llm(), logging, telemetry (LangSmith / OpenTelemetry)
└── settings.py    ← CellusSettings (extensível)

industrial/        ← implementação de referência
├── graph/         ← Neo4jClient, cypher_queries, seed.cypher
├── tools/         ← LangChain Tools para Neo4j
├── mcp_server/    ← servidor MCP mock (substitua pelo historiador real em produção)
├── prompts.py     ← persona do especialista industrial
└── settings.py    ← IndustrialSettings
```

## Fluxo do agente

```
Pergunta → planning → execute → planning → ... → synthesize → Resposta
```

- **planning** — o LLM decide quais fontes consultar (sem if/else de roteamento)
- **execute** — consulta Neo4j e historiador via MCP em paralelo, acumula telemetria por fonte
- **synthesize** — consolida tudo em uma resposta com rastreabilidade

## Fontes de dados suportadas

| Fonte | Conector | Como conectar |
|-------|----------|---------------|
| OSIsoft PI / vNode / AVEVA Historian | `MCPConnector` | MCP Server sobre o historiador |
| Neo4j (Knowledge Graph) | `Neo4jConnector` | Bolt direto |
| PostgreSQL / MySQL | `SQLConnector` | SQLAlchemy connection string |
| SAP Datasphere | `SQLConnector` | HANA JDBC via `hdbcli` |
| Databricks | `SQLConnector` | Databricks SQL Connector |

## Setup do domínio industrial

### Dependências

```bash
uv sync
cp .env.example .env   # configure OPENAI_API_KEY, NEO4J_PASSWORD e MCP_SERVER_URL
```

### Neo4j Desktop
1. Instale: https://neo4j.com/download/
2. Crie um DBMS local (versão 5.x), defina senha, clique **Start**.
3. Coloque a senha em `NEO4J_PASSWORD` no `.env`.

### Execução

```bash
# 1. Carrega o Knowledge Graph
python app.py --seed

# 2. Sobe o servidor MCP mock (terminal separado)
python -m industrial.mcp_server.server

# 3a. CLI interativa
python app.py

# 3b. API REST
uvicorn main:app --reload
```

### Em produção — aponte para o historiador real

```env
MCP_SERVER_URL=http://seu-vnode-ou-pi:8000/mcp
```

## Memória de conversação

Cada sessão mantém histórico entre turnos. Passe `session_id` no request:

```json
{ "question": "e o compressor C-102?", "session_id": "sala-controle-1" }
```

O agente lembra o contexto da conversa anterior. Para limpar:

```
DELETE /memory/{session_id}
```

## Observabilidade

Configure no `.env` — ambos são opcionais:

```env
# LangSmith — rastreia chamadas LLM, tools, latência e tokens
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=cellus-industrial

# OpenTelemetry — envia traces para Jaeger, Grafana Tempo, Datadog, etc.
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=cellus-agent
```

```bash
uv sync --extra otel   # instala dependências OpenTelemetry
```

## Endpoints REST

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat` | Pergunta ao agente (suporta `session_id`) |
| POST | `/query` | Alias de `/chat` |
| DELETE | `/memory/{session_id}` | Limpa histórico da sessão |
| GET | `/health` | Status dos conectores e sessões ativas |
| GET | `/tools` | Tools disponíveis agrupadas por fonte |

## Implementando um novo conector

```python
from cellus.connectors.base import ToolConnector
from langchain_core.tools import StructuredTool

class MinhaFonteConnector(ToolConnector):
    name = "minha_fonte"

    async def load_tools(self) -> list:
        def buscar_dados(query: str) -> str:
            """Busca dados operacionais."""
            return meu_banco.query(query)
        return [StructuredTool.from_function(buscar_dados)]
```

```python
agent = await CellusAgent.create(
    llm=build_llm(settings),
    connectors=[Neo4jConnector(...), MCPConnector(...), MinhaFonteConnector()],
    planner_prompt="Você é especialista em...",
    synthesis_prompt="Consolide os dados coletados...",
)
```

Nenhum arquivo dentro de `cellus/` precisa ser alterado.
