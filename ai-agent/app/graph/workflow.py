from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.clients.tool_gateway_client import tool_gateway_client
from app.clients.rag_client import rag_client
from app.core.config import settings
from app.graph.state import AgentState
from app.services.intent_router import intent_router
from app.services.response_service import response_service
from app.services.security_service import security_service


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
    decision = intent_router.classify(
        state["message"],
        tool_name_override=state.get("tool_name_override"),
        tool_arguments_override=state.get("tool_arguments_override"),
    )
    return {
        "intent": decision.intent,
        "route": decision.route,
        "tool_name": decision.tool_name,
        "tool_arguments": decision.arguments,
        "clarification": decision.clarification,
    }


async def execute_tool(state: AgentState):
    calls = state.get("tool_calls", 0)
    if calls >= settings.max_tool_calls:
        return {
            "status": "failed",
            "response_message": "Agent tool-call limit reached. No further banking action was attempted.",
            "requires_confirmation": False,
        }

    result = await tool_gateway_client.execute(
        tool_name=state["tool_name"],
        tenant_id=state["tenant_id"],
        customer_id=state["customer_id"],
        user_id=state.get("user_id"),
        conversation_id=state["conversation_id"],
        channel=state["channel"],
        arguments=state.get("tool_arguments", {}),
        confirmed=state.get("confirmed", False),
        correlation_id=state["correlation_id"],
    )
    message, status, requires_confirmation = response_service.from_tool_result(
        state["tool_name"], result
    )
    return {
        "tool_calls": calls + 1,
        "tool_result": result,
        "status": status,
        "response_message": message,
        "requires_confirmation": requires_confirmation,
    }


async def retrieve_knowledge(state: AgentState):
    result = await rag_client.search(
        query=state["message"],
        tenant_id=state["tenant_id"],
        correlation_id=state["correlation_id"]
    )
    
    docs = result.get("results", [])
    if not docs:
        return {
            "status": "completed",
            "response_message": "I searched the knowledge base, but I couldn't find any information answering your question.",
            "requires_confirmation": False,
        }
        
    # In a full implementation with LLM_PROVIDER set, we would pass these docs to the LLM to generate the answer.
    # For deterministic fallback, we just return the most relevant document's content.
    
    if settings.model_provider != "deterministic":
        try:
            from app.services.intent_router import intent_router
            if intent_router.llm:
                llm = intent_router.llm.model
                prompt = (
                    "You are a helpful banking assistant. Answer the user's question based strictly on the provided knowledge context. "
                    "If the context does not answer the question, state that you do not have the information.\n\n"
                    f"CONTEXT:\n{chr(10).join(d['content'] for d in docs)}\n\n"
                    f"USER QUESTION: {state['message']}"
                )
                response = llm.invoke(prompt)
                return {
                    "status": "completed",
                    "response_message": response.content,
                    "requires_confirmation": False,
                }
        except Exception as e:
            pass
            
    # Deterministic fallback
    doc_content = docs[0]["content"]
    title = docs[0]["title"]
    
    return {
        "status": "completed",
        "response_message": f"Based on our policy '{title}':\n\n{doc_content}",
        "requires_confirmation": False,
    }


async def respond_without_tool(state: AgentState):
    route = state.get("route")
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


def after_security(state: AgentState) -> str:
    return "blocked" if not state.get("security_allowed", False) else "continue"


def after_intent(state: AgentState) -> str:
    if state.get("intent") == "knowledge_question":
        return "knowledge"
    return "tool" if state.get("route") == "tool" else "respond"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("security_check", security_check)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("respond_without_tool", respond_without_tool)
    graph.add_node("retrieve_knowledge", retrieve_knowledge)

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
            "tool": "execute_tool", 
            "respond": "respond_without_tool",
            "knowledge": "retrieve_knowledge"
        },
    )
    graph.add_edge("execute_tool", END)
    graph.add_edge("respond_without_tool", END)
    graph.add_edge("retrieve_knowledge", END)
    return graph.compile(checkpointer=MemorySaver())


agent_graph = build_graph()
