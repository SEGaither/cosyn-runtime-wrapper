# Artifact 5 — Logging & Telemetry

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define deterministic runtime logging and telemetry storage.

## 2. Logging Principles
- Append-only
- Structured
- Local-first
- No mutation of historical entries
- High-signal event names
- Correlatable by request id and artifact id

## 3. Exact Log Streams
| Stream | Format | Path Pattern | Purpose |
|---|---|---|---|
| runtime.jsonl | JSONL | `./runtime/logs/YYYY/MM/DD/runtime.jsonl` | stage transitions and system events |
| error.jsonl | JSONL | `./runtime/logs/YYYY/MM/DD/error.jsonl` | failures only |
| audit.jsonl | JSONL | `./runtime/logs/YYYY/MM/DD/audit.jsonl` | consistency, manifest, package evidence |
| ui.log | text | `./runtime/logs/YYYY/MM/DD/ui.log` | non-authoritative rendering/debug |

## 4. Required Runtime Event Schema
```json
{
  "timestamp_utc": "ISO8601",
  "sequence": 1,
  "request_id": "UUID",
  "event_type": "stage_transition",
  "artifact_id": 5,
  "stage": "Validation",
  "status": "passed",
  "duration_ms": 184,
  "details": {
    "content_path": "runtime/artifacts/05_logging_telemetry.md"
  }
}
```

## 5. Required Telemetry Metrics
Governance-aligned metrics:
- request_sequence
- personas_invoked
- synthesis_mode
- gate_triggers_fired
- halt_triggered
- halt_reason_code
- rerender_requested
- provisional_labeling_count
- assumption_block_present
- numeric_claims_count
- numeric_claims_with_basis_count
- scope_violation_flags
- ui_visual_reference_present
- ui_schema_inference_used
- ui_screenshot_requested
- ui_schema_drift_detected
- ui_clickpath_deterministic_requested
- ui_clickpath_deterministic_blocked

Additional product metrics:
- config_load_ms
- binding_resolve_ms
- input_gate_ms
- model_request_ms
- validator_ms
- manifest_ms
- package_ms
- artifact_success_count
- artifact_failure_count
- locked_artifact_count

## 6. Event Types
- `startup`
- `config_loaded`
- `binding_resolved`
- `input_gate_passed`
- `input_gate_blocked`
- `stage_started`
- `stage_completed`
- `stage_failed`
- `model_fallback`
- `consistency_passed`
- `consistency_failed`
- `golden_passed`
- `golden_failed`
- `manifest_written`
- `package_gate_passed`
- `package_created`
- `package_failed`

## 7. Storage Rules
- Daily rotation by UTC date.
- Parent directories created before write.
- Each JSONL line must be valid standalone JSON object.
- Failed write is mirrored to in-memory ring buffer and surfaced in UI.
- Sequence counter is monotonic per request.

## 8. Privacy Rules
- Default export anonymizes absolute paths to basenames.
- API keys never logged.
- Raw model payload logging disabled by default.
- Optional diagnostic payload capture must redact secrets.

## 9. Audit Event Examples
### 9.1 Fallback event
```json
{
  "event_type": "model_fallback",
  "request_id": "UUID",
  "artifact_id": 2,
  "reason": "MODEL_PRIMARY_UNAVAILABLE",
  "from_model": "gpt-5.4",
  "to_model": "gpt-5.4-mini"
}
```

### 9.2 Packaging gate pass
```json
{
  "event_type": "package_gate_passed",
  "request_id": "UUID",
  "locked_artifact_count": 14,
  "golden_tests_passed": true,
  "manifest_present": true
}
```

## 10. Validation Fixture
Fixture input:
- request id: fixed UUID `11111111-1111-1111-1111-111111111111`
- artifact id: `5`
- stage: `Validation`
Expected:
- exactly one `stage_started`
- exactly one `stage_completed`
- matching request id and artifact id
- `duration_ms >= 0`
- `sequence` increments by one

## 11. Definition of Done
- Event schemas explicit
- Metrics complete
- Secret handling defined
- Storage and rotation rules deterministic
- Concrete fixture available for implementation tests