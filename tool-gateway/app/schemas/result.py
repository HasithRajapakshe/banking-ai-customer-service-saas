from typing import Any

from pydantic import BaseModel

from app.core.risk import RiskLevel


class ToolError(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    risk_level: RiskLevel

    data: Any | None = None
    error: ToolError | None = None

    correlation_id: str

    requires_confirmation: bool = False
    executed: bool = True