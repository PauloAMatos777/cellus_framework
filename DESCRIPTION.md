# Cellus Framework

**Framework modular para construção de Agentes de IA industriais com LangGraph + Tool Calling.**

Cellus resolve um problema recorrente em ambientes industriais: conectar um LLM a múltiplas fontes de dados heterogêneas (Knowledge Graphs, servidores MCP, APIs, bancos de dados) sem reescrever a lógica do agente a cada novo domínio ou fonte.

O dev implementa um conector, passa os prompts, e o framework cuida do resto.

---

## Como funciona

O agente opera em um ciclo ReAct compilado com LangGraph:

```
START → planning → execute → planning → ... → synthesize → END
```

- **planning** — o LLM decide quais ferramentas chamar (puro tool calling, sem if/else de roteamento)
- **execute** — executa as ferramentas, acumula resultados e telemetria por fonte
- **synthesize** — o LLM consolida todos os dados coletados em uma resposta final

Qualquer fonte de dados vira uma `ToolConnector` — a única interface que o framework exige.

---

## Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — orquestração do workflow ReAct
- **[LangChain](https://github.com/langchain-ai/langchain)** — abstração de LLMs e tools
- **[FastAPI](https://fastapi.tiangolo.com/)** — API REST pronta para uso
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — configuração extensível via `.env`
- **[MCP (Model Context Protocol)](https://modelcontextprotocol.io/)** — integração com servidores de dados via protocolo aberto
- **[Neo4j](https://neo4j.com/)** — conector opcional para Knowledge Graphs
- **Python 3.12+**

---

## Estrutura

```
cellus/               ← framework (instale e não mexa)
├── core/             ← AgentState, Planner, Nodes, Workflow, CellusAgent
├── connectors/       ← ToolConnector (ABC), Neo4jConnector, MCPConnector
├── api/              ← create_app() + rotas REST genéricas
├── utils/            ← build_llm(), logging
└── settings.py       ← CellusSettings (extensível por herança)

seu_dominio/          ← sua implementação (copie industrial/ como template)
├── tools/            ← suas LangChain Tools
├── prompts.py        ← persona e regras do seu especialista
└── settings.py       ← suas variáveis de ambiente
```

---

## Quickstart

### 1. Instale as dependências

```bash
uv sync
cp .env.example .env  # configure OPENAI_API_KEY e demais variáveis
```

### 2. Implemente um conector

```python
from cellus.connectors.base import ToolConnector
from langchain_core.tools import StructuredTool

class MinhaFonteConector(ToolConnector):
    name = "minha_fonte"

    async def load_tools(self) -> list:
        def buscar_dados(query: str) -> str:
            """Busca dados operacionais."""
            return meu_banco.query(query)

        return [StructuredTool.from_function(buscar_dados)]
```

### 3. Monte o agente

```python
from cellus.core.agent import CellusAgent
from cellus.utils.llm import build_llm

agent = await CellusAgent.create(
    llm=build_llm(settings),
    connectors=[MinhaFonteConector(), MCPConnector(...)],
    planner_prompt="Você é especialista em...",
    synthesis_prompt="Consolide os dados coletados...",
)
```

### 4. Exponha via API ou use direto

```python
# API REST (FastAPI)
from cellus.api.server import create_app
app = create_app(agent_factory=lambda: build_agent())

# Direto no código
from cellus.core.nodes import initial_state
result = await agent.graph.ainvoke(initial_state("qual o status do equipamento X?"))
print(result["final_answer"])
```

---

## Domínio industrial (exemplo incluído)

O repositório inclui `industrial/` — uma implementação completa para plantas industriais com:

- **Neo4j** como Knowledge Graph (hierarquia de planta, POPs, equipamentos, instrumentos, variáveis, decisões)
- **MCP** como fonte de dados operacionais em tempo real (telemetria, alarmes, status)
- Servidor MCP mock substituível pelo endpoint real sem alterar nenhuma linha do framework

Para usar em produção, basta apontar `MCP_SERVER_URL` no `.env` para o servidor real.

### Executando o exemplo industrial

```bash
# 1. Carrega o Knowledge Graph no Neo4j
python app.py --seed

# 2. Sobe o servidor MCP mock (terminal separado)
python -m industrial.mcp_server.server

# 3a. CLI interativa
python app.py

# 3b. API REST
uvicorn main:app --reload
```

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

MCP_SERVER_URL=http://localhost:8000/mcp
MCP_TRANSPORT=streamable_http

LOG_LEVEL=INFO
AGENT_MAX_TOOL_ITERATIONS=6
```

---

## Endpoints REST

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat` | Conversa com o agente |
| POST | `/query` | Alias de `/chat` |
| GET | `/health` | Status dos conectores |
| GET | `/tools` | Tools disponíveis agrupadas por fonte |

---

## Criando um novo domínio

Use `industrial/` como template. O que precisa ser adaptado:

| Arquivo | O que mudar |
|--------|-------------|
| `meu_dominio/prompts.py` | Persona e regras do especialista do seu setor |
| `meu_dominio/settings.py` | Variáveis de ambiente específicas do domínio |
| `meu_dominio/tools/` | LangChain Tools das suas fontes de dados |
| `meu_dominio/graph/seed.cypher` | Knowledge Graph do seu domínio (se usar Neo4j) |
| `meu_dominio/mcp_server/` | Servidor MCP mock para desenvolvimento |

Nenhum arquivo dentro de `cellus/` precisa ser alterado.

---

## Roadmap

- [ ] Suporte a múltiplos servidores MCP simultâneos
- [ ] Memória de conversação entre sessões
- [ ] Interface de observabilidade (LangSmith / OpenTelemetry)
- [ ] Conector genérico para REST APIs
- [ ] Empacotamento como biblioteca PyPI (`pip install cellus`)

---

> Cellus foi construído para o setor industrial, mas o framework é agnóstico de domínio.
> O mesmo núcleo serve para qualquer área onde um LLM precise raciocinar sobre dados de múltiplas fontes heterogêneas.
