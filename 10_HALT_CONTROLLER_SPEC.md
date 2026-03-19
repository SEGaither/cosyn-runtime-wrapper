# 10_HALT_CONTROLLER_SPEC

Version: 3.0
Status: Required

## Purpose

Centralize deterministic halt behavior for runtime and build-time violations.

## Halt Categories

### Governance Halt
Triggered when required governance conditions fail.

### Scope Halt
Triggered when work exceeds authorized scope.

### Authority Halt
Triggered when a lower actor attempts higher-authority behavior.

### Integrity Halt
Triggered when artifact integrity checks fail.

### Schema Halt
Triggered when required structured payloads are invalid.

## Agentic Build Halt Triggers

- unauthorized sub-agent action
- sub-agent attempts merge
- sub-agent attempts completion declaration
- conflicting returned artifacts on same file
- invalid or missing task contract
- unresolved cross-file dependency conflict
- acceptance criteria contradiction

## Halt Result

On halt the system must output:
- halt_code
- halt_reason
- affected_files
- blocking_condition
- next_required_action

## Non-Optional Rule

Halts may not be silently ignored or downgraded by sub-agents.
