# Artifact 13 — Implementation Handoff Pack

Version: 1.1
Status: Hardened Final

## 1. Purpose
Provide implementation-ready handoff guidance for the engineering build.

## 2. Deliverables
- module map
- directory structure
- implementation order
- acceptance checklist
- handoff risks

## 3. Locked Directory Layout
```text
src/
  app/
  binding/
  config/
  errors/
  input_gate/
  llm/
  manifest/
  orchestrator/
  packaging/
  state/
  telemetry/
  ui/
  validator/
tests/
  fixtures/
  unit/
  contract/
  integration/
  system/
  golden/
runtime/
  artifacts/
  validation/
  state/
  manifest/
  logs/
  staging/
dist/
```

## 4. Implementation Order
1. `config::loader`
2. core schemas in `app::types`
3. `binding::resolver`
4. `input_gate::engine`
5. `state::store`
6. `orchestrator::engine`
7. `validator::engine`
8. `telemetry::writer`
9. `llm::responses_client`
10. `ui::tauri_shell`
11. `manifest::builder`
12. `packaging::zipper`
13. golden tests

Reason:
upstream gating and determinism logic must exist before UI convenience and packaging.

## 5. Acceptance Checklist
| Item | Pass Condition |
|---|---|
| Config path enforced | exact path supported |
| Auth schema enforced | exact key required |
| Input rules enforced | all IG rules pass/fail correctly |
| Stage order enforced | no skip possible |
| Artifact lock immutable | post-lock edits blocked |
| Telemetry written | JSONL valid |
| Package gate enforced | package unavailable until all pass |
| UI framework locked | Tauri only |
| API transport locked | reqwest only |

## 6. Risks and Controls
| Risk | Control |
|---|---|
| UI built before orchestration stable | implement core first |
| model fallback hides failures | explicit log + UI badge |
| validation drift across artifacts | centralized validator rules |
| package built from stale files | checksum verification pre-zip |

## 7. Engineering Prohibitions
- do not replace Tauri with another UI framework
- do not replace reqwest in the authoritative Responses API path
- do not add a second model provider
- do not relax packaging gates

## 8. Real Scenario
A new engineer clones repository and follows this pack:
- implement `AppConfig`
- wire config load
- add input gate tests
- implement stage machine
- then connect Tauri UI and OpenAI client
This order prevents inversion where UI permits invalid state.

## 9. Definition of Done
- handoff is implementation-sequenced
- risks and controls explicit
- acceptance checklist actionable
- hardening locks preserved through engineering handoff