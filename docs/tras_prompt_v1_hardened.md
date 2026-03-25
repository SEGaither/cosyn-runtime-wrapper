Write the Trinity Runtime Architecture Spec (TRAS v1) for the current CoSyn prototype.

Use the locked ESD as the sole canonical baseline. The ESD is immutable. No statement in the TRAS may contradict, override, reinterpret, or extend the ESD. If a requirement cannot be satisfied without violating the ESD, halt and declare the violation. Do not attempt to resolve it.

Objective:
Define the additive architecture required to evolve the current ESD-locked prototype into a constraint-capturing, constraint-persisting, and constraint-reusing runtime. All new capability must attach around existing executable behavior. No existing executable behavior may be modified, removed, replaced, or reinterpreted.

Hard rules — violation of any rule invalidates the output:

* Do not change code.
* Do not rebuild.
* Do not redesign the system.
* Do not alter the ESD baseline.
* Do not change the five-stage sequence: Input, Draft, Validation, Lock, Output.
* Do not rename any stage.
* Do not reorder any stage.
* Do not insert stages between existing stages.
* Do not remove any stage.
* Do not introduce multi-pass execution.
* Do not introduce async execution.
* Do not introduce concurrency.
* Do not introduce multi-agent systems.
* Do not introduce persona routing.
* Do not introduce enterprise features.
* Do not introduce network connectivity.
* Do not introduce model selection or multi-model routing.
* Do not speculate beyond constraint-capture, constraint-persistence, and constraint-reuse.
* Do not define UI changes beyond additive display elements.
* Do not replace any existing module.
* Do not redefine any existing module's behavior.
* Do not introduce implicit retries, fallbacks, or recovery loops.
* Do not introduce bypass paths around any stage.
* Halt immediately if any requirement cannot be satisfied without violating the ESD.
* Halt immediately if any section contradicts another section of this spec.
* Halt immediately if any additive module would alter the output of the existing pipeline when no constraints are loaded.

Regression invariant — this is the master constraint:
With an empty Constraint Library and no persisted state, the augmented system must produce byte-identical behavior to the ESD baseline for every input. If this invariant cannot be preserved, the architecture is invalid.

Failure semantics:
If any new module fails (constraint loading, compilation, persistence, artifact ingestion), the pipeline must execute as if that module does not exist. Failure in additive modules must never block, alter, or delay the existing pipeline. The fallback is always the ESD baseline — there is no other fallback.

Required output sections, in this exact order. Do not add sections. Do not remove sections. Do not reorder sections:

1. TRAS Title
2. TRAS Version
3. Purpose
4. Canonical Baseline
5. Architecture Principles
6. Execution Invariants
7. Pipeline Injection Points
8. New Modules
9. Augmented Runtime Flow
10. Storage Model
11. Constraint Lifecycle
12. Migration Boundaries
13. Phased Implementation Order
14. Non-Goals
15. Acceptance Statement

Section requirements:

**Purpose**

* State that TRAS defines additive architecture only.
* State that ESD remains canonical for current executable behavior.
* State that TRAS does not redefine, replace, or extend the ESD.

**Canonical Baseline**

* State that ESD v1.2.1-ESD-1 is the sole source of truth for the current system.
* State that current executable behavior must not be redefined in this document.
* State that any conflict between TRAS and ESD is an error in TRAS.

**Architecture Principles**

Define principles for:

* Additive layering: new modules attach around, not inside, existing pipeline stages.
* Deterministic execution: same input and same constraint set must produce the same outcome.
* No baseline mutation: existing stage logic, order, and pass/block semantics are immutable.
* No hidden fallback behavior: if a new module fails, the pipeline executes the ESD baseline. No silent recovery. No alternative paths.
* Explicit constraint handling: every constraint must be explicitly loaded, compiled, and traceable. No implicit or ambient constraints.
* Single-pass preservation: one request, one traversal, no iteration, no feedback loops within a request.
* Failure transparency: all failures in additive modules must be observable (logged or reported), never silent.

