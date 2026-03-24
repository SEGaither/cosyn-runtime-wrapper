# Artifact 9 — Input Gate Rules

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define all input admissibility checks before any reasoning or execution.

## 2. Required Inputs
| Field | Type | Required |
|---|---|---|
| request_id | UUID | Yes |
| build_mode | enum | Yes |
| artifact_scope | array<int> | Yes |
| operator_prompt | string | Yes |
| allow_packaging | bool | Yes |
| allow_fallback_model | bool | Yes |

## 3. Rule Table
| Rule ID | Condition | Result on Fail |
|---|---|---|
| IG-001 | request_id valid UUID | reject |
| IG-002 | build_mode in allowed enum | reject |
| IG-003 | artifact_scope non-empty | reject |
| IG-004 | all artifact ids in range 1–14 | reject |
| IG-005 | no duplicate artifact ids | reject |
| IG-006 | canonical build requires full ordered set 1–14 | reject |
| IG-007 | operator_prompt non-empty and non-whitespace | reject |
| IG-008 | allow_packaging false forbids package stage | accept with package disabled |
| IG-009 | fallback allowed only if boolean explicit | reject |
| IG-010 | config must be valid before request activation | reject |
| IG-011 | binding snapshot must resolve before request activation | reject |
| IG-012 | operator prompt length must be <= 20000 bytes UTF-8 | reject |

## 4. Execution Logic
1. Parse request.
2. Validate schema.
3. Apply rule table in order.
4. Accumulate all non-dependent failures.
5. If any fail, return blocked result with ordered error list.
6. If pass, issue `ValidatedExecutionRequest`.

## 5. Normalization Rules
- If scope is complete but unordered, sort ascending and add warning.
- Trim leading and trailing whitespace from `operator_prompt`.
- Preserve interior whitespace and line breaks.
- Do not alter request id.

## 6. Failure Schema
```json
{
  "status": "blocked",
  "errors": [
    {
      "code": "IG-004",
      "message": "artifact_scope contains value outside 1-14"
    }
  ],
  "warnings": []
}
```

## 7. Exact Acceptance Fixture
Input:
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
Result:
```json
{
  "status": "accepted",
  "normalized_scope": [1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "warnings": []
}
```

## 8. Edge Cases
| Case | Handling |
|---|---|
| Scope order shuffled but complete | normalize order and warn |
| Scope contains strings instead of ints | reject schema |
| Very long operator prompt | reject if > 20000 bytes UTF-8 |
| Empty prompt with non-empty metadata | reject |

## 9. Definition of Done
- All admissibility rules explicit
- Failure output machine-readable
- Normalization rules explicit
- Upstream gate to all execution clear