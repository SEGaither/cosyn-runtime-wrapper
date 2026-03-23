# 07_GOVERNANCE_GATE_ENGINE_SPEC

Version: 3.0
Status: Required

## Purpose

Implement the runtime enforcement engine that checks outputs against required governance gates before continuation or emission.

## Minimum Gate Set

- assumption declaration gate
- bias / tradeoff declaration gate
- confidence declaration gate
- schema compliance gate
- deterministic halt rule

## Build-Time Extension

During agentic build, the same engine concept must also validate sub-agent returns before merge.

## Sub-Agent Return Validation

Before a returned artifact may be merged, the gate engine must check:
- task scope respected
- allowed files only
- prohibited actions not violated
- required sections present
- no authority claims beyond assigned role
- no completion claim by sub-agent
- no merge directive by sub-agent

## Enforcement Outputs

For each evaluated artifact, return:
- pass_or_fail
- triggered_gates
- violations
- required_corrections
- merge_eligible

## Required Halt Triggers

- missing required governance structure
- role boundary violation
- undeclared assumptions where material
- tradeoff reasoning without declared frame
- schema failure
- scope drift
