"""LangGraph workflow (spec section 7).

START -> security_check -> classify_intent -> resolve_references -> execute_tool ─┐
                                           -> retrieve_knowledge ──────────────────┼─> validate_response -> END
                                           -> respond_without_tool ────────────────┘

Routing uses the LLM when a model provider is configured and falls back to
the keyword router otherwise. Either way every banking action goes through
the Tool Gateway, which validates arguments and holds HIGH/CRITICAL tools for
user confirmation; nothing in this graph can confirm an action by itself.
"""

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app import llm
from app.clients.rag_client import rag_client
from app.clients.tool_gateway_client import tool_gateway_client
from app.core.config import settings
from app.graph.state import AgentState
from app.services.action_summary import action_summary_service
from app.services.intent_router import intent_router
from app.services.llm_router import llm_router
from app.services.rag_answer import answer_question
from app.services.reference_resolver import reference_resolver
from app.services.response_service import response_service
from app.services.response_validator import safe_fallback, validate_response
from app.services.security_service import security_service

logger = logging.getLogger("ai_agent.workflow")


def _context(state: AgentState) -> dict:
    return {
        "tenant_id": state["tenant_id"],
        "customer_id": state["customer_id"],
        "user_id": state.get("user_id"),
        "conversation_id": state["conversation_id"],
        "channel": state["channel"],
        "correlation_id": state["correlation_id"],
    }


async def security_check(state: AgentState):
    allowed, reason = security_service.check(state["message"])
    if not allowed:
        return {
            "security_allowed": False,
            "intent": "security_blocked",
            "route": "blocked",
            "status": "blocked",
            "response_message": reason or "Request blocked.",
            "requires_confirmation": False,
        }
    return {"security_allowed": True}


async def classify_intent(state: AgentState):
    override = state.get("tool_name_override")
    gateway = llm.get_model_gateway()
    decision, router = None, "keyword"

    # A replayed confirmation (server-stored action) never goes to the LLM.
    if gateway is not None and not override:
        try:
            catalogue = await tool_gateway_client.list_tools(state["correlation_id"])
        except Exception as exc:
            logger.warning("Tool catalogue unavailable, using keyword router: %s", exc)
            catalogue = None
        if catalogue is not None:
            decision = await llm_router.route(state["message"], gateway=gateway, catalogue=catalogue)
            router = "llm" if decision is not None else "keyword_fallback"

    if decision is None:
        decision = intent_router.classify(
            state["message"],
            tool_name_override=override,
            tool_arguments_override=state.get("tool_arguments_override"),
        )

    return {
        "router": router,
        "intent": decision.intent,
        "route": decision.route,
        "tool_name": decision.tool_name,
        "tool_arguments": decision.arguments,
        "clarification": decision.clarification,
    }


async def resolve_references(state: AgentState):
    if state.get("tool_name_override"):
        return {}  # replayed confirmation: arguments are the stored ones

    schema = None
    try:
        catalogue = await tool_gateway_client.list_tools(state["correlation_id"])
        schema = next((t.get("input_schema") for t in catalogue if t["name"] == state["tool_name"]), None)
    except Exception as exc:
        logger.warning("Tool catalogue unavailable during resolution: %s", exc)

    resolution = await reference_resolver.resolve(
        tool_name=state["tool_name"],
        arguments=state.get("tool_arguments") or {},
        message=state["message"],
        input_schema=schema,
        context=_context(state),
    )
    update = {
        "tool_calls": state.get("tool_calls", 0) + resolution.lookups,
        "tool_arguments": resolution.arguments,
    }
    if resolution.tool_name:
        update["tool_name"] = resolution.tool_name
    if resolution.clarification:
        update.update(route="clarify", clarification=resolution.clarification)
    elif resolution.final_message:
        update.update(route="answered", response_message=resolution.final_message, status="completed")
    return update


