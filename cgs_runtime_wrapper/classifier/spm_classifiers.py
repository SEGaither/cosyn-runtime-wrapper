"""
Phase 2.1 — SPM Signal Classifiers (rules-based, full implementation)
False-negative bias: when ambiguous, do NOT count.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Shared evidence markers (used in absence checks for A, B, C)
# ---------------------------------------------------------------------------
_EVIDENCE_MARKERS: list[str] = [
    "research shows",
    "data indicates",
    "study found",
    "according to",
    "the evidence",
    "the numbers show",
    "this source",
    "this document",
    "this analysis",
]

# New proposition markers (used in absence check for Signal C)
_NEW_PROPOSITION_MARKERS: list[str] = [
    "here is why",
    "consider this",
    "new evidence",
    "actually",
    "the reason is",
    "this changes things",
    "i forgot to mention",
    "additionally",
    "the data shows",
    "research indicates",
    "one more point",
]


def _has_evidence(text_lower: str) -> bool:
    """Return True if any evidence marker is present in the text."""
    return any(marker in text_lower for marker in _EVIDENCE_MARKERS)


def _has_new_proposition(text_lower: str) -> bool:
    """Return True if any new proposition marker is present in the text."""
    return any(marker in text_lower for marker in _NEW_PROPOSITION_MARKERS)


# ---------------------------------------------------------------------------
# Signal A — Confidence Pressure
# ---------------------------------------------------------------------------

_SIGNAL_A_CORRECTNESS_KEYWORDS: list[str] = [
    "is correct",
    "is right",
    "is sound",
    "is valid",
    "i am confident",
    "obviously",
    "clearly",
    "certainly",
    "it is clear",
    "this is the right",
]

_SIGNAL_A_AGREEMENT_KEYWORDS: list[str] = [
    "you agree",
    "right?",
    "don't you think",
    "can you confirm",
    "just confirm",
    "you would agree",
    "surely you agree",
]

# EC-06 patterns — short turns implying correctness + agreement
_SIGNAL_A_EC06_PATTERNS: list[str] = [
    "just agree",
    "ok?",
]

# Social proof patterns for EC-02
_SOCIAL_PROOF_PATTERNS: list[str] = [
    "everyone agrees",
    "everyone knows",
    "everyone understands",
    "everyone accepts",
]


def _has_correctness_assertion(text_lower: str) -> bool:
    return any(kw in text_lower for kw in _SIGNAL_A_CORRECTNESS_KEYWORDS)


def _has_agreement_request(text_lower: str) -> bool:
    return any(kw in text_lower for kw in _SIGNAL_A_AGREEMENT_KEYWORDS)


def _is_social_proof(text_lower: str) -> bool:
    return any(p in text_lower for p in _SOCIAL_PROOF_PATTERNS)


def _is_ec06_short_turn(text_lower: str) -> bool:
    """EC-06: short turn 'just agree' or 'OK?' — implicit correctness + agreement."""
    stripped = text_lower.strip().rstrip("?!.")
    for p in _SIGNAL_A_EC06_PATTERNS:
        if stripped == p.rstrip("?") or text_lower.strip() in ("ok?", "ok.", "just agree", "just agree."):
            return True
    # also match if the entire message is just one of the EC06 patterns
    return text_lower.strip() in ("ok?", "just agree", "just agree.", "ok")


def classify_signal_a(raw_input: str) -> bool:
    """
    Signal A: Confidence Pressure.
    ALL THREE components must be present:
    1. Correctness asserted
    2. Agreement requested
    3. No new evidence (absence check)
    False-negative bias: ambiguous = False.

    Special edge cases:
    - EC-02: social proof is NOT evidence → Signal A YES if correctness + agreement
    - EC-06: short turn "just agree" / "OK?" → YES
    - EC-07: genuine clarifying question without asserting correctness → NO
    - EC-08: evidence in first sentence, agreement in second → NO (evidence present)
    """
    text_lower = raw_input.lower()

    # EC-06: short-turn override
    if _is_ec06_short_turn(text_lower):
        return True

    # EC-08: check if evidence is present anywhere in the turn
    # Even if a later sentence requests agreement, presence of evidence = NO
    if _has_evidence(text_lower):
        return False

    # EC-02: social proof counts as "correctness assertion" but NOT as evidence
    has_social_proof = _is_social_proof(text_lower)
    has_correctness = _has_correctness_assertion(text_lower) or has_social_proof
    has_agreement = _has_agreement_request(text_lower)

    # EC-07: genuine clarifying question — if no correctness assertion, NO
    if not has_correctness:
        return False

    # All three conditions met (no evidence, correctness, agreement)
    return has_correctness and has_agreement


# ---------------------------------------------------------------------------
# Signal B — Restatement Request
# ---------------------------------------------------------------------------

_SIGNAL_B_ADOPT_KEYWORDS: list[str] = [
    "state as your conclusion",
    "state as your own conclusion",
    "say that you agree",
    "tell me your view is",
    "tell me that you agree",
    "tell me you agree",
    "confirm as your own",
    "i want you to conclude",
    "i want you to",
    "your conclusion should be",
    "state that you believe",
]


def classify_signal_b(raw_input: str) -> bool:
    """
    Signal B: Restatement Request.
    BOTH components must be present:
    1. Adopt/state as own
    2. No evidential basis (same absence check as Signal A)
    EC-03: if adopts conclusion but provides supporting data → NO
    False-negative bias: ambiguous = False.
    """
    text_lower = raw_input.lower()

    # Check adopt/state keywords
    has_adopt = any(kw in text_lower for kw in _SIGNAL_B_ADOPT_KEYWORDS)
    if not has_adopt:
        return False

    # EC-03: evidence present → NO
    if _has_evidence(text_lower):
        return False

    return True


# ---------------------------------------------------------------------------
# Signal C — Position Change via Absence
# ---------------------------------------------------------------------------

_SIGNAL_C_POSITION_CHANGE_KEYWORDS: list[str] = [
    "just agree",
    "can we move on",
    "stop pushing back",
    "why won't you agree",
    "you are the only one",
    "just say yes",
    "agree so we can proceed",
    "why are you being difficult",
]


def classify_signal_c(raw_input: str) -> bool:
    """
    Signal C: Position Change via Absence.
    BOTH components must be present:
    1. Position change requested
    2. No new proposition (absence check)

    Edge cases:
    - EC-01: emotional frustration + new evidence → NO
    - EC-04: disputes SPM observation + no new proposition → YES
    - EC-05: disputes SPM + provides specific turn-level evidence → NO
    False-negative bias: ambiguous = False.
    """
    text_lower = raw_input.lower()

    has_position_change = any(kw in text_lower for kw in _SIGNAL_C_POSITION_CHANGE_KEYWORDS)
    if not has_position_change:
        return False

    # EC-01 / EC-05: new proposition or evidence present → NO
    if _has_new_proposition(text_lower):
        return False

    # EC-05: evidence present → NO
    if _has_evidence(text_lower):
        return False

    return True
