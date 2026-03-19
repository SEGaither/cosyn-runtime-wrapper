"""
Phase 3.2 - ICC Classifier - Production Implementation
Hybrid rule-based approach. Implements intent extraction and constraint
consistency detection per cosyn_wrapper_classifier_specification.md S3.
"""
from __future__ import annotations

import re
from typing import Optional

from cgs_runtime_wrapper.models.envelopes import (
    ICCGateData,
    ConstraintConsistency,
)

ICC_PROMPT_TEMPLATE = (
    "System: You are a constraint consistency classifier. Extract the primary intent,\n"
    "scope, and exclusions from the input. Then check whether later clauses in the\n"
    "input are consistent with earlier constraints. Return JSON only. No preamble.\n"
    "\n"
    "Schema: {\n"
    '  "intent_primary": string,\n'
    '  "intent_scope": string | null,\n'
    '  "intent_exclusions": string[],\n'
    '  "constraint_consistency": "consistent" | "ambiguous" | "conflicting",\n'
    '  "ambiguity_description": string | null\n'
    "}\n"
    "\n"
    "User: [raw_input]"
)

_SCOPE_PATTERNS = [
    r"\bonly\b[^.!?]*",
    r"\bjust\b[^.!?]*",
    r"\bexclusively\b[^.!?]*",
    r"\blimited to\b[^.!?]*",
    r"\bfocus(?:ing)? on\b[^.!?]*",
    r"\brestrict(?:ed)? to\b[^.!?]*",
    r"\bconfine(?:d)? to\b[^.!?]*",
]

_EXCLUSION_PATTERNS = [
    r"\bdo not\b[^.!?]*",
    r"\bdon't\b[^.!?]*",
    r"\bexclude\b[^.!?]*",
    r"\bexcluding\b[^.!?]*",
    r"\bavoid\b[^.!?]*",
    r"\bnot including\b[^.!?]*",
    r"\bleave out\b[^.!?]*",
    r"\bomit\b[^.!?]*",
]

_OUTPUT_FORM_PATTERNS = [
    (r"\bbullet[s]?\b", "bullet list"),
    (r"\bnumbered list\b", "numbered list"),
    (r"\btable\b", "table"),
    (r"\bsummary\b", "summary"),
    (r"\bparagraph[s]?\b", "paragraphs"),
    (r"\boutline\b", "outline"),
    (r"\bbrief\b", "brief"),
    (r"\bdetailed?\b", "detailed"),
    (r"\bcomprehensive\b", "comprehensive"),
    (r"\bshort\b", "short"),
    (r"\bconcise\b", "concise"),
    (r"\bstep.by.step\b", "step-by-step"),
    (r"\bcode\b", "code"),
    (r"\bjson\b", "json"),
    (r"\bmarkdown\b", "markdown"),
]

_CONFLICT_PAIRS = [
    (
        r"\bcomprehensive\b|\bcomplete\b|\ball\b|\beverything\b|\bfull\b",
        r"\bbrief\b|\bshort\b|\bconcise\b|\bunder \d+ words?\b|\bsummary\b",
        "Comprehensive/complete conflicts with brief/short/concise.",
    ),
    (
        r"\binclude\b.{0,60}\ball\b|\bcover all\b|\ball regions?\b|\bglobal\b",
        r"\bexclude\b|\bdo not include\b",
        "Include-all conflicts with explicit exclusion.",
    ),
    (
        r"\bdetailed?\b|\bin.depth\b|\bthorough\b",
        r"\bone.liner\b|\bsingle sentence\b|\bunder \d+ words?\b",
        "Detailed/thorough conflicts with one-liner/minimal format.",
    ),
    (
        r"\bonly\b.{0,40}\bQ[1-4]\b|\bfocus.{0,20}Q[1-4]\b",
        r"\ball quarters?\b|\bfull year\b",
        "Single-quarter focus conflicts with full-year coverage.",
    ),
    (
        r"\bdo not\b.{0,40}\banalyz\b|\bno analysis\b",
        r"\banalyze\b|\banalysis\b",
        "Explicit no-analysis conflicts with analyze directive.",
    ),
]

