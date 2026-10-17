"""Model gateway package.

`model_gateway` is the process-wide gateway (None when MODEL_PROVIDER is
"deterministic"). Tests replace it with `set_model_gateway`.
"""

from app.core.config import settings
from app.llm.gateway import ModelGateway, build_model_gateway

model_gateway: ModelGateway | None = build_model_gateway(settings)


def get_model_gateway() -> ModelGateway | None:
    return model_gateway


def set_model_gateway(gateway: ModelGateway | None) -> None:
    global model_gateway
    model_gateway = gateway
