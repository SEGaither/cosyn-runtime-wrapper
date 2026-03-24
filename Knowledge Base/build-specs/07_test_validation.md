# Artifact 7 — Test & Validation

Version: 1.1
Status: Hardened Final

## 1. Objective
Define test strategy, exact fixtures, expected outputs, and comparison rules for correctness, determinism, and packaging eligibility.

## 2. Test Layers
| Layer | Scope | Required |
|---|---|---|
| Unit | module functions and parsers | Yes |
| Contract | schema and interface boundaries | Yes |
| Integration | module interaction incl. Responses API client | Yes |
| System | full pipeline in desktop runtime | Yes |
| Golden | canonical end-to-end build outputs | Yes |

## 3. Exact Test Fixtures

### 3.1 Config fixture
File: `tests/fixtures/config_valid.json`
```json
{
  "openai_api_key": "sk-test-valid-key"
}
```
Expected:
- parse success
- validation success

### 3.2 Invalid config fixture
File: `tests/fixtures/config_empty_key.json`
```json
{
  "openai_api_key": ""
}
```
Expected:
- `CONFIG_API_KEY_EMPTY`

### 3.3 Canonical request fixture
File: `tests/fixtures/request_canonical.json`
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "build_mode": "CanonicalBuild",
  "artifact_scope": [1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "operator_prompt": "Generate canonical artifact set.",
  "runtime_options": {
    "allow_packaging": true,
    "allow_fallback_model": true
  }
}
```
Expected:
- accepted
- normalized scope unchanged

### 3.4 Invalid scope fixture
File: `tests/fixtures/request_invalid_scope.json`
```json
{
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "build_mode": "CanonicalBuild",
  "artifact_scope": [1,15],
  "operator_prompt": "Generate canonical artifact set.",
  "runtime_options": {
    "allow_packaging": true,
    "allow_fallback_model": true
  }
}
```
Expected:
- blocked
- primary code `INPUT_SCOPE_INVALID`

### 3.5 Placeholder artifact fixture
File: `tests/fixtures/artifact_with_todo.md`
```text
# Artifact
TODO
```
Expected:
- validation or DoD fail
- package blocked

## 4. Unit Tests
- config parser accepts exact auth schema
- input gate rejects out-of-range artifact ids
- stage transition guard rejects skips
- checksum writer produces stable SHA-256

## 5. Contract Tests
- `ExecutionRequest` JSON schema round-trip
- `ArtifactRecord` persistence schema round-trip
- error record serialization/deserialization
- telemetry event required field presence

## 6. Integration Tests
- valid request flows from UI submit to `InputGate` to `Orchestrator`
- model primary failure invokes logged fallback only when enabled
- validation failure prevents lock
- manifest generation blocked until all artifacts locked

## 7. System Tests
### 7.1 Happy path
Given valid config and canonical build request,
when pipeline executes,
then 14 artifacts lock, golden tests pass, manifest emits, zip emits.

### 7.2 Missing config
Given no config file,
when app starts,
then state is `ConfigBlocked` and run controls disabled.

### 7.3 Consistency conflict
Given artifact 1 prohibits silent retry and artifact 6 implies silent retry,
when consistency validation runs,
then conflict error emitted and packaging blocked.

## 8. Determinism Tests
- repeated identical request produces materially equivalent manifest excluding timestamp and UUID
- locked artifact checksums stable across restart
- telemetry order stable for equivalent run

## 9. Validation Evidence Schema
```json
{
  "artifact_id": 7,
  "scenario_name": "happy_path_full_build",
  "preconditions": ["valid config", "canonical scope 1-14"],
  "steps": ["submit request", "run pipeline", "verify locks", "verify package"],
  "expected_results": ["all stages pass", "zip exists"],
  "actual_results": ["PASS"],
  "evidence_refs": ["runtime/logs/runtime.jsonl", "dist/Cosign_Build_Artifacts_1-14.zip"]
}
```

## 10. Comparison Rules
- compare semantic fields only for manifest timestamps and request UUIDs
- normalize path separators before compare
- normalize line endings before compare
- require exact artifact id set and stage sequence
- compare package inventory by manifest checksum table

## 11. Definition of Done
- All test layers defined
- exact fixture inputs defined
- expected outputs explicit
- comparison method explicit
- pass/fail gates package eligibility