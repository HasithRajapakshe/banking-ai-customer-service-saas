# Phase 6 — AI Agent Service

This service implements the Phase 6 LangGraph orchestration boundary.

Flow:

`START -> Security Check -> Intent Router -> Tool/Response -> END`

Banking data is never accessed directly. All banking operations are delegated to the existing Tool Gateway.

## Run

```powershell
cd ai-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8004
```

## Test

```powershell
pytest -q
```

## Example

POST `/api/v1/agent/chat`

```json
{
  "message": "Show me my accounts",
  "tenant_id": "<tenant-uuid>",
  "customer_id": "<customer-uuid>"
}
```

High-risk operations such as `card.block` remain gated by the Tool Gateway and return `confirmation_required` until the same request is sent with `confirmed: true`.

RAG is intentionally not implemented here; it is the next service boundary in the master engineering specification.
