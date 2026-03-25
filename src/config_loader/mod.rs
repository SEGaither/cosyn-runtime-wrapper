use crate::core::errors::{CosynError, CosynResult};
use crate::core::types::AppConfig;
use std::fs;

pub fn load_config(path: &str) -> CosynResult<AppConfig> {
    let content = fs::read_to_string(path)
        .map_err(|e| CosynError::Config(format!("failed to read config: {}", e)))?;
    let config: AppConfig = serde_json::from_str(&content)
        .map_err(|e| CosynError::Config(format!("invalid config json: {}", e)))?;
    if config.openai_api_key.is_empty() {
        return Err(CosynError::Config("openai_api_key is empty".into()));
    }
    Ok(config)
}
