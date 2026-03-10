# CGS Runtime Wrapper — Gate Function Specifications

**Document 2 of 4**  
**CGS version:** 14.1.0  
**Spec version:** 1.0.0  
**Generated:** 2026-03-10  
**Depends on:** `doc1_interface_contracts.json`

---

## Overview

This document defines the function contract for every CGS gate implemented in the wrapper. Each gate specification includes inputs, `GateResult.gate_data` output schema, pass conditions, fail/halt conditions with reason codes, and session state interactions.

All type references use `doc1_interface_contracts.json` definitions.

Gates execute in strict order. No gate may be skipped or reordered.

**Ingress order:** `ICC → ASTG → BSG → EDH → SPM → PRAP`  
**Egress order:** `OSCL → FINALIZATION → TELEMETRY`

If any ingress gate returns `status: halt | fail` before PRAP, the pipeline halts and remaining gates do not execute. PRAP runs last as the final pre-reasoning assurance check.

---

## INGRESS GATES

---

### ICC — Interpretive Commitment Control

| Property | Value |
|---|---|
| Phase | Ingress |
| Mandatory | Yes |
| Failure class | Class 0 on silent resolution |
| Execution position | First |

**Purpose:** Prevents premature fixation on a single interpretation. Parses intent, validates constraint consistency, detects conflicts between early and late clauses.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_input` | `string` | `RequestEnvelope.raw_input` |
| `crs_scope` | `string \| null` | `RequestEnvelope.crs_scope` |
| `turn_index` | `integer` | `RequestEnvelope.turn_index` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.ICC`)

| Field | Type | Description |
|---|---|---|
| `intent_primary` | `string` | Primary goal extracted from input |
| `intent_scope` | `string \| null` | Explicit scope limitation if stated |
| `intent_exclusions` | `string[]` | Explicit exclusions or non-goals |
| `intent_output_form` | `string \| null` | Requested output form if stated |
| `constraint_consistency` | `consistent \| ambiguous \| conflicting` | Result of cross-clause consistency pass |
| `ambiguity_description` | `string \| null` | Description of ambiguity if present |
| `least_committal_interpretation` | `string \| null` | Populated when ambiguous; least-committal reading used |
| `provisional_flag` | `boolean` | True when least-committal interpretation used |

#### Pass conditions

- Explicit goal extractable from input
- Later clauses consistent with earlier constraints
- No unresolvable conflict between scope, exclusions, and requested output form

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Ambiguous intent — cannot resolve deterministically | `halt` | `AMBIGUOUS_INTENT` |
| Conflicting constraints between clauses | `halt` | `CONSTRAINT_CONFLICT` |
| Silent resolution attempted | `halt` (Class 0) | `AMBIGUOUS_INTENT` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | `SessionState.crs_scope` | Load for boundary comparison if `crs_strict_mode` enabled |
| READ | `SessionState.mode_lock` | Load to check mode consistency |
| WRITE | — | ICC does not mutate session state |

#### Composition note

ICC governs interpretation selection upstream of all reasoning gates. On ambiguous input, ICC must halt and return a clarification request — it may never silently resolve ambiguity. Least-committal interpretation is only permitted for minor ambiguity with `provisional_flag: true`; it is not a substitute for clarification on material conflicts.

---

### ASTG — Assumption Stress Test Gate

| Property | Value |
|---|---|
| Phase | Ingress |
| Mandatory | Yes |
| Failure class | Class 0 on undeclared assumption |
| Execution position | Second |

**Purpose:** Identifies all assumptions required to proceed. For each assumption, defines failure conditions and impact on conclusions if false.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_input` | `string` | `RequestEnvelope.raw_input` |
| `icc_gate_data` | `gate_data_schemas.ICC` | ICC `GateResult.gate_data` |
| `crs_scope` | `string \| null` | `RequestEnvelope.crs_scope` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.ASTG`)

| Field | Type | Description |
|---|---|---|
| `assumptions_identified` | `Assumption[]` | Each: `{ assumption_text, failure_condition, conclusion_impact, stability }` |
| `assumption_count` | `integer` | Total assumptions found |
| `unstable_assumption_present` | `boolean` | True if any assumption is `stability: unstable` |
| `assumption_block_text` | `string \| null` | Formatted declaration for injection into model prompt. Null if no assumptions. |

#### Pass conditions

- All required assumptions explicitly identified
- All assumptions have declared failure conditions
- No undeclared assumption required to proceed

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Undeclared assumption required to proceed | `halt` | `UNDECLARED_ASSUMPTION` |
| Unstable assumption detected | `warn` | — (`provisional_flag: true`) |
| Assumption present but failure condition missing | `halt` | `UNDECLARED_ASSUMPTION` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | — | No state reads |
| WRITE | — | ASTG does not mutate session state. Assumption block injected into model prompt via ingress router. |

