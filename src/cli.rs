fn main() {
    println!("CoSyn Runtime Wrapper — core loop");
    println!();

    // Pass case
    let pass_input = "Summarize the governance policy";
    println!("--- PASS CASE ---");
    println!("input: \"{}\"", pass_input);
    println!();
    match cosyn::orchestrator::run(pass_input) {
        Ok(output) => println!("RESULT: {}\n", output.text),
        Err(e) => println!("BLOCKED: {}\n", e),
    }

    // Block case: sentinel
    let block_input = "TODO fix this later";
    println!("--- BLOCK CASE (sentinel) ---");
    println!("input: \"{}\"", block_input);
    println!();
    match cosyn::orchestrator::run(block_input) {
        Ok(output) => println!("RESULT: {}\n", output.text),
        Err(e) => println!("BLOCKED: {}\n", e),
    }

    // Block case: too short
    let short_input = "hi";
    println!("--- BLOCK CASE (short draft) ---");
    println!("input: \"{}\"", short_input);
    println!();
    match cosyn::orchestrator::run(short_input) {
        Ok(output) => println!("RESULT: {}\n", output.text),
        Err(e) => println!("BLOCKED: {}\n", e),
    }
}
