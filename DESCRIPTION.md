# Cellus Framework

**Agente de IA para plantas industriais que raciocina sobre Knowledge Graph de ativos e dados operacionais em tempo real de qualquer historiador.**

Engenheiros de processo fazem perguntas em linguagem natural. O Cellus consulta o Knowledge Graph da planta (Neo4j) para entender contexto, hierarquia e POPs — e busca os dados operacionais diretamente no historiador (OSIsoft PI, vNode, AVEVA Historian) via MCP. A resposta chega consolidada, com rastreabilidade de fonte.

Trocar de historiador é mudar uma linha no `.env`. Nenhum código muda.

---

## O problema que resolve

Plantas industriais têm dois mundos separados:

- **Dados de contexto** — hierarquia de planta, equipamentos, instrumentos, POPs, limites operacionais → vivem em documentos, ERPs ou grafos
- **Dados operacionais** — telemetria, alarmes, status em tempo real → vivem no historiador (PI, vNode, Historian)

Hoje, um engenheiro precisa consultar esses dois mundos manualmente para responder: *"por que o compressor X está em alarme e qual é o procedimento?"*

O Cellus faz isso automaticamente, em linguagem natural.

---

## Como funciona

```
Pergunta → planning → execute → planning → ... → synthesize → Resposta
```

- **planning** — o LLM decide quais ferramentas chamar (Knowledge Graph e/ou historiador)
- **execute** — consulta Neo4j (contexto de ativos) e o historiador via MCP (dados em tempo real) em paralelo
- **synthesize** — consolida tudo em uma resposta com rastreabilidade de fonte

O agente opera em ciclo ReAct compilado com LangGraph. Sem if/else de roteamento — o LLM decide o que consultar.

---

## Arquitetura de dados

```
Agente
├── Neo4jConnector   → Knowledge Graph (hierarquia, POPs, limites, decisões)
└── MCPConnector     → MCP Server → { OSIsoft PI | vNode | AVEVA Historian | mock }
```

O MCP Server é a camada de abstração sobre o historiador. Em desenvolvimento, use o mock incluso. Em produção, aponte para o endpoint real do seu historiador — o agente não sabe a diferença.

---

## Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — orquestração do ciclo ReAct
- **[LangChain](https://github.com/langchain-ai/langchain)** — abstração de LLMs e tools
- **[MCP (Model Context Protocol)](https://modelcontextprotocol.io/)** — protocolo aberto para dados operacionais (historiadores)
- **[Neo4j](https://neo4j.com/)** — Knowledge Graph de ativos industriais
- **[FastAPI](https://fastapi.tiangolo.com/)** — API REST pronta para uso
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — configuração via `.env`
- **Python 3.12+**

---

## Estrutura

```
cellus/               ← framework (não mexa)
├── core/             ← AgentState, Planner, Nodes, Workflow, CellusAgent
├── connectors/       ← ToolConnector (ABC), Neo4jConnector, MCPConnector
├── api/              ← create_app() + rotas REST
├── utils/            ← build_llm(), logging
└── settings.py       ← CellusSettings

industrial/           ← implementação de referência (use como template)
├── graph/            ← seed.cypher com hierarquia de planta, POPs, variáveis
├── tools/            ← LangChain Tools para Neo4j
├── mcp_server/       ← servidor MCP mock (substitua pelo seu historiador em produção)
├── prompts.py        ← persona do especialista industrial
└── settings.py       ← variáveis do domínio
```

---

## Quickstart

### 1. Dependências

```bash
uv sync
cp .env.example .env  # configure OPENAI_API_KEY, NEO4J_PASSWORD e MCP_SERVER_URL
```

### 2. Suba o Knowledge Graph e o mock do historiador

```bash
# Carrega hierarquia de planta, POPs e variáveis no Neo4j
python app.py --seed

# Sobe o servidor MCP mock (simula o historiador)
python -m industrial.mcp_server.server
```

### 3. Use

```bash
# CLI interativa
python app.py

# API REST
uvicorn main:app --reload
```

### 4. Em produção — aponte para o historiador real

```env
# .env
MCP_SERVER_URL=http://seu-vnode-ou-pi:8000/mcp
```

Nenhuma linha de código muda.

---

## Exemplo de pergunta

> *"O compressor C-101 está operando fora dos limites? Qual é o POP de resposta?"*

O agente:
1. Consulta o Neo4j → localiza C-101 na hierarquia, recupera limites operacionais e o POP associado
2. Consulta o historiador via MCP → busca telemetria recente das variáveis do C-101
3. Consolida → responde com status atual, desvios identificados e passos do POP

---

## Conectando seu historiador

Implemente um `MCPServer` compatível com seu historiador ou use um adaptador existente:

| Historiador | Como conectar |
|-------------|---------------|
| OSIsoft PI | MCP Server sobre PI Web API |
| vNode | MCP Server nativo (V2) |
| AVEVA Historian | MCP Server sobre REST API |
| Qualquer outro | Implemente `ToolConnector` |

## Conectando fontes de dados corporativas

Além do historiador, o agente pode consultar qualquer fonte de dados via `ToolConnector`:

| Fonte | Tipo | Como conectar |
|-------|------|---------------|
| PostgreSQL | Banco relacional | `ToolConnector` sobre `psycopg2` / `asyncpg` |
| MySQL | Banco relacional | `ToolConnector` sobre `mysql-connector-python` |
| SAP Datasphere | Data warehouse | `ToolConnector` sobre OData API ou JDBC |
| Databricks | Lakehouse | `ToolConnector` sobre Databricks SQL Connector |

O agente raciocina sobre todas as fontes simultaneamente — Knowledge Graph, historiador e dados corporativos — e consolida a resposta em uma única saída.

---

## Variáveis de ambiente

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1   # ou Azure AI Foundry
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.0

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

MCP_SERVER_URL=http://localhost:8000/mcp    # mock local ou historiador real
MCP_TRANSPORT=streamable_http

LOG_LEVEL=INFO
AGENT_MAX_TOOL_ITERATIONS=6
```

---

## Endpoints REST

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat` | Pergunta ao agente |
| POST | `/query` | Alias de `/chat` |
| GET | `/health` | Status dos conectores (Neo4j + MCP) |
| GET | `/tools` | Tools disponíveis por fonte |

---

## Roadmap

- [ ] Suporte a múltiplos servidores MCP simultâneos (múltiplos historiadores)
- [ ] Memória de conversação entre sessões
- [ ] Observabilidade (LangSmith / OpenTelemetry)
- [ ] Empacotamento como biblioteca PyPI (`pip install cellus`)
