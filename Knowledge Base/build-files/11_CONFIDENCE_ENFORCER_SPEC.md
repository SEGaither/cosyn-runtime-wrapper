# 11_CONFIDENCE_ENFORCER_SPEC

Version: 3.0
Status: Required

## Purpose

Enforce proportional confidence and visible uncertainty.

## Runtime Responsibilities

- calibrate confidence to evidence strength
- reduce certainty when inferential distance increases
- prevent speculative claims from being presented as verified

## Build-Time Responsibilities

When sub-agents return:
- unresolved assumptions
- uncertain implementation choices
- missing dependency knowledge

those conditions must be surfaced explicitly for main-agent review.

## Required Build Return Fields When Uncertain

- confidence_level
- basis_for_confidence
- unresolved_dependencies
- what_would_change_recommendation

## Violation Handling

If a file body or evaluation summary presents unsupported certainty, mark it invalid for acceptance until corrected.
