# 00B_EXECUTION_MODE

Version: 1.0
Status: Required

## Supported Modes

### single_agent
One builder agent performs all tasks directly.
Retained only for compatibility.

### sub_agent_orchestrated
One Main Builder Agent plans, routes, validates, and merges.
Sub-agents execute bounded tasks only.

## Active Mode for This Package

`sub_agent_orchestrated`

## Mode Lock Rules

- One execution mode per build session
- No mid-session mode switching
- No hybridized merge authority
- No implicit reversion to single-agent behavior

## Consequences of Violation

If mode drift is detected:
- halt active task acceptance
- mark session invalid
- require explicit restart under a single declared mode

## Rationale

This pack exists to support actual build execution by sub-agents while preserving deterministic main-agent authority.
