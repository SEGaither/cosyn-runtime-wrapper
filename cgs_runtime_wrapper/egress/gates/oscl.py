"""
OSCL Gate - Egress position 1
Outcome-Scored Self-Critique Loop - Production Implementation

Scores draft output on five axes. Triggers revision below threshold.
Maximum 2 revision cycles per spec.

Axes:
  evidence_alignment         (threshold: 0.70)
  assumption_minimality      (no independent threshold)
  overclaim_risk_inverse     (no independent threshold)
  user_constraint_adherence  (threshold: 0.75)
  actionability_clarity      (no independent threshold)
  aggregate_score            (threshold: 0.72, weighted)

References:
- cosyn_wrapper_gate_specifications.md OSCL gate
- cosyn_wrapper_interface_contracts.json gate_data_schemas.OSCL
"""
from __future__ import annotations

import re
import time
from typing import Optional

from cgs_runtime_wrapper.models.envelopes import (
    ASTGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
    OSCLGateData,
)

_THRESHOLD_EVIDENCE_ALIGNMENT = 0.70
_THRESHOLD_USER_CONSTRAINT_ADHERENCE = 0.75
_THRESHOLD_AGGREGATE = 0.72
_RERENDER_MAX = 2

_HEDGE_PATTERNS = [
    r"\bI think\b", r"\bI believe\b", r"\bit appears?\b", r"\bseems?\b",
    r"\bmight\b", r"\bmay\b", r"\bcould\b", r"\bpossibly\b", r"\bperhaps\b",
    r"\buncertain\b", r"\bunknown\b", r"\bnot confirmed\b", r"\bnot verified\b",
    r"\bprovision(?:al|ally)\b", r"\bestimate[sd]?\b", r"\bapproximate(?:ly)?\b",
    r"\bsuggest[s]?\b", r"\bindicate[s]?\b",
]

_OVERCLAIM_PATTERNS = [
    r"\bit is (?:definitely|certainly|undoubtedly|absolutely|clearly|obviously)\b",
    r"\bproven\b", r"\bfactually\b", r"\bguaranteed\b",
    r"\beveryone knows\b", r"\bwithout question\b",
    r"\bindisputably\b", r"\bunquestionably\b", r"\bwithout doubt\b",
    r"\bI am 100%\b", r"\bI am certain\b", r"\bI know for a fact\b",
]

_EVIDENCE_CITATION_PATTERNS = [
    r"\baccording to\b",
    r"\bthe (?:data|evidence|research|study|report|document|source)\b",
    r"\bas (?:shown|stated|noted|mentioned|described)\b",
    r"\b(?:based on|drawing from|derived from)\b",
    r"\b(?:cite|cited|citation|reference|referenced)\b",
    r"\b\d+\.?\d*%\b",
    r"\bin turn \d+\b",
    r"\bsection \d+\b", r"\bpage \d+\b",
]

_STRUCTURE_MARKERS = [
    r"^\s*[-*]",
    r"^\s*\d+[\.\)]",
    r"\*\*[^*]+\*\*",
    r"^#{1,3} ",
    r"\n\n",
]

_MISSING_INPUT_PATTERNS = [
    r"\bI (?:do not|don't) have (?:access to|enough information|sufficient data)\b",
    r"\bI (?:cannot|can't) (?:answer|respond|help) without\b",
    r"\bmore information (?:is|would be) (?:required|needed)\b",
    r"\binsufficient (?:context|information|data)\b",
    r"\bcannot proceed without\b",
]


def _score_evidence_alignment(
    raw_output: str,
    icc_gate_data: Optional[ICCGateData],
) -> float:
    """Score evidence alignment. Base 0.80. Adjust for citations, hedging, overclaims."""
    score = 0.80
    text = raw_output
    citation_count = sum(
        1 for p in _EVIDENCE_CITATION_PATTERNS if re.search(p, text, re.IGNORECASE | re.MULTILINE)
    )
    overclaim_count = sum(
        1 for p in _OVERCLAIM_PATTERNS if re.search(p, text, re.IGNORECASE)
    )
    hedge_count = sum(
        1 for p in _HEDGE_PATTERNS if re.search(p, text, re.IGNORECASE)
    )
    score += min(0.15, citation_count * 0.04)
    score += min(0.05, hedge_count * 0.01)
    score -= min(0.40, overclaim_count * 0.08)
    return float(max(0.0, min(1.0, score)))


