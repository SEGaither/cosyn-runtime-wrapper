# Artifact 6 — UI + LLM Integration

Version: 1.1
Status: Hardened Final

## 1. Objective
Specify the single desktop UI and single LLM integration path.

## 2. Locked UI Architecture
UI framework is fixed to:
- `Tauri v2`

No alternative UI framework is permitted.

Window model:
- single main window
- no hidden admin console
- no web-hosted control surface

Fixed panels:
- Request Panel
- Artifact Progress Panel
- Validation Evidence Panel
- Logs Panel
- Package Output Panel

## 3. UI States
| State | Description |
|---|---|
| Booting | app launching |
| ConfigBlocked | config invalid or missing |
| Ready | config valid, no active run |
| Running | pipeline in progress |
| Failed | run halted on failure |
| Complete | package emitted |

## 4. User Inputs
- build mode selector
- operator prompt
- artifact scope selector
- run button
- retry failed stage button
- open logs button
- open package folder button

Rules:
- `CanonicalBuild` auto-selects artifacts 1–14 and disallows edits removing required ids.
- Run button disabled unless local prechecks pass.
- Locked artifacts are read-only in the UI.

## 5. Locked LLM Client Contract
API:
- OpenAI Responses API
- HTTP client: `reqwest`
- JSON parse: `serde_json`

### Request construction
1. Load API key from `C:\.rtw\cosyn-runtime-wrapper\API\cosign.config.json`
2. Build exact POST request to `https://api.openai.com/v1/responses`
3. Add headers:
   - `Authorization: Bearer <key>`
   - `Content-Type: application/json`
4. Send JSON body:
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

### Fallback construction
Fallback request repeats the same body with only:
- `model: "gpt-5.4-mini"`

Fallback allowed only for:
- network transport failure,
- timeout,
- HTTP 5xx.

### Response handling
- Accept structured or text result.
- Extract final text payload.
- Reject empty or ambiguous content.
- Validate against stage requirements before committing state.

## 6. Prompt Construction Rules
Each stage prompt must include:
- artifact identifier,
- artifact objective,
- upstream locked dependencies,
- stage objective,
- required sections for that artifact and stage,
- forbidden behaviors:
  - placeholders,
  - stage skipping,
  - packaging claims,
  - omitted validation evidence.

## 7. UI-to-Orchestrator Data Flow
1. Operator enters request.
2. UI performs local field validation.
3. UI submits to `InputGate`.
4. `Orchestrator` begins stage execution.
5. Progress panel updates from persisted state.
6. Errors surface immediately with code and recovery path.
7. On completion, package output panel exposes zip path.

## 8. Failure Conditions
| Condition | Handling |
|---|---|
| UI attempts exact current-interface guidance without screenshot evidence | label as inferred or block deterministic guidance |
| Operator edits locked artifact manually through UI | deny and surface immutability message |
| LLM returns content without required sections | validation fail |
| Network unavailable | model failure, fallback branch or halt |
| Fallback disabled and primary transport fails | halt with `MODEL_PRIMARY_UNAVAILABLE` |

## 9. Concrete UI Command Surface
Tauri command functions:
```rust
#[tauri::command]
fn load_runtime_status() -> Result<UiRuntimeStatus, UiCommandError>;

#[tauri::command]
async fn submit_execution_request(req: ExecutionRequest) -> Result<RunStartAck, UiCommandError>;

#[tauri::command]
async fn retry_failed_stage(request_id: String) -> Result<RetryAck, UiCommandError>;

#[tauri::command]
fn open_logs_folder() -> Result<(), UiCommandError>;

#[tauri::command]
fn open_package_folder() -> Result<(), UiCommandError>;
```

## 10. Real Scenario
Operator starts canonical build. Artifact 3 Draft request is sent to `gpt-5.4`. Transport fails. App logs event, sends explicit fallback request to `gpt-5.4-mini`, validates the returned content, persists the result, and surfaces a visible fallback badge in the run details.

## 11. Definition of Done
- Single UI path explicit
- Single LLM path explicit
- OpenAI request construction fixed
- Auth load path fixed
- integration failure conditions and UX behavior defined