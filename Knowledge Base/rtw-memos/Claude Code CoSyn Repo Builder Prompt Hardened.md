# Claude Code Prompt --- CoSyn Repository Builder (Hardened)

You are running inside Claude Code in the current workspace.

Execution target: Build the initial public GitHub repository for CoSyn
as a single monorepo named `cosyn` inside this workspace.

Environment assumptions: - You may use Claude Code file tools and Bash
when available in this session. - Work only inside the current
workspace. - Treat `./canonical_source/` as the canonical source
authority if it exists. - Treat `./cosyn/` as the repo working tree to
create or update. - Treat `./canonical_source/Claude created files/` as
the mirror backup location for all files you create or modify inside
`./cosyn/`. - Do not assume access to any path outside the current
workspace. - Do not claim a file was inspected, created, edited, copied,
mirrored, or validated unless tool results confirm it.

  ------------------------------
  Workspace Verification Phase
  ------------------------------

Before beginning repository construction:

1.  Confirm the current workspace is writable.
2.  Check whether `./canonical_source/` exists.
3.  Check whether `./cosyn/` already exists.
4.  If `./cosyn/` exists:
    -   inspect contents
    -   reuse only if it clearly represents a partial CoSyn repo
    -   otherwise halt and report conflict
5.  Confirm that the mirror directory can be created at:
    `./canonical_source/Claude created files/`

Report workspace state before proceeding.

  -------------------------
  Tool Verification Phase
  -------------------------

Verify availability of the following capabilities:

Required: - file read - file write - directory creation

Optional: - bash execution - git

Procedure:

1.  Confirm each capability.
2.  Report capability status.
3.  If bash is unavailable: proceed using file tools only.
4.  If git is unavailable: build repository structure but skip commit
    operations.
5.  If filesystem write capability is unavailable: halt and report
    environment limitation.

  ---------
  Mission
  ---------

Build a legible, trustworthy, minimally runnable open-source CoSyn
monorepo that can be publicly released.

Primary objective: Create a repo that is understandable before
doctrinally deep, minimally runnable, and quick to evaluate.

Secondary objective: Stress test the plan during implementation. If you
find friction, missing dependencies, contradictory structure, onboarding
failures, or documentation gaps, correct them with the minimum necessary
change while preserving intent. Log every meaningful deviation and why
it was necessary.

  ------------------
  Hard Constraints
  ------------------

1.  Single public monorepo first.
2.  Quickstart must be 3 commands or fewer.
3.  Runtime usability comes before doctrinal weight in first-run
    experience.
4.  Include:
    -   one domain-agnostic example
    -   one enterprise-oriented claims example
5.  Keep the runtime small, readable, and locally runnable.
6.  Do not simulate capabilities that are not actually implemented.
7.  If a required artifact is missing from canonical source, create a
    clearly marked starter artifact and note it in the final report.
8.  Do not modify or delete original files under `./canonical_source/`.
9.  Mirror every created or modified repo file into
    `./canonical_source/Claude created files/`.
10. If a command requires permission or is blocked, continue with the
    next feasible step and report the blocker precisely.

  ---------------------------
  Canonical Source Handling
  ---------------------------

-   Inspect `./canonical_source/` first.
-   Preserve exact filenames for constitutional or governance artifacts
    when found.
-   If governance language conflicts across canonical files, prefer:
    1.  constitutional artifact
    2.  companion interpretation artifacts
    3.  runtime reference material
-   Prefer Markdown as source text when available.
-   Preserve both Markdown and PDF when practical.

  -----------------------------
  Required Monorepo Structure
  -----------------------------

cosyn/ - README.md - WHY.md - LICENSE - SECURITY.md -
CODE_OF_CONDUCT.md - CONTRIBUTING.md - SUPPORT.md - .github/ -
ISSUE_TEMPLATE/ - PULL_REQUEST_TEMPLATE.md - CODEOWNERS - workflows/ -
docs/ - getting-started/ - concepts/ - examples/ - reference/ -
adoption/ - constitution/ - governance/ - runtime/ - schemas/ -
examples/ - minimal/ - decision_audit_demo/ - claims_analysis_demo/ -
templates/ - tests/ - evals/ - scripts/ - releases/

  ---------------------------
  Required Docs and Content
  ---------------------------

