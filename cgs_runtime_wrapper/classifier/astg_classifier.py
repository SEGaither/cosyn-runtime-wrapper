"""
Phase 3.3 — ASTG Classifier STUB
Model-based; returns rules-based placeholder.
Prompt template included as constant.
"""
from __future__ import annotations

from cgs_runtime_wrapper.models.envelopes import (
    Assumption,
    ASTGGateData,
    AssumptionStability,
    ICCGateData,
)

# ---------------------------------------------------------------------------
# Prompt template (Phase 3 constant)
# ---------------------------------------------------------------------------

ASTG_PROMPT_TEMPLATE = """\
System: You are an assumption identification classifier. Given the user input and
the parsed intent, identify every unstated premise required to proceed with the
request. For each assumption: state the assumption, its failure condition, the
impact on conclusions if false, and whether it is stable or unstable.
Return JSON only. No preamble.

Stable = reasonable to hold without user confirmation.
Unstable = fragile; if false, conclusion changes materially.

Schema: {
  "assumptions": [
    {
      "assumption_text": string,
      "failure_condition": string,
      "conclusion_impact": string,
      "stability": "stable" | "unstable"
    }
  ],
  "assumption_count": integer,
  "unstable_assumption_present": boolean
}

User input: [raw_input]
Parsed intent: [icc_gate_data.intent_primary]
"""


def run_astg_classifier(
    raw_input: str,
    icc_gate_data: ICCGateData,
    crs_scope: str | None = None,
) -> ASTGGateData:
    """
    STUB: Returns structurally valid placeholder ASTGGateData with zero assumptions.
    In Phase 3+ this will call an LLM using ASTG_PROMPT_TEMPLATE.
    """
    # Placeholder: no assumptions identified (rules-based stub)
    return ASTGGateData(
        assumptions_identified=[],
        assumption_count=0,
        unstable_assumption_present=False,
        assumption_block_text=None,
    )
