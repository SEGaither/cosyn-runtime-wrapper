use crate::core::errors::{CosynError, CosynResult};
use crate::core::types::{AppConfig, ModelOutput};

pub fn invoke(_config: &AppConfig, _input: &str) -> CosynResult<ModelOutput> {
    // TODO: implement OpenAI Responses API call via reqwest
    Err(CosynError::LlmClient("not yet implemented".into()))
}
