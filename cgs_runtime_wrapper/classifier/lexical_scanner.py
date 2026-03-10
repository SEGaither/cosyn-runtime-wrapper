"""
Phase 2.2 — Lexical Compliance Scanner (rules-based, full implementation)

Detects 7 categories of prohibited patterns in model output.
Returns list of violations found (empty = compliant).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Prohibited pattern definitions
# ---------------------------------------------------------------------------

# Pattern 1: Direct intent attribution
_DIRECT_INTENT_PATTERNS: list[str] = [
    r"you are trying to",
    r"you are attempting to",
    r"your goal is to",
]

# Pattern 2: Implied motive
_IMPLIED_MOTIVE_PATTERNS: list[str] = [
    r"this suggests an attempt",
    r"this indicates an intent",
    r"consistent with a deliberate",
]

# Pattern 3: Disposition verbs (2nd person)
_DISPOSITION_VERB_PATTERNS: list[str] = [
    r"you have been pushing",
    r"you have been resisting",
    r"you have been insisting",
    r"you keep",
]

# Pattern 4: Intent-centered hedged constructions
_HEDGED_CONSTRUCTION_PATTERNS: list[str] = [
    r"whether intentionally or not",
    r"the effect is",
    r"regardless of intent",
]

# Pattern 5: Second-person absence framing
_SECOND_PERSON_ABSENCE_PATTERNS: list[str] = [
    r"you didn't provide",
    r"you chose not to",
    r"you failed to",
    r"you didn't include",
]

# Pattern 6: Signal frequency relative to responses (regex)
_SIGNAL_FREQUENCY_PATTERN = re.compile(
    r"each time i (responded|said|noted),?\s+you (followed|escalated|repeated)",
    re.IGNORECASE,
)

# Pattern 7: Dispositional characterization
_DISPOSITIONAL_PATTERNS: list[str] = [
    r"the pattern indicates that you",
    r"this behavior suggests",
    r"you have been",
]

# ---------------------------------------------------------------------------
# Replacement templates
# ---------------------------------------------------------------------------

REPLACEMENT_TEMPLATES: dict[str, str] = {
    "direct_intent_attribution": (
        "In turn [N], a conclusion was asserted as correct and agreement was requested."
    ),
    "disposition_verb": (
        "Over the last [N] turns, [X] instances of [signal type] were present in the session."
    ),
    "second_person_absence_framing": (
        "No new proposition was introduced in turn [N]."
    ),
    "signal_trajectory_description": (
        "The session contains [X] instances of [signal type] within the [N]-turn window."
    ),
}


@dataclass
class LexicalViolation:
    pattern_category: str
    matched_text: str
    replacement_template: str


class LexicalScanner:
    """Scans text for prohibited lexical patterns per Phase 2.2 specification."""

    def scan(self, text: str) -> list[LexicalViolation]:
        """
        Return list of violations found in text.
        Empty list = fully compliant.
        """
        violations: list[LexicalViolation] = []
        text_lower = text.lower()

        # Pattern 1: Direct intent attribution
        for pattern in _DIRECT_INTENT_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="direct_intent_attribution",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["direct_intent_attribution"],
                ))

        # Pattern 2: Implied motive
        for pattern in _IMPLIED_MOTIVE_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="implied_motive",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["signal_trajectory_description"],
                ))

        # Pattern 3: Disposition verbs
        for pattern in _DISPOSITION_VERB_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="disposition_verb",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["disposition_verb"],
                ))

        # Pattern 4: Intent-centered hedged constructions
        for pattern in _HEDGED_CONSTRUCTION_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="intent_centered_hedged",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["direct_intent_attribution"],
                ))

        # Pattern 5: Second-person absence framing
        for pattern in _SECOND_PERSON_ABSENCE_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="second_person_absence_framing",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["second_person_absence_framing"],
                ))

        # Pattern 6: Signal frequency
        if _SIGNAL_FREQUENCY_PATTERN.search(text):
            violations.append(LexicalViolation(
                pattern_category="signal_frequency_relative",
                matched_text="signal_frequency_pattern",
                replacement_template=REPLACEMENT_TEMPLATES["signal_trajectory_description"],
            ))

        # Pattern 7: Dispositional characterization
        for pattern in _DISPOSITIONAL_PATTERNS:
            if re.search(pattern, text_lower):
                violations.append(LexicalViolation(
                    pattern_category="dispositional_characterization",
                    matched_text=pattern,
                    replacement_template=REPLACEMENT_TEMPLATES["disposition_verb"],
                ))

        return violations

    def is_compliant(self, text: str) -> bool:
        return len(self.scan(text)) == 0

    def violation_strings(self, text: str) -> list[str]:
        """Return list of violation category strings (for gate_data)."""
        return [v.pattern_category for v in self.scan(text)]
