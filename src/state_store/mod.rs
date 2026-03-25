use crate::core::errors::CosynResult;

pub struct StateStore;

impl StateStore {
    pub fn new() -> CosynResult<Self> {
        Ok(Self)
    }
}
