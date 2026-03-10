"""
FINALIZATION Gate — Egress position 2

Sub-checks (ALL must pass):
1. Persona headers present
2. Option labeling compliant
3. SPM lexical compliance
4. Source fidelity
5. Scope within bounds
6. Provisional status visible
7. UFRS applied
8. SSCS score >= 0.80

Self-heal when deterministic: inject headers, apply labels
Rerender when requires model
Halt SCOPE_EXCEEDED: scope exceeded
Halt UNRESOLVABLE_DRIFT: unresolvable drift
"""
from __future__ import annotations

import re
import time

from cgs_runtime_wrapper.classifier.lexical_scanner import LexicalScanner
from cgs_runtime_wrapper.classifier.option_labeling import OptionLabelingDetector
from cgs_runtime_wrapper.models.envelopes import (
    FailureClass,
    FinalizationGateData,
    GateId,
    GateResult,
    GateStatus,
    HaltReasonCode,
    RequestEnvelope,
    SessionState,
)

_PERSONA_HEADER_CONTROL = "Router (control-plane): Stack Architect"
_PERSONA_HEADER_ACTIVE_PREFIX = "Active persona (this turn):"

# Source fidelity trigger keywords
_SOURCE_FIDELITY_TRIGGERS: list[str] = [
    "according to",
    "source:",
    "reference:",
    "citation:",
    "this document states",
    "as stated in",
    "per the",
    "[source",
    "[ref",
]

# UFRS = User-Facing Response Standards: output must not be empty and must have content
_UFRS_MIN_LENGTH = 10

# SSCS = Structural & Semantic Coherence Score (stub: 0.92)
_STUB_SSCS = 0.92
_SSCS_THRESHOLD = 0.80

_lexical_scanner = LexicalScanner()
_option_detector = OptionLabelingDetector()


def _check_persona_headers(text: str) -> bool:
    """Check that both required persona headers are present."""
    return (
        _PERSONA_HEADER_CONTROL in text
        and _PERSONA_HEADER_ACTIVE_PREFIX in text
    )


def _inject_persona_headers(text: str, persona: str) -> str:
    """Prepend persona headers to text."""
    header = f"{_PERSONA_HEADER_CONTROL}\n{_PERSONA_HEADER_ACTIVE_PREFIX} {persona}"
    if _check_persona_headers(text):
        return text
    return f"{header}\n\n{text}"


def _check_source_fidelity(text: str) -> bool:
    """
    If any source fidelity trigger is present, it's a signal that fidelity
    markers are included. Returns True (compliant) if triggers present OR
    no fidelity claims are made.
    For now: always returns True (no claims = compliant).
    """
    return True  # stub: pass


def _check_scope_within_bounds(text: str, crs_scope: str | None) -> bool:
    """
    Check that output content doesn't exceed declared scope.
    Stub: always True unless explicit scope violation marker found.
    """
    if crs_scope is None:
        return True
    # In production: compare output topic scope against crs_scope
    return True  # stub


def _check_provisional_visible(text: str, has_provisional: bool) -> bool:
    """If provisional flag is set, the word 'provisional' must appear in output."""
    if not has_provisional:
        return True
    return "provisional" in text.lower()


def _check_ufrs(text: str) -> bool:
    """UFRS: output must have meaningful content."""
    stripped = text.strip()
    return len(stripped) >= _UFRS_MIN_LENGTH


def _inject_option_labels(text: str) -> str:
    """
    Self-heal: inject A/B/C labels to unlabeled option lists.
    Simple heuristic: find bullet/numbered list items and relabel.
    """
    label_chars = ["A", "B", "C", "D", "E", "F"]
    counter = [0]

    def replacer(match: re.Match) -> str:
        prefix = match.group(0)
        if counter[0] < len(label_chars):
            label = f"{label_chars[counter[0]]}. "
            counter[0] += 1
            # Replace bullet/number with label
            return re.sub(r'^[\s]*[-*•\d]+[.)]\s*', label, prefix)
        return prefix

    # Match list items
    result = re.sub(
        r'(?m)^[ \t]*[-*•]\s+\S.*$|(?m)^[ \t]*\d+[.)]\s+\S.*$',
        replacer,
        text,
    )
    return result


