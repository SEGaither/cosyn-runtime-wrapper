"""
All Pydantic models — single source of truth for CGS Runtime Wrapper.
Matches cosyn_wrapper_interface_contracts.json exactly.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class HaltReasonCode(str, Enum):
    MISSING_REQUIRED_INPUTS = "MISSING_REQUIRED_INPUTS"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"
    CONSTRAINT_CONFLICT = "CONSTRAINT_CONFLICT"
    UNDECLARED_ASSUMPTION = "UNDECLARED_ASSUMPTION"
    IMPLICIT_BIAS = "IMPLICIT_BIAS"
    CONFLICTING_BIAS_SIGNALS = "CONFLICTING_BIAS_SIGNALS"
    ECHO_REPETITION = "ECHO_REPETITION"
    CRS_SCOPE_VIOLATION = "CRS_SCOPE_VIOLATION"
    MODE_LOCK_VIOLATION = "MODE_LOCK_VIOLATION"
    CONFIDENCE_INFLATION = "CONFIDENCE_INFLATION"
    SCOPE_EXCEEDED = "SCOPE_EXCEEDED"
    LEXICAL_VIOLATION = "LEXICAL_VIOLATION"
    UNRESOLVABLE_DRIFT = "UNRESOLVABLE_DRIFT"
    RERENDER_LIMIT_EXCEEDED = "RERENDER_LIMIT_EXCEEDED"


class GateId(str, Enum):
    ICC = "ICC"
    ASTG = "ASTG"
    BSG = "BSG"
    EDH = "EDH"
    SPM = "SPM"
    PRAP = "PRAP"
    OSCL = "OSCL"
    FINALIZATION = "FINALIZATION"
    TELEMETRY = "TELEMETRY"


class GateStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"
    halt = "halt"
    warn = "warn"
    rerender = "rerender"


class FailureClass(str, Enum):
    class0 = "class0"
    class1 = "class1"
    none = "none"


class BiasFrame(str, Enum):
    conversion_optimized = "conversion-optimized"
    risk_avoidant = "risk-avoidant"
    neutral_descriptive = "neutral-descriptive"
    dual_track_labeled = "dual-track-labeled"
    exploratory = "exploratory"
    adversarial = "adversarial"
    execution_focused = "execution-focused"


class ConstraintConsistency(str, Enum):
    consistent = "consistent"
    ambiguous = "ambiguous"
    conflicting = "conflicting"


class AssumptionStability(str, Enum):
    stable = "stable"
    unstable = "unstable"


class EchoType(str, Enum):
    semantic_repetition = "semantic_repetition"
    premise_reuse = "premise_reuse"
    reaffirmation_without_anchor = "reaffirmation_without_anchor"


class TelemetryRenderLevel(str, Enum):
    minimal = "minimal"
    standard = "standard"
    full = "full"


class PipelineStatusIngress(str, Enum):
    proceed = "proceed"
    halt = "halt"
    clarify = "clarify"


class PipelineStatusOutput(str, Enum):
    emitted = "emitted"
    halted = "halted"
    rerender_limit_exceeded = "rerender_limit_exceeded"


class HaltType(str, Enum):
    halt = "halt"
    clarify = "clarify"
    scp = "scp"
    rerender_limit = "rerender_limit"


# ---------------------------------------------------------------------------
# Sub-objects
# ---------------------------------------------------------------------------

class Assumption(BaseModel):
    assumption_text: str
    failure_condition: str
    conclusion_impact: str
    stability: AssumptionStability


class EDHBufferEntry(BaseModel):
    turn_index: int = Field(..., ge=1)
    conclusion_embedding: list[float]
    conclusion_summary: str


class GateResult(BaseModel):
    gate_id: GateId
    status: GateStatus
    failure_class: FailureClass
    halt_reason_code: Optional[HaltReasonCode] = None
    provisional_flag: bool
    assumption_declared: bool
    fired_at_ms: int
    rerender_reason: Optional[str] = None
    gate_data: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Request / Response Envelopes
# ---------------------------------------------------------------------------

class RequestEnvelope(BaseModel):
    session_id: str
    turn_index: int = Field(..., ge=1)
    raw_input: str
    wrapper_version: str
    cgs_version: str
    crs_scope: Optional[str] = None
    crs_strict_mode: bool = False
    spm_suppress: bool = False
    mode_lock: Optional[str] = None
    persona_override: Optional[str] = None


class IngressPipelineEnvelope(BaseModel):
    request: RequestEnvelope
    gate_results: list[GateResult]
    pipeline_status: PipelineStatusIngress
    halt_response: Optional[str] = None
    model_prompt: Optional[str] = None
    active_persona: str
    ingress_completed_at_ms: int
    spm_output: Optional[str] = None


class ModelResponseEnvelope(BaseModel):
    raw_output: str
    ingress_envelope: IngressPipelineEnvelope
    rerender_count: int = Field(..., ge=0)
    rerender_reason_history: list[str]
    model_completed_at_ms: int


class OutputEnvelope(BaseModel):
    session_id: str
    turn_index: int
    emission: str
    pipeline_status: PipelineStatusOutput
    gate_results_egress: list[GateResult]
    telemetry_payload: TelemetryTurnRecord
    provisional: bool
    spm_fired_this_turn: bool
    halt_response: Optional[str] = None
    rerender_count: int
    turn_completed_at_ms: int
    latency_ms: int


class HaltResponse(BaseModel):
    type: HaltType
    halt_reason_code: HaltReasonCode
    user_facing_text: str
    gate_id: GateId
    session_id: str
    turn_index: int
    missing_inputs: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

class SessionState(BaseModel):
    session_id: str
    cgs_version: str
    wrapper_version: str
    turn_index: int = Field(default=0, ge=0)
    spm_signal_a_turns: list[int] = Field(default_factory=list)
    spm_signal_b_turns: list[int] = Field(default_factory=list)
    spm_signal_c_turns: list[int] = Field(default_factory=list)
    spm_fired: bool = False
    spm_suppress: bool = False
    ccd_confidence_register: float = Field(default=0.7, ge=0.0, le=1.0)
    edh_buffer: list[EDHBufferEntry] = Field(default_factory=list, max_length=10)
    edh_fired: bool = False
    crs_strict_mode: bool = False
    active_persona: str = "Core"
    session_started_at_ms: int = 0
    ttl_seconds: int = 3600
    spm_fired_at_turn: Optional[int] = None
    spm_window_reset_at_turn: Optional[int] = None
    mode_lock: Optional[str] = None
    crs_scope: Optional[str] = None
    last_turn_completed_at_ms: Optional[int] = None


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

class TelemetryTurnRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    turn_index: int
    personas_invoked: list[str]
    synthesis_mode: bool
    gate_triggers_fired: list[GateId]
    halt_triggered: bool
    halt_reason_code: Optional[HaltReasonCode] = None
    rerender_requested: bool
    rerender_count: int
    provisional_labeling_count: int
    assumption_block_present: bool
    numeric_claims_count: int
    numeric_claims_with_basis_count: int
    scope_violation_flags: list[str]
    spm_signal_a_count: int
    spm_signal_b_count: int
    spm_signal_c_count: int
    spm_threshold_crossed: bool
    spm_fired: bool
    spm_dispute_event: bool
    spm_dispute_signal_classification: Optional[str] = None
    latency_ms: int
    classifier_latency_ms: int
    model_latency_ms: int


class TelemetrySessionRollup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    total_turns: int
    halt_rate: float = Field(..., ge=0.0, le=1.0)
    rerender_rate: float = Field(..., ge=0.0, le=1.0)
    provisional_rate: float = Field(..., ge=0.0, le=1.0)
    assumption_rate: float = Field(..., ge=0.0, le=1.0)
    spm_fire_count: int
    spm_dispute_count: int
    spm_retraction_count: int
    class0_failure_count: int
    class1_failure_count: int
    governance_regression_flag: bool
    numeric_basis_ratio: Optional[float] = None


# ---------------------------------------------------------------------------
# State Annotation Block
# ---------------------------------------------------------------------------

class StateAnnotationBlock(BaseModel):
    TURN_INDEX: int
    SPM_SIGNAL_A_COUNT: int
    SPM_SIGNAL_B_COUNT: int
    SPM_SIGNAL_C_COUNT: int
    SPM_FIRED_THIS_SESSION: bool
    CCD_CONFIDENCE_REGISTER: float
    EDH_ECHO_FLAG: bool
    PRAP_STATUS: str  # "pass" | "fail"
    MODE_LOCK: str
    ACTIVE_PERSONA: str


# ---------------------------------------------------------------------------
# API-level request/response models
# ---------------------------------------------------------------------------

class TelemetryRenderRequest(BaseModel):
    session_id: str
    level: TelemetryRenderLevel
    range: Optional[list[int]] = None


class SessionResetRequest(BaseModel):
    session_id: str


class SessionResetResponse(BaseModel):
    status: str = "ok"


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    session_id: Optional[str] = None
    turn_index: Optional[int] = None


# ---------------------------------------------------------------------------
# Gate-data schemas (typed dicts / models for gate_data fields)
# ---------------------------------------------------------------------------

class ICCGateData(BaseModel):
    intent_primary: str
    constraint_consistency: ConstraintConsistency
    provisional_flag: bool
    intent_scope: Optional[str] = None
    intent_exclusions: list[str] = Field(default_factory=list)
    intent_output_form: Optional[str] = None
    ambiguity_description: Optional[str] = None
    least_committal_interpretation: Optional[str] = None


class ASTGGateData(BaseModel):
    assumptions_identified: list[Assumption]
    assumption_count: int
    unstable_assumption_present: bool
    assumption_block_text: Optional[str] = None


class BSGGateData(BaseModel):
    tradeoff_detected: bool
    implicit_bias_detected: bool
    conflicting_signals: bool
    bias_frame_selected: Optional[BiasFrame] = None


class EDHGateData(BaseModel):
    echo_detected: bool
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    forced_reframe_required: bool
    external_anchor_check_triggered: bool
    ecfd_triggered: bool
    echo_type: Optional[EchoType] = None


class SPMGateData(BaseModel):
    signal_a_this_turn: bool
    signal_b_this_turn: bool
    signal_c_this_turn: bool
    threshold_crossed: bool
    dispute_detected: bool
    spm_output_text: Optional[str] = None
    window_turn_range: Optional[list[int]] = None
    dispute_response_text: Optional[str] = None


class PRAPGateData(BaseModel):
    all_checks_passed: bool
    failed_checks: list[str]
    scope_satisfiable: bool
    source_fidelity_satisfiable: bool
    mode_lock_viable: bool
    delegation_boundary_clean: bool
    crs_scope_clean: bool


class OSCLGateData(BaseModel):
    evidence_alignment: float
    assumption_minimality: float
    overclaim_risk_inverse: float
    user_constraint_adherence: float
    actionability_clarity: float
    aggregate_score: float
    revision_required: bool
    scp_trigger: bool
    lowest_scoring_axes: Optional[list[str]] = None


class FinalizationGateData(BaseModel):
    persona_headers_present: bool
    option_labeling_compliant: bool
    spm_lexical_compliant: bool
    source_fidelity_enforced: bool
    scope_within_bounds: bool
    provisional_status_visible: bool
    ufrs_applied: bool
    sscs_score: float
    lexical_violations_found: Optional[list[str]] = None
    final_emission_text: Optional[str] = None


class TelemetryGateData(BaseModel):
    record_written: bool
    write_error: Optional[str] = None
