# 06B_SUB_AGENT_TASK_CONTRACT_SCHEMA

Version: 1.0
Status: Required

## Required Fields

Each sub-agent task contract must include:

- task_id
- assigned_role
- objective
- scope_statement
- allowed_files
- prohibited_actions
- required_output_format
- acceptance_checks
- return_to_main_agent = true

## Example Contract Shape

```text
task_id: T-07
assigned_role: module_builder
objective: Draft 07_GOVERNANCE_GATE_ENGINE_SPEC.md
scope_statement: Define enforcement behavior for non-bypassable gates in the RTW implementation layer
allowed_files:
  - 07_GOVERNANCE_GATE_ENGINE_SPEC.md
prohibited_actions:
  - modify acceptance criteria
  - declare build complete
required_output_format:
  - full file body
  - assumptions block if any
  - unresolved issues block if any
acceptance_checks:
  - file addresses required sections
  - no authority inversion
  - returns to main agent
return_to_main_agent: true
```

## Invalid Contract Conditions

A task contract is invalid if it omits:
- allowed_files
- prohibited_actions
- acceptance_checks
- return_to_main_agent

An invalid contract may not be executed.
