# 15_ARTIFACT_INTEGRITY_ENFORCEMENT_SPEC

Version: 3.0
Status: Required

## Purpose

Protect the integrity of build artifacts before and after merge.

## Integrity Checks

- file path matches contract authorization
- content not empty when full file required
- checksum generated after acceptance
- no duplicate active version of same artifact in output package
- manifest entry exists for each accepted file

## Sub-Agent Specific Checks

- returned artifact references correct task_id
- returned artifact identifies producing role
- no undeclared extra files
- no hidden overwrite instruction
- no package staging before acceptance

## Main-Agent Duties

The Main Builder Agent must perform or enforce integrity checks before merge.

## Packaging Rule

The final zip may contain:
- accepted execution-layer files
- flat canonical reference copies
- manifest
- checksums

It may not contain:
- rejected artifacts
- scratch drafts
- conflicting versions of active execution files