**Execution Invariants**

Explicitly preserve — these are non-negotiable:

* Input → Draft → Validation → Lock → Output. Fixed. Always.
* No stage may be skipped, inserted, reordered, renamed, or removed.
* Each stage produces pass or block. Block halts the pipeline for that request.
* Execution is synchronous and single-threaded.
* Execution is single-pass. One request, one traversal.
* Deterministic governed flow for a given input and constraint set.
* No runtime reordering.
* No implicit retries.
* No architecture-level bypass path.
* No stage may be replaced by a wrapper that changes its pass/block logic.

**Pipeline Injection Points**

Define only additive attachment points for:

* Pre-Input: constraint loading (before Input stage; must not alter input text; must not block pipeline; failure falls back to empty constraint set)
* Post-Input / Pre-Draft: artifact ingestion (after Input produces ExecutionRequest, before Draft; must not modify ExecutionRequest.input; must not block pipeline)
* Validation expansion: constraint-aware validation (additive checks after the existing non-empty check; existing check must always execute first; if no constraints loaded, validation is identical to ESD baseline)
* Post-Outcome: rejection capture (after pipeline outcome; read-only observation; must not alter outcome; must not retry)
* Post-Outcome: persistence writeback (after rejection capture; must not alter displayed result; must not delay result beyond synchronous acceptability; failure does not affect pipeline outcome)

Constraints on injection points:

* Do not alter stage order.
* Do not rename stages.
* Do not replace existing stages.
* Do not insert new stages between existing stages.
* Injection points are outside the five-stage boundary, not inside it — with the sole exception of validation expansion, which adds checks after the existing check, never before or instead of it.

**New Modules**

Define exactly these modules — no more, no fewer:

* Rejection Capture Layer
* Constraint Library
* Artifact Ingestion Layer
* Constraint Compiler
* Persistence Layer

For each module, define:

* Purpose (what it does)
* Inputs (what it receives)
* Outputs (what it produces)
* Interaction boundary (how it connects to the existing pipeline)
* Must-not list (what it is explicitly forbidden from doing)

Every module must-not list must include at minimum:

* Must not alter any existing stage's pass/block logic.
* Must not modify ExecutionRequest.input or DraftOutput.text.
* Must not introduce network calls.
* Must not introduce async behavior.

**Augmented Runtime Flow**

Describe the additive single-pass runtime flow showing:

* Constraint loading occurs before Input. If loading fails, pipeline proceeds with empty constraint set.
* Input, Draft, Lock, Output execute exactly as defined in the ESD. No change.
* Validation executes the existing non-empty check first. If a compiled constraint set is present, additional checks execute after. If no constraints are loaded, validation is identical to ESD baseline.
* Rejection capture occurs after the pipeline outcome. It is read-only.
* Persistence writeback occurs after rejection capture. It is a side effect.
* The five-stage pipeline is unmodified. Pre-processing and post-processing attach around it.

This must remain a single-pass architecture. State this explicitly.

**Storage Model**

Define durable storage for:

* Rejection logs (append-only, keyed by request ID and timestamp)
* Constraint artifacts (keyed by constraint ID)
* Compiled constraint cache (keyed by content hash of active constraint set, invalidated on any constraint change)

Explicitly state:

* What is persisted (rejection logs, constraint artifacts, compiled cache)
* What remains transient (StateStore, telemetry buffer, ExecutionRequest, DraftOutput, LockedOutput, CompiledConstraintSet — all per-invocation, in-memory only, as defined in the ESD)
* What keys or indexes are required
* What is out of scope (session state, undo/redo, multi-user coordination, remote storage, encryption, database engines)
* Storage is local filesystem structured files only.

**Constraint Lifecycle**

Define exactly six lifecycle states — no more, no fewer:

