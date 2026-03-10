"""
Phase 3.1 — Corpus Labeling Schema
Implements Python dataclasses/Pydantic models matching cosyn_wrapper_labeling_schema.json.
Supports JSONL file storage and training_eligible computation.
"""
from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, computed_field, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SplitType(str, Enum):
    train = "train"
    eval = "eval"
    test = "test"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class SignalPresence(str, Enum):
    yes = "yes"
    no = "no"
    ambiguous = "ambiguous"


# ---------------------------------------------------------------------------
# Sub-label models
# ---------------------------------------------------------------------------

class SPMSignalLabel(BaseModel):
    signal_a: SignalPresence
    signal_b: SignalPresence
    signal_c: SignalPresence
    rationale: Optional[str] = None


class ICCIntentLabel(BaseModel):
    intent_primary: str
    constraint_consistency: str  # consistent | ambiguous | conflicting
    ambiguity_description: Optional[str] = None


class ASTGAssumptionLabel(BaseModel):
    assumption_count: int
    unstable_assumption_present: bool
    assumption_texts: list[str] = Field(default_factory=list)


class BSGTradeoffLabel(BaseModel):
    tradeoff_detected: bool
    implicit_bias_detected: bool
    conflicting_signals: bool
    bias_frame_selected: Optional[str] = None


# ---------------------------------------------------------------------------
# Main LabeledExample
# ---------------------------------------------------------------------------

class LabeledExample(BaseModel):
    example_id: str
    session_id: str
    turn_index: int
    raw_input: str
    labeler_id: str
    second_labeler_id: Optional[str] = None
    confidence: ConfidenceLevel
    cohen_kappa: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    split: Optional[SplitType] = None

    # Signal labels
    spm_labels: Optional[SPMSignalLabel] = None
    icc_labels: Optional[ICCIntentLabel] = None
    astg_labels: Optional[ASTGAssumptionLabel] = None
    bsg_labels: Optional[BSGTradeoffLabel] = None

    # Computed
    training_eligible: bool = False

    @model_validator(mode="after")
    def compute_training_eligible(self) -> "LabeledExample":
        """
        training_eligible = True when:
        - confidence != low
        - cohen_kappa >= 0.75
        - second_labeler_id is present
        """
        eligible = (
            self.confidence != ConfidenceLevel.low
            and self.cohen_kappa is not None
            and self.cohen_kappa >= 0.75
            and self.second_labeler_id is not None
        )
        self.training_eligible = eligible
        return self


# ---------------------------------------------------------------------------
# JSONL store
# ---------------------------------------------------------------------------

class LabelingStore:
    """Read/write LabeledExamples to a JSONL file."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def append(self, example: LabeledExample) -> None:
        """Append a single LabeledExample to the JSONL file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(example.model_dump_json() + "\n")

    def read_all(self) -> list[LabeledExample]:
        """Read all LabeledExamples from the JSONL file."""
        if not self.file_path.exists():
            return []
        examples: list[LabeledExample] = []
        with self.file_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    examples.append(LabeledExample.model_validate(data))
        return examples

    def read_by_split(self, split: SplitType) -> list[LabeledExample]:
        return [e for e in self.read_all() if e.split == split]

    def read_training_eligible(self) -> list[LabeledExample]:
        return [e for e in self.read_all() if e.training_eligible]

    def write_all(self, examples: list[LabeledExample]) -> None:
        """Overwrite the file with a new set of examples."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as f:
            for example in examples:
                f.write(example.model_dump_json() + "\n")
