# 09_SCHEMA_VALIDATOR_SPEC

Version: 3.0
Status: Required

## Purpose

Validate configuration, output, and telemetry against defined schemas.

## Schema Targets

- 17_CONFIG_SCHEMA.json
- 18_OUTPUT_SCHEMA.json
- 19_TELEMETRY_SCHEMA.json

## Responsibilities

- parse candidate payload
- validate required fields and types
- reject malformed payloads
- return machine-readable validation results

## Build-Time Use

Sub-agent returns that include structured payloads must pass the relevant schema before merge.

## Minimum Validation Result

- schema_id
- valid
- errors[]
- warnings[]
- normalized_candidate if valid

## Halt Rule

If a required payload fails schema validation, dependent execution must halt until corrected.