1. Rejection event — raw evidence from a pipeline block
2. Articulated constraint — human-authored rule statement linked to a rejection event
3. Candidate constraint — structured definition with type, expression, and block reason
4. Approved constraint — explicitly approved for inclusion in the Constraint Library
5. Compiled constraint — deterministically compiled from an approved definition
6. Runtime reuse — loaded into CompiledConstraintSet and evaluated during Validation

Transitions are forward-only within a single lifecycle. No automatic promotion from candidate to approved. Approval is an explicit act. Do not invent approval workflows beyond stating that approval is required and explicit.

**Migration Boundaries**

Define:

* What existing modules remain untouched (list every module from the ESD and state it is unchanged)
* What modules may be extended (list only validator and orchestrator; state that extension is additive wrapping, not internal modification)
* Where wrappers or adapters may be added (pipeline_runner wrapper around orchestrator::run; constraint_validator adapter that delegates to existing validator::validate first)
* What must remain behaviorally identical to the ESD (everything, when no constraints are loaded)
* State the regression invariant again in this section.

**Phased Implementation Order**

Use exactly these three phases — no more, no fewer:

Phase 1: Capture Only
* Objective: observe and record pipeline rejections as a post-outcome side effect.
* Modules: Rejection Capture Layer, Persistence Layer (write path only).
* Unchanged: all five stages, all pass/block logic, all UI behavior.
* Invariant: pipeline output is identical to ESD baseline.

Phase 2: Persistence and Reuse
* Objective: introduce Constraint Library, Constraint Compiler, Artifact Ingestion Layer. Enable constraint lifecycle from definition through runtime evaluation.
* Modules: Constraint Library, Constraint Compiler, Artifact Ingestion Layer, Persistence Layer (read and write), Validation Expansion.
* Unchanged: Input, Draft, Lock, Output. Existing non-empty validation check. Mocked LLM. Synchronous single-pass execution. UI layout.
* Invariant: with empty Constraint Library, behavior is identical to Phase 1 and to ESD baseline.

Phase 3: Deterministic Enforcement Expansion
* Objective: expand constraint expressiveness (pattern matching, length bounds, required terms, forbidden terms, structural checks). Enrich rejection metadata.
* Modules: Constraint Compiler (expanded types), Constraint Library (expanded schema), Rejection Capture Layer (richer metadata), Artifact Ingestion Layer (structured parsing).
* Unchanged: Input, Draft, Lock, Output. Stage order. Pass/block semantics. Synchronous single-pass execution. Existing non-empty validation check. Mocked LLM.
* Invariant: with empty Constraint Library, behavior is identical to ESD baseline.

**Non-Goals**

Explicitly forbid all of the following. Each item is a hard prohibition, not a deferral:

* Architecture redesign
* Changing the ESD
* Replacing the validator
* Replacing the orchestrator
* Replacing any existing module
* Async refactor
* Concurrency introduction
* Multi-model routing
* Persona routing
* Multi-agent execution
* Enterprise control planes
* UI redesign
* Network connectivity
* Remote storage
* Speculative future platform expansion
* Any feature not directly required for constraint capture, persistence, or reuse

**Acceptance Statement**

State that the TRAS is valid if and only if:

* It preserves the ESD v1.2.1-ESD-1 baseline in full.
* It defines additive architecture only.
* It does not alter runtime invariants.
* It creates a safe, phased path toward constraint capture, persistence, and reuse — and nothing else.
* The regression invariant holds: empty Constraint Library produces ESD-identical behavior.
* No section contradicts any other section.
* No section contradicts the ESD.

Output constraints:

* Output only the completed architecture spec.
* No code.
* No commentary before or after the spec.
* No implementation steps outside the phased architecture order.
* No explanations outside section content.
* No tables unless strictly necessary for clarity.
* No aspirational features outside the defined scope.
* No restatement of this prompt.
* If any requirement cannot be met, halt and state which requirement and why. Do not produce a partial spec.
