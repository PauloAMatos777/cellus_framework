# Cellus Framework

**Plataforma de agente de IA para plantas industriais que raciocina sobre Knowledge Graph de ativos, dados operacionais em tempo real e fontes corporativas — entregando respostas consolidadas, rastreáveis e defensáveis em linguagem natural.**

---

## O problema que resolve

Plantas industriais operam com dados fragmentados em mundos separados:

- **Contexto de planta** — hierarquia de ativos, equipamentos, instrumentos, POPs, limites operacionais → vivem em documentos, ERPs ou grafos
- **Dados operacionais** — telemetria, alarmes, status em tempo real → vivem no historiador (PI, vNode, AVEVA Historian)
- **Dados corporativos** — consumo de insumos, ordens de produção, análises → vivem em SAP, Databricks, bancos relacionais

Hoje, um engenheiro precisa consultar esses mundos manualmente, cruzar informações e chegar a uma conclusão. O Cellus faz isso automaticamente, em linguagem natural, com rastreabilidade de cada fonte consultada.

---

## Como funciona

O Cellus é um agente ReAct compilado com LangGraph. O LLM decide quais ferramentas chamar a cada ciclo — sem roteamento hardcoded. O agente consulta as fontes necessárias, acumula contexto e sintetiza a resposta.

```
Pergunta → planning → execute → planning → ... → synthesize → Resposta
```

- **planning** — o LLM analisa o contexto acumulado e decide quais ferramentas chamar
- **execute** — consulta Neo4j, historiador via MCP e fontes corporativas em paralelo
- **synthesize** — consolida tudo em uma resposta com rastreabilidade de fonte

---

## Capacidades

### Raciocínio multi-fonte

O agente raciocina sobre Neo4j, historiador industrial e fontes corporativas em um único ciclo. Não há if/else de roteamento — o LLM decide o que consultar com base no contexto acumulado.

### Knowledge Graph de ativos

O Neo4j armazena a hierarquia completa da planta: áreas, processos, equipamentos, instrumentos, variáveis, POPs e decisões de processo. O agente usa esse grafo para entender *o que* medir, *onde* medir e *o que fazer* quando algo está fora dos limites.

### Dados operacionais via MCP

O Model Context Protocol (MCP) é a camada de abstração sobre o historiador. Em desenvolvimento, use o mock incluso. Em produção, aponte para o endpoint do seu historiador — o agente não sabe a diferença.

```env
MCP_SERVER_URL=http://seu-vnode-ou-pi:8000/mcp
```

### Memória de conversação

Cada sessão mantém histórico entre turnos. O engenheiro pode fazer perguntas de acompanhamento sem repetir contexto.

```json
{ "question": "e o compressor C-102?", "session_id": "sala-controle-1" }
```

### Assurance Layer (JEV Engine)

Camada intermediária entre planejamento e execução que torna o agente industrialmente defensável:

- **Validação de evidências** — bloqueia execução se o contexto não tem as variáveis necessárias para responder ao objetivo. Para investigar kappa, o agente precisa de temperatura, pressão, tempo de residência e dosagem química antes de concluir.
- **Controle de acesso** — nenhuma tool executa sem verificação de política para o usuário e a fonte de dados (SAP, PI, Neo4j, OT).
- **Classificação de risco** — tools de ação operacional (`OPERATIONAL_ACTION`) são bloqueadas automaticamente. Prescrições (`PRESCRIPTIVE`) exigem aprovação humana explícita.
- **Score de confiança** — cada resposta tem um score 0–1 baseado em cobertura de evidências, diversidade de fontes e consistência dos resultados.
- **Auditoria completa** — cada execução gera um `AuditRecord` com pergunta, plano, validações, fontes, confiança e resposta final. Recuperável via API.

### Observabilidade

Suporte nativo a LangSmith (rastreamento de chamadas LLM, tools e latência) e OpenTelemetry (traces para Jaeger, Grafana Tempo, Datadog).

### Extensibilidade

Novos conectores, novas tools e novos domínios sem alterar o framework. Basta implementar `ToolConnector` e injetar no `CellusAgent.create()`.

---

## Stack

| Componente | Tecnologia |
|------------|------------|
| Orquestração do agente | LangGraph |
| Abstração de LLMs e tools | LangChain |
| Dados operacionais | MCP (Model Context Protocol) |
| Knowledge Graph | Neo4j |
| API REST | FastAPI |
| Configuração | Pydantic Settings |
| Observabilidade | LangSmith + OpenTelemetry |
| Runtime | Python 3.12+ |

---

## Fontes de dados suportadas

| Fonte | Tipo | Conector |
|-------|------|----------|
| OSIsoft PI / AVEVA Historian | Historiador industrial | `MCPConnector` |
| vNode | Historiador industrial | `MCPConnector` |
| Neo4j | Knowledge Graph | `Neo4jConnector` |
| PostgreSQL / MySQL | Banco relacional | `SQLConnector` |
| SAP Datasphere | Data warehouse | `SQLConnector` |
| Databricks | Lakehouse | `SQLConnector` |

---

## Quickstart

```bash
uv sync
cp .env.example .env

# Carrega o Knowledge Graph
python app.py --seed

# Sobe o mock do historiador
python -m industrial.mcp_server.server

# CLI interativa
python app.py

# API REST
uvicorn main:app --reload
```

---

## Exemplo de uso

> *"O compressor C-101 está operando fora dos limites? Qual é o POP de resposta?"*

O agente:
1. Consulta o Neo4j → localiza C-101 na hierarquia, recupera limites operacionais e o POP associado
2. Consulta o historiador via MCP → busca telemetria recente das variáveis do C-101
3. Valida evidências → confirma que tem dados suficientes para concluir
4. Consolida → responde com status atual, desvios identificados, passos do POP e `confidence_score`

---

## Endpoints REST

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/chat` | Pergunta ao agente |
| POST | `/query` | Alias de `/chat` |
| GET | `/audit/{audit_id}` | Registro completo de auditoria da execução |
| DELETE | `/memory/{session_id}` | Limpa histórico da sessão |
| GET | `/health` | Status dos conectores |
| GET | `/tools` | Tools disponíveis por fonte |

---

## Variáveis de ambiente

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.0

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

MCP_SERVER_URL=http://localhost:8000/mcp
MCP_TRANSPORT=streamable_http

LOG_LEVEL=INFO
AGENT_MAX_TOOL_ITERATIONS=6

# Observabilidade (opcionais)
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=cellus-industrial
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=cellus-agent
```
