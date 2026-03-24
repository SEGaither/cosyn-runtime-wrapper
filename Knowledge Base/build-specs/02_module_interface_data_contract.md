# Artifact 2 — Module Interface & Data Contract

Version: 1.1
Status: Hardened Final

## 1. Objective
Define strict interfaces, schemas, typed boundaries, and file/module contracts for all major runtime modules.

## 2. Locked Cargo Dependencies
| Crate | Version Line | Purpose |
|---|---|---|
| `tauri` | `2` | desktop UI shell |
| `serde` | `1` | serialization |
| `serde_json` | `1` | JSON parsing |
| `reqwest` | `0.12` | OpenAI API transport |
| `tokio` | `1` | async runtime |
| `uuid` | `1` | request identifiers |
| `sha2` | `0.10` | SHA-256 checksums |
| `zip` | `2` | package archive creation |
| `thiserror` | `1` | typed errors |
| `chrono` | `0.4` | UTC timestamps |

## 3. Directory Structure
```text
src/
  main.rs
  app/mod.rs
  app/types.rs
  binding/mod.rs
  binding/resolver.rs
  config/mod.rs
  config/loader.rs
  errors/mod.rs
  input_gate/mod.rs
  input_gate/engine.rs
  llm/mod.rs
  llm/responses_client.rs
  manifest/mod.rs
  manifest/builder.rs
  orchestrator/mod.rs
  orchestrator/engine.rs
  packaging/mod.rs
  packaging/zipper.rs
  state/mod.rs
  state/store.rs
  telemetry/mod.rs
  telemetry/writer.rs
  ui/mod.rs
  ui/commands.rs
  ui/state.rs
  validator/mod.rs
  validator/engine.rs
tests/
  fixtures/
  unit/
  contract/
  integration/
  system/
  golden/
runtime/
dist/
```

## 4. File Naming Convention
- Rust source: snake_case file names
- Artifact markdown: `01_*.md` through `14_*.md`
- Validation evidence JSON: `01_evidence.json` through `14_evidence.json`
- Manifest files: `canonical_manifest.json`, `canonical_manifest.md`
- Log files: `runtime.jsonl`, `error.jsonl`, `audit.jsonl`, `ui.log`

## 5. Core Data Structures

### 5.1 AppConfig
```json
{
  "openai_api_key": "STRING"
}
```
Rules:
- Exact top-level object required.
- Additional keys permitted only if prefixed `x_` and ignored by runtime.
- `openai_api_key` must be non-empty UTF-8 string.

### 5.2 BuildMode
```text
CanonicalBuild | ValidationOnly | PackageExisting
```

### 5.3 ArtifactId
Integer range: 1..14 inclusive

### 5.4 StageName
```text
Draft | Refinement | DepthEnforcement | Validation | DefinitionOfDone | Lock
```

### 5.5 ArtifactRecord
```json
{
  "artifact_id": 1,
  "name": "Core Build Specification",
  "version": "1.1",
  "stage_status": {
    "Draft": "passed",
    "Refinement": "passed",
    "DepthEnforcement": "passed",
    "Validation": "passed",
    "DefinitionOfDone": "passed",
    "Lock": "passed"
  },
  "content_path": "runtime/artifacts/01_core_build_specification.md",
  "validation_evidence_path": "runtime/validation/01_evidence.json",
  "checksum_sha256": "HEX",
  "locked": true
}
```

### 5.6 ExecutionRequest
```json
{
  "request_id": "UUID",
  "build_mode": "CanonicalBuild",
  "artifact_scope": [1,2,3,4,5,6,7,8,9,10,11,12,13,14],
  "operator_prompt": "STRING",
  "runtime_options": {
    "allow_packaging": true,
    "allow_fallback_model": true
  }
}
```

### 5.7 ResponsesEnvelope
```json
{
  "model": "gpt-5.4",
  "input": "STRING_OR_STRUCTURED",
  "metadata": {
    "request_id": "UUID",
    "artifact_id": 1,
    "stage": "Draft",
    "app_version": "1.1.0"
  }
}
```

### 5.8 ExecutionResult
```json
{
  "request_id": "UUID",
  "artifact_id": 1,
  "stage": "Draft",
  "status": "passed",
  "errors": [],
  "warnings": [],
  "output_ref": "PATH_OR_NULL",
  "duration_ms": 0
}
```

## 6. Typed Rust Interfaces

### 6.1 `config::loader`
File: `src/config/loader.rs`

```rust
pub fn load_config(path: &std::path::Path) -> Result<AppConfig, ConfigError>;
pub fn validate_config(config: &AppConfig) -> Result<(), ConfigError>;
```

Inputs:
- fixed config path

Outputs:
- validated `AppConfig`

Error types:
- `ConfigError::FileNotFound`
- `ConfigError::JsonInvalid`
- `ConfigError::ApiKeyEmpty`

### 6.2 `input_gate::engine`
File: `src/input_gate/engine.rs`

```rust
pub fn validate_request(req: ExecutionRequest) -> Result<ValidatedExecutionRequest, InputGateError>;
```

Inputs:
- `ExecutionRequest`

Outputs:
- `ValidatedExecutionRequest`

Error types:
- `InputGateError::InvalidUuid`
- `InputGateError::InvalidBuildMode`
- `InputGateError::EmptyScope`
- `InputGateError::OutOfRangeArtifact`
- `InputGateError::DuplicateArtifact`
- `InputGateError::CanonicalScopeIncomplete`
- `InputGateError::EmptyPrompt`
- `InputGateError::ConfigBlocked`

