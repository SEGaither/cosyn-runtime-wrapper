# 04_MODULE_SPECIFICATION

Version: 3.0
Status: Required

## Purpose

Define the modules that must exist in the RTW implementation and the task partitioning rules used during agentic build.

## Required Modules

### M1 Artifact Loader
Loads and binds governance artifacts and local configuration.

### M2 Persona Router
Routes requests to the correct persona role without violating authority discipline.

### M3 Governance Gate Engine
Executes non-bypassable governance checks.

### M4 Runtime Executor
Runs the runtime interaction flow after gates pass.

### M5 Schema Validator
Validates configuration, output, and telemetry against defined schemas.

### M6 Halt Controller
Triggers deterministic halts on violations.

### M7 Confidence Enforcer
Ensures uncertainty and confidence calibration remain proportional.

### M8 Telemetry Adapter
Captures structured event data.

### M9 Evaluation Harness
Runs validation and regression checks.

## Sub-Agent Ownership Rules

Sub-agents may be assigned module slices, but:
- each task must identify the target module
- cross-module edits require explicit authorization in the task contract
- integration logic remains main-agent-controlled

## Edit Policy

Default policy:
- sub-agents may propose direct file content for assigned module files
- cross-cutting changes require explicit mention in the task contract
- shared files require merge review by the Main Builder Agent
