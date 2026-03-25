use crate::core::stage::Stage;

#[derive(Debug, Clone)]
pub struct ExecutionRequest {
    pub id: String,
    pub input: String,
}

#[derive(Debug, Clone)]
pub struct DraftOutput {
    pub text: String,
}

#[derive(Debug, Clone)]
pub struct LockedOutput {
    pub text: String,
    pub locked: bool,
}

#[derive(Debug, Clone)]
pub struct StageRecord {
    pub stage: Stage,
    pub passed: bool,
    pub detail: String,
}
