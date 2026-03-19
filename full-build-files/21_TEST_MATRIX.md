# 21_TEST_MATRIX

Version: 3.0
Status: Required

## Runtime Tests

1. Required gate order enforced
2. Assumption gate blocks undeclared material assumption
3. Bias gate blocks tradeoff recommendation without frame
4. Confidence enforcer downgrades unsupported certainty
5. Schema validator rejects malformed output payload

## Build Process Tests

6. Main agent instantiation required before task dispatch
7. Execution mode must equal sub_agent_orchestrated
8. Invalid task contract halts dispatch
9. Sub-agent cannot modify unauthorized file
10. Sub-agent merge attempt triggers authority halt
11. Sub-agent completion attempt triggers authority halt
12. Returned artifact without validation record cannot merge
13. Conflicting returned artifacts trigger halt
14. Packager may include accepted files only
15. Build-complete signal emitted only by main agent after all acceptance criteria pass

## Package Tests

16. Flat package structure preserved
17. Manifest includes all packaged files
18. Checksum file matches included artifacts
19. Canonical reference files included as reference copies only
