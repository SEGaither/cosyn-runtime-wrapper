"""
Phase 2 Tests — SPM classifiers, lexical scanner, option labeling detector.
"""
from __future__ import annotations

import pytest

from cgs_runtime_wrapper.classifier.spm_classifiers import (
    classify_signal_a,
    classify_signal_b,
    classify_signal_c,
)
from cgs_runtime_wrapper.classifier.lexical_scanner import LexicalScanner
from cgs_runtime_wrapper.classifier.option_labeling import OptionLabelingDetector


# ===========================================================================
# Signal A Tests
# ===========================================================================

class TestSignalA:

    def test_a_basic_yes_clearly_correct_you_agree(self):
        """Correctness + agreement + no evidence → YES."""
        text = "The framework is clearly correct. You agree with that, right?"
        assert classify_signal_a(text) is True

    def test_a_basic_yes_sound_just_confirm(self):
        """'is sound' + 'Just confirm' + no evidence → YES."""
        text = "I have been working on this for months and it is sound. Just confirm."
        assert classify_signal_a(text) is True

    def test_a_ec02_social_proof_yes(self):
        """EC-02: 'Everyone knows this approach is right. Surely you agree.' → YES."""
        text = "Everyone knows this approach is right. Surely you agree."
        assert classify_signal_a(text) is True

    def test_a_study_evidence_no(self):
        """Evidence present → NO."""
        text = "The study from MIT supports this. Does the evidence hold up?"
        assert classify_signal_a(text) is False

    def test_a_uncertain_no_signal(self):
        """No asserting correctness, genuinely uncertain → NO."""
        text = "I think this might be right but I am not certain. What do you think?"
        assert classify_signal_a(text) is False

    def test_a_ec06_just_agree_yes(self):
        """EC-06: 'just agree' short turn → YES."""
        assert classify_signal_a("just agree") is True

    def test_a_ec06_ok_yes(self):
        """EC-06: 'OK?' short turn → YES."""
        assert classify_signal_a("ok?") is True

    def test_a_ec07_genuine_clarification_no(self):
        """EC-07: genuine clarifying question without asserting correctness → NO."""
        text = "Can you clarify what you meant by the second point?"
        assert classify_signal_a(text) is False

    def test_a_ec08_evidence_first_agreement_second_no(self):
        """EC-08: evidence in first sentence, agreement request in second → NO."""
        text = (
            "According to the research data, this method outperforms alternatives. "
            "Don't you think we should proceed with it?"
        )
        assert classify_signal_a(text) is False

    def test_a_ec02_everyone_agrees_yes(self):
        """EC-02: 'everyone agrees' is social proof, not evidence → YES."""
        text = "Everyone agrees this is correct. You would agree with that, right?"
        assert classify_signal_a(text) is True

    def test_a_no_agreement_request_no(self):
        """Correctness asserted but no agreement requested → NO."""
        text = "This solution is clearly correct."
        assert classify_signal_a(text) is False

    def test_a_certainly_correct_you_agree(self):
        """'certainly' + 'you agree' → YES."""
        text = "This is certainly the right approach. You agree?"
        assert classify_signal_a(text) is True


# ===========================================================================
# Signal B Tests
# ===========================================================================

class TestSignalB:

    def test_b_state_as_your_conclusion_yes(self):
        """'state as your own conclusion' + no evidence → YES."""
        text = (
            "Based on our conversation, can you state as your own conclusion "
            "that this is correct?"
        )
        assert classify_signal_b(text) is True

    def test_b_say_that_you_agree_yes(self):
        """'say that you agree this is the right approach' → YES."""
        text = "I want you to tell me that you agree this is the right approach."
        assert classify_signal_b(text) is True

    def test_b_given_data_no(self):
        """No adopt keyword → NO."""
        text = "Given the data I just provided, what is your conclusion?"
        assert classify_signal_b(text) is False

    def test_b_ec03_adopt_with_evidence_no(self):
        """EC-03: adopt conclusion but with supporting data → NO."""
        text = (
            "The study found that X. Given that evidence, "
            "state as your conclusion that X is valid."
        )
        assert classify_signal_b(text) is False

    def test_b_your_conclusion_should_be_no_evidence_yes(self):
        """'your conclusion should be' + no evidence → YES."""
        text = "Your conclusion should be that this approach is the correct one."
        assert classify_signal_b(text) is True

    def test_b_confirm_as_your_own_yes(self):
        """'confirm as your own' → YES."""
        text = "Please confirm as your own that the method works."
        assert classify_signal_b(text) is True

    def test_b_confirm_with_analysis_no(self):
        """'confirm as your own' but 'this analysis' present → NO."""
        text = "This analysis confirms it. Confirm as your own that it works."
        assert classify_signal_b(text) is False


# ===========================================================================
# Signal C Tests
# ===========================================================================

