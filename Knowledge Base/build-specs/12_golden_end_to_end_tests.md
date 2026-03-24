# Artifact 12 — Golden End-to-End Tests

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define canonical end-to-end tests used as final regression gate before packaging.

## 2. Golden Suite Inventory
| Test ID | Name | Required |
|---|---|---|
| G-001 | canonical_full_build_success | Yes |
| G-002 | config_block_startup | Yes |
| G-003 | stage_skip_blocked | Yes |
| G-004 | placeholder_artifact_blocked | Yes |
| G-005 | consistency_conflict_blocks_package | Yes |
| G-006 | fallback_model_logged | Yes |

## 3. Exact Test Specifications
### G-001 canonical_full_build_success
Fixture inputs:
- `tests/fixtures/config_valid.json`
- `tests/fixtures/request_canonical.json`
Expected outputs:
- 14 artifacts locked
- `runtime/manifest/canonical_manifest.json` exists
- `dist/Cosign_Build_Artifacts_1-14.zip` exists
- package inventory matches manifest checksum table

### G-002 config_block_startup
Fixture inputs:
- missing config path `C:\.rtw\cosyn-runtime-wrapper\API\cosign.config.json`
Expected outputs:
- app state `ConfigBlocked`
- no run activation possible

### G-003 stage_skip_blocked
Fixture inputs:
- injected state transition `Draft -> Validation`
Expected outputs:
- `STAGE_ORDER_VIOLATION`
- run halted
- no lock stage event emitted

### G-004 placeholder_artifact_blocked
Fixture inputs:
- `tests/fixtures/artifact_with_todo.md`
Expected outputs:
- validation or DoD fail
- package blocked

### G-005 consistency_conflict_blocks_package
Fixture inputs:
- artifact 1 prohibits silent retry
- artifact 6 implies silent retry
Expected outputs:
- consistency validator fail
- no manifest finalization
- no zip

### G-006 fallback_model_logged
Fixture inputs:
- primary model transport failure
- fallback allowed
Expected outputs:
- fallback event logged
- stage completed on fallback or explicit fail recorded

## 4. Golden Baseline Files
- `tests/golden/expected_manifest.json`
- `tests/golden/expected_package_inventory.json`
- `tests/golden/expected_event_sequence.json`

## 5. Comparison Rules
- compare semantic fields, not volatile timestamps
- ignore run-specific UUIDs in baseline compare
- require exact artifact id set and stage sequence
- normalize path separators and line endings before compare

## 6. Failure Conditions
- missing golden baseline
- extra artifact in package
- absent lock stage event
- baseline compare mismatch beyond allowed volatility

## 7. Definition of Done
- required golden tests explicit
- fixture inputs explicit
- pass criteria unambiguous
- packaging dependency explicit