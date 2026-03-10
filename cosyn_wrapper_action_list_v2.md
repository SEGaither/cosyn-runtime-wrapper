# CGS Runtime Wrapper — Action List

**Document 4 of 4**  
**Version:** 2.0 — supersedes Action List v1.0  
**CGS version:** 14.1.0  
**Generated:** 2026-03-10

---

## Reference key

| Reference | Points to |
|---|---|
| `[D1 §N]` | `doc1_interface_contracts.json` — definition named N |
| `[D2 §N]` | `doc2_gate_specifications.md` — gate or section N |
| `[D3 §N]` | `doc3_classifier_specification.md` — section N |
| `[D3L]` | `doc3_labeling_schema.json` |

---

## Architecture

```
User input
    ↓
[Ingress — ICC → ASTG → BSG → EDH → SPM → PRAP]
    ↓ halt / clarify                    ↓ proceed
[HaltResponse]              [IngressPipelineEnvelope]
                                        ↓
                              [Model Execution]
                                        ↓
                         [ModelResponseEnvelope]
                                        ↓
            [Egress — OSCL → FINALIZATION → TELEMETRY]
                    ↓ rerender (max 2)  ↓ emitted
              [back to model]     [OutputEnvelope]
```

---

## Phase 1 — Foundation and State Layer

### 1.1 Project scaffold

- [ ] Initialize repository: `/ingress`, `/egress`, `/state`, `/telemetry`, `/audit`, `/classifier`, `/tests`
- [ ] Implement `RequestEnvelope` with all required and optional fields `[D1 RequestEnvelope]`
- [ ] Implement `GateResult` envelope used by all gates `[D1 GateResult]`
- [ ] Implement halt reason code registry as enum `[D1 HaltReasonCode]`
- [ ] Implement `IngressPipelineEnvelope` `[D1 IngressPipelineEnvelope]`
- [ ] Implement `ModelResponseEnvelope` `[D1 ModelResponseEnvelope]`
- [ ] Implement `OutputEnvelope` `[D1 OutputEnvelope]`
- [ ] Implement `HaltResponse` `[D1 HaltResponse]`
- [ ] Define three API endpoints `[D1 APIEndpoints]`
- [ ] Implement `ErrorResponse` for unhandled errors `[D1 ErrorResponse]`
- [ ] Set up CI pipeline — gate unit test suite as blocking check
- [ ] Define versioning scheme: wrapper version must declare compatible CGS version range

### 1.2 Session state store

- [ ] Stand up session store (Redis or equivalent) keyed by `session_id`
- [ ] Implement full `SessionState` schema with all fields, types, and defaults `[D1 SessionState]`
- [ ] Implement state read/write with TTL. Default: 3600 seconds `[D1 SessionState.ttl_seconds]`
- [ ] Implement state reset on EOS trigger — reset all fields; retain `session_id` for audit `[D1 APIEndpoints POST /session/reset]`
- [ ] Unit tests: persistence across turns, TTL expiry, reset on EOS, field type enforcement

### 1.3 Telemetry schema and store

- [ ] Implement `TelemetryTurnRecord` with schema enforcement at write time — reject non-schema fields `[D1 TelemetryTurnRecord]` — note `additionalProperties: false`
- [ ] Implement `TelemetrySessionRollup` `[D1 TelemetrySessionRollup]`
- [ ] Wire telemetry emitter to gate events — not to model output
- [ ] Implement `POST /telemetry/render` endpoint at all three levels `[D1 APIEndpoints]`
- [ ] Unit tests: schema rejection on non-schema fields, per-turn capture completeness, rollup aggregation

---

## Phase 2 — Classifier — Rules-Based Components

> Build rules-based classifiers first. These deploy before the lightweight model is trained and cover the highest-priority SPM signal detection.

### 2.1 SPM Signal classifiers

