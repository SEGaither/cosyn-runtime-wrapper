# CGS Runtime Wrapper — Architecture

**CGS version:** 14.1.0
**Wrapper version:** 0.1.0

---

## Overview

The CGS Runtime Wrapper sits between the caller and the language model. Every user turn passes through a deterministic gate pipeline before the model is called (ingress) and again after the model responds (egress). The pipeline enforces governance constraints, accumulates session state, and controls what the model is allowed to emit.

No reasoning executes before all ingress gates pass. No output is emitted before all egress gates pass.

---

## Gate pipeline — full flow

```
Caller
  │
  │  POST /turn  { RequestEnvelope }
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  INGRESS PIPELINE                                               │
│                                                                 │
│  1. ICC  — parse intent, detect constraint conflicts            │
│       ↓ halt: AMBIGUOUS_INTENT / CONSTRAINT_CONFLICT            │
│  2. ASTG — identify all unstated premises                       │
│       ↓ halt: UNDECLARED_ASSUMPTION                             │
│  3. BSG  — require explicit bias frame when tradeoff present    │
│       ↓ halt: IMPLICIT_BIAS / CONFLICTING_BIAS_SIGNALS         │
│  4. EDH  — cosine similarity vs. session conclusion buffer      │
│       ↓ halt: ECHO_REPETITION (only if EDH already fired)       │
│  5. SPM  — accumulate Signal A / B / C (non-blocking)          │
│       ↓ always pass; fires observation when threshold crossed   │
│  6. PRAP — aggregate all prior results; final pre-model check   │
│       ↓ halt: MODE_LOCK_VIOLATION / CRS_SCOPE_VIOLATION / ...   │
│                                                                 │
│  On any halt → assemble HaltResponse → return to caller         │
│  On pass    → assemble IngressPipelineEnvelope                  │
└─────────────────────────────────────────────────────────────────┘
  │
  │  model_prompt  (governance block + state annotation + user input)
  ▼
┌────────────────────┐
│  MODEL CALL        │  ← abstracted via ModelAdapter
│  (any LLM)         │    stub | claude | custom
└────────────────────┘
  │
  │  raw_output  (verbatim, unmodified)
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  EGRESS PIPELINE                                                │
│                                                                 │
│  1. OSCL        — score output on 5 axes; rerender if low       │
│       ↓ rerender loop: max 2 cycles → RERENDER_LIMIT_EXCEEDED   │
│  2. FINALIZATION — 8 sub-checks (all must pass):                │
│       • Persona headers present                                 │
│       • Option labeling compliant (A/B/C labels)                │
│       • SPM lexical compliance (prohibited construction scan)   │
│       • Source fidelity (time-sensitive claims labelled)        │
│       • Output within declared CRS scope                        │
│       • Provisional status visible                              │
│       • UFRS epistemic labels present                           │
│       • SSCS structural conformance score >= 0.80               │
│       ↓ self-heal when deterministic; rerender when not         │
│       ↓ halt: SCOPE_EXCEEDED / UNRESOLVABLE_DRIFT               │
│  3. TELEMETRY   — write TelemetryTurnRecord; increment          │
│                   turn_index (only gate that does this)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
  │
  │  OutputEnvelope  { emission, pipeline_status, gate_results, telemetry }
  ▼
Caller
```

---

## Ingress flow — detail

### Model prompt assembly

When all ingress gates pass, the ingress router assembles the model prompt in three sections:

```
[SYSTEM GOVERNANCE BLOCK]
(fixed CGS governance instructions)

[STATE ANNOTATION BLOCK]
TURN_INDEX: 4
SPM_SIGNAL_A_COUNT: 2
SPM_SIGNAL_B_COUNT: 0
SPM_SIGNAL_C_COUNT: 1
SPM_FIRED_THIS_SESSION: false
CCD_CONFIDENCE_REGISTER: 0.7
EDH_ECHO_FLAG: false
PRAP_STATUS: pass
MODE_LOCK: none
ACTIVE_PERSONA: Core

[ASSUMPTION BLOCK — injected by ASTG when assumptions identified]
Assumption 1: ...
  Failure condition: ...
  Impact if false: ...
  Stability: stable

[SPM OBSERVATION — injected when SPM fires]
Session Pattern Monitor — Threshold Crossed
...

[USER INPUT]
<verbatim raw_input>
```

