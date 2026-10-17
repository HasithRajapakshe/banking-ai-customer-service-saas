import os
import uuid

import pytest

from app import llm
from app.graph.workflow import agent_graph
from app.llm.gateway import ModelGateway
from app.testing.doubles import FakeRag, FakeToolGateway


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    os.environ["APP_ENV"] = "test"
    os.environ["TOOL_GATEWAY_BASE_URL"] = "http://localhost:8003"
    os.environ["TENANT_ID"] = "f498100f-80c4-467e-84ec-ebfe5470b442"


@pytest.fixture(autouse=True)
def no_model_by_default():
    """Every test starts in keyword-only mode; tests opt in to a fake LLM."""
    llm.set_model_gateway(None)
    yield
    llm.set_model_gateway(None)


@pytest.fixture
def bank(monkeypatch) -> FakeToolGateway:
    """Tool Gateway double wired into every module that calls it."""
    double = FakeToolGateway()
    for module in ("app.graph.workflow", "app.services.reference_resolver", "app.services.action_summary"):
        monkeypatch.setattr(f"{module}.tool_gateway_client", double)
    return double


@pytest.fixture
def rag(monkeypatch) -> FakeRag:
    double = FakeRag()
    monkeypatch.setattr("app.graph.workflow.rag_client", double)
    return double


def use_llm(provider) -> ModelGateway:
    gateway = ModelGateway(provider, max_retries=0, backoff_seconds=0)
    llm.set_model_gateway(gateway)
    return gateway


async def run_agent(message: str, **extra) -> dict:
    conversation_id = str(uuid.uuid4())
    state = {
        "message": message,
        "tenant_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "channel": "web",
        "correlation_id": "test",
        "tool_calls": 0,
        **extra,
    }
    return await agent_graph.ainvoke(state, {"configurable": {"thread_id": conversation_id}})