def _score_assumption_minimality(
    raw_output: str,
    astg_gate_data: Optional[ASTGGateData],
) -> float:
    """Score assumption minimality. Base 0.85."""
    score = 0.85
    text = raw_output.lower()
    if astg_gate_data and astg_gate_data.unstable_assumption_present:
        ack_patterns = [
            r"\bassumption\b", r"\bpremise\b", r"\bconditional on\b",
            r"\bprovided that\b", r"\bsubject to\b", r"\bgiven that\b",
        ]
        ack_count = sum(1 for p in ack_patterns if re.search(p, text, re.IGNORECASE))
        if ack_count == 0:
            score -= 0.20
        else:
            score += 0.05
    new_assumption_markers = [
        r"\bI assume\b", r"\bwe can assume\b", r"\bobviously\b",
        r"\bclearly\b", r"\beveryone knows\b", r"\bwithout doubt\b",
    ]
    new_count = sum(1 for p in new_assumption_markers if re.search(p, raw_output, re.IGNORECASE))
    score -= min(0.30, new_count * 0.10)
    return float(max(0.0, min(1.0, score)))


def _score_overclaim_risk_inverse(raw_output: str) -> float:
    """Score overclaim risk (inverted: higher = less overclaiming). Base 0.85."""
    score = 0.85
    text = raw_output
    overclaim_count = sum(1 for p in _OVERCLAIM_PATTERNS if re.search(p, text, re.IGNORECASE))
    hedge_count = sum(1 for p in _HEDGE_PATTERNS if re.search(p, text, re.IGNORECASE))
    score -= min(0.35, overclaim_count * 0.07)
    score += min(0.10, hedge_count * 0.02)
    return float(max(0.0, min(1.0, score)))