### Halt path

On the first gate that returns `status: halt | fail`, the pipeline stops immediately. Later gates do not execute. The ingress router assembles a `HaltResponse` and returns it to the caller in an `OutputEnvelope` with `pipeline_status: halted`.

### Session state

Session state (`SessionState`) is loaded from Redis at the start of every turn and written back after the TELEMETRY gate completes. Only the TELEMETRY gate increments `turn_index`.

---

## Egress flow — detail

### Rerender loop

```
Model output
    │
    ▼
  OSCL scoring
    │ score below threshold?
    ├── YES (and rerender_count < 2) ──→ return annotated prompt to model
    │                                      (rerender_count++)
    ├── YES (and rerender_count >= 2) ─→ warn, continue with provisional flag
    └── NO ──────────────────────────→ FINALIZATION
                                           │ sub-check fails?
                                           ├── deterministic fix → apply inline
                                           ├── rerender needed → back to model
                                           │   (max 2 total cycles across OSCL + FINALIZATION)
                                           └── halt needed → SCOPE_EXCEEDED etc.
```

### Persona header injection

Before emission, the egress router prepends to all user-facing output:

```
Router (control-plane): Stack Architect
Active persona (this turn): Core
```

### Special output handlers

| Trigger | Detection | Action |
|---|---|---|
| `NFAR` or `no further action required` | Case-insensitive substring match in `raw_output` | Emit exactly `Standing by.` — no further processing |
| `EOS` | Substring match in `raw_output` | Assemble session snapshot from state + telemetry stores; call `POST /session/reset` |
| `Trace This` | Substring match in `raw_input` | Build audit ledger from all `TelemetryTurnRecord` entries for this session; return as emission |

---

## Component responsibility map

```
cgs_runtime_wrapper/
│
├── models/envelopes.py          Single source of truth — all Pydantic models
│                                (RequestEnvelope, SessionState, GateResult, ...)
│
├── state/session_store.py       Redis KV store for SessionState
│                                Key: session:{session_id}
│                                TTL: SessionState.ttl_seconds (default 3600s)
│
├── telemetry/store.py           Redis KV store for TelemetryTurnRecord
│                                Key: telemetry:{session_id}:{turn_index}
│                                Provides: rollup aggregation, anonymised export,
│                                          render at minimal / standard / full
│
├── classifier/
│   ├── spm_classifiers.py       Rules — Signal A / B / C (full, EC-01–EC-08)
│   ├── lexical_scanner.py       Rules — 7 prohibited pattern categories + templates
│   ├── option_labeling.py       Rules — trigger phrase + 2-action heuristic
│   ├── icc_classifier.py        STUB — prompt template constant included
│   ├── astg_classifier.py       STUB — prompt template constant included
│   ├── edh_similarity.py        STUB — numpy zeros, score=0.0
│   └── labeling_schema.py       Corpus schema (LabeledExample, JSONL store)
│
├── ingress/
│   ├── gates/                   icc · astg · bsg · edh · spm · prap
│   └── router.py                Orchestrates ICC→ASTG→BSG→EDH→SPM→PRAP
│
├── egress/
│   ├── gates/                   oscl · finalization · telemetry_gate
│   └── router.py                Rerender loop, special handlers, OutputEnvelope assembly
│
├── audit/regression.py          Governance regression detector
│                                Flags halt_rate or class0_failure_count
│                                degradation > 20% vs baseline
│
├── adapters/model_adapter.py    Abstract ModelAdapter + Stub + ClaudeAPI + OpenAI
│
└── api/
    ├── middleware.py            APIKeyMiddleware (X-API-Key)
    │                            RateLimiter (per-session, Redis-backed, 60 RPM default)
    └── main.py                  FastAPI app — lifespan, routes, exception handler
```

---

## Stub upgrade path

When classifier training is complete, replace each stub with a real implementation. The gate interfaces do not change.

### Step 1 — ICC classifier

File: `classifier/icc_classifier.py`