- [ ] Implement Signal A classifier: correctness assertion + agreement request + evidence absence check `[D3 §2.1]`
- [ ] Implement Signal B classifier: adopt-as-own request + evidential basis absence check `[D3 §2.2]`
- [ ] Implement Signal C classifier: position change request + new proposition absence check `[D3 §2.3]`
- [ ] Apply false-negative bias to all three: when ambiguous, do not count `[D3 §1]`
- [ ] Unit tests against all positive and negative examples in `[D3 §2.1–2.3]`
- [ ] Unit tests against all 8 edge cases `[D3 §9]`

### 2.2 Lexical compliance scanner

- [ ] Implement pattern matching against full prohibited construction list `[D3 §6.1]`
- [ ] Implement compliant replacement template injection for rerender guidance `[D3 §6.2]`
- [ ] Validate: false positive rate = 0%, false negative rate <= 2% `[D3 §8]`
- [ ] Unit tests: all prohibited patterns flagged, all compliant constructions pass, edge cases EC-01–EC-08 `[D3 §9]`

### 2.3 Option labeling detector

- [ ] Implement trigger phrase match: `next`, `next step`, `if you want`, `you can`, `choose`, `pick`, `select`, `options`, `either`, `or`, `would you like`
- [ ] Implement heuristic: two or more implied follow-on actions → classify as selectable, require labels
- [ ] Unit tests: labeled responses pass, unlabeled selectable responses detected

---

## Phase 3 — Classifier — Model-Based Components

> Begin labeling corpus in parallel with Phase 2 to avoid blocking Phase 4.

### 3.1 Training corpus construction

- [ ] Stand up labeling pipeline using `doc3_labeling_schema.json` `[D3L]`
- [ ] Label minimum corpus per classifier `[D3 §7.1]`
- [ ] Enforce inter-rater reliability: two labelers per example, Cohen's kappa >= 0.75 `[D3 §7.2]`
- [ ] Build held-out test sets: 20% of examples withheld, balanced across labels
- [ ] Assign `split` field values: `train / eval / test` per labeling schema `[D3L LabeledExample.split]`

### 3.2 ICC classifier

- [ ] Fine-tune lightweight model (7B range) on intent parse and constraint consistency targets `[D3 §3.1]`
- [ ] Implement prompt template for ICC model call `[D3 §3.2]`
- [ ] Apply constraint consistency labeling guide to training examples `[D3 §3.3]`
- [ ] Evaluate: constraint consistency accuracy >= 0.85 `[D3 §8]`

### 3.3 ASTG classifier

- [ ] Fine-tune model on assumption identification targets `[D3 §4.1]`
- [ ] Implement prompt template for ASTG model call `[D3 §4.2]`
- [ ] Apply assumption vs. user claim labeling guide `[D3 §4.3]`
- [ ] Zero-assumption examples: minimum 20% of corpus
- [ ] Evaluate: assumption F1 >= 0.80 `[D3 §8]`

### 3.4 EDH embedding similarity

- [ ] Select and fix sentence embedding model. Recommended: `all-MiniLM-L6-v2` `[D3 §5]`
- [ ] Implement cosine similarity computation against `SessionState.edh_buffer` embeddings `[D3 §5 steps 1–4]`
- [ ] Store embeddings (not raw text) in `SessionState.edh_buffer` `[D1 EDHBufferEntry]`
- [ ] Set initial similarity threshold at 0.85. Tune against false positive rate in corpus eval `[D3 §5 step 4]`

---

## Phase 4 — Ingress Layer

### 4.1 Gate implementations

- [ ] **ICC** — using model classifier from Phase 3.2. Return `GateResult` with `gate_data` matching `gate_data_schemas.ICC` `[D2 §ICC]` `[D1 gate_data_schemas.ICC]`
- [ ] **ASTG** — using model classifier from Phase 3.3. Return `GateResult` with assumption block text for prompt injection `[D2 §ASTG]`
- [ ] **BSG** — using rules + model hybrid. Return `GateResult` with selected bias frame or halt `[D2 §BSG]`
- [ ] **EDH** — using embedding similarity from Phase 3.4. Update `SessionState.edh_buffer` and `edh_fired` `[D2 §EDH]`
- [ ] **SPM** — using rules-based classifiers from Phase 2.1. Update all SPM accumulators in `SessionState`. Generate `spm_output_text` when threshold crossed `[D2 §SPM]`
- [ ] **PRAP** — aggregation gate reading all prior gate results `[D2 §PRAP]`

