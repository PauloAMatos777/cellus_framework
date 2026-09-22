"""Nodes isolados do workflow LangGraph com Assurance Layer (JEV)."""
from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

from cellus.core.assurance.jev_engine import JEVEngine
from cellus.core.assurance.models import RiskLevel, ToolCallRecord
from cellus.core.planner import Planner
from cellus.core.state import AgentState
from cellus.utils.logging import get_logger

logger = get_logger("cellus.nodes")


def make_planning_node(planner: Planner):
    def planning_node(state: AgentState) -> dict:
        ai_msg: AIMessage = planner.plan(state)
        tool_calls = getattr(ai_msg, "tool_calls", []) or []
        logger.info("[PLANNING] tools=%s", [tc["name"] for tc in tool_calls] or "none")
        return {"messages": [ai_msg], "iterations": state.get("iterations", 0) + 1}
    return planning_node


def make_execution_node(tools: list[BaseTool], jev: JEVEngine | None = None):
    tools_by_name = {t.name: t for t in tools}

    async def execution_node(state: AgentState) -> dict:
        last: AIMessage = state["messages"][-1]
        outputs: list[ToolMessage] = []
        used: list[str] = []
        times: dict[str, float] = {}
        jev_validations: list[dict[str, Any]] = []
        jev_assessments: list[dict[str, Any]] = []
        evidence_collected: list[str] = []
        sources_consulted: list[str] = []
        tool_results_raw: list[dict[str, Any]] = []

        objective = state.get("question", "")
        context = {
            "messages": state.get("messages", []),
            **{k: v for k, v in state.items() if k not in ("messages",)},
        }

        for tc in last.tool_calls:
            tool = tools_by_name.get(tc["name"])
            if tool is None:
                outputs.append(ToolMessage(
                    content=f"Tool '{tc['name']}' not found.",
                    tool_call_id=tc["id"], name=tc["name"]))
                continue

            # ── JEV Pre-Execution Validation ──────────────────────────────────
            jev_validation = None
            if jev:
                jev_validation = await jev.validate(tc["name"], objective, {**context, **tc["args"]})
                jev_validations.append(jev_validation.model_dump(mode="json"))

                if not jev_validation.approved:
                    reason = jev_validation.tool_result.justification
                    logger.warning("[JEV] Execução bloqueada — tool=%s reason=%s", tc["name"], reason)
                    outputs.append(ToolMessage(
                        content=f"[JEV BLOCKED] {reason}",
                        tool_call_id=tc["id"], name=tc["name"]))
                    continue

                if jev_validation.tool_result.requires_human_approval:
                    logger.warning("[JEV] Tool requer aprovação humana — tool=%s", tc["name"])
                    outputs.append(ToolMessage(
                        content=f"[JEV PENDING APPROVAL] Tool '{tc['name']}' requer aprovação humana.",
                        tool_call_id=tc["id"], name=tc["name"]))
                    continue

            # ── Tool Execution ─────────────────────────────────────────────────
            t0 = time.perf_counter()
            try:
                result = await tool.ainvoke(tc["args"])
            except Exception as exc:
                result = {"error": str(exc)}
                logger.error("Tool %s error: %s", tc["name"], exc)
            elapsed = time.perf_counter() - t0

            prefix = tc["name"].split("_")[0]
            times[prefix] = times.get(prefix, 0.0) + elapsed
            used.append(tc["name"])
            sources_consulted.append(prefix)
            tool_results_raw.append(result if isinstance(result, dict) else {"result": str(result)})

            # ── JEV Post-Execution Assessment ─────────────────────────────────
            if jev:
                assessment = jev.validate_result(
                    objective=objective,
                    tool_name=tc["name"],
                    result=result,
                    evidence_collected=evidence_collected,
                )
                jev_assessments.append(assessment.model_dump(mode="json"))
                evidence_collected.extend(assessment.present_evidence if hasattr(assessment, "present_evidence") else [])

                if assessment.continue_investigation:
                    logger.info("[JEV-POST] Investigação deve continuar — missing=%s", assessment.missing_evidence)

            outputs.append(ToolMessage(
                content=str(result), tool_call_id=tc["id"], name=tc["name"]))

        # ── Confidence Score ───────────────────────────────────────────────────
        confidence_score = 0.0
        if jev and used:
            cs = jev.compute_confidence(evidence_collected, sources_consulted, tool_results_raw)
            confidence_score = cs.score
            logger.info("[CONFIDENCE] score=%.2f reason=%s", cs.score, cs.reason)

        logger.info(
            "[EXECUTION] tools=%s times=%s confidence=%.2f",
            used,
            {k: f"{v*1000:.1f}ms" for k, v in times.items()},
            confidence_score,
        )

        return {
            "messages": outputs,
            "selected_tools": used,
            "tool_times": times,
            "jev_validations": jev_validations,
            "jev_assessments": jev_assessments,
            "evidence_collected": evidence_collected,
            "sources_consulted": sources_consulted,
            "confidence_score": confidence_score,
        }

    return execution_node


def make_synthesis_node(planner: Planner, jev: JEVEngine | None = None):
    def synthesis_node(state: AgentState) -> dict:
        answer: AIMessage = planner.synthesize(state)
        logger.info("[SYNTHESIS] %d chars confidence=%.2f", len(answer.content), state.get("confidence_score", 0.0))

        # Finaliza auditoria assíncrona (fire-and-forget via task)
        if jev:
            import asyncio
            audit_id = state.get("audit_id", "")
            if audit_id:
                asyncio.ensure_future(_finalize_audit(jev, state, answer.content))

        return {"messages": [answer], "final_answer": answer.content}
    return synthesis_node


async def _finalize_audit(jev: JEVEngine, state: AgentState, final_response: str) -> None:
    from cellus.core.assurance.models import AuditRecord, RiskLevel
    from cellus.core.assurance.audit_registry import new_audit_id
    try:
        record = AuditRecord(
            audit_id=state.get("audit_id") or new_audit_id(),
            session_id=state.get("session_id", "default"),
            question=state.get("question", ""),
            tool_calls=[],
            jev_summary={
                "validations": state.get("jev_validations", []),
                "assessments": state.get("jev_assessments", []),
            },
            confidence=jev.compute_confidence(
                state.get("evidence_collected", []),
                state.get("sources_consulted", []),
                [],
            ),
            risk_level=RiskLevel(state.get("risk_level", RiskLevel.INFO)),
            evidence_collected=state.get("evidence_collected", []),
            sources_consulted=list(set(state.get("sources_consulted", []))),
            final_response=final_response,
        )
        await jev.finalize_audit(record)
    except Exception as exc:
        logger.error("[AUDIT] Falha ao finalizar auditoria: %s", exc)


def route_after_planning(state: AgentState, max_iterations: int) -> str:
    last = state["messages"][-1]
    has_calls = bool(getattr(last, "tool_calls", None))
    if has_calls and state.get("iterations", 0) < max_iterations:
        return "execute"
    return "synthesize"


def initial_state(question: str, session_id: str = "default") -> AgentState:
    from cellus.core.assurance.audit_registry import new_audit_id
    return {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "session_id": session_id,
        "selected_tools": [],
        "tool_times": {},
        "final_answer": "",
        "iterations": 0,
        # JEV fields
        "jev_validations": [],
        "jev_assessments": [],
        "evidence_collected": [],
        "sources_consulted": [],
        "audit_id": new_audit_id(),
        "confidence_score": 0.0,
        "risk_level": RiskLevel.INFO.value,
    }