Replace the `classify_icc(raw_input, crs_scope)` stub body with:
- A call to the fine-tuned 7B model using `ICC_PROMPT_TEMPLATE`
- JSON response parsed into `ICCGateData`
- Evaluate: constraint consistency accuracy >= 0.85 on held-out test set

### Step 2 — ASTG classifier

File: `classifier/astg_classifier.py`

Replace the `classify_astg(raw_input, intent_primary, crs_scope)` stub body with:
- A call to the fine-tuned model using `ASTG_PROMPT_TEMPLATE`
- JSON response parsed into `ASTGGateData`
- Evaluate: assumption F1 >= 0.80 on held-out test set

### Step 3 — EDH similarity

File: `classifier/edh_similarity.py`

Replace the stub with:
- Load `all-MiniLM-L6-v2` (or fixed equivalent) once at module level
- `encode(text)` → fixed 384-dim embedding vector
- `cosine_similarity(vec_a, vec_b)` → float 0–1
- Echo detected when max similarity > 0.85 AND no evidence markers present
- Fix the embedding model per session — do not change mid-session

### Step 4 — OSCL scorer

File: `egress/gates/oscl.py`

Replace the stub (which returns 0.85 across all axes) with:
- A scoring function that evaluates `raw_output` against ICC and ASTG gate data
- Thresholds: evidence_alignment >= 0.7, user_constraint_adherence >= 0.75, aggregate >= 0.72
- Trigger `revision_required: True` when any axis is below threshold

### Training corpus

Use `classifier/labeling_schema.py` (`LabelingStore`) to manage JSONL corpus files. The `LabeledExample` schema enforces:
- Two independent labelers per example
- Cohen's kappa >= 0.75 for training admission
- `split` assignment: 80% train / 10% eval / 10% test

Minimum corpus sizes before training begins (from `cosyn_wrapper_classifier_specification.md §7.1`):
- ICC intent: 500 examples (2,000 recommended)
- ICC consistency: 300 per label = 900 total
- ASTG assumption: 500 examples (20% zero-assumption)
- BSG tradeoff: 200 per label = 600 total

---

## Multi-model adapter interface

The `ModelAdapter` abstract base class is the only integration point for any language model.

```python
class ModelAdapter(ABC):
    @abstractmethod
    async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]:
        """
        Call the language model with the assembled prompt.
        Returns:
            raw_output  — verbatim model response, unmodified
            latency_ms  — wall-clock time for the model call in milliseconds
        """
```

### Provided implementations

| Class | File | Notes |
|---|---|---|
| `StubModelAdapter` | `adapters/model_adapter.py` | Returns canned text; no network calls; used in tests |
| `ClaudeAPIAdapter` | `adapters/model_adapter.py` | Placeholder; calls Anthropic Messages API; requires `anthropic` SDK |
| `OpenAIAdapter` | `adapters/model_adapter.py` | Placeholder; requires `openai` SDK |

### Adding a new adapter

1. Subclass `ModelAdapter` in any file.
2. Implement `async call_model(self, prompt, session_id) -> tuple[str, int]`.
3. Return the verbatim model response — do not modify it before returning. OSCL receives it raw.
4. Record wall-clock latency in milliseconds and return it as the second element.
5. Wire it into `api/main.py` lifespan by setting `MODEL_ADAPTER=<your-value>` and adding a branch in the lifespan block.

The wrapper guarantees that `raw_output` is passed unmodified to OSCL. Any post-processing belongs in the egress pipeline, not in the adapter.

---

## Gate composition rules

1. **Ingress halts on first failure.** If ICC halts, ASTG through PRAP do not execute.
2. **PRAP is the aggregation checkpoint.** It inherits the halt reason from the first failing gate.
3. **Egress rerender loop max 2 cycles.** After 2 cycles without FINALIZATION pass, emit `RERENDER_LIMIT_EXCEEDED`.
4. **TELEMETRY is always the last gate.** It fires even when the turn ends in halt.
5. **SPM is non-blocking at ingress.** Its lexical compliance check runs inside FINALIZATION at egress.
6. **Mode lock is enforced by PRAP.** Mid-turn mode switching detected at PRAP, not BSG.
7. **turn_index is incremented only by TELEMETRY.** No other gate or router may mutate it.
