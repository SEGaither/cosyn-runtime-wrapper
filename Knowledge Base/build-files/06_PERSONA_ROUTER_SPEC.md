# 06_PERSONA_ROUTER_SPEC

Version: 3.0
Status: Required

## Purpose

Define persona routing for the implemented runtime and role routing for the build session.

## Runtime Persona Routing

The runtime must support deterministic routing between the bound persona layer and execution pipeline.

Minimum requirements:
- one active persona per turn by default
- no implicit persona carryover unless configured
- no multi-persona synthesis unless explicitly enabled
- routing output must be inspectable

## Build-Time Routing

The Main Builder Agent may route work to the following sub-agent classes only:
- module_builder
- governance_auditor
- test_runner
- packager

## Routing Inputs

Each routing decision must include:
- task_id
- target_role
- scope
- target_files
- prohibited_actions
- return_artifact_format

## Prohibited Routing

- no routing of completion authority
- no routing of merge authority
- no routing of constitutional interpretation authority
- no unspecific "go work on the build" delegation

## Required Router Output

- assigned_role
- routing_basis
- task_contract_id
- authorized_files
- return_deadline_or_step