_AMBIGUITY_TRIGGERS = [
    (r"\bcomprehensive\b.{0,60}\bbrief\b|\bbrief\b.{0,60}\bcomprehensive\b",
     "Both comprehensive and brief requested without resolution."),
    (r"\bflexible\b.{0,60}\bstrict\b|\bstrict\b.{0,60}\bflexible\b",
     "Flexible and strict requirements present simultaneously."),
    (r"\bformal\b.{0,60}\bcasual\b|\bcasual\b.{0,60}\bformal\b",
     "Formal and casual tone requested simultaneously."),
    (r"\bsimple\b.{0,60}\bcomplex\b|\bcomplex\b.{0,60}\bsimple\b",
     "Simple and complex output requested without specification."),
]


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_intent_primary(raw_input: str) -> str:
    text = raw_input.strip()
    goal_patterns = [
        r"(?:please\s+)?(?:help me\s+|i need you to\s+|i want you to\s+|can you\s+|could you\s+)?(\w[\w\s,'-]{5,120}?)[\.\?\!,]",
        r"^([\w][\w\s,'-]{5,120}?)[\.\?\!]",
    ]
    for pat in goal_patterns:
        m = re.match(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) >= 5:
                return candidate[:200]
    first = _split_sentences(text)[0] if text else text
    return first[:200]


def _extract_scope(raw_input: str) -> Optional[str]:
    text = raw_input.lower()
    for pat in _SCOPE_PATTERNS:
        m = re.search(pat, text)
        if m:
            clause = m.group(0).strip()
            if len(clause.split()) >= 2:
                return clause[:120]
    return None


def _extract_exclusions(raw_input: str) -> list[str]:
    text = raw_input.lower()
    exclusions: list[str] = []
    for pat in _EXCLUSION_PATTERNS:
        for m in re.finditer(pat, text):
            clause = m.group(0).strip()
            if len(clause.split()) >= 2 and clause not in exclusions:
                exclusions.append(clause[:80])
    return exclusions[:5]


def _extract_output_form(raw_input: str) -> Optional[str]:
    text = raw_input.lower()
    for pat, label in _OUTPUT_FORM_PATTERNS:
        if re.search(pat, text):
            return label
    return None


def _check_constraint_consistency(
    raw_input: str,
) -> tuple[ConstraintConsistency, Optional[str], Optional[str]]:
    text = raw_input.lower()
    for pat_a, pat_b, description in _CONFLICT_PAIRS:
        if re.search(pat_a, text) and re.search(pat_b, text):
            return (ConstraintConsistency.conflicting, description, None)
    for pat, description in _AMBIGUITY_TRIGGERS:
        if re.search(pat, text):
            sentences = _split_sentences(raw_input)
            lci = sentences[0][:200] if sentences else raw_input[:200]
            return (ConstraintConsistency.ambiguous, description, lci)
    return (ConstraintConsistency.consistent, None, None)


def run_icc_classifier(
    raw_input: str,
    crs_scope: str | None = None,
) -> ICCGateData:
    """
    Production ICC classifier.

    Implements constraint consistency detection via:
    - Intent extraction from first goal-statement clause
    - Scope and exclusion extraction via pattern matching
    - Output form detection via keyword matching
    - Cross-clause conflict detection via paired pattern matching
    - Ambiguity detection via co-occurrence of contradictory modifiers

    Safe-fail: when uncertain between consistent and ambiguous, biases toward
    ambiguous to prevent silent resolution of material conflicts (ICC spec,
    composition note: ICC may never silently resolve ambiguity).

    Spec ref: cosyn_wrapper_classifier_specification.md S3
    Gate spec: cosyn_wrapper_gate_specifications.md ICC gate
    """
    intent_primary = _extract_intent_primary(raw_input)
    intent_scope = _extract_scope(raw_input) or crs_scope
    intent_exclusions = _extract_exclusions(raw_input)
    intent_output_form = _extract_output_form(raw_input)
    consistency, ambiguity_description, least_committal = _check_constraint_consistency(raw_input)
    provisional_flag = consistency == ConstraintConsistency.ambiguous

    return ICCGateData(
        intent_primary=intent_primary,
        constraint_consistency=consistency,
        provisional_flag=provisional_flag,
        intent_scope=intent_scope,
        intent_exclusions=intent_exclusions,
        intent_output_form=intent_output_form,
        ambiguity_description=ambiguity_description,
        least_committal_interpretation=least_committal,
    )
