# 02_SYSTEM_AUTHORITY_AND_PRECEDENCE

Version: 3.0
Status: Binding

## Authority Hierarchy

1. CoSyn Constitution
2. Persona Governor
3. Stack Architect
4. RTW Build Pack
5. Main Builder Agent
6. Sub-Agents
7. Build outputs

Authority is deterministic and non-overridable downward.

## Interpretation Rule

If a lower layer conflicts with a higher layer:
- the lower layer is invalid
- execution must halt until corrected

## Main Agent vs Sub-Agent Authority

### Main Builder Agent
Authorized to:
- orchestrate
- route
- merge
- halt
- accept
- declare completion

### Sub-Agents
Authorized only to:
- execute assigned bounded tasks
- propose outputs
- return artifacts for review

Sub-agents are not authority holders.

## Canonical Boundary

This pack may implement runtime behavior, routing, schemas, controls, and orchestration logic.
This pack may not redefine constitutional meaning or weaken governance gates.

## Priority of This File

Use this file whenever:
- task ownership is disputed
- a sub-agent attempts merge or completion
- an output appears to override governance
