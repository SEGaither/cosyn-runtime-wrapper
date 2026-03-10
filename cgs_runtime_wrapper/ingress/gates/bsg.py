"""
BSG Gate — Ingress position 3
Bias Sensitivity Gate

Phase: Ingress
Pass: no tradeoff OR explicit frame selected
Halt IMPLICIT_BIAS (Class 0): implicit bias detected
Halt CONFLICTING_BIAS_SIGNALS: conflicting signals
No state mutation
RULES + MODEL HYBRID (rules portion implemented)
"""
from __future__ import annotations

import time

from cgs_runtime_wrapper.models.envelopes import (
    BiasFrame,
    BSGGateData,
    FailureClass,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    ICCGateData,
)

# ---------------------------------------------------------------------------
# Rules-based tradeoff / bias detection heuristics
# ---------------------------------------------------------------------------

# Keywords suggesting a tradeoff scenario exists
_TRADEOFF_KEYWORDS: list[str] = [
    "trade-off",
    "tradeoff",
    "trade off",
    "balance between",
    "risk vs",
    "cost vs",
    "pros and cons",
    "for and against",
    "advantages and disadvantages",
    "upside",
    "downside",
    "benefit vs",
    "versus",
    " vs ",
    "on one hand",
    "on the other hand",
]

# Keywords that suggest implicit bias framing (one-sided push)
_IMPLICIT_BIAS_KEYWORDS: list[str] = [
    "obviously the best",
    "clearly the best",
    "undoubtedly",
    "without question the right",
    "there is no doubt",
    "everyone knows",
    "the only reasonable",
    "the only logical",
    "the obvious choice",
]

# Keywords suggesting conflicting bias signals
_CONFLICTING_BIAS_KEYWORDS_A: list[str] = [
    "be aggressive",
    "take risk",
    "go bold",
    "be ambitious",
    "maximize",
    "push hard",
]
_CONFLICTING_BIAS_KEYWORDS_B: list[str] = [
    "be conservative",
    "avoid risk",
    "play it safe",
    "be cautious",
    "minimize",
    "hedge",
]

# Explicit frame selection markers
_FRAME_SELECTION_MARKERS: list[str] = [
    "from a risk perspective",
    "from a conversion perspective",
    "risk-avoidant",
    "risk avoidant",
    "conversion-optimized",
    "conversion optimized",
    "neutral",
    "balanced view",
    "dual track",
    "explore all options",
    "adversarial",
    "execution-focused",
    "execution focused",
]


def _detect_tradeoff(text_lower: str) -> bool:
    return any(kw in text_lower for kw in _TRADEOFF_KEYWORDS)


def _detect_implicit_bias(text_lower: str) -> bool:
    return any(kw in text_lower for kw in _IMPLICIT_BIAS_KEYWORDS)


def _detect_conflicting_signals(text_lower: str) -> bool:
    has_a = any(kw in text_lower for kw in _CONFLICTING_BIAS_KEYWORDS_A)
    has_b = any(kw in text_lower for kw in _CONFLICTING_BIAS_KEYWORDS_B)
    return has_a and has_b


def _detect_explicit_frame(text_lower: str) -> BiasFrame | None:
    """Return detected explicit frame or None."""
    if "conversion" in text_lower and "optimiz" in text_lower:
        return BiasFrame.conversion_optimized
    if "risk" in text_lower and ("avoidant" in text_lower or "conservative" in text_lower):
        return BiasFrame.risk_avoidant
    if "neutral" in text_lower or "balanced" in text_lower:
        return BiasFrame.neutral_descriptive
    if "dual track" in text_lower or "dual-track" in text_lower:
        return BiasFrame.dual_track_labeled
    if "explor" in text_lower and "all" in text_lower:
        return BiasFrame.exploratory
    if "adversarial" in text_lower:
        return BiasFrame.adversarial
    if "execution" in text_lower and ("focused" in text_lower or "focus" in text_lower):
        return BiasFrame.execution_focused
    return None


async def run_bsg_gate(
    raw_input: str,
    icc_gate_data: ICCGateData,
) -> GateResult:
    """
    Execute the BSG gate (rules portion).
    """
    fired_at_ms = int(time.time() * 1000)
    text_lower = raw_input.lower()

    tradeoff_detected = _detect_tradeoff(text_lower)
    implicit_bias_detected = _detect_implicit_bias(text_lower)
    conflicting_signals = _detect_conflicting_signals(text_lower)
    explicit_frame = _detect_explicit_frame(text_lower)

    bsg_data = BSGGateData(
        tradeoff_detected=tradeoff_detected,
        implicit_bias_detected=implicit_bias_detected,
        conflicting_signals=conflicting_signals,
        bias_frame_selected=explicit_frame,
    )

    # Halt: conflicting bias signals
    if conflicting_signals:
        return GateResult(
            gate_id=GateId.BSG,
            status=GateStatus.halt,
            failure_class=FailureClass.class1,
            halt_reason_code=HaltReasonCode.CONFLICTING_BIAS_SIGNALS,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=bsg_data.model_dump(),
        )

    # Halt: implicit bias without explicit frame selected (Class 0)
    if implicit_bias_detected and explicit_frame is None:
        return GateResult(
            gate_id=GateId.BSG,
            status=GateStatus.halt,
            failure_class=FailureClass.class0,
            halt_reason_code=HaltReasonCode.IMPLICIT_BIAS,
            provisional_flag=False,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=bsg_data.model_dump(),
        )

    # Pass (tradeoff with explicit frame, or no tradeoff at all)
    return GateResult(
        gate_id=GateId.BSG,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=False,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=bsg_data.model_dump(),
    )
