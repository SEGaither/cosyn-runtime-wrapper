# 08A_ORCHESTRATION_LOOP_SPEC

Version: 1.0
Status: Required

## Main Agent Orchestration Loop

1. Load active plan
2. Select next unresolved build target
3. Determine whether the task should be:
   - executed directly by main agent
   - delegated to one sub-agent
4. If delegated, create a task contract
5. Route to exactly one allowed sub-agent
6. Receive returned artifact package
7. Run governance and structural validation
8. Decide:
   - accept and merge
   - reject and request correction
   - halt
9. Update state model
10. Repeat until acceptance criteria pass
11. Emit build-complete signal if and only if all conditions pass

## Delegation Decision Criteria

Delegate when the task is:
- module-local
- test-executable
- audit-bounded
- packaging-specific

Retain under main agent when the task is:
- cross-cutting
- authority-related
- merge-related
- completion-related
- amendment-related

## Loop Invariants

- one active delegated task per target file unless explicitly parallelized by the plan
- parallel work may not target the same file without merge staging
- every accepted output must have a validation record
