use cosyn::core::types::ExecutionRequest;

fn main() {
    println!("CoSyn Runtime Wrapper — starting");

    let config_path = r"C:\.rtw\cosyn-runtime-wrapper\API\cosign.config.json";
    let config = match cosyn::config_loader::load_config(config_path) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("startup blocked: {}", e);
            return;
        }
    };

    let request = ExecutionRequest {
        id: "init".into(),
        input: "hello".into(),
    };

    let validated = match cosyn::input_gate::validate(request) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("input rejected: {}", e);
            return;
        }
    };

    match cosyn::orchestrator::run_pipeline(&config, validated) {
        Ok(output) => println!("result: {}", output.text),
        Err(e) => eprintln!("pipeline error: {}", e),
    }
}
