# Artifact 4 — Error Handling & Failure

Version: 1.1
Status: Hardened Final

## 1. Objective
Define failure taxonomy, containment rules, operator-visible recovery, and exact mapping from runtime fault to code.

## 2. Error Principles
- Error containment before continuation
- No silent retries
- Exact cause over generic message
- Recoverability classification is mandatory
- Upstream failure blocks dependent downstream execution

## 3. Failure Classes
| Class | Meaning | Recoverable |
|---|---|---|
| Config | startup/config/auth failure | Sometimes |
| Binding | canonical/trinity resolution failure | No |
| Input | request invalid | Usually |
| Contract | schema/constraint violation | Usually |
| Model | API/network/response failure | Sometimes |
| Validation | artifact failed evidence gate | Usually |
| Consistency | cross-artifact mismatch | Usually |
| Manifest | manifest build/write failure | Usually |
| Packaging | zip/final assembly failure | Usually |
| System | disk/process/permission fault | Sometimes |

## 4. Canonical Error Codes
| Code | Description | Recoverable |
|---|---|---|
| CONFIG_FILE_NOT_FOUND | auth file absent | false |
| CONFIG_JSON_INVALID | malformed JSON | false |
| CONFIG_API_KEY_EMPTY | key empty | false |
| BINDING_CANONICAL_SECTION_MISSING | required canonical section absent | false |
| BINDING_VERSION_MISMATCH | trinity version incompatibility | false |
| INPUT_SCOPE_INVALID | artifact ids out of range | true |
| INPUT_MODE_INVALID | unsupported build mode | true |
| STAGE_ORDER_VIOLATION | attempted skip or regression | false |
| MODEL_PRIMARY_UNAVAILABLE | primary model transport failure | true |
| MODEL_HTTP_STATUS_ERROR | non-success HTTP status | true |
| MODEL_RESPONSE_INVALID | response cannot be parsed | true |
| MODEL_FALLBACK_UNAVAILABLE | fallback also failed | true |
| DEPTH_REQUIREMENT_MISSING | required depth item absent | true |
| VALIDATION_SCENARIO_INCOMPLETE | scenario missing full data flow | true |
| DOD_FAILED | definition of done failed | true |
| CONSISTENCY_CONFLICT | artifact disagreement detected | true |
| MANIFEST_GENERATION_FAILED | manifest write/build failed | true |
| PACKAGE_PRECONDITION_FAILED | attempted package before gates | false |
| STAGING_COPY_FAILED | staging copy failed | true |
| ZIP_WRITE_FAILED | final zip failed | true |
| ZIP_VERIFY_FAILED | zip unreadable or incomplete | true |
| STATE_WRITE_FAILED | snapshot persistence failed | false |

## 5. Error Record Schema
```json
{
  "timestamp_utc": "ISO8601",
  "request_id": "UUID",
  "artifact_id": 4,
  "stage": "Validation",
  "code": "CONSISTENCY_CONFLICT",
  "message": "Artifact 4 references a retry policy prohibited by Artifact 1.",
  "recoverable": true,
  "operator_action": "Correct artifact content and rerun validation.",
  "details": {
    "upstream_artifact": 1,
    "conflict_field": "no_silent_retry"
  }
}
```

## 6. Containment Rules
1. Config failure blocks execution startup.
2. Binding failure blocks request creation.
3. Input failure blocks artifact execution.
4. Artifact stage failure blocks later stages for same artifact.
5. Any artifact failure blocks subsequent artifacts in the same run.
6. Cross-artifact consistency failure blocks manifest and package.
7. Golden test failure blocks package.
8. Lock failure invalidates artifact completion.

## 7. Recovery Rules
| Failure | Recovery |
|---|---|
| Config path absent | operator fixes file at exact path and reloads |
| Invalid request scope | operator edits scope and resubmits |
| Model transport failure | operator may rerun or allow fallback |
| Validation content gap | regenerate artifact stage and revalidate |
| Consistency conflict | repair conflicting artifacts then rerun consistency |
| Zip write failure | fix destination permissions or space and rerun packaging only if all locks remain valid |

## 8. UI Messaging Requirements
Each surfaced error must show:
- code
- plain message
- stage
- artifact id if applicable
- recoverability
- operator action
- evidence/log reference

## 9. Ordered Error Preference
When multiple errors occur in one stage:
1. preserve full ordered list,
2. first entry is primary blocker,
3. UI surfaces primary blocker first,
4. audit log preserves all remaining blockers.

## 10. Failure Scenarios
### 10.1 Invalid artifact scope
Input `[1,15]`
Expected:
- `INPUT_SCOPE_INVALID`
- no artifact execution begins
- telemetry records blocked run

### 10.2 Responses API parse failure
Server returns JSON lacking extractable content.
Expected:
- `MODEL_RESPONSE_INVALID`
- no state commit for stage output
- fallback not used because content parse failure is not transport failure

### 10.3 Package precondition violation
Operator attempts packaging before golden tests pass.
Expected:
- `PACKAGE_PRECONDITION_FAILED`
- no staging directory creation

## 11. Definition of Done
- Error codes explicit
- Recovery model bounded
- Containment rules prevent cascading corruption
- Mapping from failure to operator action is complete