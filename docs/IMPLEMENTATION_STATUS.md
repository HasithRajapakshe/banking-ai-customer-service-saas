# Implementation Status

Last updated: 2026-10-19, branch `fix/e2e-integration`.

**Summary:** one honest, green, end-to-end demo works. A clean
`docker compose up -d --build` brings up every service; a customer can log in,
read their accounts, get a grounded knowledge-base answer, and block a card in
natural language ("I lost my card, please block it", also in Singlish) through
the full confirmation flow. With a local LLM (`qwen2.5:7b` via Ollama) the
agent routes 97.6% of the 82 evaluation prompts correctly, against 69.5% for
the keyword router, and confirmation safety is 100% for both. Internal
services authenticate every call with a short-lived identity token, tool
permissions are enforced against roles, and every tool execution is audited
in the database. Observability and deployment are **not** done; see
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
| 5 | Real AI agent: internal ports unpublished, model gateway (Ollama/Gemini/OpenAI/Anthropic + fake), LLM tool-calling over the tool-gateway catalogue with keyword fallback, `card.list` tool, "my card"/"my account" resolution, grounded RAG answers, `validate_response` node, more injection patterns, PII masking in logs, evaluation harness (82 prompts) | `b0e6aa4` | synthetic-bank 18, banking-adapter 89, tool-gateway 69, ai-agent 116, e2e 5; evaluation reports for keyword, fake and Ollama routers |
| 6 | Production hardening: internal identity token (api-gateway signs, tool-gateway/rag verify, identity only from the token), RBAC reference data in Alembic 0002 + permission enforcement, persistent audit (`tool_execution` + `audit_log`) and `/admin/audit`, `/accounts` + new `/cards` through the tool-gateway, frontend `NEXT_PUBLIC_API_URL` + in-memory token + silent refresh + "My cards", server-side cancel, tool-catalogue CI check | this commit | tool-gateway 102, ai-agent 121, api-gateway 42, rag 32, database 9, e2e 8 (adds direct attacks on tool-gateway); e2e passes with the keyword router and with Ollama |

### Current test suites

| Suite | Tests | Needs |
|---|---|---|
| synthetic-bank | 18 | — |
| banking-adapter | 89 | — |
| tool-gateway | 102 | Redis |
| ai-agent | 121 | — (fake LLM, in-memory doubles) |
| api-gateway | 42 | — (fakeredis) |
| rag | 32 | — |
| database/tests (schema, RBAC data, audit SQL) | 9 | PostgreSQL + pgvector |
| scripts/e2e_test.py | 8 | Running compose stack (passes with the keyword router and with Ollama) |
| tool catalogue snapshot | `git diff --exit-code` | tool-gateway dependencies |
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
- **Service-to-service identity:** the api-gateway signs a 60 s HS256 token
  (own secret, `iss`/`aud`) with tenant, customer, user, roles and
  conversation; the agent forwards it; tool-gateway and rag verify it and take
  identity only from it. Missing/expired/tampered/wrong-secret/wrong-audience
  tokens are 401; body identity that disagrees with the token is 403 (and is
  audited). Covered by unit tests in both services and by e2e attacks on the
  tool-gateway from inside the Compose network.
- **Permissions:** Alembic revision 0002 holds all RBAC reference data
  (additive, idempotent; applied in place to the existing database). Every
  tool permission exists and is granted to CUSTOMER; SUPPORT_AGENT is read-only
  plus complaints; ADMIN has no banking tools. The tool-gateway checks the
  token's roles before confirmation and before the adapter.
- **Audit:** every execution is persisted (`requires_approval`, `succeeded`,
  `failed`, `denied`) with masked arguments; persistence failures are logged
  at ERROR and never fail the request; `/admin/audit` shows it to admins.
- **Dashboard reads** (`/accounts`, `/cards`) go through the tool-gateway with
  a signed token (permissions + audit); the api-gateway holds no banking key.
- **Frontend:** API URL from `NEXT_PUBLIC_API_URL` (build arg), access token
  in memory only, silent refresh through the HttpOnly cookie (one shared
  refresh request, retried once on 401), "My cards" panel, Cancel deletes the
  server-side pending action, admin audit table.
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

1. **Observability:** OpenTelemetry traces across services (correlation IDs
   are already propagated), Prometheus metrics, Grafana dashboards. LLM
   latency, fallback rates and audit-write failures are logged but not
   measured.
2. **Deployment:** Terraform / Kubernetes (EKS) per the spec; production
   secrets management; non-default `JWT_SECRET`, `INTERNAL_JWT_SECRET` and
   internal API keys.

Done in Phase 6 (previously items 1-4 here): service-to-service auth for
tool-gateway and RAG, permission enforcement, persistent audit, and routing
`/accounts` away from the synthetic bank.

Known limitations of what exists:

- **Internal token design.** HS256 with a shared secret: every service that
  verifies could also mint tokens; asymmetric signing (api-gateway holds the
  private key) would remove that. Tokens are not single-use (`jti` is issued
  but not tracked), so a stolen token can be replayed for up to 60 s. The
  ai-agent forwards the token without verifying it itself. Requests rejected
  with 401 are logged but not written to `audit_log` (there is no trusted
  identity to attribute them to).
- **Support agents** have read permissions but no way to act on a customer:
  there is no UI or token flow for "support agent working on customer X".
- **Admin "Users" page** is a placeholder.
- **Small local models are slow.** `qwen2.5:7b` on a laptop RTX 3050 (4 GB)
  runs about 55% on CPU: ~7 s per routing call, ~20 s for the first call.
  Compose lowers `LLM_TIMEOUT_SECONDS` to 25 so a whole turn fits inside the
  60 s internal token (verified: the e2e suite passes with Ollama and no token
  expired).
- **Ollama GPU crash.** Ollama 0.40.x's `cuda_v13` backend crashed on this GPU;
  `OLLAMA_LLM_LIBRARY=cuda_v12` works (see README).
- **Evaluation dataset** is self-authored and small (82 prompts); treat it as a
  regression baseline, not an independent benchmark.
- **Seeded users cannot log in.** The 104 users from the synthetic seed have
  non-bcrypt password hashes; only the three demo users can log in.
- **Agent state** uses an in-process `MemorySaver`: lost on restart, not
  shared across replicas.
- **Pending actions** expire after 5 minutes; Cancel now deletes them
  server-side.
