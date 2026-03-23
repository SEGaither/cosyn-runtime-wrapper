# 22A_BUILD_COMPLETE_SIGNAL

Version: 1.0
Status: Required

## Purpose

Define the only valid build-complete declaration for this pack.

## Required Preconditions

All of the following must be true:
- all required files exist
- validation records exist for accepted outputs
- no unresolved halt state
- test matrix required cases pass
- acceptance criteria pass
- package manifest and checksums generated

## Authorized Emitter

Only the Main Builder Agent.

## Forbidden Emitters

- module_builder
- governance_auditor
- test_runner
- packager

## Valid Signal Shape

```text
build_complete: true
emitter_role: main_builder_agent
execution_mode: sub_agent_orchestrated
acceptance_status: passed
open_halts: none
```

## Invalid Signal Cases

- missing acceptance_status
- emitted by sub-agent
- emitted while any halt remains active
- emitted before package manifest/checksums exist
