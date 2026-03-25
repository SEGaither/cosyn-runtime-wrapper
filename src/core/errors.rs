use std::fmt;

#[derive(Debug)]
pub enum CosynError {
    Config(String),
    InputGate(String),
    Governance(String),
    Validation(String),
    Orchestration(String),
    LlmClient(String),
    StateStore(String),
    Packager(String),
    Telemetry(String),
    UiRuntime(String),
}

impl fmt::Display for CosynError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Config(msg) => write!(f, "[config] {}", msg),
            Self::InputGate(msg) => write!(f, "[input_gate] {}", msg),
            Self::Governance(msg) => write!(f, "[governance] {}", msg),
            Self::Validation(msg) => write!(f, "[validation] {}", msg),
            Self::Orchestration(msg) => write!(f, "[orchestration] {}", msg),
            Self::LlmClient(msg) => write!(f, "[llm_client] {}", msg),
            Self::StateStore(msg) => write!(f, "[state_store] {}", msg),
            Self::Packager(msg) => write!(f, "[packager] {}", msg),
            Self::Telemetry(msg) => write!(f, "[telemetry] {}", msg),
            Self::UiRuntime(msg) => write!(f, "[ui_runtime] {}", msg),
        }
    }
}

impl std::error::Error for CosynError {}

pub type CosynResult<T> = Result<T, CosynError>;
