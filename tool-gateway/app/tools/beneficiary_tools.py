from app.clients.banking_adapter_client import (
    banking_adapter_client,
)
from app.core.risk import RiskLevel
from app.schemas.context import ToolExecutionContext
from app.schemas.tool import (
    BeneficiaryCreateInput,
    BeneficiaryIdInput,
    ListInput,
)
from app.tools.base import BaseTool


class ListBeneficiariesTool(BaseTool):
    name = "beneficiary.list"

    description = (
        "List beneficiaries belonging to the "
        "current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "beneficiary.read"

    input_model = ListInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: ListInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/beneficiaries"
            ),
            correlation_id=context.correlation_id,
            params={
                "limit": arguments.limit,
                "offset": arguments.offset,
            },
        )


class GetBeneficiaryTool(BaseTool):
    name = "beneficiary.get"

    description = (
        "Get details of a specific beneficiary "
        "belonging to the current customer."
    )

    risk_level = RiskLevel.LOW
    permission = "beneficiary.read"

    input_model = BeneficiaryIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: BeneficiaryIdInput,
    ):
        return await banking_adapter_client.request(
            method="GET",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/beneficiaries/"
                f"{arguments.beneficiary_id}"
            ),
            correlation_id=context.correlation_id,
        )


class CreateBeneficiaryTool(BaseTool):
    name = "beneficiary.create"

    description = (
        "Create a new beneficiary for the current "
        "customer."
    )

    risk_level = RiskLevel.HIGH
    permission = "beneficiary.create"

    input_model = BeneficiaryCreateInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: BeneficiaryCreateInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/beneficiaries"
            ),
            correlation_id=context.correlation_id,
            json=arguments.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )


class DeactivateBeneficiaryTool(BaseTool):
    name = "beneficiary.deactivate"

    description = (
        "Deactivate a specific beneficiary belonging "
        "to the current customer."
    )

    risk_level = RiskLevel.HIGH
    permission = "beneficiary.deactivate"

    input_model = BeneficiaryIdInput

    async def execute(
        self,
        context: ToolExecutionContext,
        arguments: BeneficiaryIdInput,
    ):
        return await banking_adapter_client.request(
            method="POST",
            path=(
                f"/api/v1/customers/"
                f"{context.customer_id}/beneficiaries/"
                f"{arguments.beneficiary_id}/deactivate"
            ),
            correlation_id=context.correlation_id,
        )
