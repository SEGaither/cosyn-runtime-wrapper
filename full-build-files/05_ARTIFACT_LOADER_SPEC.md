# 05_ARTIFACT_LOADER_SPEC

Version: 3.0
Status: Required

## Purpose

The Artifact Loader binds the runtime to its governance inputs without reinterpreting them.

## Responsibilities

- locate configured governance artifacts
- verify expected file presence
- classify artifacts by type
- bind active versions to session state
- expose loaded artifacts to downstream modules

## Required Inputs

- constitutional reference
- governor reference
- architect reference
- local runtime config
- execution mode
- active prompts/contracts if used by build tooling

## Required Output

A normalized artifact registry containing:
- artifact_id
- artifact_type
- version
- source_path
- hash
- active_status
- authority_rank

## Failure Conditions

- missing required governance artifact
- duplicate active version for same authority layer
- unsupported or malformed config
- authority inversion

## Build Guidance

Sub-agent implementations of the loader must not embed alternative governance language.
