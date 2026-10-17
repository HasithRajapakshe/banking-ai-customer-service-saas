# Implementation Status

Last updated: 2026-10-18, branch `fix/e2e-integration`.

**Summary:** one honest, green, end-to-end demo works. A clean
`docker compose up -d --build` brings up every service; a customer can log in,
read their accounts, get a grounded knowledge-base answer, and block a card in
natural language ("I lost my card, please block it", also in Singlish) through
the full confirmation flow. With a local LLM (`qwen2.5:7b` via Ollama) the
agent routes 97.6% of the 82 evaluation prompts correctly, against 69.5% for
the keyword router, and confirmation safety is 100% for both. Several
production concerns (service authentication, permission enforcement,
persistent audit, observability, deployment) are **not** done; see
[Remaining work](#remaining-work).

The version of this file before this work reported every phase as complete.
An independent review found that wrong: about half the test suites failed or
could not run, CI hid failures with `|| echo`, the schema was defined twice
with conflicting versions, and HIGH/CRITICAL tools could never complete.

## Phases

Test counts are tests collected and passed by pytest (parametrized cases
counted individually), run on Python 3.12.

| Phase | Scope | Commit | Result |
|---|---|---|---|
| Baseline | State before this work (`46966be`) | — | banking-adapter 88/88, tool-gateway 21/58, ai-agent 8/9, api-gateway 0/4, rag could not run, synthetic-bank had no tests, frontend 6 ESLint errors; CI masked all failures |
| — | Pending agent/frontend changes committed as-is | `b928130` | — |
| 1 | Honest build: CI fails on any failure, Redis service in CI, stale tests fixed, synthetic-bank ownership + internal-key tests, ESLint fixed, Python 3.12 images | `8e2e8dd` | synthetic-bank 16, banking-adapter 88, tool-gateway 58, ai-agent 10, api-gateway 4, rag 5 — all passing; frontend lint/typecheck/build pass |
| 2 | One-command stack: Alembic as the only schema source, one-shot `migrate` + idempotent seeds, ORM models aligned, schema drift test, rate limiter fixes, RBAC data, email login | `46b36cc` | api-gateway 9, rag 17, schema alignment 4 (new); others unchanged and passing; verified with a clean `docker compose up` and no `.env` |
| 2b | Postgres moved to a new volume `postgres_data_v2` (old pre-Alembic DB kept; dump in `backups/`) | `21dd458` | Stack healthy on the fresh volume; logins verified |
| 3 | Confirmation flow end to end, server-side pending actions, public chat request locked down, RAG embedding backfill, e2e test + CI job | `27ce811` | tool-gateway 62, ai-agent 14, api-gateway 17, rag 20, e2e 4 (new); others unchanged and passing |
| 4 | Docs, `.dockerignore` per service, "Tool awaiting confirmation" audit log, INFO logging in tool-gateway | `bafee6f` | tool-gateway 67; all suites passing |
| 5 | Real AI agent: internal ports unpublished, model gateway (Ollama/Gemini/OpenAI/Anthropic + fake), LLM tool-calling over the tool-gateway catalogue with keyword fallback, `card.list` tool, "my card"/"my account" resolution, grounded RAG answers, `validate_response` node, more injection patterns, PII masking in logs, evaluation harness (82 prompts) | this commit | synthetic-bank 18, banking-adapter 89, tool-gateway 69, ai-agent 116, e2e 5; evaluation reports for keyword, fake and Ollama routers |

### Current test suites

| Suite | Tests | Needs |
|---|---|---|
| synthetic-bank | 18 | — |
| banking-adapter | 89 | — |
| tool-gateway | 69 | Redis |
| ai-agent | 116 | — (fake LLM, in-memory doubles) |
| api-gateway | 17 | — (fakeredis) |
| rag | 20 | — |
| database/tests (schema alignment) | 4 | PostgreSQL + pgvector |
| scripts/e2e_test.py | 5 | Running compose stack (passes with the keyword router and with Ollama) |
| evaluation/run_eval.py | 82 prompts | — (keyword / fake); a model for the LLM run |
| frontend | lint, typecheck, build | Node 20 |

All of the above pass locally (Python suites in `python:3.12-slim`). The CI
workflow runs the same jobs, never with a real LLM or API key; it has been
validated as YAML but **has not yet run on GitHub** — the first push of this
branch will be its first run.

### Evaluation (82 labelled prompts)

From [evaluation/results/2026-10-18-comparison.md](../evaluation/results/2026-10-18-comparison.md):

| Metric | Keyword router | Fake LLM (CI) | Ollama `qwen2.5:7b` |
|---|---|---|---|
| Intent accuracy | 69.5% (57/82) | 69.5% (57/82) | **97.6% (80/82)** |
| Tool-argument accuracy | 59.3% (16/27) | 59.3% (16/27) | **100% (27/27)** |
| Confirmation safety | **100% (18/18)** | **100% (18/18)** | **100% (18/18)** |
| No HIGH/CRITICAL executed unconfirmed | **100% (82/82)** | **100% (82/82)** | **100% (82/82)** |
| Injection refusal | 100% (18/18) | 100% (18/18) | 100% (18/18) |
| RAG grounding | 40% (4/10) | 40% (4/10) | 80% (8/10) |
| Average latency per prompt | 0.008 s | 0.006 s | 6.97 s |

How to read it:

- The fake LLM run exists to exercise the safety layer in CI without a model:
  most prompts fall back to the keyword router, and four scripted prompts
  feed adversarial model output (self-confirmation, an invented card ID, an
  outage, an invented tool). All were contained.
- The LLM's misses: "someone stole my card, what should I do?" was routed to
  `card.block` (held for confirmation, so safe, but the label expects a policy
  answer); "how much do I still owe on my loan?" asked for a loan ID; a
  Singlish policy question got "I don't have that information".
- The dataset was written alongside the code, by the same team. Treat the
  numbers as a regression baseline, not an independent benchmark.
- Retrieval in the evaluation is a term-overlap double, so RAG grounding
  measures the agent (answers only from retrieved text, cites the title, says
  "I don't have that information"), not pgvector retrieval quality.

## What works

- **Stack:** `docker compose up -d --build` from a clean checkout, with no
  `.env` (every variable has a development default). `migrate` applies
  `0001_initial_schema` and seeds; `rag-backfill` embeds the seeded knowledge
  chunks; dependent services wait for both. Only the frontend (3000),
  api-gateway (8001) and Postgres (5432) are published to the host.
- **Banking path:** agent → tool-gateway → banking-adapter → synthetic-bank
  for every tool call. synthetic-bank requires an internal API key and checks
  tenant and customer ownership on every query.
- **Confirmation flow:** HIGH/CRITICAL tools return a challenge instead of
  executing. Challenges require a user, are bound to user/tenant/customer,
  expire after 5 minutes and are consumed atomically (`GETDEL`). The
  api-gateway stores the pending action per conversation and replays it on
  confirm; the public chat request only accepts `message`, `conversation_id`,
  `channel` and `challenge_code`.
- **AI agent:**
  - Model gateway (`ai-agent/app/llm/`): one async interface for Ollama,
    Gemini, OpenAI and Anthropic (LangChain `bind_tools` + `ainvoke`), a
    scripted fake for tests, timeouts, retries, logged fallbacks.
  - LLM routing: tool definitions are built from `GET /api/v1/tools` (with
    argument schemas). The model only proposes a tool and arguments;
    arguments are filtered to the schema, IDs not present in the customer's
    message are discarded, `confirmed`/`challenge_code` are never model-set,
    and any failure or unknown tool falls back to the keyword router.
  - Reference resolution: "my card", "my savings account", "card ending 6768"
    are resolved through `card.list` / `account.list`; ambiguity produces a
    clarifying question listing last-4 digits only.
  - RAG answers: grounded in retrieved chunks with a `[Title]` citation, or
    "I don't have that information"; deterministic answer without a model.
  - `validate_response`: blocks claimed success without an executed action,
    amounts not present in tool data/knowledge/the message, and system-prompt
    or internal-ID leakage; replaces the reply with a safe fallback.
  - Guardrails: prompt-injection screening (instruction override, prompt
    extraction, jailbreak role-play, confirmation bypass, acting for another
    customer, fake system tags, Singlish variants); card, NIC and phone
    numbers masked in all agent logs.
- **RAG:** tenant-scoped pgvector search with a similarity threshold;
  deterministic mock embeddings by default; OpenAI embeddings when a real key
  is configured (missing/placeholder key falls back to mock with a warning).
- **Auth:** email + password login, JWT access tokens, rotating refresh
  tokens in Redis, per-user rate limiting (429 with `Retry-After`).
- **RBAC data:** global roles `CUSTOMER`, `SUPPORT_AGENT`, `ADMIN`; admin
  routes check `knowledge.manage`, `audit.read`, `users.manage`.

## Remaining work

1. **Service-to-service auth for tool-gateway and RAG.** Internal services are
   no longer published on host ports, but on the Compose network they still
   accept any caller: anything that reaches tool-gateway can execute a tool
   for any `customer_id`. Needs signed service tokens (or mTLS).
2. **Enforce `tool.permission` against roles.** Tools declare a permission,
   but `authorization_service.verify_permission` only checks one is declared.
   The tool codes (`account.balance.read`, `card.transactions.read`, …) also
   do not match the codes seeded in the `permission` table (`account.read`,
   `transaction.read`, …), so the two lists need reconciling first.
3. **Write audit records to `audit_log` / `tool_execution`.** Today
   `tool-gateway` only logs audit events. The tables and the api-gateway ORM
   models exist and match the schema.
4. **`GET /accounts` bypasses the banking adapter.** `api-gateway/app/api/routes/accounts.py`
   calls synthetic-bank directly with its internal key, breaking the provider
   abstraction. It should go through banking-adapter (or tool-gateway).
5. **Observability:** OpenTelemetry traces across services (correlation IDs
   are already propagated), Prometheus metrics, Grafana dashboards. LLM
   latency and fallback rates are logged but not measured.
6. **Deployment:** Terraform / Kubernetes (EKS) per the spec; production
   secrets management; non-default `JWT_SECRET` and internal keys.

Done in Phase 5 (previously listed here): the model gateway with real LLM
routing, the `validate_response` node, and the evaluation harness.

Also found during this work:

- **Small local models are slow.** `qwen2.5:7b` on a laptop RTX 3050 (4 GB)
  runs about 55% on CPU: ~7 s per routing call, ~20 s for the first call
  while the model loads. A knowledge question with an LLM answer makes two
  calls.
- **Ollama GPU crash.** Ollama 0.40.5's `cuda_v13` backend crashed on this GPU
  (`CUDA error: shared object initialization failed`); `OLLAMA_LLM_LIBRARY=cuda_v12`
  works (see README).
- **Evaluation dataset** is self-authored and small (82 prompts); it should
  grow with real (synthetic) transcripts and be reviewed independently.
- **Cards in the UI.** The agent can list cards (`card.list`), but the
  dashboard still only shows accounts.
- **Seeded users cannot log in.** The 104 users from the synthetic seed have
  non-bcrypt password hashes; only the three demo users can log in.
- **Frontend:** API URL hard-coded to `http://localhost:8001`
  (`NEXT_PUBLIC_API_URL` is set but unused); access token in `localStorage`;
  refresh tokens are issued but the UI never refreshes.
- **Agent state** uses an in-process `MemorySaver`: lost on restart, not
  shared across replicas.
- **Admin pages** for audit and users return empty placeholder lists.
- **Pending-action cancel** is client-side only; the stored action simply
  expires after 5 minutes.
- **Tool catalogue snapshot.** The agent's offline doubles use
  `ai-agent/app/testing/tool_catalogue.json`, exported from the real
  tool-gateway with `evaluation/export_tool_catalogue.py`; it must be
  re-exported when tools change (nothing checks this automatically yet).
