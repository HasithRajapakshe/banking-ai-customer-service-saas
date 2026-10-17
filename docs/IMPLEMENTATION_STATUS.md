# Implementation Status

Last updated: 2026-10-17, branch `fix/e2e-integration`.

**Summary:** one honest, green, end-to-end demo works: a clean
`docker compose up -d --build` brings up every service, a customer can log in,
read their accounts, get a knowledge-base answer, and block a card through the
full confirmation flow. Several production concerns (service authentication,
permission enforcement, persistent audit, real LLM routing, observability,
deployment) are **not** done; see [Remaining work](#remaining-work).

The previous version of this file reported every phase as complete. An
independent review found that wrong: about half the test suites failed or
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
| 4 | Docs, `.dockerignore` per service (local `.env`/`.venv` were being baked into images), held requests logged as "Tool awaiting confirmation", INFO logging enabled in tool-gateway (INFO audit events were silently dropped) | this commit | tool-gateway 67; all suites below |

### Current test suites

| Suite | Tests | Needs |
|---|---|---|
| synthetic-bank | 16 | — |
| banking-adapter | 88 | — |
| tool-gateway | 67 | Redis |
| ai-agent | 14 | — |
| api-gateway | 17 | — (fakeredis) |
| rag | 20 | — |
| database/tests (schema alignment) | 4 | PostgreSQL + pgvector |
| scripts/e2e_test.py | 4 | Running compose stack |
| frontend | lint, typecheck, build | Node 20 |

All of the above pass locally (Python suites in `python:3.12-slim`). The CI
workflow runs the same jobs; it has been validated as YAML but **has not yet
run on GitHub** — the first push of this branch will be its first run.

## What works

- **Stack:** `docker compose up -d --build` from a clean checkout, with no
  `.env` (every variable has a development default). `migrate` applies
  `0001_initial_schema` and seeds; `rag-backfill` embeds the seeded knowledge
  chunks; dependent services wait for both.
- **Banking path:** agent → tool-gateway → banking-adapter → synthetic-bank
  for every tool call. synthetic-bank requires an internal API key and checks
  tenant and customer ownership on every query.
- **Confirmation flow:** HIGH/CRITICAL tools return a challenge instead of
  executing. Challenges require a user, are bound to user/tenant/customer,
  expire after 5 minutes and are consumed atomically (`GETDEL`). The
  api-gateway stores the pending action per conversation and replays it on
  confirm; the public chat request only accepts `message`, `conversation_id`,
  `channel` and `challenge_code`. Replays, other users and wrong codes are
  rejected (covered by unit and e2e tests).
- **RAG:** tenant-scoped pgvector search with a similarity threshold;
  deterministic mock embeddings by default; OpenAI embeddings when a real key
  is configured (missing/placeholder key falls back to mock with a warning).
- **Auth:** email + password login, JWT access tokens, rotating refresh
  tokens in Redis, per-user rate limiting (429 with `Retry-After`).
- **RBAC data:** global roles `CUSTOMER`, `SUPPORT_AGENT`, `ADMIN`; admin
  routes check `knowledge.manage`, `audit.read`, `users.manage`.

## Remaining work

Requested items, in no particular order:

1. **Service-to-service auth for tool-gateway and RAG.** They (and ai-agent,
   banking-adapter, synthetic-bank) accept any caller and are published on
   host ports 8000–8005. Anyone who can reach tool-gateway can execute a tool
   for any `customer_id`. Needs signed service tokens (or mTLS) and removal
   of the host port mappings for internal services.
2. **Enforce `tool.permission` against roles.** Tools declare a permission,
   but `authorization_service.verify_permission` only checks one is declared.
   The tool codes (`account.balance.read`, `card.transactions.read`, …) also
   do not match the codes seeded in the `permission` table (`account.read`,
   `transaction.read`, …), so the two lists need reconciling first.
3. **Write audit records to `audit_log` / `tool_execution`.** Today
   `tool-gateway` only logs audit events to stdout. The tables and the
   api-gateway ORM models exist and match the schema.
4. **`GET /accounts` bypasses the banking adapter.** `api-gateway/app/api/routes/accounts.py`
   calls synthetic-bank directly with its internal key, breaking the provider
   abstraction. It should go through banking-adapter (or tool-gateway).
5. **Real LLM routing via a model gateway.** The intent router is keyword
   rules. The LLM branch in `intent_router.py` is not wired: compose passes no
   `MODEL_PROVIDER`/`MODEL_NAME`, and `.env.example`'s `LLM_PROVIDER` /
   `LLM_MODEL` are not read. The RAG answer path calls `llm.invoke`
   synchronously and swallows errors. Needs a provider-agnostic model gateway
   (langchain-openai / anthropic, `ainvoke`), timeouts and error handling.
6. **`validate_response` node** in the LangGraph workflow (the spec's
   "Response Validation" step) before replying.
7. **Evaluation harness** for routing accuracy, refusal behaviour and RAG
   answer quality, independent of LLM wording.
8. **Observability:** OpenTelemetry traces across services (correlation IDs
   are already propagated), Prometheus metrics, Grafana dashboards.
9. **Deployment:** Terraform / Kubernetes (EKS) per the spec; production
   secrets management; non-default `JWT_SECRET` and internal keys.

Also found during this work:

- **No card list.** No API or UI lists a customer's cards, so card IDs must be
  looked up in the database to try "block my card" (the e2e test does the
  same as setup).
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
