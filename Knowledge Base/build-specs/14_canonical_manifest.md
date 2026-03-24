# Artifact 14 — Canonical Manifest

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define the machine-readable and human-readable manifest for the final build package.

## 2. Manifest Schema
```json
{
  "package_name": "Cosign_Build_Artifacts_1-14.zip",
  "manifest_version": "1.1",
  "generated_utc": "ISO8601",
  "artifact_scope": [1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "stage_order": [
    "Draft",
    "Refinement",
    "DepthEnforcement",
    "Validation",
    "DefinitionOfDone",
    "Lock"
  ],
  "artifacts": [
    {
      "artifact_id": 1,
      "name": "Core Build Specification",
      "path": "artifacts/01_core_build_specification.md",
      "sha256": "HEX",
      "locked": true
    }
  ],
  "validation_evidence": [
    {
      "artifact_id": 1,
      "path": "validation/01_evidence.json",
      "status": "passed"
    }
  ],
  "golden_tests": {
    "status": "passed",
    "suite_ids": ["G-001","G-002","G-003","G-004","G-005","G-006"]
  },
  "package_inventory_verified": true
}
```

## 3. Required Manifest Fields
- package name
- version
- timestamp
- artifact scope
- stage order
- artifact entries
- validation evidence entries
- golden test summary
- package verification flag

## 4. Generation Logic
1. read locked artifact directory `./runtime/artifacts/`
2. compute SHA-256 checksums for artifacts 1–14
3. read validation evidence statuses from `./runtime/validation/`
4. read golden test outcomes
5. assemble manifest object
6. write `./runtime/manifest/canonical_manifest.json`
7. write `./runtime/manifest/canonical_manifest.md`
8. use manifest as authoritative package inventory basis

## 5. Human-Readable Summary Requirements
`canonical_manifest.md` must include:
- package name
- generated timestamp
- artifact table with id, path, checksum, locked status
- validation evidence table
- golden suite summary
- package verification result

## 6. Failure Conditions
| Condition | Result |
|---|---|
| Missing artifact entry | fail manifest |
| Missing checksum | fail manifest |
| Artifact not locked | fail manifest |
| Golden tests not passed | fail manifest |
| Inventory verification false | fail package finalization |

## 7. Edge Cases
| Case | Handling |
|---|---|
| Duplicate artifact ids | fail manifest build |
| Artifact file missing after lock | fail and require rerun |
| Validation evidence file absent | fail manifest |
| Manifest JSON write partial | fail and retry only on explicit rerun |

## 8. Validation Scenario
Create manifest from all locked artifacts and evidence files, then cross-check zip inventory and checksums after packaging.
Expected result: manifest and zip agree exactly.

## 9. Definition of Done
- manifest schema complete
- generation logic explicit
- package verification bound to manifest
- human-readable and machine-readable outputs both required