"""
Phase 3.3 - ASTG Classifier - Production Implementation
Pattern-based assumption detection with severity scoring.
"""
from __future__ import annotations

import re
from typing import Optional

from cgs_runtime_wrapper.models.envelopes import (
    Assumption,
    ASTGGateData,
    AssumptionStability,
    ICCGateData,
)

ASTG_PROMPT_TEMPLATE = (
    "System: You are an assumption identification classifier. "
    "Return JSON only. Schema: {assumptions: [{assumption_text, "
    "failure_condition, conclusion_impact, stability}], "
    "assumption_count, unstable_assumption_present}"
)

_EXPLICIT_PATTERNS: list[tuple[str, str, str, AssumptionStability]] = [
    (r"\bI assume\b[^.!?]*", "The declared assumption is false",
     "response based on this premise may be incorrect",
     AssumptionStability.unstable),
    (r"\bassuming\b[^.!?]*", "The embedded assumption is false",
     "assumption-dependent conclusions may be invalid",
     AssumptionStability.unstable),
    (r"\bpresumably\b[^.!?]*", "The presumption does not hold",
     "presumption-dependent conclusions may be invalid",
     AssumptionStability.unstable),
    (r"\bit is likely that\b[^.!?]*", "The stated likelihood does not obtain",
     "probability-based reasoning may fail",
     AssumptionStability.unstable),
    (r"\bgiven that\b[^.!?]*", "The given condition is false or inapplicable",
     "all conclusions conditioned on this premise become invalid",
     AssumptionStability.unstable),
    (r"\bwe can assume\b[^.!?]*", "The collective assumption is not warranted",
     "shared-premise reasoning collapses",
     AssumptionStability.unstable),
    (r"\bobviously\b[^.!?]*", "The obvious claim is disputed or false",
     "certainty framing loses validity if claim is contested",
     AssumptionStability.unstable),
    (r"\bclearly\b[^.!?]*", "The claim is not as clear as stated",
     "certainty framing misleads if claim is contested",
     AssumptionStability.unstable),
    (r"\beveryone knows\b[^.!?]*",
     "The consensus claim is incorrect or irrelevant",
     "social-proof premise invalidates conclusion",
     AssumptionStability.unstable),
]

_IMPLICIT_PATTERNS: list[tuple[str, str, str, str, AssumptionStability]] = [
    (r"\bif (?:we|you|I|it|this)\b[^.!?]*\bthen\b[^.!?]*",
     "Causal if-then premise",
     "The if-then relationship holds as described",
     "The antecedent does not hold or does not cause the stated result",
     AssumptionStability.unstable),
    (r"\bsince\b[^.!?]{3,80}\b(?:we|you|I|it|this)\b",
     "Causal since premise",
     "The causal relationship implied by since is valid",
     "The since clause is false or the causal link is broken",
     AssumptionStability.unstable),
    (r"\bbecause\b[^.!?]{3,80}(?:we|you|I|it|this|the)",
     "Causal because premise",
     "The reason in the because clause is accurate",
     "The causal premise is false or the relationship is not causal",
     AssumptionStability.unstable),
    (r"\bthis means\b[^.!?]*",
     "Implied inferential step",
     "The inferential step this-means-X is valid",
     "The inference does not follow from the stated premise",
     AssumptionStability.unstable),
    (r"\bwhich means\b[^.!?]*",
     "Implied inferential step",
     "The inferential step which-means-X is valid",
     "The inference does not follow from the stated premise",
     AssumptionStability.unstable),
    (r"\bthis (?:shows?|proves?|demonstrates?|confirms?)\b[^.!?]*",
     "Evidential claim in reasoning",
     "The referenced evidence supports the stated conclusion",
     "Evidence is absent or does not support the conclusion",
     AssumptionStability.unstable),
]

_REFERENCE_PATTERNS: list[tuple[str, str, str, AssumptionStability]] = [
    (
        r"\b(?:the|this|my|our)"
        r" (?:document|file|report|data|dataset|analysis|framework"
        r"|plan|proposal|contract|article|paper|draft|spreadsheet|code|script)\b",
        "Referenced artifact is available and matches described context",
        "The referenced artifact is missing or inaccessible",
        AssumptionStability.unstable,
    ),
    (
        r"\b(?:the|this) (?:above|following|attached|provided|given)\b",
        "Referenced content has been provided",
        "The referenced content is not present in the current context",
        AssumptionStability.unstable,
    ),
    (
        r"\bas (?:I|we) (?:discussed|mentioned|agreed|noted|said)"
        r" (?:before|earlier|previously|above)\b",
        "Prior conversation context is available and consistent",
        "The prior context is unavailable or differs from what is recalled",
        AssumptionStability.stable,
    ),
]

