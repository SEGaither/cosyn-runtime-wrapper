# 22_ACCEPTANCE_CRITERIA

Version: 3.0
Status: Binding

## The build is accepted only if all criteria below pass

### Structural
- full flat execution pack present
- all required files exist
- schemas are valid JSON
- manifest and checksums are present

### Governance
- authority precedence preserved
- required gates defined
- non-bypassable halt behavior defined
- sub-agents remain non-authoritative

### Agentic Execution
- main-agent choreographer role explicitly defined
- allowed sub-agent roster defined
- task-contract schema defined
- return-to-main-agent merge rule defined
- unauthorized merge/completion blocked

### Packaging
- package is flat
- architecture-agnostic
- canonical reference files included as convenience copies only
- no rejected outputs included

### Validation
- test matrix complete
- evaluation harness covers build and runtime
- build-complete signal file present and correct

## Failure Rule

If any criterion fails, completion may not be declared.
