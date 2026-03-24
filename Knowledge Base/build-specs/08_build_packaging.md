# Artifact 8 — Build & Packaging

Version: 1.1
Status: Hardened Final

## 1. Objective
Define build process, output layout, exact staging rules, overwrite/versioning behavior, and recovery behavior.

## 2. Build Inputs
- Rust source tree
- Cargo manifest
- config schema docs
- artifacts 1–14 locked
- canonical manifest
- golden test results

## 3. Output Layout
```text
dist/
  Cosign/
    artifacts/
    validation/
    manifest/
    logs/
  Cosign_Build_Artifacts_1-14.zip
  Cosign_Build_Artifacts_1-14.failed.zip.tmp
runtime/
  staging/
    <request_id>/
```

## 4. Build Commands
1. `cargo fmt --check`
2. `cargo clippy --all-targets -- -D warnings`
3. `cargo test`
4. `cargo build --release`
5. run golden suite
6. generate manifest
7. create zip

## 5. Packaging Preconditions
| Check | Must Pass |
|---|---|
| Artifacts 1–14 exist | Yes |
| All artifacts locked | Yes |
| No placeholder markers | Yes |
| Validation evidence exists for each artifact | Yes |
| Golden tests pass | Yes |
| Manifest checksum table complete | Yes |

## 6. Exact Runtime Paths
| Purpose | Path |
|---|---|
| Locked artifacts source | `./runtime/artifacts/` |
| Validation evidence source | `./runtime/validation/` |
| Manifest output | `./runtime/manifest/` |
| Staging root | `./runtime/staging/<request_id>/` |
| Final package root | `./dist/Cosign/` |
| Final zip path | `./dist/Cosign_Build_Artifacts_1-14.zip` |

## 7. Package Contents
- artifact markdown files 1–14 under `artifacts/`
- validation evidence files under `validation/`
- `manifest/canonical_manifest.json`
- `manifest/canonical_manifest.md`
- `README.md`
- optional logs snapshot under `logs/` only when explicitly enabled

## 8. Packaging Logic
1. verify preconditions,
2. remove any prior staging directory for current request,
3. create fresh staging directory,
4. copy locked artifacts,
5. copy validation evidence,
6. copy manifest files,
7. optionally copy logs snapshot,
8. generate package inventory from staging contents,
9. write zip to temporary path `./dist/Cosign_Build_Artifacts_1-14.failed.zip.tmp`,
10. reopen zip and verify inventory count and checksums,
11. atomically rename temporary zip to `./dist/Cosign_Build_Artifacts_1-14.zip`,
12. delete staging directory.

## 9. Overwrite and Versioning Rules
- Existing final zip must never be overwritten in place.
- New zip is written to temporary file first.
- Atomic rename may replace prior final zip only after successful verification.
- If verification fails, prior final zip remains untouched.

## 10. Recovery Behavior
| Failure | Recovery |
|---|---|
| Precondition fail | stop before staging |
| Staging copy fail | delete current staging directory and fail |
| Zip write fail | keep prior final zip, preserve tmp for diagnostics |
| Zip verify fail | delete invalid final candidate, preserve logs, fail |
| Locked artifact checksum mismatch after staging | delete staging and require rerun |

## 11. Validation Scenario
Build temp staging folder with all locked artifacts and manifest, create zip, reopen zip, compare inventory count and checksums against manifest.
Expected result: pass only if exact match.

## 12. Definition of Done
- packaging logic explicit
- filesystem paths fixed
- overwrite/versioning behavior fixed
- recovery behavior fixed
- directly implementable in Rust build pipeline