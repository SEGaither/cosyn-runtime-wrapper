# 24_IMPLEMENTATION_CHECKLIST

Version: 3.0
Status: Required

## Pre-Build
- [ ] Main Builder Agent instantiated
- [ ] Execution mode locked to sub_agent_orchestrated
- [ ] Authority precedence loaded
- [ ] Canonical references available
- [ ] State model initialized

## During Build
- [ ] Every delegated task has a valid contract
- [ ] Every sub-agent role is allowed by roster
- [ ] Every returned artifact is validated
- [ ] Every accepted file has merge record
- [ ] Every halt is resolved before continuation
- [ ] No sub-agent merge/completion attempts remain unresolved

## Packaging
- [ ] Flat package structure preserved
- [ ] Manifest generated
- [ ] Checksums generated
- [ ] Canonical reference copies included
- [ ] No rejected artifacts packaged

## Completion
- [ ] Test matrix required cases passed
- [ ] Acceptance criteria passed
- [ ] Build-complete signal conditions passed
- [ ] Completion emitted by Main Builder Agent only