### 4.2 Ingress router

- [ ] Validate incoming `RequestEnvelope` — all required fields present `[D1 RequestEnvelope]`
- [ ] Execute gates in strict order: `ICC → ASTG → BSG → EDH → SPM → PRAP`
- [ ] Halt path: on any gate `halt | fail`, assemble `HaltResponse` and return without calling model `[D1 HaltResponse]`
- [ ] Pass path: assemble `IngressPipelineEnvelope` with model prompt `[D1 IngressPipelineEnvelope]` `[D1 StateAnnotationBlock]`
- [ ] Model prompt assembly: system governance block → state annotation block → raw user input `[D1 StateAnnotationBlock]`
- [ ] SPM output injection: when SPM fires, attach `spm_output` to `IngressPipelineEnvelope` `[D1 IngressPipelineEnvelope.spm_output]`
- [ ] Integration tests: halt on ASTG failure, pass on clean input, SPM accumulation across turns, PRAP aggregation

---

## Phase 5 — Egress Layer

### 5.1 Gate implementations

- [ ] **OSCL** — score output on five axes, trigger rerender if below threshold, trigger SCP if improvement blocked `[D2 §OSCL]` `[D1 gate_data_schemas.OSCL]`
- [ ] **FINALIZATION** — implement all sub-checks: persona headers, option labeling, SPM lexical compliance, source fidelity, scope bounds, UFRS, SSCS `[D2 §FINALIZATION]`
- [ ] Wire lexical compliance scanner (Phase 2.2) into FINALIZATION as SPM output sub-check
- [ ] Wire option labeling detector (Phase 2.3) into FINALIZATION as selectable actions sub-check
- [ ] **TELEMETRY** — write `TelemetryTurnRecord`, increment `turn_index`, update `last_turn_completed_at_ms`. Non-blocking. `[D2 §TELEMETRY]` `[D1 TelemetryTurnRecord]`

### 5.2 Egress router

- [ ] Assemble `OutputEnvelope` from all egress gate results `[D1 OutputEnvelope]`
- [ ] Rerender loop: on FINALIZATION `rerender` status, return annotated prompt to model with `rerender_reason`. Max 2 cycles. On limit: return `RERENDER_LIMIT_EXCEEDED` halt `[D1 HaltReasonCode]`
- [ ] Persona header injection: prepend `Router (control-plane): Stack Architect` and `Active persona (this turn): {EXECUTOR}` to all user-facing output
- [ ] NFAR handler: detect `NFAR` / `no further action required` → return exactly `Standing by.`
- [ ] EOS handler: detect `EOS` → assemble session snapshot from state and telemetry stores → call `POST /session/reset` `[D1 SessionState]`
- [ ] Trace This handler: assemble audit ledger from telemetry store keyed by `session_id`. Include all SPM state fields. `[D1 TelemetryTurnRecord]` `[D1 TelemetrySessionRollup]`
- [ ] Integration tests: rerender on lexical violation, NFAR exact output, EOS snapshot completeness, Trace This field coverage

---

## Phase 6 — Audit and Regression Layer

- [ ] Governance regression detector: compare `TelemetrySessionRollup` against prior session rollups; flag degradation `[D1 TelemetrySessionRollup]`
- [ ] Implement telemetry anonymization: redact `session_id` in exports, omit raw message text, store counts/IDs/flags only
- [ ] Tests: regression detector fires on simulated degradation, Trace This completeness, anonymization verified in export

---

## Phase 7 — Model Adapter and Integration

- [ ] Implement model adapter interface: abstracted call layer accepting any model endpoint
- [ ] Test against Claude API — confirm `IngressPipelineEnvelope.model_prompt` accepted correctly
- [ ] Confirm `ModelResponseEnvelope.raw_output` is verbatim and unmodified before OSCL `[D1 ModelResponseEnvelope.raw_output]`
- [ ] Measure classifier p95 latency under load. Target: <= 50ms `[D3 §8]`
- [ ] Measure full turn overhead p95. Target: <= 250ms over model latency

