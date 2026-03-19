# 16_STATE_MODEL_AND_SESSION_SPEC

Version: 3.0
Status: Required

## Purpose

Define the minimum state model for an RTW build session and runtime session.

## Build Session State

Required fields:
- build_session_id
- execution_mode
- main_agent_status
- active_plan_step
- active_task_id
- active_sub_agent_role
- queued_tasks[]
- accepted_files[]
- rejected_files[]
- pending_validation[]
- halt_status
- completion_status

## Runtime Session State

Required fields:
- session_id
- loaded_artifacts[]
- active_persona
- active_scope
- gate_state
- confidence_state
- telemetry_state

## State Update Rules

- every delegated task changes state
- every merge decision changes state
- every halt changes state
- completion requires explicit terminal state update
