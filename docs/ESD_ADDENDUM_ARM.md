Title: Artifact Render Mode (ARM) — ESD Addendum
Version: v1.0
Date: 2026-03-25

Summary:
Artifact Render Mode (ARM) introduces output-domain separation at the UI/output layer.
When triggered, the system suppresses all non-payload output and returns only the artifact body.

Scope:
- Output layer only
- No modification to pipeline stages
- No modification to validation logic
- No modification to orchestrator

Behavior:
- Standard mode: unchanged from ESD baseline
- Artifact mode: payload-only output

Trigger:
- Input contains "paste-ready", "render as artifact", or "artifact only"

Invariant:
- With Artifact Mode OFF → behavior identical to ESD
- With Artifact Mode ON → output is payload-only, pipeline unchanged

Constraints:
- No governance metadata in artifact output
- No headers, explanations, or control-plane content
- No impact on pass/block behavior
