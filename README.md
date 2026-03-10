# CGS Runtime Wrapper

FastAPI + Redis implementation of the Cosyn Governance Stack (CGS) v14.1.0 runtime wrapper.
Covers all 8 build phases from the action list. Model-based classifier components are stubs pending training corpus completion — see [Stub Disclosure](#stub-disclosure).

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Installation — local run](#installation--local-run)
3. [Running with Docker](#running-with-docker)
4. [Authentication](#authentication)
5. [Rate limiting](#rate-limiting)
6. [API endpoints](#api-endpoints)
7. [Gate architecture overview](#gate-architecture-overview)
8. [Stub disclosure](#stub-disclosure)
9. [Adapter extension guide](#adapter-extension-guide)
10. [Running tests](#running-tests)
11. [Environment variable reference](#environment-variable-reference)

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Redis | 6+ (7-alpine used in Docker) |
| pip | 23+ |

---

## Installation — local run

```bash
# 1. Clone or copy the project into your working directory
cd <project-root>

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .                 # installs the cgs_runtime_wrapper package

# 4. Configure environment
cp .env.example .env
# Edit .env — set CGS_API_KEY and REDIS_URL at minimum

# 5. Start Redis (if not already running)
redis-server --daemonize yes

# 6. Start the API server
uvicorn cgs_runtime_wrapper.api.main:app --reload --port 8000
```

The server is now available at `http://localhost:8000`.

---

## Running with Docker

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — set CGS_API_KEY (REDIS_URL is overridden by compose)

# 2. Build and start both services
docker compose up --build

# Tear down
docker compose down
```

- The `redis` service runs on port `6379` (host-accessible).
- The `wrapper` service runs on port `8000` (host-accessible).
- The wrapper will not start until Redis passes its healthcheck.

---

## Authentication

Every request must include the `X-API-Key` header.

```bash
curl -X POST http://localhost:8000/turn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{ ... }'
```

| Response | Meaning |
|---|---|
| `401 UNAUTHORIZED` | Header absent or key does not match `CGS_API_KEY` |
| `500 SERVER_MISCONFIGURED` | `CGS_API_KEY` environment variable is not set |

Set `CGS_API_KEY` in `.env` before starting the server.

---

## Rate limiting

`POST /turn` is rate-limited per `session_id`.

| Variable | Default | Description |
|---|---|---|
| `RATE_LIMIT_RPM` | `60` | Maximum requests per session per minute |

When the limit is exceeded the server returns `429 RATE_LIMIT_EXCEEDED` with a JSON body describing the session and limit. The counter resets automatically each calendar minute.

All other endpoints (`/telemetry/render`, `/session/reset`) are not rate-limited.

---

## API endpoints

All bodies are JSON. All responses are JSON unless noted.

### `POST /turn`

Process one user turn through the full ingress → model → egress pipeline.

**Request:** `RequestEnvelope`

```json
{
  "session_id": "sess-abc123",
  "turn_index": 1,
  "raw_input": "Help me analyse this strategy.",
  "wrapper_version": "0.1.0",
  "cgs_version": "14.1.0"
}
```

**Response:** `OutputEnvelope` — includes `emission` (user-facing text), `pipeline_status`, full gate results, and telemetry payload.

---

### `POST /telemetry/render`

Render telemetry for a session at a specified detail level.

**Request:**
```json
{
  "session_id": "sess-abc123",
  "level": "standard",
  "range": { "from_turn": 1, "to_turn": 5 }
}
```

`level` values: `minimal` | `standard` | `full`. `range` is optional.

**Response:** Formatted plain-text telemetry string.

---

### `POST /session/reset`

Reset session state. Called automatically on `EOS` trigger. Preserves `session_id` in audit log.

**Request:**
```json
{ "session_id": "sess-abc123" }
```

**Response:** `{ "status": "ok" }`

---

## Gate architecture overview

The pipeline has two sequential stages: **ingress** and **egress**.

### Ingress gates (pre-reasoning, run before the model)

| Gate | Purpose | Implementation |
|---|---|---|
| **ICC** | Interpretive Commitment Control — parse intent, detect constraint conflicts | Stub (model-based) |
| **ASTG** | Assumption Stress Test — identify all unstated premises with failure conditions | Stub (model-based) |
| **BSG** | Bias Selection — require explicit optimization frame when tradeoff present | Rules (partial) |
| **EDH** | Echo Detection Heuristic — cosine similarity against prior turn embeddings | Stub (embedding) |
| **SPM** | Session Pattern Monitor — accumulate Signal A/B/C, fire observation at threshold | Rules (full) |
| **PRAP** | Pre-Reasoning Assurance Protocol — aggregate all prior gate results before model call | Rules (full) |

Ingress halts on the first gate failure. Remaining gates do not execute.

### Egress gates (post-reasoning, run after the model returns)

| Gate | Purpose | Implementation |
|---|---|---|
| **OSCL** | Outcome-Scored Self-Critique Loop — score output on 5 axes, trigger rerender | Stub (returns 0.85) |
| **FINALIZATION** | Pre-emission gate — all 8 sub-checks: headers, option labels, lexical compliance, scope, UFRS, SSCS | Rules (full) |
| **TELEMETRY** | Write `TelemetryTurnRecord` to store; increment `turn_index` | Full |

FINALIZATION triggers a rerender loop (maximum 2 cycles) if any sub-check fails. After 2 cycles without a pass, the pipeline emits `RERENDER_LIMIT_EXCEEDED`.

TELEMETRY is always the last gate. It fires even when the turn ends in halt.

### Special handlers (egress router)

| Signal | Detection | Output |
|---|---|---|
| `NFAR` / `no further action required` in model output | String match | Exactly `Standing by.` |
| `EOS` in model output | String match | Session snapshot + `POST /session/reset` |
| `Trace This` in user input | String match | Audit ledger from telemetry store |

---

## Stub disclosure

The following components are **stubs**. They return structurally valid output but do not perform real classification. They will be replaced when the training corpus is complete.

| Component | File | What the stub returns |
|---|---|---|
| ICC classifier | `classifier/icc_classifier.py` | `consistent`, generic intent, no exclusions |
| ASTG classifier | `classifier/astg_classifier.py` | Zero assumptions identified |
| EDH similarity | `classifier/edh_similarity.py` | `similarity_score: 0.0`, no echo detected |
| OSCL scorer | `egress/gates/oscl.py` | All axes at 0.85, `revision_required: False` |

**Prompt templates** for ICC and ASTG are included in their stub files as `ICC_PROMPT_TEMPLATE` and `ASTG_PROMPT_TEMPLATE` constants. These are the exact templates specified in `cosyn_wrapper_classifier_specification.md §3.2 / §4.2`.

**Rules-based components are fully implemented and production-ready:**
SPM Signal A/B/C classifiers, lexical compliance scanner, option labeling detector, PRAP, FINALIZATION sub-checks.

---

## Adapter extension guide

The model adapter is an abstract interface in `adapters/model_adapter.py`.

```python
class ModelAdapter(ABC):
    @abstractmethod
    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        """Returns (raw_output, latency_ms)."""
```

### Switching to Claude

1. Set `MODEL_ADAPTER=claude` in `.env`.
2. Set `ANTHROPIC_API_KEY=sk-ant-...` in `.env`.
3. Optionally set `CLAUDE_MODEL=claude-opus-4-6`.

The `ClaudeAPIAdapter` in `model_adapter.py` is a placeholder that calls the Anthropic Messages API. Install the SDK if needed:

```bash
pip install anthropic
```

### Implementing a custom adapter

```python
from cgs_runtime_wrapper.adapters.model_adapter import ModelAdapter

class MyAdapter(ModelAdapter):
    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        start = time.time()
        response = await my_model_client.complete(prompt)
        latency_ms = int((time.time() - start) * 1000)
        return response.text, latency_ms
```

Pass the adapter instance to `run_egress_pipeline` or replace `_model_adapter` in `api/main.py` lifespan.

---

## Running tests

Tests use `FakeRedis` — no live Redis instance required.

```bash
# From project root
pytest

# With coverage
pip install pytest-cov
pytest --cov=cgs_runtime_wrapper --cov-report=term-missing
```

---

## Environment variable reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `CGS_API_KEY` | Yes | — | API key for `X-API-Key` header authentication |
| `REDIS_URL` | Yes | `redis://localhost:6379` | Redis connection URL |
| `ANTHROPIC_API_KEY` | No | — | Required when `MODEL_ADAPTER=claude` |
| `MODEL_ADAPTER` | No | `stub` | `stub` \| `claude` \| `openai` |
| `CLAUDE_MODEL` | No | `claude-opus-4-6` | Claude model name |
| `RATE_LIMIT_RPM` | No | `60` | Max `/turn` requests per session per minute |
