# 00_README_BUILD_ORDER

Version: 3.0
Status: Active
Package Type: Full RTW Agentic Build Pack
Date: 2026-03-19

## Purpose

This file defines the deterministic read order for the RTW build pack.

This package is designed for agentic execution using:
- one Main Builder Agent acting as the choreographer
- bounded Sub-Agents executing assigned task slices
- strict return-to-main-agent merge control

## Build Order

Read in the following order without skipping:

1. 00_README_BUILD_ORDER.md
2. 00A_AGENT_INSTANTIATION_COMMAND.md
3. 00B_EXECUTION_MODE.md
4. 01_RTW_BUILD_CONTRACT.md
5. 02_SYSTEM_AUTHORITY_AND_PRECEDENCE.md
6. 03_EXECUTION_PIPELINE_SPEC.md
7. 04_MODULE_SPECIFICATION.md
8. 05_ARTIFACT_LOADER_SPEC.md
9. 06_PERSONA_ROUTER_SPEC.md
10. 06A_SUB_AGENT_ROSTER.md
11. 06B_SUB_AGENT_TASK_CONTRACT_SCHEMA.md
12. 07_GOVERNANCE_GATE_ENGINE_SPEC.md
13. 08_REASONING_RUNTIME_EXECUTION_SPEC.md
14. 08A_ORCHESTRATION_LOOP_SPEC.md
15. 09_SCHEMA_VALIDATOR_SPEC.md
16. 10_HALT_CONTROLLER_SPEC.md
17. 11_CONFIDENCE_ENFORCER_SPEC.md
18. 12_TELEMETRY_ADAPTER_SPEC.md
19. 13_EVALUATION_HARNESS_SPEC.md
20. 14_COMMAND_TRIGGERS_AND_CONTROL_FLAGS.md
21. 15_ARTIFACT_INTEGRITY_ENFORCEMENT_SPEC.md
22. 16_STATE_MODEL_AND_SESSION_SPEC.md
23. 17_CONFIG_SCHEMA.json
24. 18_OUTPUT_SCHEMA.json
25. 19_TELEMETRY_SCHEMA.json
26. 20_ERROR_CODES_AND_HALTS.md
27. 21_TEST_MATRIX.md
28. 22_ACCEPTANCE_CRITERIA.md
29. 22A_BUILD_COMPLETE_SIGNAL.md
30. 23_BUILDER_AGENT_EXECUTION_PROMPT.md
31. 23A_MAIN_AGENT_CHOREOGRAPHER_PROMPT.md
32. 23B_SUB_AGENT_MODULE_BUILDER_PROMPT.md
33. 23C_SUB_AGENT_GOVERNANCE_AUDITOR_PROMPT.md
34. 23D_SUB_AGENT_TEST_RUNNER_PROMPT.md
35. 23E_SUB_AGENT_PACKAGER_PROMPT.md
36. 24_IMPLEMENTATION_CHECKLIST.md
37. MANIFEST.md
38. CHECKSUMS.sha256

## Authority Note

This pack is implementation-layer only.
Canonical governance references are included in this zip for convenience as flat files prefixed `CANONICAL_`.
Those copies are reference copies only and do not supersede external authoritative sources.

## Execution Rule

Do not begin building until:
- main agent is instantiated
- execution mode is bound to `sub_agent_orchestrated`
- task routing and merge control are active
- halt controller is active
- artifact integrity enforcement is active

## Completion Rule

Only the Main Builder Agent may declare the build complete signal.
