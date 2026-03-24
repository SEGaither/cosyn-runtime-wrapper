# Artifact 11 — UI + Project Mode

Version: 1.1
Status: Hardened Final

## 1. Purpose
Define project-mode behavior in the Tauri desktop UI.

## 2. Project Modes
| Mode | Description |
|---|---|
| CanonicalBuild | Full artifact run 1–14 with package eligibility |
| ValidationOnly | Validate selected existing artifacts |
| PackageExisting | Package already locked artifacts only |

## 3. Mode Rules
| Rule ID | Condition | Enforcement |
|---|---|---|
| PM-001 | CanonicalBuild selected | force scope 1–14 |
| PM-002 | ValidationOnly selected | packaging disabled |
| PM-003 | PackageExisting selected | require locked artifacts + manifest |
| PM-004 | active run present | mode selector locked |
| PM-005 | failed canonical run | rerun from earliest failed artifact only |

## 4. UI Controls by Mode
### CanonicalBuild
- build mode selector
- read-only scope display `1–14`
- operator prompt
- run

### ValidationOnly
- artifact picker
- validation scenario selector
- run validation

### PackageExisting
- package destination
- manifest selector
- build package

## 5. Data Contract
```json
{
  "project_mode": "CanonicalBuild",
  "ui_state": "Ready",
  "allowed_actions": ["run"],
  "locked_controls": ["artifact_scope_editor"]
}
```

## 6. Exact Control Behavior
- Scope editor is hidden in `CanonicalBuild`.
- Scope editor is enabled in `ValidationOnly`.
- Package controls are disabled unless mode is `PackageExisting` and manifest passes local precheck.
- Mode selector is disabled while state is `Running`.

## 7. Failure Conditions
| Condition | Result |
|---|---|
| Canonical mode with partial scope | block |
| PackageExisting without manifest | block |
| ValidationOnly with no selected artifacts | block |
| Mode switch mid-run | deny |
| Manual UI mutation of locked artifact | deny |

## 8. Edge Cases
| Case | Handling |
|---|---|
| Restart during failed run | restore previous mode and state |
| Operator loads package mode with stale manifest | fail precheck |
| Locked artifact count less than selection in package mode | reject |

## 9. Real Scenario
Operator switches to `CanonicalBuild`. UI locks scope to 1–14, enables run after prompt entry, and disables packaging controls until run completion.

## 10. Definition of Done
- mode-specific UI behavior explicit
- rule table present
- invalid mode transitions blocked
- terminology aligned with artifacts 1–10