# banking-ai-customer-service-saas

A multi-tenant AI customer-service platform for banks and fintechs, built as a
demonstration environment on 100% synthetic data. Customers chat with an AI
assistant that answers policy questions from a knowledge base (RAG) and
performs banking tasks — balances, transactions, blocking a card — through
controlled tools. The core rule (see
[docs/03_Master_Engineering_Specification_v1.0.md](docs/03_Master_Engineering_Specification_v1.0.md)):
**the AI never touches banking data directly.** Every banking action goes
agent → tool-gateway → banking-adapter → synthetic-bank, and high-risk actions
need explicit user confirmation.

Status and remaining work: [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md).

## Architecture

```mermaid
flowchart LR
    user([Browser]) --> fe[frontend<br/>Next.js :3000]
    fe --> gw[api-gateway<br/>FastAPI :8001<br/>JWT, RBAC, rate limit]

    gw -- "chat (+ internal token)" --> agent[ai-agent<br/>LangGraph :8004<br/>LLM or keyword routing,<br/>response validation]
    gw -- "admin docs (+ token)" --> rag
    gw -- "/accounts, /cards (+ token)" --> tg

    agent -. "model gateway<br/>(optional)" .-> llm[(LLM<br/>Ollama / Gemini /<br/>OpenAI / Anthropic)]
    agent -- "policy questions (+ token)" --> rag[rag<br/>pgvector :8005<br/>verifies token]
    agent -- "every banking action (+ token)" --> tg[tool-gateway :8003<br/>verifies token, RBAC,<br/>confirmation, audit]
    tg --> adapter[banking-adapter :8002<br/>provider abstraction]
    adapter --> bank[synthetic-bank :8000<br/>ownership checks]

    gw --> redis[(Redis 7<br/>rate limits, sessions,<br/>pending actions)]
    tg --> redis
    tg -- "audit_log, tool_execution" --> pg
    gw --> pg[(PostgreSQL 16 + pgvector)]
    rag --> pg
    bank --> pg

    migrate[[migrate<br/>alembic upgrade + seeds]] --> pg
    backfill[[rag-backfill<br/>embed seeded chunks]] --> pg
```

`migrate` and `rag-backfill` are one-shot jobs: the services that need the
database start only after they exit successfully. Only the frontend (3000)
and api-gateway (8001) are published to the host (plus Postgres 5432 for
local tooling); every other service is reachable only on the Compose network.

**Service-to-service identity.** For every request the api-gateway signs a
short-lived internal JWT (60 s, `INTERNAL_JWT_SECRET`, separate from the user
`JWT_SECRET`) carrying tenant, customer, user, roles and conversation. The
agent forwards it unchanged; tool-gateway and rag verify it and take identity
**only** from it: a missing, expired or tampered token is a 401, and a request
whose body names a different tenant/customer/user is a 403. banking-adapter and
synthetic-bank keep their internal API keys.

## Features

- **RAG answers** — policy questions are answered from tenant-scoped knowledge
  documents (pgvector cosine search with a similarity threshold). Admins can
  upload PDF/text documents.
- **Banking tools with risk levels** — 26 tools in the tool-gateway: 20 LOW
  (read), 1 MEDIUM (`complaint.create`), 4 HIGH (`card.block`,
  `payment.cancel`, `beneficiary.create`, `beneficiary.deactivate`) and 1
  CRITICAL (`payment.create`). Arguments are strictly validated.
- **LLM routing with tool calling** — with a model configured, the agent
  builds tool definitions from the tool-gateway catalogue and lets the model
  pick the tool and arguments. The model can never confirm anything, IDs it
  did not get from the customer are discarded, and any failure, timeout or
  unknown tool falls back to the keyword router. "Block my card" or "my
  savings account" are resolved from the customer's own cards/accounts (a
  clarifying question if ambiguous). Sinhala-English (Singlish) phrasing works
  with the LLM.