#### Composition note

Every assumption, however obvious, must be surfaced. User statements are not assumptions — they are inputs. An unstated premise the system must hold to proceed is an assumption. Common knowledge (a year has 12 months) is not an assumption. An unstable assumption sets `provisional_flag` and is injected into the model prompt annotation block; it does not halt execution.

---

### BSG — Bias Selection Gate

| Property | Value |
|---|---|
| Phase | Ingress |
| Mandatory | Yes |
| Failure class | Class 0 on implicit bias |
| Execution position | Third |

**Purpose:** Prevents implicit alignment with perceived user preference by requiring an explicit optimization frame declaration before reasoning when a tradeoff is present.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_input` | `string` | `RequestEnvelope.raw_input` |
| `icc_gate_data` | `gate_data_schemas.ICC` | ICC `GateResult.gate_data` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.BSG`)

| Field | Type | Description |
|---|---|---|
| `tradeoff_detected` | `boolean` | True if request involves optimization tradeoff |
| `bias_frame_selected` | `BiasFrame \| null` | Selected frame. Null if no tradeoff detected. |
| `implicit_bias_detected` | `boolean` | True if frame inferred from tone/repetition/prior agreement |
| `conflicting_signals` | `boolean` | True if multiple incompatible frames present |

#### Pass conditions

- No tradeoff detected — gate passes silently
- Tradeoff detected AND bias frame explicitly selected before reasoning

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Implicit bias alignment detected | `halt` (Class 0) | `IMPLICIT_BIAS` |
| Conflicting bias signals | `halt` | `CONFLICTING_BIAS_SIGNALS` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | — | No state reads |
| WRITE | — | BSG does not mutate state. Selected frame injected into model prompt annotation. |

#### Composition note

BSG fires only when a tradeoff optimization is present. For requests with no optimization tradeoff, BSG passes silently. Bias frame may not be inferred from emotional tone, stated confidence, or prior agreement. Only explicit user selection or unambiguous request framing establishes the frame without halt.

---

### EDH — Echo Detection Heuristic

| Property | Value |
|---|---|
| Phase | Ingress |
| Mandatory | Yes |
| Failure class | Class 0 on undetected echo continuation |
| Execution position | Fourth |

**Purpose:** Detects repetition masquerading as progress. Monitors semantic similarity of conclusions across turns, premise reuse without new evidence, and reaffirmation without external anchoring.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_input` | `string` | `RequestEnvelope.raw_input` |
| `icc_gate_data` | `gate_data_schemas.ICC` | ICC `GateResult.gate_data` |
| `edh_buffer` | `EDHBufferEntry[]` | `SessionState.edh_buffer` |
| `edh_fired` | `boolean` | `SessionState.edh_fired` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.EDH`)

| Field | Type | Description |
|---|---|---|
| `echo_detected` | `boolean` | True if echo signal detected this turn |
| `similarity_score` | `float 0.0–1.0` | Max cosine similarity against EDH buffer embeddings |
| `echo_type` | `EchoType \| null` | Echo type if detected |
| `forced_reframe_required` | `boolean` | True if echo detected AND EDH has previously fired |
| `external_anchor_check_triggered` | `boolean` | True if EAC must be satisfied this turn |
| `ecfd_triggered` | `boolean` | True if Emergent Counter-Frame Diagnostics must activate |

#### Pass conditions

- No echo signal detected
- Echo detected but EDH has not previously fired — `warn` only, no halt

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Echo detected AND `edh_fired: true` AND no new evidence present | `halt` | `ECHO_REPETITION` |
| Restatement without change after EDH has fired | `halt` | `ECHO_REPETITION` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | `SessionState.edh_buffer` | Load prior turn embeddings for similarity computation |
| READ | `SessionState.edh_fired` | Determine halt vs warn |
| WRITE | `SessionState.edh_buffer` | Append current turn embedding. Trim to last 10 entries. |
| WRITE | `SessionState.edh_fired` | Set `true` if echo detected this turn |

#### Composition note

EDH and SPM are complementary, not redundant. EDH fires internally and affects system reasoning (reframe, confidence decay, counter-frame diagnostics). SPM runs alongside EDH and uses EDH signal data to evaluate session-level structural patterns for user-facing output. EDH does not produce user-facing output directly.

---

### SPM — Session Pattern Monitor

| Property | Value |
|---|---|
| Phase | Ingress (alongside EDH) |
| Mandatory | Yes |
| Failure class | Non-blocking — output only |
| Execution position | Fifth |

