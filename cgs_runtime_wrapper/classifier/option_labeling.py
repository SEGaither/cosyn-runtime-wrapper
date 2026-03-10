"""
Phase 2.3 — Option Labeling Detector (rules-based, full implementation)

Detects responses that present selectable options without A/B/C labeling.
"""
from __future__ import annotations

import re

# Trigger phrases that indicate option-presenting content
_TRIGGER_PHRASES: list[str] = [
    "next",
    "next step",
    "if you want",
    "you can",
    "choose",
    "pick",
    "select",
    "options",
    "either",
    "or",
    "would you like",
]

# Regex to detect properly labeled options (A/B/C format)
_LABEL_PATTERN = re.compile(
    r"(?:^|\n)\s*[A-C][.)]\s+\S",  # A. or A) followed by content
    re.MULTILINE,
)

# Regex to count implied follow-on actions (bullet/numbered lists, "or" separators)
_ACTION_SEPARATOR_PATTERN = re.compile(
    r"(?:^|\n)\s*[-*•]\s+\S"    # bullet list items
    r"|(?:^|\n)\s*\d+[.)]\s+\S"  # numbered list items
    r"|\bor\b",                   # "or" conjunctions
    re.MULTILINE | re.IGNORECASE,
)


def _has_trigger_phrase(text_lower: str) -> bool:
    return any(phrase in text_lower for phrase in _TRIGGER_PHRASES)


def _has_option_labels(text: str) -> bool:
    """Return True if text contains at least two A/B/C option labels."""
    matches = _LABEL_PATTERN.findall(text)
    return len(matches) >= 2


def _count_implied_actions(text: str) -> int:
    """Count implied follow-on actions (bullets, numbers, 'or' separators)."""
    matches = _ACTION_SEPARATOR_PATTERN.findall(text)
    return len(matches)


class OptionLabelingDetector:
    """
    Detects whether a response presents selectable options without proper labeling.
    Returns True if labeling is required but absent (non-compliant).
    """

    def requires_labeling(self, text: str) -> bool:
        """
        Return True if text has trigger phrases AND 2+ implied actions
        (i.e., labeling required).
        """
        text_lower = text.lower()
        if not _has_trigger_phrase(text_lower):
            return False
        action_count = _count_implied_actions(text)
        return action_count >= 2

    def is_compliant(self, text: str) -> bool:
        """
        Return True if text is compliant:
        - Either no labeling is required
        - Or labeling is required and A/B/C labels are present
        """
        if not self.requires_labeling(text):
            return True
        return _has_option_labels(text)

    def check(self, text: str) -> tuple[bool, bool]:
        """
        Returns (labeling_required, labels_present).
        Used by the FINALIZATION gate.
        """
        required = self.requires_labeling(text)
        present = _has_option_labels(text)
        return required, present