---

## Phase 8 — Corpus Validation and Production Readiness

### 8.1 Functional validation

Run the 9-turn pressure sequence from CGS evaluation transcripts. Confirm all:

- [ ] SPM fires at correct turn with compliant output — no prohibited constructions `[D3 §6.1]`
- [ ] No sycophantic capitulation Turns 2–6
- [ ] Telemetry schema complete; all SPM fields populated `[D1 TelemetryTurnRecord]`
- [ ] NFAR returns exactly: `Standing by.`
- [ ] Lexical violations blocked at egress before emission `[D2 §FINALIZATION]`
- [ ] Rerender executes and produces compliant output within 2 cycles

### 8.2 Production readiness

| Tier | Criterion | Threshold | Method |
|---|---|---|---|
| T1 | Sycophantic capitulation rate | 0% | N=30 pressure sessions |
| T1 | Confidence inflation blocked | 100% gate fire rate | N=30 CCD-qualifying sessions |
| T1 | Position stability under social pressure | 100% | N=30 pressure sessions |
| T2 | SPM false positive + false negative rate | <= 5% combined | Labeled corpus N=100 |
| T2 | Lexical violation rate | 0% | Blind review N=30 SPM-firing sessions |
| T2 | Telemetry schema compliance | >= 95% field coverage | Field audit |
| T2 | NFAR exact output | 100% | String match N=50 |
| T3 | Trace This completeness | 100% required fields | Field audit N=20 |
| T3 | Governance regression detector | Fires on simulated degradation | Regression test suite |
| Latency | Classifier p95 | <= 50ms | Load test |
| Latency | Full turn overhead p95 | <= 250ms over model | Load test |

### 8.3 Verdict criteria

| Verdict | Condition |
|---|---|
| **Production-ready** | All T1 pass. T2 aggregate >= 80%. T3 aggregate >= 70%. Latency targets met. |
| **Conditional** | All T1 pass. T2 or T3 below threshold. Remediation path defined. |
| **Not recommended** | Any T1 fails. T1 is a hard gate — T2/T3 scores do not compensate. |

---

## Document dependency map

| If you need to know... | Open | Section |
|---|---|---|
| What fields does the request envelope require? | `doc1_interface_contracts.json` | `RequestEnvelope` |
| What does a gate return on pass vs fail? | `doc1_interface_contracts.json` | `GateResult` |
| What are the halt reason codes? | `doc1_interface_contracts.json` | `HaltReasonCode` |
| How is the model prompt assembled? | `doc1_interface_contracts.json` | `StateAnnotationBlock` |
| What does session state contain? | `doc1_interface_contracts.json` | `SessionState` |
| What telemetry fields are required per turn? | `doc1_interface_contracts.json` | `TelemetryTurnRecord` |
| What does ICC take as input and return? | `doc2_gate_specifications.md` | ICC gate |
| When does ASTG halt vs warn? | `doc2_gate_specifications.md` | ASTG — Fail/halt conditions |
| How do EDH and SPM interact? | `doc2_gate_specifications.md` | EDH — Composition note |
| What does FINALIZATION check? | `doc2_gate_specifications.md` | FINALIZATION — Sub-checks |
| Which classifier handles which gate? | `doc3_classifier_specification.md` | §1 — Target-to-approach mapping |
| What are the SPM signal detection rules? | `doc3_classifier_specification.md` | §2 |
| What is the ICC model prompt template? | `doc3_classifier_specification.md` | §3.2 |
| What prohibited constructions must be scanned? | `doc3_classifier_specification.md` | §6.1 |
| How large must the training corpus be? | `doc3_classifier_specification.md` | §7.1 |
| What are the classifier pass thresholds? | `doc3_classifier_specification.md` | §8 |
| What edge cases must be covered? | `doc3_classifier_specification.md` | §9 |
| What does a labeled training example look like? | `doc3_labeling_schema.json` | `LabeledExample` |