- **Grounded answers and response validation** — knowledge answers come only
  from retrieved documents and cite the title ("I don't have that
  information" otherwise). Every reply is checked before it is sent: no
  claimed success without an executed action, no amounts that are not in the
  data, no system-prompt or internal-ID leakage.
- **Guardrails** — prompt-injection screening before any model sees the
  message; card, NIC and phone numbers are masked in the agent's logs.
- **Confirmation flow** — HIGH/CRITICAL tools are held until the user
  confirms. The tool-gateway issues a one-time challenge (Redis, 5 min, bound
  to user, tenant and customer, consumed atomically); the api-gateway stores
  the pending action server-side per conversation, so the browser can only
  confirm it, never choose or alter it. The UI shows a confirm card such as
  "Block card ending 6768".
- **RBAC, enforced at the tool-gateway** — global roles `CUSTOMER`,
  `SUPPORT_AGENT`, `ADMIN` (Alembic revision 0002). Every tool declares a
  permission, and a tool runs only if one of the token's roles grants it;
  otherwise 403 and the adapter is never called. Customers can use all
  self-service tools; support agents can read but not move money or block
  cards; admins have no banking tools. Admin routes require
  `knowledge.manage`, `audit.read` or `users.manage`.
- **Persistent audit** — every tool execution (held, executed, failed, denied,
  including identity mismatches) is written to `tool_execution` and
  `audit_log`; an audit-store outage is logged loudly and never breaks the
  request. Admins see it on the admin page (`/admin/audit`, paginated,
  tenant-scoped).
- **Tenant isolation and ownership** — every query is scoped by tenant, and
  the synthetic bank only returns a customer's own accounts, cards and loans.

## Quick start

Requires Docker Desktop (or Docker Engine with Compose v2).

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env      # optional: compose has working defaults
docker compose up -d --build
docker compose ps                 # wait until services are healthy
Start-Process http://localhost:3000
```

**macOS / Linux (bash)**

```bash
cp .env.example .env              # optional: compose has working defaults
docker compose up -d --build
docker compose ps                 # wait until services are healthy
open http://localhost:3000        # or xdg-open
```

`.env.example` uses `EMBEDDING_PROVIDER=mock` (deterministic, offline
embeddings). Only set `EMBEDDING_PROVIDER=openai` with a real
`OPENAI_API_KEY`; with an invalid key `rag-backfill` fails and RAG does not
start.

### Optional: a real LLM

Without a reachable model the agent runs on the keyword router (it logs the
connection error and falls back). The default configuration expects
[Ollama](https://ollama.com) on the host with `qwen2.5:7b`:

```powershell
winget install Ollama.Ollama
ollama pull qwen2.5:7b      # about 4.7 GB
```

Containers reach it at `host.docker.internal:11434`. To use another provider,
set `MODEL_PROVIDER` / `MODEL_NAME` and its API key in `.env`
(`gemini` + `GOOGLE_API_KEY`, `openai` + `OPENAI_API_KEY`, `anthropic` +
`ANTHROPIC_API_KEY`), or `MODEL_PROVIDER=deterministic` to switch the LLM off.

On a laptop RTX 3050 (4 GB), Ollama 0.40.5's default `cuda_v13` backend
crashed (`CUDA error: shared object initialization failed`); forcing the
bundled v12 backend fixed it:
`[Environment]::SetEnvironmentVariable("OLLAMA_LLM_LIBRARY", "cuda_v12", "User")`,
then restart Ollama.

On first start, `migrate` creates the schema with Alembic and loads the
synthetic dataset (100 customers, 150 accounts, 150 cards, 7 knowledge
documents) plus the demo users. Re-running is safe: every seed step is
idempotent.

### Demo logins

| Email | Password | Role |
|---|---|---|
| `alice@example.com` | `password123` | CUSTOMER |
| `bob@example.com` | `password123` | CUSTOMER |
| `admin@example.com` | `password123` | ADMIN (opens the admin knowledge-base page) |

### Example chat prompts (as alice)

1. `Show my accounts` — lists Alice's accounts through `account.list`.
2. `What is the policy for a lost or stolen card?` — answered from the
   "Lost or Stolen Card Procedure" knowledge document.
3. `I lost my card, please block my card` — the agent finds Alice's card
   (`card.list`), and replies with a confirm card ("Block card ending 6768").
   **Confirm** executes it, **Cancel** discards it.

With a model configured, paraphrases and Singlish also work, e.g.
`please freeze my debit card` or `mage card eka block karanna`.

To unblock Alice's card again after the demo:

```powershell
docker exec banking-postgres psql -U banking_app -d banking_ai -c "UPDATE card SET status = 'active', blocked_at = NULL WHERE customer_id = (SELECT customer_id FROM app_user WHERE email = 'alice@example.com')"
```

## Running the tests

All Python suites run on Python 3.12. The commands below run them in Docker,
so no local Python is needed. tool-gateway needs a real Redis; the schema
tests need a disposable PostgreSQL + pgvector.

**One-time setup (PowerShell or bash):**

```bash
docker network create ci-net
docker run -d --name ci-redis --network ci-net redis:7
docker run -d --name ci-pg --network ci-net -e POSTGRES_DB=schema_test -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test pgvector/pgvector:pg16
```

**A service suite** (`synthetic-bank`, `banking-adapter`, `tool-gateway`,
`ai-agent`, `api-gateway` or `rag`):

```powershell
# PowerShell
$svc = "tool-gateway"
docker run --rm --network ci-net -e REDIS_URL=redis://ci-redis:6379/0 -v "${PWD}\${svc}:/src:ro" python:3.12-slim sh -c "cp -r /src /app && cd /app && pip install -q -r requirements.txt && python -m pytest -q"
```

```bash
# bash
svc=tool-gateway
docker run --rm --network ci-net -e REDIS_URL=redis://ci-redis:6379/0 -v "$PWD/$svc:/src:ro" python:3.12-slim sh -c "cp -r /src /app && cd /app && pip install -q -r requirements.txt && python -m pytest -q"
```

**Schema alignment** (Alembic migrations vs every service's ORM; downgrades
and upgrades the database it is given):

```bash
docker run --rm --network ci-net -e DATABASE_URL=postgresql+asyncpg://test:test@ci-pg:5432/schema_test -v "${PWD}:/repo:ro" -w /repo python:3.12-slim sh -c "pip install -q -r database/requirements-test.txt && python -m pytest -q database/tests"
```

**End-to-end** (against the running stack from the quick start; blocks
Alice's card, then restores it). It runs inside the Compose network because
its attack tests call tool-gateway directly:

```bash
docker run --rm --network container:api-gateway -e E2E_API_URL=http://api-gateway:8001/api/v1 -e E2E_DATABASE_URL=postgresql://banking_app:change_me_in_production@postgres:5432/banking_ai -v "${PWD}:/repo:ro" -w /repo python:3.12-slim sh -c "pip install -q -r scripts/requirements-e2e.txt && python -m pytest -v scripts/e2e_test.py"
```

Use your own `POSTGRES_PASSWORD` in `E2E_DATABASE_URL` if `.env` changes it.

**Frontend:**

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

**Agent evaluation** (82 labelled prompts in
[evaluation/dataset.jsonl](evaluation/dataset.jsonl): paraphrases, Singlish,
ambiguous requests, prompt injection, high-risk actions). Runs the real agent
in-process against offline doubles of tool-gateway and RAG, and writes
`evaluation/results/<date>-<provider>.md`. It exits non-zero if confirmation
safety is below 100%.

```bash
# keyword router, and a scripted fake LLM (what CI runs; no model or key needed)
docker run --rm -v "${PWD}:/repo" -w /repo python:3.12-slim sh -c "pip install -q -r ai-agent/requirements.txt && python evaluation/run_eval.py --provider deterministic && python evaluation/run_eval.py --provider fake"
# a real model, e.g. Ollama on the host
docker run --rm -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -v "${PWD}:/repo" -w /repo python:3.12-slim sh -c "pip install -q -r ai-agent/requirements.txt && python evaluation/run_eval.py --provider ollama --model qwen2.5:7b"
# side-by-side table from two runs
python evaluation/run_eval.py --compare evaluation/results/<a>.json evaluation/results/<b>.json
```

Latest results: [evaluation/results/](evaluation/results/).

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs all of the
above except the real-model evaluation: one job per backend service (with
Redis), the schema/RBAC/audit-SQL tests (with pgvector), the e2e test on a
fresh `docker compose up` (keyword router), a check that the agent's tool
catalogue snapshot matches the real tool-gateway, the evaluation with the
keyword router and the fake LLM, the frontend checks, and a compose build. Any
failing test fails the build. CI never needs a real LLM or API key.

## Project structure

| Path | Contents |
|---|---|
| `frontend/` | Next.js customer dashboard (chat, accounts, my cards, confirm card) and admin page (knowledge base, audit log) |
| `api-gateway/` | Public API: login/JWT, RBAC, rate limiting, chat persistence, pending-action store; signs internal tokens |
| `ai-agent/` | LangGraph agent: guardrails, LLM/keyword routing, reference resolution, RAG answers, response validation; model gateway in `app/llm/` |
| `tool-gateway/` | The only way to banking data: 26 tools, token verification, permission checks, confirmation challenges, persistent audit |
| `banking-adapter/` | Provider abstraction between tools and a bank API (synthetic provider today) |
| `synthetic-bank/` | Simulated core banking API with tenant and customer ownership checks |
| `rag/` | Document ingestion, embeddings, pgvector search, embedding backfill job |
| `database/` | Alembic migrations (schema source of truth), seed SQL, migrate image, schema tests |
| `scripts/` | Seeds (`seed.py`), synthetic data generator, e2e test |
| `evaluation/` | Agent evaluation dataset, runner, tool-catalogue export, results |
| `docs/` | Engineering specification, SRS, proposal, implementation status |
| `.github/workflows/` | CI pipeline |
| `backups/` | Local database dumps (git-ignored) |

## Known limitations

This is a demonstration environment, not production. The main gaps (full
list in [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)):

- **The internal token uses a shared secret (HS256).** Any service holding
  `INTERNAL_JWT_SECRET` could mint tokens; asymmetric keys (api-gateway signs,
  others only verify) would remove that. The development default secret must
  be replaced outside development. Tokens are not single-use (`jti` is not
  tracked), so one can be replayed within its 60 s. The ai-agent forwards the
  token but does not verify it itself.
- **Without a model the agent is keyword-based**, and misses most paraphrases
  and Singlish (see the evaluation results). A small local model
  (`qwen2.5:7b`) is slow on modest hardware: several seconds per message.
- **Embeddings are mock by default** (feature hashing: matches on shared
  words, not meaning). The evaluation uses a term-overlap retrieval double, so
  its RAG numbers measure grounding, not pgvector retrieval quality.
- Only the three demo users can log in; the 104 seeded users have no usable
  passwords. The admin "Users" page is still a placeholder.
- Agent conversation state is in process memory (`MemorySaver`), so it is lost
  on restart and not shared between replicas.

## Notes

- If you have a pre-Alembic database, restore from `backups/` or start with a
  fresh volume. The Postgres volume is now `postgres_data_v2`; the old
  `postgres_data` volume is not used.
