# Cellus Framework

Framework modular de Agente de IA com **LangGraph + Tool Calling**.
Qualquer desenvolvedor acopla suas próprias fontes de dados implementando `ToolConnector`.

## Arquitetura

```
cellus/                  ← pacote do framework (genérico, reutilizável)
├── core/                ← AgentState, Planner, Nodes, Workflow, CellusAgent
├── connectors/          ← ToolConnector (base), Neo4jConnector, MCPConnector
├── api/                 ← create_app() + rotas REST genéricas
├── utils/               ← build_llm(), logging
└── settings.py          ← CellusSettings (extensível)

industrial/              ← domínio Cellus (exemplo de implementação)
├── graph/               ← Neo4jClient, cypher_queries, seed.cypher
├── tools/               ← get_neo4j_tools() (tools específicas do POP)
├── mcp_server/          ← servidor MCP mock (substituível pelo vNode na V2)
├── models.py            ← modelos de domínio (VariableReading, Alarm, ...)
├── prompts.py           ← prompts do especialista industrial
└── settings.py          ← IndustrialSettings (estende CellusSettings)
```

## Como criar um novo agente (outro domínio)

### 1. Implemente seus conectores

```python
from cellus.connectors.base import ToolConnector
from langchain_core.tools import StructuredTool

class MyDBConnector(ToolConnector):
    name = "mydb"

    async def load_tools(self) -> list:
        def mydb_search(query: str) -> str:
            """Busca informações no banco de dados."""
            return my_db.search(query)

        return [StructuredTool.from_function(mydb_search)]
```

### 2. Monte o agente

```python
from cellus.core.agent import CellusAgent
from cellus.utils.llm import build_llm
from my_domain.settings import settings

agent = await CellusAgent.create(
    llm=build_llm(settings),
    connectors=[MyDBConnector(), MCPConnector(...)],
    planner_prompt="Você é especialista em...",
    synthesis_prompt="Consolide os dados...",
)
```

### 3. Use via API ou CLI

```python
# API REST
from cellus.api.server import create_app
app = create_app(agent_factory=lambda: build_agent())

# CLI / direto
from cellus.core.nodes import initial_state
result = await agent.graph.ainvoke(initial_state("sua pergunta"))
print(result["final_answer"])
```

## Setup do domínio industrial (Cellus)

### Dependências
```bash
uv sync
cp .env.example .env   # configure OPENAI_API_KEY e NEO4J_PASSWORD
```

### Neo4j Desktop
1. Instale: https://neo4j.com/download/
2. Crie um DBMS local (versão 5.x), defina senha, clique **Start**.
3. Coloque a senha em `NEO4J_PASSWORD` no `.env`.

### Execução
```bash
# 1) Carrega o Knowledge Graph
python app.py --seed

# 2) Sobe o servidor MCP mock (terminal separado)
python -m industrial.mcp_server.server

# 3a) CLI interativa
python app.py

# 3b) API REST
uvicorn main:app --reload
```

## Endpoints REST
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat` | Conversa com o agente |
| POST | `/query` | Alias de /chat |
| GET | `/health` | Status dos conectores |
| GET | `/tools` | Tools disponíveis agrupadas por prefixo |

## Evolução V2 (vNode)
Altere apenas `MCP_SERVER_URL` no `.env` para apontar ao endpoint MCP real.
Nada muda no framework, no agente, nas tools Neo4j ou na API.
