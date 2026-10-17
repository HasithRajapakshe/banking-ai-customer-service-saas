"""Answers to knowledge questions, grounded in retrieved chunks.

- No chunk passed the similarity threshold: "I don't have that information".
- A real model is configured: it answers ONLY from the chunks and cites the
  document title as [Title]. An answer that cites no retrieved title is
  treated as ungrounded and replaced by the deterministic answer.
- No model, the fake provider, or any LLM failure: the deterministic answer
  (the best chunk, quoted, with its title).
"""

import logging
from typing import Any

from app.llm.base import ChatMessage, LLMError
from app.llm.gateway import ModelGateway

logger = logging.getLogger("ai_agent.rag_answer")

NO_INFORMATION = "I don't have that information in our knowledge base."

ANSWER_PROMPT = """You answer bank customers' questions using ONLY the knowledge-base excerpts below.
- Use only facts stated in the excerpts. Do not add amounts, fees, times or rules that are not there.
- Cite the document you used as [Title], with the exact title shown.
- If the excerpts do not answer the question, reply exactly: I don't have that information.
- Keep it to a few sentences.

Excerpts:
{excerpts}"""


def deterministic_answer(docs: list[dict[str, Any]]) -> str:
    best = docs[0]
    return f"Based on our policy '{best['title']}':\n\n{best['content']}"


async def answer_question(
    question: str,
    docs: list[dict[str, Any]],
    gateway: ModelGateway | None,
) -> tuple[str, list[str]]:
    """Returns (answer, titles cited)."""
    if not docs:
        return NO_INFORMATION, []

    if gateway is None or gateway.provider_name == "fake":
        return deterministic_answer(docs), [docs[0]["title"]]

    excerpts = "\n\n".join(f"[{d['title']}]\n{d['content']}" for d in docs)
    try:
        response = await gateway.chat(
            [
                ChatMessage(role="system", content=ANSWER_PROMPT.format(excerpts=excerpts)),
                ChatMessage(role="user", content=question),
            ]
        )
    except LLMError as exc:
        logger.warning("LLM RAG answer failed, using deterministic answer: %s", exc)
        return deterministic_answer(docs), [docs[0]["title"]]

    text = (response.content or "").strip()
    if "don't have that information" in text.lower() or "do not have that information" in text.lower():
        return NO_INFORMATION, []

    cited = [d["title"] for d in docs if d["title"].lower() in text.lower()]
    if not text or not cited:
        logger.warning("LLM RAG answer cited no retrieved document; using deterministic answer")
        return deterministic_answer(docs), [docs[0]["title"]]
    return text, sorted(set(cited))
