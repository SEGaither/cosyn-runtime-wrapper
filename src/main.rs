#![windows_subsystem = "windows"]

fn main() {
    if let Err(e) = cosyn::ui_runtime::launch() {
        eprintln!("fatal: {}", e);
    }
}