_DOMAIN_PATTERNS: list[tuple[str, str, str, AssumptionStability]] = [
    (
        r"\b(?:current|existing|present)"
        r" (?:law|regulation|policy|rules?|guidelines?|standards?)\b",
        "Current regulatory environment is stable and accurately known",
        "Regulatory changes have occurred or assumed rules are incorrect",
        AssumptionStability.unstable,
    ),
    (
        r"\b(?:market|industry) (?:conditions?|trends?|landscape)\b",
        "Market or industry conditions are as described",
        "Market conditions have materially changed",
        AssumptionStability.unstable,
    ),
    (
        r"\b(?:users?|customers?|clients?|stakeholders?|team)\b"
        r".{0,60}\b(?:want|need|expect|prefer|will)\b",
        "User or stakeholder preferences are as described",
        "Actual preferences differ from the stated assumption",
        AssumptionStability.unstable,
    ),
]

_COMMON_KNOWLEDGE_PATTERNS = [
    r"\ba year has (?:12|twelve) months\b",
    r"\bthere are (?:60|sixty) (?:seconds|minutes)\b",
    r"\bwater (?:freezes|boils)\b",
]


def _is_common_knowledge(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in _COMMON_KNOWLEDGE_PATTERNS)


def _deduplicate(assumptions: list[Assumption]) -> list[Assumption]:
    seen: list[str] = []
    unique: list[Assumption] = []
    for a in assumptions:
        key = a.assumption_text.lower()[:60]
        if key not in seen:
            seen.append(key)
            unique.append(a)
    return unique


def _format_block(assumptions: list[Assumption]) -> Optional[str]:
    if not assumptions:
        return None
    lines = ["[ASTG ASSUMPTION BLOCK]"]
    for i, a in enumerate(assumptions, 1):
        lines.append(
            f"  A{i}: {a.assumption_text}"
            f" | failure: {a.failure_condition}"
            f" | impact: {a.conclusion_impact}"
            f" | stability: {a.stability.value}"
        )
    lines.append("[END ASSUMPTION BLOCK]")
    return "\n".join(lines)


def _classify(raw_input: str, intent_primary: str) -> list[Assumption]:
    text = raw_input
    assumptions: list[Assumption] = []

    for pat, failure_cond, impact_label, stability in _EXPLICIT_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            clause = m.group(0).strip()
            if _is_common_knowledge(clause):
                continue
            assumptions.append(Assumption(
                assumption_text=(
                    f"The premise {clause[:120]!r} is accurate and applicable."
                ),
                failure_condition=failure_cond,
                conclusion_impact=(
                    f"If false: {impact_label} - response based on this "
                    "premise may be incorrect or misleading."
                ),
                stability=stability,
            ))

    for pat, label, assumption_tmpl, failure_cond, stability in _IMPLICIT_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            clause = m.group(0).strip()
            if _is_common_knowledge(clause):
                continue
            assumptions.append(Assumption(
                assumption_text=f"{assumption_tmpl}: {clause[:100]!r}",
                failure_condition=failure_cond,
                conclusion_impact=(
                    f"If the {label.lower()} is invalid, downstream reasoning "
                    "built on it will produce incorrect conclusions."
                ),
                stability=stability,
            ))

    for pat, assumption_tmpl, failure_cond, stability in _REFERENCE_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            clause = m.group(0).strip()
            if _is_common_knowledge(clause):
                continue
            assumptions.append(Assumption(
                assumption_text=(
                    f"{assumption_tmpl} (referenced as: {clause[:80]!r})"
                ),
                failure_condition=failure_cond,
                conclusion_impact=(
                    "If the referenced content is absent or differs, "
                    "the response will address the wrong subject."
                ),
                stability=stability,
            ))

    for pat, assumption_tmpl, failure_cond, stability in _DOMAIN_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            clause = m.group(0).strip()
            if _is_common_knowledge(clause):
                continue
            assumptions.append(Assumption(
                assumption_text=(
                    f"{assumption_tmpl} (referenced: {clause[:80]!r})"
                ),
                failure_condition=failure_cond,
                conclusion_impact=(
                    "If this domain premise is incorrect, recommendations "
                    "may be invalid or non-compliant."
                ),
                stability=stability,
            ))

    return _deduplicate(assumptions)


def run_astg_classifier(
    raw_input: str,
    icc_gate_data: ICCGateData,
    crs_scope: str | None = None,
) -> ASTGGateData:
    """
    Production ASTG classifier.

    Detects undeclared assumptions using:
    - Explicit markers: I assume, presumably, given that, obviously, clearly
    - Implicit causality: if/then, since, because, this means, this shows
    - Reference-without-provision: refs to docs/data not in context
    - Domain premises: regulatory, market, user-behavior assumptions

    Severity via AssumptionStability:
    - unstable: if false, conclusion changes materially
    - stable: reasonable to hold without user confirmation

    Safe-fail: when uncertain whether a premise qualifies, include it.
    Common knowledge filtered per spec S4.3.

    Spec ref: cosyn_wrapper_classifier_specification.md S4
    Gate spec: cosyn_wrapper_gate_specifications.md ASTG gate
    """
    assumptions = _classify(raw_input, icc_gate_data.intent_primary)
    unstable_present = any(
        a.stability == AssumptionStability.unstable for a in assumptions
    )
    assumption_block_text = _format_block(assumptions)

    return ASTGGateData(
        assumptions_identified=assumptions,
        assumption_count=len(assumptions),
        unstable_assumption_present=unstable_present,
        assumption_block_text=assumption_block_text,
    )
