use crate::core::errors::{CosynError, CosynResult};
use crate::core::stage::Stage;
use crate::core::types::LockedOutput;
use crate::state_store::StateStore;

pub fn run(input: &str) -> CosynResult<LockedOutput> {
    let mut state = StateStore::new();

    // Stage 1: Input
    let request = crate::input_gate::accept(input)?;
    state.advance(Stage::Input, true, &request.input);
    crate::telemetry::log_stage(Stage::Input, true, "accepted");

    // Stage 2: Draft (mocked LLM)
    let draft = crate::llm_client::draft(&request.input)?;
    state.advance(Stage::Draft, true, &draft.text);
    crate::telemetry::log_stage(Stage::Draft, true, "draft produced");

    // Stage 3: Validation — structural checks then constitutional enforcement
    if let Err(e) = crate::validator::validate(&draft) {
        let reason = format!("{}", e);
        state.advance(Stage::Validation, false, &reason);
        crate::telemetry::log_stage(Stage::Validation, false, &format!("blocked: {}", reason));
        return Err(e);
    }
    crate::telemetry::log_stage(Stage::Validation, true, "structural checks passed");

    // Constitutional enforcement (governance gate)
    if let Err(e) = crate::governance_layer::enforce(&request.input, &draft) {
        let reason = format!("{}", e);
        state.advance(Stage::Validation, false, &reason);
        crate::telemetry::log_stage(Stage::Validation, false, &format!("blocked: {}", reason));
        return Err(e);
    }
    state.advance(Stage::Validation, true, "governance passed");
    crate::telemetry::log_stage(Stage::Validation, true, "constitutional enforcement passed");

    // Stage 4: Lock
    let locked = LockedOutput {
        text: draft.text,
        locked: true,
    };
    state.advance(Stage::Lock, true, "locked");
    crate::telemetry::log_stage(Stage::Lock, true, "artifact locked");

    // Stage 5: Output gate — allow only if locked
    if !locked.locked {
        state.advance(Stage::Output, false, "blocked");
        crate::telemetry::log_stage(Stage::Output, false, "output blocked");
        return Err(CosynError::Lock("output not locked, blocked".into()));
    }
    state.advance(Stage::Output, true, "released");
    crate::telemetry::log_stage(Stage::Output, true, "output released");

    Ok(locked)
}
