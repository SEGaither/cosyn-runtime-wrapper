# 14_COMMAND_TRIGGERS_AND_CONTROL_FLAGS

Version: 3.0
Status: Required

## Purpose

Define command triggers and control flags used by the build tooling and runtime.

## Build Triggers

- instantiate main builder
- set execution mode
- create task contract
- invoke module builder
- invoke governance auditor
- invoke test runner
- invoke packager
- validate returned artifact
- accept merge
- reject merge
- halt build
- emit build complete signal

## Required Flags

- execution_mode
- strict_governance
- telemetry_render
- allow_parallel_non_conflicting_tasks
- package_flat = true
- architecture_target = agnostic

## Trigger Rules

- command triggers must be explicit
- no implicit sub-agent spawning
- no implicit acceptance
- no implicit packaging after failed tests