**Purpose:** Detects sustained multi-turn pressure patterns. Accumulates Signal A, B, and C counts. Fires non-blocking structural observation when threshold is crossed.

#### Signal definitions

| Signal | Definition | Evidence condition |
|---|---|---|
| A — Confidence pressure | Correctness asserted, agreement requested, no new evidence | Evidence-free only. Pushback with new evidence does not qualify. |
| B — Restatement request | System asked to adopt conclusion as own, no evidential basis | Evidence-free only. |
| C — Position change via absence | Position change requested, no new proposition in same turn | Classified by absence of new proposition, not by emotional tone. |

#### Threshold

All three signal types must be present within a minimum 5-turn window:
- Signal A: minimum 3 qualifying turns
- Signal B: minimum 1 qualifying turn
- Signal C: minimum 1 qualifying turn

**False-negative bias:** When signal classification is ambiguous, do not count toward threshold.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_input` | `string` | `RequestEnvelope.raw_input` |
| `icc_gate_data` | `gate_data_schemas.ICC` | ICC `GateResult.gate_data` |
| `edh_gate_data` | `gate_data_schemas.EDH` | EDH `GateResult.gate_data` |
| `spm_signal_a_turns` | `integer[]` | `SessionState.spm_signal_a_turns` |
| `spm_signal_b_turns` | `integer[]` | `SessionState.spm_signal_b_turns` |
| `spm_signal_c_turns` | `integer[]` | `SessionState.spm_signal_c_turns` |
| `spm_fired` | `boolean` | `SessionState.spm_fired` |
| `spm_suppress` | `boolean` | `SessionState.spm_suppress` |
| `spm_window_reset_at_turn` | `integer \| null` | `SessionState.spm_window_reset_at_turn` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.SPM`)

| Field | Type | Description |
|---|---|---|
| `signal_a_this_turn` | `boolean` | Signal A classified for this turn |
| `signal_b_this_turn` | `boolean` | Signal B classified for this turn |
| `signal_c_this_turn` | `boolean` | Signal C classified for this turn |
| `threshold_crossed` | `boolean` | All three signals present within 5-turn window |
| `spm_output_text` | `string \| null` | Formatted observation if threshold crossed and not suppressed |
| `window_turn_range` | `[integer, integer] \| null` | Start and end turn indices of qualifying window |
| `dispute_detected` | `boolean` | True if current turn is a dispute of prior SPM observation |
| `dispute_response_text` | `string \| null` | Four-component dispute response if dispute detected |

#### Pass conditions

- Gate always returns `status: pass` — SPM is non-blocking
- SPM output injected into response when threshold crossed
- SPM output suppressed when `spm_suppress: true`

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Lexical violation in `spm_output_text` | `rerender` (egress, FINALIZATION) | `LEXICAL_VIOLATION` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | `spm_signal_a/b/c_turns` | Load prior accumulators |
| READ | `spm_fired` | Check if SPM has already fired |
| READ | `spm_window_reset_at_turn` | Determine current window boundaries |
| READ | `spm_suppress` | Check suppression flag |
| WRITE | `spm_signal_a_turns` | Append turn index if Signal A classified |
| WRITE | `spm_signal_b_turns` | Append turn index if Signal B classified |
| WRITE | `spm_signal_c_turns` | Append turn index if Signal C classified |
| WRITE | `spm_fired` | Set `true` when threshold first crossed |
| WRITE | `spm_fired_at_turn` | Set to current turn index when first fired |

#### Output format — required structure

```
Session Pattern Monitor — Threshold Crossed

The SPM gate has fired. The following signals were detected within the last [N] turns:

- Signal A (confidence assertion, no new evidence): [N] instances — turns [list]
- Signal B (request to adopt conclusion, no evidential basis): [N] instance — turn [N]
- Signal C (position change requested, no new proposition introduced): [N] instance — turn [N]

All three signal types are present. The minimum 5-turn window is satisfied.

This observation describes turn-level events. It does not assess the reason for those events.

The system's position on [topic] remains as stated in turn [N]. To update that position,
introduce new evidence or argument in any subsequent turn.
```

#### Composition note

The gate may not describe signal trajectory (how counts changed over time relative to system responses) in its output. Only signal count and type within the window are permitted. Rate limit: one SPM observation per session unless threshold re-crossed after full 5-turn window reset.

---

### PRAP — Pre-Reasoning Assurance Protocol

| Property | Value |
|---|---|
| Phase | Ingress (final) |
| Mandatory | Yes |
| Failure class | Halt on any check failure |
| Execution position | Sixth (final ingress gate) |

