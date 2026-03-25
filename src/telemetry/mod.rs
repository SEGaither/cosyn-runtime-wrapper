use crate::core::errors::CosynResult;

pub fn log_event(_stage: &str, _detail: &str) -> CosynResult<()> {
    // TODO: append JSONL to telemetry log
    Ok(())
}
