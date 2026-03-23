# 01_RTW_BUILD_CONTRACT

Version: 3.0
Status: Binding

## Objective

Build the Runtime Wrapper (RTW) as an implementation-layer enforcement system that operationalizes constitutional governance during runtime interaction.

## Execution Contract

The build must be carried out using:
- one Main Builder Agent acting as the choreographer
- bounded Sub-Agents executing assigned task slices
- deterministic validation and merge through the Main Builder Agent only

## Main Builder Agent Authority

The Main Builder Agent holds sole authority for:
- build planning
- task decomposition
- sub-agent invocation
- output acceptance or rejection
- merge decisions
- halting decisions
- build-complete declaration

## Sub-Agent Contract

Sub-agents:
- are non-authoritative
- may execute only bounded tasks
- may not expand scope
- may not self-merge outputs
- may not declare build completion
- must return all work to the Main Builder Agent

## Build Deliverables

The build must produce:
- artifact loader
- persona router
- governance gate engine
- runtime execution layer
- schema validation layer
- halt controller
- confidence enforcer
- telemetry adapter
- evaluation harness
- test matrix
- acceptance criteria

## Package Constraints

- architecture-agnostic
- deterministic
- governance-preserving
- auditable
- no implementation-specific packaging assumptions
- no sub-agent authority bleed

## Acceptance Rule

The build is valid only if all accepted outputs were reviewed and merged by the Main Builder Agent.
