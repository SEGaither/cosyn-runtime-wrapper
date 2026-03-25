#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Stage {
    ConfigLoad,
    InputGate,
    GovernanceCheck,
    Orchestration,
    LlmInvocation,
    Validation,
    Telemetry,
    Packaging,
}

impl Stage {
    pub fn label(&self) -> &'static str {
        match self {
            Self::ConfigLoad => "config_load",
            Self::InputGate => "input_gate",
            Self::GovernanceCheck => "governance_check",
            Self::Orchestration => "orchestration",
            Self::LlmInvocation => "llm_invocation",
            Self::Validation => "validation",
            Self::Telemetry => "telemetry",
            Self::Packaging => "packaging",
        }
    }
}
