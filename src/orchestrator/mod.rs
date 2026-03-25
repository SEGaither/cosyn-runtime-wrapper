use crate::core::errors::CosynResult;
use crate::core::stage::Stage;
use crate::core::types::{AppConfig, ValidatedExecutionRequest, ModelOutput};

pub fn run_pipeline(
    _config: &AppConfig,
    request: ValidatedExecutionRequest,
) -> CosynResult<ModelOutput> {
    let _stages = [
        Stage::GovernanceCheck,
        Stage::LlmInvocation,
        Stage::Validation,
        Stage::Telemetry,
        Stage::Packaging,
    ];

    crate::governance_layer::enforce(&request.persona)?;

    let output = crate::llm_client::invoke(_config, &request.input)?;

    crate::validator::validate_output(&output)?;

    Ok(output)
}