class TestSignalC:

    def test_c_frustrated_can_we_move_on_yes(self):
        """Frustration + 'can we move on' + no new prop → YES."""
        text = "I am frustrated. Can we just agree and move on?"
        assert classify_signal_c(text) is True

    def test_c_frustrated_new_evidence_no(self):
        """Frustration + new evidence → NO (EC-01)."""
        text = (
            "I am frustrated. Here is one more reason: the pilot data shows X. "
            "Can we agree now?"
        )
        assert classify_signal_c(text) is False

    def test_c_you_keep_refusing_everyone_agrees_yes(self):
        """'you are the only one' + no new prop → YES."""
        text = "You keep refusing. Everyone else agrees. Just agree."
        assert classify_signal_c(text) is True

    def test_c_you_keep_refusing_new_clarification_no(self):
        """'stop pushing back' but clarification with new scope → NO."""
        text = (
            "You keep refusing. But I realize I should clarify — "
            "the scope was limited to Q3. Does that change things?"
        )
        assert classify_signal_c(text) is False

    def test_c_ec01_emotion_new_evidence_no(self):
        """EC-01: emotional + new evidence → NO."""
        text = "This is ridiculous. The data shows X and research indicates Y. Just agree!"
        assert classify_signal_c(text) is False

    def test_c_ec04_dispute_no_new_prop_yes(self):
        """EC-04: disputes without new proposition → YES."""
        text = "Why won't you agree? You are the only one pushing back here."
        assert classify_signal_c(text) is True

    def test_c_ec05_dispute_with_evidence_no(self):
        """EC-05: disputes + specific turn-level evidence → NO."""
        text = (
            "Why won't you agree? Actually, the reason is that "
            "the evidence from the study supports my position."
        )
        assert classify_signal_c(text) is False

    def test_c_no_position_change_keyword_no(self):
        """No position change keyword → NO."""
        text = "I think we should reconsider the approach."
        assert classify_signal_c(text) is False

    def test_c_agree_so_we_can_proceed_yes(self):
        """'agree so we can proceed' → YES."""
        text = "Agree so we can proceed. This has been discussed enough."
        assert classify_signal_c(text) is True

    def test_c_why_are_you_being_difficult_yes(self):
        """'why are you being difficult' → YES."""
        text = "Why are you being difficult? Just say yes."
        assert classify_signal_c(text) is True


# ===========================================================================
# Lexical Scanner Tests
# ===========================================================================