def _score_user_constraint_adherence(
    raw_output: str,
    icc_gate_data: Optional[ICCGateData],
) -> float:
    """Score constraint adherence vs ICC-parsed constraints. Base 0.85."""
    score = 0.85
    if not icc_gate_data:
        return score
    text = raw_output.lower()
    words = raw_output.split()
    word_count = len(words)
    if icc_gate_data.intent_output_form:
        form = icc_gate_data.intent_output_form.lower()
        if any(k in form for k in ["brief", "short", "concise"]):
            if word_count > 400:
                score -= 0.15
            elif word_count > 250:
                score -= 0.05
        if any(k in form for k in ["comprehensive", "detailed", "thorough"]):
            if word_count < 150:
                score -= 0.15
        if "bullet" in form and not re.search(r"^\s*[-*]", raw_output, re.MULTILINE):
            score -= 0.15
        if "numbered" in form and not re.search(r"^\s*\d+[\.\)]", raw_output, re.MULTILINE):
            score -= 0.10
    for excl in icc_gate_data.intent_exclusions:
        excl_words = [w for w in excl.lower().split() if len(w) > 3]
        if excl_words:
            match_count = sum(1 for w in excl_words if w in text)
            if match_count >= max(1, len(excl_words) // 2):
                score -= 0.10
    return float(max(0.0, min(1.0, score)))


def _score_actionability_clarity(
    raw_output: str,
    icc_gate_data: Optional[ICCGateData],
) -> float:
    """Score actionability and structural coherence. Base 0.80."""
    score = 0.80
    text = raw_output
    structure_count = sum(
        1 for p in _STRUCTURE_MARKERS if re.search(p, text, re.MULTILINE)
    )
    score += min(0.10, structure_count * 0.025)
    action_count = len(re.findall(
        r"\b(?:recommend|suggest|should|must|can|will|implement|use|apply|"
        r"consider|ensure|verify|confirm|add|remove|update|check|review)\b",
        text, re.IGNORECASE
    ))
    if action_count >= 3:
        score += 0.05
    word_count = len(text.split())
    if word_count < 30:
        score -= 0.15
    elif word_count < 60:
        score -= 0.05
    stripped = text.strip()
    if stripped and not re.search(r"[.!?\)]$", stripped):
        score -= 0.10
    return float(max(0.0, min(1.0, score)))


def _compute_aggregate(scores: dict[str, float]) -> float:
    """Weighted aggregate. Weights per spec importance."""
    weights = {
        "evidence_alignment": 0.25,
        "assumption_minimality": 0.15,
        "overclaim_risk_inverse": 0.20,
        "user_constraint_adherence": 0.25,
        "actionability_clarity": 0.15,
    }
    total = sum(scores[k] * weights[k] for k in weights)
    return float(round(total, 4))


def _detect_scp(
    raw_output: str,
    scores: dict[str, float],
) -> bool:
    """SCP fires when improvement is blocked by missing inputs."""
    output_lower = raw_output.lower()
    missing_signals = sum(
        1 for p in _MISSING_INPUT_PATTERNS if re.search(p, output_lower, re.IGNORECASE)
    )
    any_below = (
        scores.get("evidence_alignment", 1.0) < _THRESHOLD_EVIDENCE_ALIGNMENT
        or scores.get("user_constraint_adherence", 1.0) < _THRESHOLD_USER_CONSTRAINT_ADHERENCE
        or scores.get("aggregate_score", 1.0) < _THRESHOLD_AGGREGATE
    )
    return missing_signals >= 1 and any_below


async def run_oscl_gate(
    raw_output: str,
    icc_gate_data: ICCGateData | None,
    astg_gate_data: ASTGGateData | None,
    rerender_count: int,
) -> GateResult:
    """
    Execute the OSCL gate (egress position 1).

    Scores output on five axes and returns GateResult with OSCLGateData.

    Thresholds:
    - evidence_alignment >= 0.70
    - user_constraint_adherence >= 0.75
    - aggregate_score >= 0.72

    Status path:
    - scp_trigger=True  -> halt (MISSING_REQUIRED_INPUTS)
    - below threshold, rerender_count < 2  -> rerender
    - below threshold, rerender_count >= 2 -> warn (provisional)
    - all above threshold -> pass

    Spec: cosyn_wrapper_gate_specifications.md OSCL gate
    """
    fired_at_ms = int(time.time() * 1000)

    evidence_alignment = _score_evidence_alignment(raw_output, icc_gate_data)
    assumption_minimality = _score_assumption_minimality(raw_output, astg_gate_data)
    overclaim_risk_inverse = _score_overclaim_risk_inverse(raw_output)
    user_constraint_adherence = _score_user_constraint_adherence(raw_output, icc_gate_data)
    actionability_clarity = _score_actionability_clarity(raw_output, icc_gate_data)

    scores: dict[str, float] = {
        "evidence_alignment": evidence_alignment,
        "assumption_minimality": assumption_minimality,
        "overclaim_risk_inverse": overclaim_risk_inverse,
        "user_constraint_adherence": user_constraint_adherence,
        "actionability_clarity": actionability_clarity,
    }

    aggregate_score = _compute_aggregate(scores)
    scores["aggregate_score"] = aggregate_score

    below_threshold = (
        evidence_alignment < _THRESHOLD_EVIDENCE_ALIGNMENT
        or user_constraint_adherence < _THRESHOLD_USER_CONSTRAINT_ADHERENCE
        or aggregate_score < _THRESHOLD_AGGREGATE
    )

    lowest_scoring_axes: list[str] = []
    if below_threshold:
        axis_thresholds = {
            "evidence_alignment": _THRESHOLD_EVIDENCE_ALIGNMENT,
            "user_constraint_adherence": _THRESHOLD_USER_CONSTRAINT_ADHERENCE,
        }
        lowest_scoring_axes = [
            k for k, thr in axis_thresholds.items() if scores.get(k, 1.0) < thr
        ]
        if aggregate_score < _THRESHOLD_AGGREGATE and not lowest_scoring_axes:
            sorted_axes = sorted(scores.items(), key=lambda x: x[1])
            lowest_scoring_axes = [k for k, _ in sorted_axes[:2]]

    revision_required = below_threshold
    scp_trigger = _detect_scp(raw_output, scores)

    oscl_data = OSCLGateData(
        evidence_alignment=evidence_alignment,
        assumption_minimality=assumption_minimality,
        overclaim_risk_inverse=overclaim_risk_inverse,
        user_constraint_adherence=user_constraint_adherence,
        actionability_clarity=actionability_clarity,
        aggregate_score=aggregate_score,
        revision_required=revision_required,
        scp_trigger=scp_trigger,
        lowest_scoring_axes=lowest_scoring_axes if lowest_scoring_axes else None,
    )

    if scp_trigger:
        return GateResult(
            gate_id=GateId.OSCL,
            status=GateStatus.halt,
            failure_class=FailureClass.class1,
            halt_reason_code=HaltReasonCode.MISSING_REQUIRED_INPUTS,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            rerender_reason="OSCL SCP: improvement blocked by missing required inputs",
            gate_data=oscl_data.model_dump(),
        )

    if below_threshold:
        if rerender_count >= _RERENDER_MAX:
            return GateResult(
                gate_id=GateId.OSCL,
                status=GateStatus.warn,
                failure_class=FailureClass.class1,
                halt_reason_code=None,
                provisional_flag=True,
                assumption_declared=False,
                fired_at_ms=fired_at_ms,
                rerender_reason=(
                    f"OSCL below threshold after {rerender_count} rerenders. "
                    f"Proceeding provisional. Axes: {lowest_scoring_axes}"
                ),
                gate_data=oscl_data.model_dump(),
            )
        axis_report = ", ".join(
            f"{k}={scores[k]:.3f}" for k in [
                "evidence_alignment", "user_constraint_adherence", "aggregate_score"
            ]
        )
        return GateResult(
            gate_id=GateId.OSCL,
            status=GateStatus.rerender,
            failure_class=FailureClass.class1,
            halt_reason_code=None,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            rerender_reason=(
                f"OSCL below threshold. Scores: {axis_report}. "
                f"Revise: {lowest_scoring_axes}."
            ),
            gate_data=oscl_data.model_dump(),
        )

    return GateResult(
        gate_id=GateId.OSCL,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=oscl_data.model_dump(),
    )
