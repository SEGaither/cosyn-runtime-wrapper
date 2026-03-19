# B. Audit Ledger Schema

## Fields
- event_id
- agent_name
- input_hash
- output_hash
- action_type
- timestamp
- validation_status
- reviewer (if human)

## Requirements
- Immutable
- Append-only
- Queryable by event_id
