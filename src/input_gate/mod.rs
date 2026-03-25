use crate::core::errors::{CosynError, CosynResult};
use crate::core::types::{ExecutionRequest, ValidatedExecutionRequest};

pub fn validate(request: ExecutionRequest) -> CosynResult<ValidatedExecutionRequest> {
    if request.input.trim().is_empty() {
        return Err(CosynError::InputGate("empty input".into()));
    }
    Ok(ValidatedExecutionRequest {
        id: request.id,
        input: request.input,
        persona: "default".into(),
    })
}
