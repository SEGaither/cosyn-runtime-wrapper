use crate::core::errors::{CosynError, CosynResult};

pub fn enforce(persona: &str) -> CosynResult<()> {
    if persona != "default" {
        return Err(CosynError::Governance(format!("unauthorized persona: {}", persona)));
    }
    Ok(())
}
