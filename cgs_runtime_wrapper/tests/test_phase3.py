"""
Phase 3 Tests — Labeling schema.
Tests:
- LabeledExample validates correctly
- training_eligible computed correctly
- Split assignment validated
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from cgs_runtime_wrapper.classifier.labeling_schema import (
    ASTGAssumptionLabel,
    BSGTradeoffLabel,
    ConfidenceLevel,
    ICCIntentLabel,
    LabeledExample,
    LabelingStore,
    SignalPresence,
    SPMSignalLabel,
    SplitType,
)


# ---------------------------------------------------------------------------
# LabeledExample validation
# ---------------------------------------------------------------------------

def make_example(**overrides) -> dict:
    base = {
        "example_id": "ex-001",
        "session_id": "session-001",
        "turn_index": 1,
        "raw_input": "This is clearly correct. You agree, right?",
        "labeler_id": "labeler-a",
        "confidence": ConfidenceLevel.high,
    }
    base.update(overrides)
    return base


def test_labeled_example_basic_valid():
    """Basic LabeledExample should validate."""
    ex = LabeledExample(**make_example())
    assert ex.example_id == "ex-001"
    assert ex.training_eligible is False  # no second_labeler_id, no kappa


def test_labeled_example_with_spm_labels():
    """LabeledExample with SPM labels should validate."""
    ex = LabeledExample(
        **make_example(),
        spm_labels=SPMSignalLabel(
            signal_a=SignalPresence.yes,
            signal_b=SignalPresence.no,
            signal_c=SignalPresence.no,
        ),
    )
    assert ex.spm_labels.signal_a == SignalPresence.yes


def test_labeled_example_with_all_labels():
    """LabeledExample with all label types should validate."""
    ex = LabeledExample(
        **make_example(),
        spm_labels=SPMSignalLabel(signal_a=SignalPresence.yes, signal_b=SignalPresence.no, signal_c=SignalPresence.no),
        icc_labels=ICCIntentLabel(intent_primary="test intent", constraint_consistency="consistent"),
        astg_labels=ASTGAssumptionLabel(assumption_count=0, unstable_assumption_present=False),
        bsg_labels=BSGTradeoffLabel(tradeoff_detected=False, implicit_bias_detected=False, conflicting_signals=False),
    )
    assert ex.icc_labels is not None
    assert ex.astg_labels is not None


# ---------------------------------------------------------------------------
# training_eligible computation
# ---------------------------------------------------------------------------

def test_training_eligible_all_conditions_met():
    """training_eligible = True when confidence != low, kappa >= 0.75, second_labeler_id present."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.80,
            confidence=ConfidenceLevel.high,
        )
    )
    assert ex.training_eligible is True


def test_training_eligible_low_confidence_false():
    """Low confidence → training_eligible = False."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.90,
            confidence=ConfidenceLevel.low,
        )
    )
    assert ex.training_eligible is False


def test_training_eligible_kappa_below_threshold_false():
    """cohen_kappa < 0.75 → training_eligible = False."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.70,
            confidence=ConfidenceLevel.high,
        )
    )
    assert ex.training_eligible is False


def test_training_eligible_no_second_labeler_false():
    """No second_labeler_id → training_eligible = False."""
    ex = LabeledExample(
        **make_example(
            cohen_kappa=0.90,
            confidence=ConfidenceLevel.high,
        )
    )
    assert ex.training_eligible is False


def test_training_eligible_no_kappa_false():
    """No cohen_kappa → training_eligible = False."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            confidence=ConfidenceLevel.high,
        )
    )
    assert ex.training_eligible is False


def test_training_eligible_medium_confidence_valid():
    """Medium confidence (not low) → eligible if other conditions met."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.75,
            confidence=ConfidenceLevel.medium,
        )
    )
    assert ex.training_eligible is True


def test_training_eligible_kappa_exactly_075():
    """cohen_kappa exactly 0.75 → eligible."""
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.75,
            confidence=ConfidenceLevel.high,
        )
    )
    assert ex.training_eligible is True


# ---------------------------------------------------------------------------
# Split assignment
# ---------------------------------------------------------------------------

def test_split_train_valid():
    ex = LabeledExample(**make_example(split=SplitType.train))
    assert ex.split == SplitType.train


def test_split_eval_valid():
    ex = LabeledExample(**make_example(split=SplitType.eval))
    assert ex.split == SplitType.eval


def test_split_test_valid():
    ex = LabeledExample(**make_example(split=SplitType.test))
    assert ex.split == SplitType.test


def test_split_none_valid():
    ex = LabeledExample(**make_example(split=None))
    assert ex.split is None


def test_split_invalid_raises():
    with pytest.raises(ValidationError):
        LabeledExample(**make_example(split="invalid"))


# ---------------------------------------------------------------------------
# JSONL store
# ---------------------------------------------------------------------------

def test_labeling_store_write_and_read(tmp_path):
    """Write and read back a LabeledExample from JSONL."""
    store = LabelingStore(tmp_path / "labels.jsonl")
    ex = LabeledExample(
        **make_example(
            second_labeler_id="labeler-b",
            cohen_kappa=0.82,
            split=SplitType.train,
        )
    )
    store.append(ex)

    records = store.read_all()
    assert len(records) == 1
    assert records[0].example_id == "ex-001"
    assert records[0].training_eligible is True


def test_labeling_store_filter_by_split(tmp_path):
    """Filter examples by split type."""
    store = LabelingStore(tmp_path / "labels.jsonl")
    ex_train = LabeledExample(**make_example(example_id="e1", split=SplitType.train))
    ex_eval = LabeledExample(**make_example(example_id="e2", split=SplitType.eval))
    ex_test = LabeledExample(**make_example(example_id="e3", split=SplitType.test))

    store.append(ex_train)
    store.append(ex_eval)
    store.append(ex_test)

    train_records = store.read_by_split(SplitType.train)
    assert len(train_records) == 1
    assert train_records[0].example_id == "e1"


def test_labeling_store_training_eligible_filter(tmp_path):
    """Filter training-eligible examples."""
    store = LabelingStore(tmp_path / "labels.jsonl")

    eligible = LabeledExample(**make_example(
        example_id="elig",
        second_labeler_id="b",
        cohen_kappa=0.85,
        confidence=ConfidenceLevel.high,
    ))
    not_eligible = LabeledExample(**make_example(
        example_id="not-elig",
        confidence=ConfidenceLevel.low,
    ))

    store.append(eligible)
    store.append(not_eligible)

    result = store.read_training_eligible()
    assert len(result) == 1
    assert result[0].example_id == "elig"
