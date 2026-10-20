"""Snapshot the Tool Gateway catalogue (GET /api/v1/tools) to JSON.

The AI agent's offline doubles (tests and evaluation) use this snapshot so the
LLM sees exactly the real tool names, descriptions and argument schemas.
Re-run after changing tools:

    docker run --rm -v "${PWD}:/repo" -w /repo/tool-gateway python:3.12-slim sh -c \
      "pip install -q -r requirements.txt && python ../evaluation/export_tool_catalogue.py"
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))  # run from tool-gateway/

from httpx import ASGITransport, AsyncClient  # noqa: E402

from main import app  # noqa: E402
from app.tools.registry import register_default_tools  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "ai-agent" / "app" / "testing" / "tool_catalogue.json"


async def main() -> None:
    register_default_tools()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tool-gateway") as client:
        response = await client.get("/api/v1/tools")
        response.raise_for_status()
    catalogue = sorted(response.json(), key=lambda tool: tool["name"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalogue, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(catalogue)} tools to {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
