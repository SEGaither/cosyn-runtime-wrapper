use crate::core::stage::Stage;
use std::sync::Mutex;

static LOG_BUFFER: Mutex<Vec<String>> = Mutex::new(Vec::new());

pub fn log_stage(stage: Stage, passed: bool, detail: &str) {
    let status = if passed { "PASS" } else { "FAIL" };
    let line = format!("[{}] {} — {}", stage.label(), status, detail);
    println!("  {}", line);
    if let Ok(mut buf) = LOG_BUFFER.lock() {
        buf.push(line);
    }
}

pub fn take_log() -> Vec<String> {
    if let Ok(mut buf) = LOG_BUFFER.lock() {
        std::mem::take(&mut *buf)
    } else {
        Vec::new()
    }
}
