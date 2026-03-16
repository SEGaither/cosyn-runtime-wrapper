# CoSyn Canonical Versioning Logic

## Purpose

This document defines the canonical versioning system for the CoSyn
repository.

The versioning system ensures that all artifacts within the CoSyn stack
remain synchronized with the constitutional kernel while allowing
independent evolution of downstream artifacts and runtime
implementations.

The system preserves constitutional authority while maintaining
operational flexibility for enforcement artifacts and runtime systems.

The constitutional kernel governs epistemic integrity but explicitly
does not define implementation or software procedures.

------------------------------------------------------------------------

# Versioning Structure

CoSyn uses a layer‑synchronized semantic versioning system.

Artifacts are versioned according to their layer position in the stack.

Stack hierarchy:

Constitution Governor Architect RTW Runtime Implementations Examples /
Templates

Each layer follows a versioning relationship with the constitutional
kernel.

------------------------------------------------------------------------

# Constitutional Version

Format

vMAJOR.MINOR

Example

v15.1

Meaning

  Component   Meaning
  ----------- ---------------------------------------------------------
  MAJOR       Structural change to constitutional reasoning rules
  MINOR       Clarification, interpretation, or constraint refinement

Constraints

1.  Constitutional versions must never include implementation details.
2.  Constitutional versions govern reasoning validity across all runtime
    implementations.
3.  All downstream artifacts must declare compatibility with a specific
    constitutional version.

------------------------------------------------------------------------

# Enforcement Artifact Versioning

Enforcement artifacts include:

-   Persona Governor
-   Stack Architect

These artifacts implement policy specification and system topology but
do not contain execution logic.

Format

vC.MAJOR.MINOR

Where

  Field   Meaning
  ------- ---------------------------------------------
  C       Constitution major version
  MAJOR   Structural change to artifact specification
  MINOR   Clarifications or non‑breaking updates

Example

Governor v15.1.0\
Architect v15.1.0

Interpretation

  Value   Meaning
  ------- ------------------------------------
  15      Compatible with Constitution v15
  1       Compatible with Constitution v15.1
  0       Artifact revision level

Rules

1.  Enforcement artifacts must synchronize their C field with the
    constitutional version.
2.  Enforcement artifacts may increment their own MAJOR or MINOR
    versions independently if constitutional compatibility is preserved.
3.  Any artifact that violates constitutional compatibility must update
    the C field.

------------------------------------------------------------------------

# Runtime Wrapper Versioning

The Runtime Wrapper (RTW) implements executable enforcement of the
Governor and Architect specifications.

RTW versions follow full semantic versioning.

Format

vMAJOR.MINOR.PATCH

Meaning

  Component   Meaning
  ----------- ----------------------------------
  MAJOR       Breaking runtime behavior change
  MINOR       New functionality
  PATCH       Bug fixes

Example

RTW v1.4.2

RTW compatibility must declare:

Compatible Constitution\
Compatible Governor\
Compatible Architect

------------------------------------------------------------------------

# Runtime Implementation Versioning

Language‑specific implementations (Python, Node, Rust, etc.) follow
standard semantic versioning independent of the constitutional
numbering.

Example

cosyn-runtime-python v0.3.1\
cosyn-runtime-node v0.2.0

Runtime implementations must declare:

Supported RTW version\
Supported Constitution version

------------------------------------------------------------------------

# Synchronization Rules

Synchronization ensures that all layers remain aligned.

Rule 1 --- Constitutional Authority

The constitution is the authoritative kernel.\
All artifacts must declare compatibility with a constitutional version.

Rule 2 --- Artifact Sync

Governor and Architect versions must update their C field when the
constitution MAJOR or MINOR version changes.

Rule 3 --- Runtime Independence

RTW versions may evolve independently as long as they remain compliant
with Governor and Architect specifications.

Rule 4 --- Implementation Independence

Language runtimes may evolve independently of RTW as long as they
maintain compatibility.

------------------------------------------------------------------------

# Version Declaration Standard

All artifacts must include a version declaration header.

Example

Compatibility

Constitution: v15.1\
Artifact: Governor v15.1.0\
Runtime Requirement: RTW compliant

------------------------------------------------------------------------

# Breaking Change Protocol

Breaking changes require explicit version updates.

  Change Type                  Required Version Change
  ---------------------------- -------------------------
  Constitution rule change     Constitution MAJOR
  Constitution clarification   Constitution MINOR
  Governor topology change     Artifact MAJOR
  Architect topology change    Artifact MAJOR
  RTW breaking change          RTW MAJOR
  Runtime bug fix              PATCH

------------------------------------------------------------------------

# Version Alignment Example

Example stack alignment:

Constitution v15.1\
Governor v15.1.0\
Architect v15.1.0\
RTW v1.0.0\
cosyn-runtime-python v0.1.0

------------------------------------------------------------------------

# Design Rationale

This versioning model ensures:

-   Constitutional invariants remain stable
-   Governance policy artifacts stay synchronized with the constitution
-   Runtime systems can evolve independently
-   Developers can build multiple runtimes without fragmenting
    governance integrity

------------------------------------------------------------------------

# Repository Placement

Canonical location

/docs/governance/versioning.md

This document governs version synchronization for the entire CoSyn
repository.
