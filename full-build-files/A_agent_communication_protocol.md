# A. Agent Communication Protocol

## Purpose
Defines deterministic message contracts between agents.

## Message Structure
- sender
- receiver
- timestamp
- input_payload
- transformation_type
- output_payload
- confidence
- log_id

## Rules
- No agent modifies prior outputs without new message
- All messages logged
