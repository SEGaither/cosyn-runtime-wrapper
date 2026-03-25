use crate::core::errors::{CosynError, CosynResult};
use crate::core::types::ModelOutput;

pub fn validate_output(output: &ModelOutput) -> CosynResult<()> {
    if output.text.is_empty() {
        return Err(CosynError::Validation("empty model output".into()));
    }
    Ok(())
}
