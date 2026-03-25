use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub openai_api_key: String,
}

#[derive(Debug, Clone)]
pub struct ExecutionRequest {
    pub id: String,
    pub input: String,
}

#[derive(Debug, Clone)]
pub struct ValidatedExecutionRequest {
    pub id: String,
    pub input: String,
    pub persona: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct ModelOutput {
    pub text: String,
}
