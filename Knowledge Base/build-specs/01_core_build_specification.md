# Artifact 1 — Core Build Specification

Version: 1.1
Status: Hardened Final
Authority Basis: Canonical Context v1.0; CGS v14.0.2; Persona Governor v2.4.2; Stack Architect v2.3.2; Hardening Prompt v1.0

## 1. Purpose
Define the full build target for Cosign as a local Rust desktop GUI application using one locked desktop UI framework and one locked LLM integration path through the OpenAI Responses API.

## 2. Binding Constraints
| Field | Value |
|---|---|
| Application type | Local desktop GUI |
| Language | Rust 1.82+ |
| Cargo edition | 2021 |
| UI framework | Tauri v2 |
| UI count | Exactly 1 |
| LLM count | Exactly 1 |
| Primary model | gpt-5.4 |
| Fallback model | gpt-5.4-mini |
| API family | OpenAI Responses API |
| HTTP client | reqwest 0.12.x |
| JSON crates | serde 1.x + serde_json 1.x |
| Async runtime | tokio 1.x |
| ZIP crate | zip 2.x |
| Checksum crate | sha2 0.10.x |
| UUID crate | uuid 1.x |
| Auth source | `C:\.rtw\cosyn-runtime-wrapper\API\cosign.config.json` |
| Auth schema | `{ "openai_api_key": "STRING" }` |

## 3. Product Objective
Provide a deterministic, governed desktop operator for a single-user workflow that:
1. accepts structured task input,
2. validates it against contract-first schemas,
3. routes it through a single governed execution pipeline,
4. invokes exactly one model path at a time,
5. records full telemetry and error state locally, and
6. blocks invalid state from contaminating downstream execution.

## 4. Non-Goals
- No browser UI
- No cloud-hosted UI
- No egui, iced, or alternative desktop UI
- No multi-model orchestration
- No hidden retries
- No speculative recovery
- No packaging before all validation gates pass
- No placeholder views or stubbed artifacts in release mode

## 5. Locked Runtime Components
| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `ui::tauri_shell` | Window lifecycle, commands, panel state | User actions | View state changes |
| `config::loader` | Load and validate auth config | Fixed filesystem path | `AppConfig` or `ConfigError` |
| `input_gate::engine` | Validate task spec and operator selections | `ExecutionRequest` | `ValidatedExecutionRequest` or `InputGateError` |
| `binding::resolver` | Load canonical context and trinity snapshot | bound file paths | `BindingSnapshot` or `BindingError` |
| `orchestrator::engine` | Stage sequencing and state locks | `ValidatedExecutionRequest` | ordered `ExecutionResult` set |
| `llm::responses_client` | Single Responses API invocation path | `ResponsesEnvelope` | `ModelOutput` or `ApiError` |
| `validator::engine` | Stage and artifact evidence validation | artifact content + fixture | pass/fail evidence |
| `telemetry::writer` | Structured append-only audit events | runtime events | JSONL log entries |
| `manifest::builder` | Assemble authoritative package manifest | locked artifact set | manifest JSON + summary MD |
| `packaging::zipper` | Persist output bundles and verify archive | finalized artifacts + manifest | zip file on disk |

## 6. Build Targets
| Target | Required |
|---|---|
| Windows x64 desktop build | Yes |
| Debug profile | Yes |
| Release profile | Yes |
| Offline startup without execution | Yes |
| Online execution after auth validation | Yes |
| Tauri desktop bundle | Yes |
| Non-Windows target parity | Not in scope |

## 7. Required Functional Capabilities
### 7.1 Configuration bootstrap
- Load config file from the bound auth path only.
- Parse JSON with exact operative schema.
- Reject startup execution if key missing or malformed.
- Permit UI startup in blocked state so operator can inspect failure.

### 7.2 Task intake
- Accept task title, scope, structured payload, execution options, and packaging target.
- Enforce artifact scope lock to 1–14 when build mode is `CanonicalBuild`.

### 7.3 Stage pipeline
Required stages, in this exact order:
1. Draft
2. Refinement
3. DepthEnforcement
4. Validation
5. DefinitionOfDone
6. Lock

No stage may be skipped.
No combined single-pass execution allowed.

### 7.4 Validation
Validation must include:
- schema conformance,
- exact fixture execution,
- full data flow trace,
- explicit failure conditions,
- definition-of-done check,
- consistency check against all prior artifacts.

### 7.5 Packaging
Packaging may execute only when:
- all artifacts 1–14 exist,
- all artifacts are locked,
- no artifact contains placeholder markers,
- all consistency checks pass,
- manifest JSON and manifest summary MD are generated,
- golden tests pass.

## 8. Quality Attributes
| Attribute | Requirement |
|---|---|
| Determinism | Same inputs produce materially identical outputs excluding timestamp and UUID fields |
| Auditability | Every stage logged with timestamp, stage, result, reason |
| Containment | Invalid state blocks downstream execution |
| Recoverability | Failures are explicit and resumable from valid checkpoint |
| Locality | Data stored locally unless sent to OpenAI API as request payload |
| Traceability | Each artifact references upstream governing constraints |

## 9. Release Definition
A release build is valid only if:
- all modules compile,
- canonical manifest matches artifact outputs,
- golden end-to-end tests pass,
- package zip includes artifacts 1–14 and manifest,
- telemetry schema version matches runtime code,
- zip inventory verifies against manifest checksums.

## 10. Filesystem Layout
Workspace root is the current working directory of the binary. Relative runtime directories are fixed:
- `./runtime/artifacts/`
- `./runtime/validation/`
- `./runtime/logs/YYYY/MM/DD/`
- `./runtime/state/`
- `./runtime/manifest/`
- `./dist/Cosign/`
- `./dist/Cosign_Build_Artifacts_1-14.zip`

## 11. Real Scenario
Scenario: operator launches Cosign, loads valid auth config, selects `CanonicalBuild`, enters a request requiring generation of artifacts 1–14, and runs pipeline.
Expected result:
- stages execute incrementally,
- each artifact reaches lock state,
- validation evidence is captured,
- manifest files are emitted,
- zip package is emitted as final product.

## 12. Definition of Done
- Platform, stack, and API path locked
- One UI framework selected and propagated
- All operative crates named
- No unstated dependencies
- Directly translatable into Rust modules
- Supports downstream interface, fixture, and packaging specification