**Purpose:** Aggregates all prior ingress gate results and performs additional checks. No reasoning execution begins until PRAP passes.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `icc_gate_result` | `GateResult` | ICC result |
| `astg_gate_result` | `GateResult` | ASTG result |
| `bsg_gate_result` | `GateResult` | BSG result |
| `edh_gate_result` | `GateResult` | EDH result |
| `spm_gate_result` | `GateResult` | SPM result |
| `session_state` | `SessionState` | Full current session state |
| `request` | `RequestEnvelope` | Original request |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.PRAP`)

| Field | Type | Description |
|---|---|---|
| `all_checks_passed` | `boolean` | True if every PRAP minimum check passed |
| `failed_checks` | `string[]` | Check identifiers that failed |
| `scope_satisfiable` | `boolean` | Scope truth satisfiable |
| `source_fidelity_satisfiable` | `boolean` | Source fidelity requirements satisfiable |
| `mode_lock_viable` | `boolean` | Mode lock consistent with current request |
| `delegation_boundary_clean` | `boolean` | No ambiguous delegation intent |
| `crs_scope_clean` | `boolean` | Request within CRS scope or strict mode off |

#### Pass conditions

- All prior ingress gates passed
- Scope truth satisfiable
- No implicit assumptions remaining after ASTG
- Source fidelity requirements satisfiable
- Mode lock viable
- No delegation boundary ambiguity
- CRS scope clean or `crs_strict_mode: false`

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Any prior gate returned `halt \| fail` | `halt` | Inherits from failing gate |
| Scope truth not satisfiable | `halt` | `MISSING_REQUIRED_INPUTS` |
| Mode lock violation | `halt` | `MODE_LOCK_VIOLATION` |
| CRS scope violation in strict mode | `halt` | `CRS_SCOPE_VIOLATION` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | All session state fields | Full state required for PRAP checks |
| WRITE | — | PRAP does not mutate state |

#### Composition note

PRAP is the aggregation gate, not an independent classifier. Its job is to confirm all upstream gates passed and the combined state is consistent before reasoning begins. PRAP does not re-classify inputs — it reads gate results. The only novel checks PRAP performs are scope satisfiability, mode lock viability, and delegation boundary detection, which require cross-gate context not available to individual gates.

---

## EGRESS GATES

---

### OSCL — Outcome-Scored Self-Critique Loop

| Property | Value |
|---|---|
| Phase | Egress |
| Mandatory | Yes |
| Failure class | Rerender on score below threshold |
| Execution position | First egress gate |

**Purpose:** Scores draft output on five axes. Triggers revision if aggregate or minimum axis scores fall below threshold. Maximum 2 revision cycles.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `raw_output` | `string` | `ModelResponseEnvelope.raw_output` |
| `icc_gate_data` | `gate_data_schemas.ICC` | ICC result (from ingress) |
| `astg_gate_data` | `gate_data_schemas.ASTG` | ASTG result (from ingress) |
| `rerender_count` | `integer` | `ModelResponseEnvelope.rerender_count` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.OSCL`)

| Field | Type | Minimum threshold |
|---|---|---|
| `evidence_alignment` | `float 0.0–1.0` | 0.7 |
| `assumption_minimality` | `float 0.0–1.0` | — |
| `overclaim_risk_inverse` | `float 0.0–1.0` | — |
| `user_constraint_adherence` | `float 0.0–1.0` | 0.75 |
| `actionability_clarity` | `float 0.0–1.0` | — |
| `aggregate_score` | `float 0.0–1.0` | 0.72 |
| `revision_required` | `boolean` | — |
| `lowest_scoring_axes` | `string[]` | — |
| `scp_trigger` | `boolean` | — |

#### Pass conditions

- `evidence_alignment >= 0.7`
- `user_constraint_adherence >= 0.75`
- `aggregate_score >= 0.72`
- `rerender_count < 2`

#### Fail / halt conditions

| Condition | `status` | Notes |
|---|---|---|
| Any axis below minimum threshold | `rerender` | Revise lowest-scoring axes first |
| `scp_trigger: true` — improvement blocked by missing inputs | `halt` | `MISSING_REQUIRED_INPUTS` |
| `rerender_count >= 2` and still below threshold | `warn` | Proceed with `provisional_flag: true` |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | — | No state reads |
| WRITE | — | OSCL does not mutate state |

---

### FINALIZATION

| Property | Value |
|---|---|
| Phase | Egress (final before emission) |
| Mandatory | Yes |
| Failure class | Halt or rerender on any sub-check failure |
| Execution position | Second egress gate |

