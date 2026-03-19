# C. Compliance Rule Engine v1.0

Status: Draft operational artifact
Scope: Deterministic rule layer for regulated AI consulting workflows

## Objective
Define machine-checkable rules that evaluate whether a workflow artifact is eligible for release, remediation, or human escalation.

## Rule Engine Model
Input:
- workflow artifact
- message envelope
- ledger event history
- client industry profile
- release intent

Output:
- pass
- fail
- conditional pass
- escalate

## Rule Categories
1. Source Fidelity Rules
2. Audit Completeness Rules
3. Human Review Rules
4. Client-Facing Claim Rules
5. Data Boundary Rules
6. Version Integrity Rules

## Severity Levels
- S1 informational
- S2 caution
- S3 blocking
- S4 critical blocking

## Rule Set
### CFR-001 Source basis required
Condition:
Any client-visible claim exists.
Requirement:
Each claim must map to evidence_basis not equal to unverified.
Failure:
S4 blocking

### CFR-002 Assumptions declared
Condition:
Recommendation or forecast exists.
Requirement:
assumptions_declared is non-empty.
Failure:
S3 blocking

### CFR-003 Audit lineage complete
Condition:
Artifact marked client_visible = true.
Requirement:
artifact has traceable parent event lineage and current artifact_version.
Failure:
S4 blocking

### CFR-004 Human review for regulated workflows
Condition:
client industry in [law, insurance, finance, healthcare, public sector]
Requirement:
human_review_required = true before delivery_released
Failure:
S4 blocking

### CFR-005 No compliance bypass
Condition:
delivery intent detected.
Requirement:
most recent compliance_status in [approved, approved_with_conditions]
Failure:
S4 blocking

### CFR-006 Conditional approval enforcement
Condition:
compliance_status = approved_with_conditions
Requirement:
all conditions resolved and logged before release
Failure:
S3 blocking

### CFR-007 Data boundary integrity
Condition:
workflow payload includes sensitive or protected data indicators
Requirement:
redaction policy and storage classification present
Failure:
S4 blocking

### CFR-008 Version continuity
Condition:
artifact revised after compliance review
Requirement:
re-review required before release
Failure:
S4 blocking

### CFR-009 Marketing claim restraint
Condition:
artifact type = marketing or sales
Requirement:
no guarantee language unless contractually validated
Failure:
S3 blocking

### CFR-010 Confidence threshold
Condition:
auto-routed recommendation
Requirement:
confidence_score >= 0.75
Failure:
S3 escalate

## Evaluation Order
1. Critical blocking rules
2. Lineage and version rules
3. Human review rules
4. Conditional release rules
5. Informational warnings

## Decision Matrix
- Any S4 fail -> block release
- Any S3 fail -> remediation or escalation
- S2 only -> conditional pass allowed
- S1 only -> pass

## Rule Execution Example
Artifact:
- industry = insurance
- client_visible = true
- confidence_score = 0.81
- evidence_basis = derived_from_user_input
- human_review_required = false

Result:
- CFR-004 fail
- disposition = block release
- reason = regulated workflow requires human review before delivery

## Mandatory Outputs
The rule engine must emit:
- evaluation_id
- artifact_id
- rule_results[]
- overall_disposition
- blocking_reasons[]
- remediation_steps[]
- human_escalation_required

## Remediation Template
For each failed rule:
- rule_id
- failure_reason
- evidence_missing
- correction_required
- responsible_agent

## Governance Constraint
The rule engine advises or blocks; it does not rewrite content.