### 6.3 `binding::resolver`
File: `src/binding/resolver.rs`

```rust
pub fn resolve_binding(snapshot_input: BindingInputPaths) -> Result<BindingSnapshot, BindingError>;
```

Inputs:
- canonical/trinity file paths

Outputs:
- immutable `BindingSnapshot`

Error types:
- `BindingError::CanonicalMissingSection`
- `BindingError::VersionMismatch`
- `BindingError::MissingTrinityFile`
- `BindingError::UnknownStageName`

### 6.4 `state::store`
File: `src/state/store.rs`

```rust
pub fn persist_transition(snapshot: &ExecutionSnapshot) -> Result<(), StateError>;
pub fn load_latest_snapshot(request_id: uuid::Uuid) -> Result<Option<ExecutionSnapshot>, StateError>;
```

Inputs:
- state transition command / request id

Outputs:
- persisted snapshot / loaded snapshot

Error types:
- `StateError::WriteFailed`
- `StateError::ReadFailed`
- `StateError::ChecksumMismatch`
- `StateError::IllegalTransition`

### 6.5 `orchestrator::engine`
File: `src/orchestrator/engine.rs`

```rust
pub async fn run_request(
    req: ValidatedExecutionRequest,
    binding: BindingSnapshot,
    state_store: &StateStore,
    llm_client: &ResponsesClient,
    validator: &Validator
) -> Result<Vec<ExecutionResult>, OrchestratorError>;
```

Inputs:
- validated request
- binding snapshot
- state store
- client
- validator

Outputs:
- ordered execution results

Error types:
- `OrchestratorError::StageFailure`
- `OrchestratorError::ConsistencyFailure`
- `OrchestratorError::GoldenFailure`
- `OrchestratorError::ManifestFailure`
- `OrchestratorError::PackagingFailure`

### 6.6 `llm::responses_client`
File: `src/llm/responses_client.rs`

```rust
pub async fn execute_stage(
    envelope: ResponsesEnvelope,
    api_key: &str,
    allow_fallback: bool
) -> Result<ModelOutput, ApiError>;
```

Inputs:
- `ResponsesEnvelope`
- API key
- fallback flag

Outputs:
- `ModelOutput`

Error types:
- `ApiError::Transport`
- `ApiError::HttpStatus`
- `ApiError::ResponseParse`
- `ApiError::FallbackUnavailable`

### 6.7 `validator::engine`
File: `src/validator/engine.rs`

```rust
pub fn validate_artifact_stage(
    artifact_id: u8,
    stage: StageName,
    content: &str,
    fixture: &ValidationFixture
) -> Result<ValidationEvidence, ValidationError>;
```

Inputs:
- artifact id
- stage
- generated content
- validation fixture

Outputs:
- `ValidationEvidence`

Error types:
- `ValidationError::MissingSchema`
- `ValidationError::MissingRuleTable`
- `ValidationError::ScenarioIncomplete`
- `ValidationError::EdgeCasesMissing`
- `ValidationError::DoDFailed`

### 6.8 `manifest::builder`
File: `src/manifest/builder.rs`

```rust
pub fn build_manifest(records: &[ArtifactRecord], golden: &GoldenSummary) -> Result<CanonicalManifest, ManifestError>;
```

Inputs:
- locked artifact records
- golden suite result

Outputs:
- manifest

Error types:
- `ManifestError::MissingArtifact`
- `ManifestError::MissingChecksum`
- `ManifestError::GoldenFailed`
- `ManifestError::WriteFailed`

### 6.9 `packaging::zipper`
File: `src/packaging/zipper.rs`

```rust
pub fn create_package(
    source_root: &std::path::Path,
    manifest: &CanonicalManifest,
    package_path: &std::path::Path
) -> Result<std::path::PathBuf, PackagingError>;
```

Inputs:
- source root
- manifest
- package path

Outputs:
- zip file path

Error types:
- `PackagingError::PreconditionFailed`
- `PackagingError::StagingCopyFailed`
- `PackagingError::InventoryMismatch`
- `PackagingError::ZipWriteFailed`
- `PackagingError::ZipVerifyFailed`

## 7. OpenAI Request Construction Pattern
- Endpoint: `POST https://api.openai.com/v1/responses`
- Headers:
  - `Authorization: Bearer <openai_api_key>`
  - `Content-Type: application/json`
- Body shape:
```json
{
  "model": "gpt-5.4",
  "input": "stage prompt text",
  "metadata": {
    "request_id": "UUID",
    "artifact_id": 1,
    "stage": "Draft",
    "app_version": "1.1.0"
  }
}
```
- Parse response into `ModelOutput` by:
  1. parse top-level JSON,
  2. extract final text payload,
  3. reject empty or whitespace-only content,
  4. return normalized UTF-8 string.

## 8. Fallback Logic
Fallback to `gpt-5.4-mini` is allowed only when:
- transport connection fails,
- request timeout occurs,
- server returns 5xx,
- gateway returns network-unavailable condition.

Fallback is not allowed for:
- content disagreement,
- validation failure,
- malformed operator prompt,
- schema mismatch caused by local code.

## 9. Definition of Done
- Modules, files, interfaces, and signatures are explicit
- Inputs, outputs, and error types are defined per module
- OpenAI integration concretized
- Directly implementable in Rust without further interface decisions