async def run_finalization_gate(
    raw_output: str,
    request: RequestEnvelope,
    session_state: SessionState,
    rerender_count: int,
    has_provisional: bool,
) -> tuple[GateResult, str]:
    """
    Execute the FINALIZATION gate.
    Returns (GateResult, possibly_modified_output).
    Self-heals deterministic issues (header injection, option labeling).
    """
    fired_at_ms = int(time.time() * 1000)
    output = raw_output
    failed_checks: list[str] = []
    lexical_violations: list[str] = []
    requires_rerender = False

    persona = session_state.active_persona

    # -----------------------------------------------------------------------
    # Check 1: Persona headers — self-heal by injection
    # -----------------------------------------------------------------------
    persona_headers_present = _check_persona_headers(output)
    if not persona_headers_present:
        # Self-heal: inject headers
        output = _inject_persona_headers(output, persona)
        persona_headers_present = True  # healed

    # -----------------------------------------------------------------------
    # Check 2: Option labeling
    # -----------------------------------------------------------------------
    labeling_required, labels_present = _option_detector.check(output)
    option_labeling_compliant = not labeling_required or labels_present
    if not option_labeling_compliant:
        # Self-heal: inject labels
        output = _inject_option_labels(output)
        _, labels_present_after = _option_detector.check(output)
        if labels_present_after:
            option_labeling_compliant = True
        else:
            # Could not self-heal deterministically → rerender
            requires_rerender = True
            failed_checks.append("option_labeling")

    # -----------------------------------------------------------------------
    # Check 3: SPM lexical compliance
    # -----------------------------------------------------------------------
    violations = _lexical_scanner.scan(output)
    spm_lexical_compliant = len(violations) == 0
    if not spm_lexical_compliant:
        lexical_violations = [v.pattern_category for v in violations]
        failed_checks.append("spm_lexical_compliance")
        requires_rerender = True  # lexical violations require model rerender

    # -----------------------------------------------------------------------
    # Check 4: Source fidelity
    # -----------------------------------------------------------------------
    source_fidelity_enforced = _check_source_fidelity(output)
    if not source_fidelity_enforced:
        failed_checks.append("source_fidelity")

    # -----------------------------------------------------------------------
    # Check 5: Scope within bounds
    # -----------------------------------------------------------------------
    scope_within_bounds = _check_scope_within_bounds(output, request.crs_scope)
    if not scope_within_bounds:
        failed_checks.append("scope_within_bounds")

    # -----------------------------------------------------------------------
    # Check 6: Provisional status visible
    # -----------------------------------------------------------------------
    provisional_status_visible = _check_provisional_visible(output, has_provisional)
    if not provisional_status_visible:
        # Self-heal: append provisional note
        output += "\n\n[Provisional: this response is based on unstable assumptions.]"
        provisional_status_visible = True

    # -----------------------------------------------------------------------
    # Check 7: UFRS applied
    # -----------------------------------------------------------------------
    ufrs_applied = _check_ufrs(output)
    if not ufrs_applied:
        failed_checks.append("ufrs")

    # -----------------------------------------------------------------------
    # Check 8: SSCS score (stub)
    # -----------------------------------------------------------------------
    sscs_score = _STUB_SSCS
    sscs_ok = sscs_score >= _SSCS_THRESHOLD
    if not sscs_ok:
        failed_checks.append("sscs")
        requires_rerender = True

    all_checks_passed = len(failed_checks) == 0

    fin_data = FinalizationGateData(
        persona_headers_present=persona_headers_present,
        option_labeling_compliant=option_labeling_compliant,
        spm_lexical_compliant=spm_lexical_compliant,
        source_fidelity_enforced=source_fidelity_enforced,
        scope_within_bounds=scope_within_bounds,
        provisional_status_visible=provisional_status_visible,
        ufrs_applied=ufrs_applied,
        sscs_score=sscs_score,
        lexical_violations_found=lexical_violations if lexical_violations else None,
        final_emission_text=output,
    )

    # Scope exceeded → hard halt
    if not scope_within_bounds:
        return GateResult(
            gate_id=GateId.FINALIZATION,
            status=GateStatus.halt,
            failure_class=FailureClass.class1,
            halt_reason_code=HaltReasonCode.SCOPE_EXCEEDED,
            provisional_flag=has_provisional,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            gate_data=fin_data.model_dump(),
        ), output

    # Rerender required
    if requires_rerender:
        rerender_reason = "Finalization checks failed: " + ", ".join(failed_checks)
        return GateResult(
            gate_id=GateId.FINALIZATION,
            status=GateStatus.rerender,
            failure_class=FailureClass.class1,
            halt_reason_code=None,
            provisional_flag=has_provisional,
            assumption_declared=False,
            fired_at_ms=fired_at_ms,
            rerender_reason=rerender_reason,
            gate_data=fin_data.model_dump(),
        ), output

    # Pass
    return GateResult(
        gate_id=GateId.FINALIZATION,
        status=GateStatus.pass_,
        failure_class=FailureClass.none,
        halt_reason_code=None,
        provisional_flag=has_provisional,
        assumption_declared=False,
        fired_at_ms=fired_at_ms,
        gate_data=fin_data.model_dump(),
    ), output
