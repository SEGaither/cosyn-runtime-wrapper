use crate::core::errors::{CosynError, CosynResult};
use crate::core::types::ExecutionRequest;

pub fn accept(input: &str) -> CosynResult<ExecutionRequest> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(CosynError::Input("empty input rejected".into()));
    }
    Ok(ExecutionRequest {
        id: "req-001".into(),
        input: trimmed.to_string(),
    })
}
