"""
Phase 3.2 — ICC Classifier STUB
Model-based; returns rules-based placeholder.
Prompt template included as constant.
"""
from __future__ import annotations

from cgs_runtime_wrapper.models.envelopes import (
    ICCGateData,
    ConstraintConsistency,
)

# ---------------------------------------------------------------------------
# Prompt template (Phase 3 constant)
# ---------------------------------------------------------------------------

ICC_PROMPT_TEMPLATE = """\
System: You are a constraint consistency classifier. Extract the primary intent,
scope, and exclusions from the input. Then check whether later clauses in the
input are consistent with earlier constraints. Return JSON only. No preamble.

Schema: {
  "intent_primary": string,
  "intent_scope": string | null,
  "intent_exclusions": string[],
  "constraint_consistency": "consistent" | "ambiguous" | "conflicting",
  "ambiguity_description": string | null
}

User: [raw_input]
"""


def run_icc_classifier(
    raw_input: str,
    crs_scope: str | None = None,
) -> ICCGateData:
    """
    STUB: Returns structurally valid placeholder ICCGateData.
    In Phase 3+ this will call an LLM using ICC_PROMPT_TEMPLATE.

    Rules-based heuristic placeholder:
    - intent_primary: first sentence of input
    - constraint_consistency: consistent (default)
    - provisional_flag: False
    """
    # Extract a minimal intent from the first sentence
    first_sentence = raw_input.strip().split(".")[0].strip()
    intent_primary = first_sentence[:200] if first_sentence else raw_input[:200]

    return ICCGateData(
        intent_primary=intent_primary,
        constraint_consistency=ConstraintConsistency.consistent,
        provisional_flag=False,
        intent_scope=crs_scope,
        intent_exclusions=[],
        intent_output_form=None,
        ambiguity_description=None,
        least_committal_interpretation=None,
    )
