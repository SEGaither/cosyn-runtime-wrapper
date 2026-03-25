use eframe::egui;

pub struct CosynApp {
    input: String,
    output: String,
    status: String,
    log_lines: Vec<String>,
}

impl Default for CosynApp {
    fn default() -> Self {
        Self {
            input: String::new(),
            output: String::new(),
            status: "Ready".into(),
            log_lines: Vec::new(),
        }
    }
}

impl CosynApp {
    fn run_pipeline(&mut self) {
        self.output.clear();
        self.log_lines.clear();
        self.status = "Running...".into();

        // Clear any prior telemetry
        crate::telemetry::take_log();

        match crate::orchestrator::run(&self.input) {
            Ok(locked) => {
                self.status = "PASS — output released".into();
                self.output = locked.text;
            }
            Err(e) => {
                self.status = format!("BLOCKED — {}", e);
            }
        }

        self.log_lines = crate::telemetry::take_log();
    }
}

impl eframe::App for CosynApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("CoSyn v2.0.1");
            ui.separator();

            ui.label("Request:");
            ui.text_edit_multiline(&mut self.input);

            if ui.button("Run governed pipeline").clicked() && !self.input.trim().is_empty() {
                self.run_pipeline();
            }

            ui.separator();
            ui.label(format!("Status: {}", self.status));

            if !self.log_lines.is_empty() {
                ui.separator();
                ui.label("Pipeline log:");
                for line in &self.log_lines {
                    ui.monospace(line);
                }
            }

            if !self.output.is_empty() {
                ui.separator();
                ui.label("Result:");
                egui::ScrollArea::vertical()
                    .max_height(200.0)
                    .show(ui, |ui| {
                        ui.monospace(&self.output);
                    });
            }
        });
    }
}

pub fn launch() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("CoSyn v2.0.1")
            .with_inner_size([520.0, 480.0]),
        ..Default::default()
    };
    eframe::run_native(
        "CoSyn",
        options,
        Box::new(|_cc| Ok(Box::new(CosynApp::default()))),
    )
}