async def execute_tool(state: AgentState):
    calls = state.get("tool_calls", 0)
    if calls >= settings.max_tool_calls:
        return {
            "status": "failed",
            "response_message": "Agent tool-call limit reached. No further banking action was attempted.",
            "requires_confirmation": False,
        }

    context = _context(state)
    arguments = state.get("tool_arguments", {})
    result = await tool_gateway_client.execute(
        tool_name=state["tool_name"],
        arguments=arguments,
        # Only a replayed, server-stored confirmation carries these.
        confirmed=state.get("confirmed", False),
        challenge_code=state.get("challenge_code"),
        **context,
    )
    message, status, requires_confirmation = response_service.from_tool_result(
        state["tool_name"], result
    )

    update = {
        "tool_calls": calls + 1,
        "tool_result": result,
        "status": status,
        "response_message": message,
        "requires_confirmation": requires_confirmation,
        "confirmation_challenge": None,
        "action_summary": None,
    }
    if requires_confirmation:
        summary = await action_summary_service.describe(
            tool_name=state["tool_name"], arguments=arguments, **context
        )
        update.update(
            confirmation_challenge=result.get("confirmation_challenge"),
            action_summary=summary,
            response_message=f"Please confirm: {summary}. {message}",
        )
    return update


async def retrieve_knowledge(state: AgentState):
    # The LLM router may restate the question (e.g. Singlish -> English).
    query = (state.get("tool_arguments") or {}).get("question") or state["message"]
    result = await rag_client.search(
        query=query,
        tenant_id=state["tenant_id"],
        correlation_id=state["correlation_id"],
    )
    docs = result.get("results", [])
    answer, cited = await answer_question(state["message"], docs, llm.get_model_gateway())
    return {
        "status": "completed",
        "response_message": answer,
        "requires_confirmation": False,
        "knowledge": [d["content"] for d in docs],
        "cited_documents": cited,
    }


async def respond_without_tool(state: AgentState):
    route = state.get("route")
    if route == "answered":
        return {}
    if route == "clarify":
        return {
            "status": "needs_clarification",
            "response_message": state.get("clarification") or "Please provide more details.",
            "requires_confirmation": False,
        }
    return {
        "status": "completed",
        "response_message": response_service.general(
            state.get("intent", "general"), state.get("clarification")
        ),
        "requires_confirmation": False,
    }


async def validate(state: AgentState):
    violations = validate_response(
        state.get("response_message", ""),
        user_message=state["message"],
        tool_result=state.get("tool_result"),
        knowledge=state.get("knowledge"),
    )
    if not violations:
        return {"validation_errors": []}
    logger.warning(
        "Response failed validation (%s); replaced with safe fallback",
        ", ".join(v.rule for v in violations),
    )
    return {
        "validation_errors": [v.rule for v in violations],
        "response_message": safe_fallback(state.get("tool_result")),
    }


def after_security(state: AgentState) -> str:
    return "blocked" if not state.get("security_allowed", False) else "continue"


def after_intent(state: AgentState) -> str:
    if state.get("intent") == "knowledge_question":
        return "knowledge"
    return "tool" if state.get("route") == "tool" else "respond"


def after_resolution(state: AgentState) -> str:
    return "execute" if state.get("route") == "tool" else "respond"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("security_check", security_check)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("resolve_references", resolve_references)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("respond_without_tool", respond_without_tool)
    graph.add_node("retrieve_knowledge", retrieve_knowledge)
    graph.add_node("validate_response", validate)

    graph.add_edge(START, "security_check")
    graph.add_conditional_edges(
        "security_check",
        after_security,
        {"blocked": END, "continue": "classify_intent"},
    )
    graph.add_conditional_edges(
        "classify_intent",
        after_intent,
        {
            "tool": "resolve_references",
            "respond": "respond_without_tool",
            "knowledge": "retrieve_knowledge",
        },
    )
    graph.add_conditional_edges(
        "resolve_references",
        after_resolution,
        {"execute": "execute_tool", "respond": "respond_without_tool"},
    )
    graph.add_edge("execute_tool", "validate_response")
    graph.add_edge("respond_without_tool", "validate_response")
    graph.add_edge("retrieve_knowledge", "validate_response")
    graph.add_edge("validate_response", END)
    return graph.compile(checkpointer=MemorySaver())


agent_graph = build_graph()
