# 13_EVALUATION_HARNESS_SPEC

Version: 3.0
Status: Required

## Purpose

Provide deterministic evaluation of runtime behavior and build-pack completeness.

## Minimum Evaluation Areas

### Runtime
- gate enforcement
- schema validation
- halt behavior
- confidence calibration

### Build Process
- sub-agent boundary enforcement
- main-agent merge control
- task-contract completeness
- completion signal correctness
- package integrity

## Required Outputs

- evaluation_case_id
- expected_result
- observed_result
- pass_or_fail
- notes

## Failure Policy

No build may be declared complete while required evaluation cases are failing.

## Suggested Evaluation Sets

- hidden assumption case
- unsupported confidence case
- tradeoff without bias frame
- unauthorized sub-agent merge attempt
- missing task contract case
- invalid completion signal case