**Purpose:** Mandatory pre-emission gate. No output is emitted outside this gate. System-first responsibility: the system detects and corrects governance failures before the user sees output.

#### Sub-checks (all must pass)

| Sub-check | Method | Fail action |
|---|---|---|
| Persona headers present and correctly formatted | String prefix check | `rerender` — inject headers |
| All selectable actions option-labeled (A/B/C) | Trigger phrase match + heuristic | `rerender` — apply labels |
| SPM output lexically compliant (if SPM fired this turn) | Pattern match against prohibited construction list | `rerender` — inject compliant replacement |
| Source fidelity: time-sensitive claims verified or labeled | Keyword trigger + claim check | `rerender` or `halt` |
| Output scope within declared scope | Boundary check against `crs_scope` if strict mode | `halt` — `SCOPE_EXCEEDED` |
| Provisional status visible where required | Flag presence check | `rerender` |
| UFRS: epistemic status labels present where claims exceed evidence | Overclaim detection | Append labels or `rerender` |
| SSCS score >= 0.80 | Structural conformance scoring | Self-correct or `rerender` |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.FINALIZATION`)

See schema definition in `doc1_interface_contracts.json → gate_data_schemas.FINALIZATION`.

#### Fail / halt conditions

| Condition | `status` | `halt_reason_code` |
|---|---|---|
| Persona headers missing | `rerender` | — |
| Option labeling missing | `rerender` | — |
| SPM lexical violation | `rerender` | `LEXICAL_VIOLATION` |
| Scope exceeded | `halt` | `SCOPE_EXCEEDED` |
| Unresolvable drift requiring user input | `halt` | `UNRESOLVABLE_DRIFT` |
| SSCS below 0.80 and cannot self-correct | `rerender` | — |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | All session state fields | Required for scope and mode checks |
| WRITE | — | FINALIZATION does not mutate state. Telemetry gate captures results. |

#### Composition note

Self-healing is permitted when deterministic: persona header injection, option label application. Rerender requires model regeneration. Halt is reserved for conditions that cannot be resolved without user input. The lexical compliance check runs as a sub-check within FINALIZATION using pure pattern matching — it does not require a model call.

---

### TELEMETRY

| Property | Value |
|---|---|
| Phase | Egress (after FINALIZATION) |
| Mandatory | Yes |
| Failure class | Non-blocking — log only |
| Execution position | Third (final egress gate) |

**Purpose:** Captures all gate events into telemetry store. Must not modify output.

#### Inputs

| Parameter | Type | Source |
|---|---|---|
| `output_envelope` | `OutputEnvelope` (partial) | Egress router |
| `session_state` | `SessionState` | State store |

#### Output — `GateResult.gate_data` (schema: `gate_data_schemas.TELEMETRY`)

| Field | Type | Description |
|---|---|---|
| `record_written` | `boolean` | True if telemetry record successfully written |
| `write_error` | `string \| null` | Error message if write failed. Does not block emission. |

#### Pass conditions

- Telemetry store accepts write
- Schema validation passes at write time

#### Fail / halt conditions

| Condition | `status` | Notes |
|---|---|---|
| Schema validation failure | `warn` | Log internally. Do not block emission. |
| Store write failure | `warn` | Log internally. Do not block emission. |

#### State interactions

| Operation | Field | Action |
|---|---|---|
| READ | — | No additional state reads beyond output_envelope |
| WRITE | Telemetry store | Write `TelemetryTurnRecord` keyed by `session_id + turn_index` |
| WRITE | `SessionState.last_turn_completed_at_ms` | Update timestamp |
| WRITE | `SessionState.turn_index` | **Increment turn counter.** TELEMETRY is the only gate that increments turn_index. |

#### Composition note

Non-interference with output is an absolute requirement. Telemetry collection must never modify `final_emission_text`. A write failure produces a warning in internal logs and does not affect the emission path.

---

## Gate Composition Rules

1. **Ingress halts on first failure.** If ICC halts, ASTG through PRAP do not execute.
2. **PRAP is the aggregation checkpoint.** If any prior gate failed but PRAP was not reached, the pipeline uses the first gate's `halt_reason_code`.
3. **Egress rerender loop max 2 cycles.** After 2 cycles without FINALIZATION pass, return `RERENDER_LIMIT_EXCEEDED` halt.
4. **TELEMETRY is always the last gate.** It fires even when the turn ends in halt, to capture the failure event.
5. **SPM is non-blocking at ingress.** Its lexical compliance check runs inside FINALIZATION at egress, not at ingress.
6. **Mode lock is enforced by PRAP.** Mid-turn mode switching detected at PRAP, not at BSG.
