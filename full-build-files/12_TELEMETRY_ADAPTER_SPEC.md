# 12_TELEMETRY_ADAPTER_SPEC

Version: 3.0
Status: Required

## Purpose

Capture telemetry without changing primary output behavior.

## Runtime Telemetry Fields

- turn_index
- persona_selected
- gate_triggers_fired
- halt_triggered
- halt_reason_code
- schema_validation_events
- confidence_adjustments

## Build-Time Telemetry Fields

- build_session_id
- main_agent_status
- sub_agent_invoked
- sub_agent_role
- task_id
- target_files
- artifact_returned
- validation_result
- merge_decision
- rejection_reason if any
- completion_state

## Render Policy

Telemetry collection may be on by default.
Telemetry rendering remains optional and should not interfere with core execution.

## Required Build Event Types

- task_created
- task_dispatched
- task_returned
- validation_passed
- validation_failed
- merge_accepted
- merge_rejected
- halt_triggered
- completion_emitted