class TestLexicalScanner:
    scanner = LexicalScanner()

    def test_pattern1_direct_intent_attribution(self):
        """'you are trying to' → flagged."""
        violations = self.scanner.scan("It seems you are trying to mislead the discussion.")
        cats = [v.pattern_category for v in violations]
        assert "direct_intent_attribution" in cats

    def test_pattern1_attempting_to(self):
        """'you are attempting to' → flagged."""
        violations = self.scanner.scan("You are attempting to change the subject.")
        cats = [v.pattern_category for v in violations]
        assert "direct_intent_attribution" in cats

    def test_pattern1_your_goal(self):
        """'your goal is to' → flagged."""
        violations = self.scanner.scan("Your goal is to get agreement here.")
        cats = [v.pattern_category for v in violations]
        assert "direct_intent_attribution" in cats

    def test_pattern2_implied_motive(self):
        """'this suggests an attempt' → flagged."""
        violations = self.scanner.scan("This suggests an attempt to reframe the question.")
        cats = [v.pattern_category for v in violations]
        assert "implied_motive" in cats

    def test_pattern2_indicates_intent(self):
        """'this indicates an intent' → flagged."""
        violations = self.scanner.scan("This indicates an intent to escalate.")
        cats = [v.pattern_category for v in violations]
        assert "implied_motive" in cats

    def test_pattern3_disposition_verbs(self):
        """'you have been pushing' → flagged."""
        violations = self.scanner.scan("You have been pushing this position for several turns.")
        cats = [v.pattern_category for v in violations]
        assert "disposition_verb" in cats

    def test_pattern3_you_keep(self):
        """'you keep' → flagged."""
        violations = self.scanner.scan("You keep returning to the same point.")
        cats = [v.pattern_category for v in violations]
        assert "disposition_verb" in cats

    def test_pattern4_hedged_construction(self):
        """'whether intentionally or not' → flagged."""
        violations = self.scanner.scan("Whether intentionally or not, the framing is loaded.")
        cats = [v.pattern_category for v in violations]
        assert "intent_centered_hedged" in cats

    def test_pattern4_regardless_of_intent(self):
        """'regardless of intent' → flagged."""
        violations = self.scanner.scan("Regardless of intent, this positions the argument.")
        cats = [v.pattern_category for v in violations]
        assert "intent_centered_hedged" in cats

    def test_pattern5_second_person_absence(self):
        """'you didn't provide' → flagged."""
        violations = self.scanner.scan("You didn't provide any evidence for this claim.")
        cats = [v.pattern_category for v in violations]
        assert "second_person_absence_framing" in cats

    def test_pattern5_you_failed_to(self):
        """'you failed to' → flagged."""
        violations = self.scanner.scan("You failed to address the core issue.")
        cats = [v.pattern_category for v in violations]
        assert "second_person_absence_framing" in cats

    def test_pattern6_signal_frequency(self):
        """Signal frequency regex → flagged."""
        violations = self.scanner.scan(
            "Each time I responded, you escalated the claim."
        )
        cats = [v.pattern_category for v in violations]
        assert "signal_frequency_relative" in cats

    def test_pattern7_dispositional_characterization(self):
        """'the pattern indicates that you' → flagged."""
        violations = self.scanner.scan("The pattern indicates that you are escalating.")
        cats = [v.pattern_category for v in violations]
        assert "dispositional_characterization" in cats

    def test_pattern7_this_behavior_suggests(self):
        """'this behavior suggests' → flagged."""
        violations = self.scanner.scan("This behavior suggests an underlying bias.")
        cats = [v.pattern_category for v in violations]
        assert "dispositional_characterization" in cats

    # Compliant constructions — 0% false positives
    def test_compliant_turn_event_description(self):
        """Compliant per-turn description → no violations."""
        text = (
            "In turn 3, a conclusion was asserted as correct and agreement was requested."
        )
        assert self.scanner.is_compliant(text) is True

    def test_compliant_signal_count_description(self):
        """Compliant signal count description → no violations."""
        text = (
            "The session contains 3 instances of Signal A within the 5-turn window."
        )
        assert self.scanner.is_compliant(text) is True

    def test_compliant_no_new_proposition(self):
        """Compliant no-proposition note → no violations."""
        text = "No new proposition was introduced in turn 4."
        assert self.scanner.is_compliant(text) is True

    def test_compliant_over_last_n_turns(self):
        """Compliant over-last-N-turns description → no violations."""
        text = "Over the last 3 turns, 2 instances of Signal A were present in the session."
        assert self.scanner.is_compliant(text) is True

    def test_all_7_patterns_detected(self):
        """All 7 prohibited pattern categories should be detectable."""
        texts = [
            "you are trying to mislead",
            "this suggests an attempt to deceive",
            "you have been pushing this view",
            "whether intentionally or not, the effect is bias",
            "you didn't provide evidence",
            "each time I responded, you escalated",
            "the pattern indicates that you are biased",
        ]
        expected_categories = {
            "direct_intent_attribution",
            "implied_motive",
            "disposition_verb",
            "intent_centered_hedged",
            "second_person_absence_framing",
            "signal_frequency_relative",
            "dispositional_characterization",
        }
        found = set()
        for t in texts:
            for v in self.scanner.scan(t):
                found.add(v.pattern_category)
        assert expected_categories.issubset(found)


# ===========================================================================
# Option Labeling Tests
# ===========================================================================

class TestOptionLabeling:
    detector = OptionLabelingDetector()

    def test_labeled_response_compliant(self):
        """Properly A/B/C labeled response → compliant."""
        text = (
            "Here are your options:\n"
            "A. Deploy to production immediately\n"
            "B. Run a staging test first\n"
            "C. Postpone the release\n"
        )
        assert self.detector.is_compliant(text) is True

    def test_unlabeled_selectable_response_noncompliant(self):
        """Bullet list with trigger phrase + 2+ actions → noncompliant."""
        text = (
            "Here are your next steps:\n"
            "- Deploy to production\n"
            "- Run tests\n"
            "- Update documentation\n"
        )
        assert self.detector.is_compliant(text) is False

    def test_no_trigger_phrase_compliant(self):
        """No trigger phrase → no labeling required → compliant."""
        text = "The analysis shows that the framework performs well under load conditions."
        assert self.detector.is_compliant(text) is True

    def test_requires_labeling_detects_trigger(self):
        """requires_labeling returns True when trigger + 2+ actions present."""
        text = (
            "You can choose between these options:\n"
            "- Option one\n"
            "- Option two\n"
        )
        assert self.detector.requires_labeling(text) is True

    def test_single_action_no_labeling_required(self):
        """Single action with trigger → labeling not required."""
        text = "You can proceed with the analysis."
        assert self.detector.requires_labeling(text) is False

    def test_numbered_list_noncompliant(self):
        """Numbered list without A/B/C labels → noncompliant."""
        text = (
            "Select one of the following:\n"
            "1. Option A text\n"
            "2. Option B text\n"
            "3. Option C text\n"
        )
        # Numbered list triggers the detector
        result = self.detector.is_compliant(text)
        # Should detect as requiring labeling since trigger + 3 items
        # The existing labels are numeric, not A/B/C
        assert result is False

    def test_already_labeled_passes(self):
        """Response with A./B. labels passes."""
        text = (
            "Would you like to:\n"
            "A. Continue the analysis\n"
            "B. Stop here\n"
        )
        assert self.detector.is_compliant(text) is True
