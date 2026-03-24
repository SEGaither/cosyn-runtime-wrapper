# Artifact 10 — Trinity Binding Specification

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define how the runtime binds and enforces the governance trinity and canonical context.

## 2. Bound Authorities
1. Canonical Context File v1.0
2. CGS v14.0.2
3. Persona Governor v2.4.2
4. Stack Architect v2.3.2

Precedence:
platform/system safety > canonical context > CGS > Governor > Architect > runtime modules

## 3. Binding Inputs
- canonical context document
- CGS markdown
- Governor markdown
- Architect markdown

## 4. Binding Procedure
1. Load canonical context.
2. Validate required sections:
   - binding decisions
   - execution contract
   - workflow definition
   - hardening rules
   - definition of done
   - scope lock
3. Load trinity documents and verify declared version compatibility.
4. Materialize runtime binding snapshot.
5. Freeze snapshot for current request.

## 5. Binding Snapshot Schema
```json
{
  "canonical_context_version": "1.0",
  "cgs_version": "14.0.2",
  "governor_version": "2.4.2",
  "architect_version": "2.3.2",
  "artifact_scope_lock": [1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "stage_order": [
    "Draft",
    "Refinement",
    "DepthEnforcement",
    "Validation",
    "DefinitionOfDone",
    "Lock"
  ],
  "single_llm_only": true,
  "single_ui_only": true,
  "ui_framework": "Tauri v2",
  "http_client": "reqwest 0.12"
}
```

## 6. Enforcement Rules
| Rule ID | Requirement | Failure Condition |
|---|---|---|
| TB-001 | exact stage order enforced | stage skip or reorder |
| TB-002 | artifact scope fixed to 1–14 in canonical build | addition/removal/deviation |
| TB-003 | single LLM only | multiple concurrent model paths |
| TB-004 | single UI only | additional interface surface |
| TB-005 | package only after all DoD checks pass | premature package attempt |
| TB-006 | placeholder artifacts forbidden | placeholder token detected |
| TB-007 | locked UI framework is Tauri v2 | runtime or build references alternate UI |
| TB-008 | locked transport crate is reqwest 0.12 | alternate HTTP client used in authoritative path |

## 7. Conflict Handling
- If canonical context conflicts with reference-only files, canonical wins.
- If trinity versions incompatible, halt binding.
- If canonical context missing required section, halt.
- If artifact content conflicts with binding snapshot, artifact fails validation.

## 8. Semantic Hash Rule
Binding documents are normalized before semantic hash by:
- trimming trailing whitespace,
- normalizing line endings to LF,
- collapsing repeated blank lines for hash only.
Raw file content remains unchanged on disk.

## 9. Validation Scenario
Load canonical context and trinity files with matching versions. Verify snapshot creation and rule activation. Attempt stage reorder. Expected result: `TB-001` fail and execution blocked.

## 10. Definition of Done
- binding snapshot explicit
- compatibility and conflict logic explicit
- hardening lock values propagated
- translatable into runtime enforcement code