README.md must include:

1.  Problem
2.  Why prompt-only workflows fail
3.  What CoSyn changes structurally
4.  5-minute quickstart
5.  Example outputs
6.  How to evaluate in a real team
7.  Contribution path
8.  Current status

WHY.md must explain:

-   the problem
-   why existing approaches fail
-   why governance is needed
-   what CoSyn changes

Starter documentation topics:

-   what CoSyn is
-   install
-   first governed run
-   how routing works
-   how to add a persona
-   governance precedence
-   amendments
-   failure modes
-   config schema
-   telemetry
-   enterprise evaluation
-   rollout playbook
-   minimal example
-   enterprise pilot example

  ----------------------
  Runtime Requirements
  ----------------------

Create a minimal runnable implementation demonstrating:

-   governed reasoning pipeline
-   persona routing
-   assumption detection or explicit assumption declaration handling
-   bias/tradeoff detection requiring declared framing
-   uncertainty/confidence handling
-   deterministic halt on missing required structure

  ----------
  Examples
  ----------

Create:

-   examples/minimal
-   examples/decision_audit_demo
-   examples/claims_analysis_demo

  -------
  Tests
  -------

Include at least:

-   smoke test for runtime startup
-   governance behavior tests for assumption/bias/halt
-   example execution test if practical

  ------------------
  Evaluation Cases
  ------------------

Provide starter governance evaluation cases:

-   hidden assumption case
-   unsupported certainty case
-   bias/tradeoff without declared frame
-   reasoning order or scope violation

  -------------------------
  Implementation Sequence
  -------------------------

1.  Inspect `./canonical_source/` and inventory files.
2.  Determine exact filenames and artifact classes to preserve.
3.  Select the simplest implementation language enabling local
    execution.
4.  Create monorepo skeleton in `./cosyn/`.
5.  Copy canonical governance artifacts.
6.  Create root community and trust files.
7.  Create README.md and WHY.md.
8.  Create docs skeleton.
9.  Scaffold minimal runtime.
10. Add examples.
11. Add tests and eval cases.
12. Add scripts needed for quickstart.
13. Validate quickstart path.
14. Validate example execution.
15. Review terminology consistency and onboarding order.
16. Mirror all created or modified repo files.
17. Produce final report.

  ----------------
  Decision Rules
  ----------------

-   Favor launchable over complete.
-   Favor smaller reliable tests over broader fragile tests.
-   If quickstart simplicity conflicts with framework ambition, preserve
    quickstart simplicity.
-   If dependencies are optional for first release, do not require them.
-   If a feature is too large for the first release, stub it clearly.

  ------------------
  Failure Protocol
  ------------------

-   Do not stop silently.
-   Do not ask open-ended questions unless necessary.
-   Make the smallest assumption needed to continue.
-   Record every assumption in the final report.
-   If blocked, still build the repo skeleton and all non-blocked
    artifacts.

  -------------------------
  Validation Requirements
  -------------------------

Before reporting success confirm:

-   `./canonical_source/` was inspected or explicitly missing.
-   canonical files were not modified.
-   mirrored copies exist for all created repo files.
-   repo tree exists with justified deviations.
-   runtime invocation works if tool results confirm.
-   minimal example runs if tool results confirm.
-   quickstart requires three commands or fewer.
-   documentation introduces function before doctrine.

  ---------------------
  Output Requirements
  ---------------------

Final output must contain only:

1.  Built
    -   exact repo tree
    -   key implementation choices
    -   quickstart commands
2.  Stress Test Findings
    -   friction points
    -   missing inputs
    -   plan deviations
3.  Next Highest-Leverage Actions
    -   minimal steps before public GitHub launch

------------------------------------------------------------------------

Begin with Workspace Verification. Then run Tool Verification. Then
inspect `./canonical_source/`. Then build `./cosyn/`. Mirror all created
or modified repo files before final report.
