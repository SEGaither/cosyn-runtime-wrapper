# 06A_SUB_AGENT_ROSTER

Version: 1.0
Status: Required

## Allowed Sub-Agents

### 1. module_builder
Purpose:
- implement assigned module or file content

Allowed:
- produce proposed file bodies
- propose module-specific notes

Forbidden:
- merge changes
- alter unrelated files
- declare completion

### 2. governance_auditor
Purpose:
- inspect outputs for governance, routing, structural, and scope compliance

Allowed:
- produce pass/fail findings
- cite violated rules from this pack

Forbidden:
- rewrite canonical governance meaning
- merge corrections directly

### 3. test_runner
Purpose:
- execute the defined test matrix and summarize failures

Allowed:
- run tests
- return failures, pass results, traces, and defect summaries

Forbidden:
- waive failed acceptance criteria
- declare build complete

### 4. packager
Purpose:
- assemble accepted files and package outputs

Allowed:
- stage accepted artifacts
- prepare manifests and checksums
- create package bundle

Forbidden:
- include rejected outputs
- replace missing accepted files with guesses

## Roster Rule

No other sub-agent roles are permitted unless the pack is amended.
