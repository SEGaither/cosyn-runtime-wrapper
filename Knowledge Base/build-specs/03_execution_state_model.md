# Artifact 3 — Execution & State Model

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define deterministic execution ordering, state machine behavior, checkpointing rules, and restart semantics.

## 2. Global Execution Order
1. Startup
2. Config validation
3. Trinity binding resolution
4. Input gate
5. Artifact loop (1–14 ascending)
6. Per-artifact stage loop
7. Cross-artifact consistency
8. Golden tests
9. Manifest generation
10. Packaging
11. Final lock summary

## 3. Artifact State Machine
```text
Pending
  -> Drafted
  -> Refined
  -> DepthEnforced
  -> Validated
  -> DoneConfirmed
  -> Locked
```

Failure branches:
```text
Any active state -> Failed(stage_code)
Failed(stage_code) -> RetriablePending (only if recoverable and operator reruns)
Failed(stage_code) -> Aborted (if unrecoverable or operator cancels)
```

## 4. Stage Transition Rules
| From | To | Condition |
|---|---|---|
| Pending | Drafted | Draft stage passed |
| Drafted | Refined | Refinement passed |
| Refined | DepthEnforced | DepthEnforcement passed |
| DepthEnforced | Validated | Validation evidence passed |
| Validated | DoneConfirmed | DefinitionOfDone passed |
| DoneConfirmed | Locked | checksum written and immutability set |

## 5. Prohibited Transitions
- Pending -> Validated
- Drafted -> Locked
- Failed -> Locked
- Locked -> any mutable state without explicit unlock authority
- Any stage skip through batch completion flag
- Any artifact with lower id starting after later id has begun in canonical mode

## 6. Orchestration Logic
Pseudologic:
1. Validate config and binding.
2. Validate request.
3. For `artifact_id` in ordered scope ascending:
   - initialize record
   - run Draft
   - persist
   - run Refinement
   - persist
   - run DepthEnforcement
   - persist
   - run Validation
   - persist
   - run DefinitionOfDone
   - persist
   - run Lock
   - persist
4. Run cross-artifact consistency validation.
5. Run golden tests.
6. Generate manifest.
7. Package zip.
8. Persist final summary.

## 7. Persistence Model
### 7.1 Snapshot file path
`./runtime/state/<request_id>/snapshot.json`

### 7.2 Per-stage append log
`./runtime/state/<request_id>/transitions.jsonl`

### 7.3 Snapshot schema
Persist after each stage:
- request id
- artifact id
- current state
- current stage
- stage status
- timestamp_utc
- content path
- content checksum if content changed
- error block if failed

## 8. Restart Recovery
On restart:
1. load latest snapshot for request id,
2. verify all locked files still match checksums,
3. identify earliest artifact not in `Locked`,
4. resume from that artifact’s earliest non-passed stage,
5. if any locked checksum mismatch exists, mark request failed and require operator review.

## 9. Depth Enforcement Requirements
Each artifact must include:
- I/O schemas where applicable,
- rule table where behavior branches,
- explicit failure conditions,
- exact execution logic,
- edge cases,
- definition of done.
A missing item is a hard `DEPTH_REQUIREMENT_MISSING` fail.

## 10. Concurrency Model
- Authoritative execution is single-threaded.
- Background threads may update UI render state only.
- No parallel artifact generation.
- No concurrent stage execution for multiple artifacts.

## 11. Packaging Gate Position
Packaging is a terminal action only after:
- all 14 artifacts are `Locked`,
- consistency passes,
- golden tests pass,
- manifest write succeeds.

## 12. Exact Resume Examples
### 12.1 Recoverable failure
Artifact 6 fails `Validation`.
Expected state:
- artifact 1–5 remain `Locked`,
- artifact 6 becomes `Failed(VALIDATION_*)`,
- artifacts 7–14 remain `Pending`,
- rerun resumes at artifact 6 / `Validation`.

### 12.2 Unrecoverable failure
Disk full during lock checksum write.
Expected state:
- current artifact becomes `Aborted`,
- request summary marks unrecoverable,
- new run required after operator correction.

## 13. Definition of Done
- State machine complete
- Illegal transitions identified
- Resume semantics explicit
- Persistence paths fixed
- Packaging gate positioned after all validations