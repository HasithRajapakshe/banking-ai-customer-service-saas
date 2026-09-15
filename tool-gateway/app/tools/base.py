from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext


class BaseTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel
    permission: str

    input_model: type[BaseModel]

    @property
    def requires_confirmation(self) -> bool:
        return self.risk_level in {
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }

    def validate_arguments(
        self,
        arguments: dict[str, Any],
    ) -> BaseModel:
        return self.input_model.model_validate(arguments)

    @abstractmethod
    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: BaseModel,
    ) -> Any:
        raise NotImplementedError