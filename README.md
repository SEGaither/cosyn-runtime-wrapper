# CoSyn Runtime Wrapper (CGS Runtime Wrapper)

Runtime governance environment enforcing the **CoSyn Governance Stack (CGS) v15.1.0** on every AI interaction.

The runtime wrapper places AI models **inside a deterministic governance pipeline** that enforces reasoning discipline before and after model execution.

Unlike prompt guardrails, policy engines, or tool-call security layers, CoSyn governs the **reasoning process itself**.

---

# Governance Versions (Runtime Distribution)

The Runtime Wrapper distribution includes the following constitutional artifacts:

| Artifact           | Version |
| ------------------ | ------- |
| CoSyn Constitution | v15.1.0 |
| Persona Governor   | v3.15.0 |
| Stack Architect    | v3.15.0 |

These artifacts define the governance rules enforced by the runtime wrapper.

---

# What CoSyn Is

CoSyn is a **runtime governance operating environment for AI systems**.

Every interaction passes through a structured governance pipeline:

User
↓
Ingress Governance Gates
↓
LLM Reasoning
↓
Egress Governance Gates
↓
User Response + Telemetry Ledger

The model does not operate freely.

It operates **inside the CoSyn governance pipeline**.

The wrapper enforces:

• explicit interpretation of user intent
• identification of hidden assumptions
• bias and optimization frame declaration
• reasoning outcome scoring
• structured response compliance
• full telemetry audit trail

---

# Why Runtime Governance Is Necessary

AI safety approaches typically operate at one of three layers:

| Approach          | Enforcement Layer        |
| ----------------- | ------------------------ |
| Prompt guardrails | Input / output text      |
| Policy engines    | Model output evaluation  |
| Tool contracts    | Tool invocation boundary |

These approaches leave the **reasoning pipeline itself ungoverned**.

CoSyn addresses this gap by enforcing governance **before and after reasoning occurs**.

---

# How CoSyn Differs From Other Systems

| System    | Governance Layer                                                |
| --------- | --------------------------------------------------------------- |
| SmythOS   | Agent workflow orchestration                                    |
| SAFi      | Policy enforcement on model outputs                             |
| CORE      | Constitutional governance for AI-assisted development workflows |
| Edictum   | Deterministic contracts on tool calls                           |
| **CoSyn** | Governance of the AI reasoning pipeline                         |

CoSyn governs the **cognitive structure of AI interactions**, not just the actions or outputs.

---

# Architecture Overview

The runtime wrapper acts as **governance middleware** between the user and the AI model.

User
↓
FastAPI Runtime Wrapper
↓
Ingress Governance Gates
↓
Model Adapter
↓
Egress Governance Gates
↓
Telemetry Store
↓
Response

Components:

• FastAPI runtime service
• Redis session state store
• ingress governance gates
• egress governance gates
• model adapter layer
• telemetry audit system

---

# Gate Architecture

The pipeline contains **two governance stages**.

## Ingress Gates (Pre-Reasoning)

These gates execute **before the model runs**.

| Gate | Purpose                                                                        | Implementation     |
| ---- | ------------------------------------------------------------------------------ | ------------------ |
| ICC  | Interpretive Commitment Control — parse intent and detect constraint conflicts | Stub (model-based) |
| ASTG | Assumption Stress Test — enumerate hidden premises                             | Stub (model-based) |
| BSG  | Bias Selection Gate — require explicit optimization frame                      | Partial rules      |
| EDH  | Echo Detection Heuristic — detect repetition patterns                          | Stub (embedding)   |
| SPM  | Session Pattern Monitor — detect emerging interaction signals                  | Rules              |
| PRAP | Pre-Reasoning Assurance Protocol — aggregate gate outcomes                     | Rules              |

Ingress halts immediately if any gate fails.

---

## Egress Gates (Post-Reasoning)

These gates execute **after the model returns**.

| Gate         | Purpose                           | Implementation |
| ------------ | --------------------------------- | -------------- |
| OSCL         | Outcome-Scored Self-Critique Loop | Stub           |
| FINALIZATION | Structured output validation      | Rules          |
| TELEMETRY    | Audit logging                     | Full           |

The FINALIZATION gate enforces:

• structured response format
• scope compliance
• lexical compliance
• option labeling discipline
• governance stack rules

---

# Telemetry and Auditability

Each interaction generates a **TelemetryTurnRecord** containing:

• gate outcomes
• model latency
• reasoning metadata
• session state
• compliance results

Telemetry can be rendered using:

POST /telemetry/render

Supported levels:

minimal
standard
full

---

# Special Governance Handlers

The runtime includes special command handlers:

| Signal                            | Behavior                 |
| --------------------------------- | ------------------------ |
| NFAR / no further action required | Output: `Standing by.`   |
| EOS                               | Session snapshot + reset |
| Trace This                        | Emit audit ledger        |

---

# Stub Disclosure

The following components are **placeholders pending training corpus completion**.

| Component       | File                          | Stub Behavior                 |
| --------------- | ----------------------------- | ----------------------------- |
| ICC classifier  | classifier/icc_classifier.py  | generic intent classification |
| ASTG classifier | classifier/astg_classifier.py | no assumptions detected       |
| EDH similarity  | classifier/edh_similarity.py  | similarity score 0            |
| OSCL scorer     | egress/gates/oscl.py          | fixed score 0.85              |

Rules-based governance gates are **fully implemented**.

---

# Prerequisites

| Requirement | Version |
| ----------- | ------- |
| Python      | 3.11+   |
| Redis       | 6+      |
| pip         | 23+     |

---

# Installation — Local Run

cd <project-root>

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .

cp .env.example .env

redis-server --daemonize yes

uvicorn cgs_runtime_wrapper.api.main:app --reload --port 8000

Server runs at:

[http://localhost:8000](http://localhost:8000)

---

# Running with Docker

cp .env.example .env

docker compose up --build

Services:

| Service         | Port |
| --------------- | ---- |
| Redis           | 6379 |
| Runtime Wrapper | 8000 |

Shutdown:

docker compose down

---

# Authentication

All requests must include an API key.

Header:

X-API-Key

Example:

curl -X POST [http://localhost:8000/turn](http://localhost:8000/turn) 
-H "Content-Type: application/json" 
-H "X-API-Key: your-api-key"

---

# Adapter Architecture

Model adapters implement the ModelAdapter interface:

class ModelAdapter(ABC):
async def call_model(self, prompt: str, session_id: str) -> tuple[str, int]

Supported adapters:

• stub
• Claude
• OpenAI
• custom implementations

---

# Licensing

This repository is distributed under the **Source Available License v4**.

• Non-commercial use permitted.
• Commercial licensing available under `LICENSE-COMMERCIAL`.

Contact the project maintainer for enterprise licensing.

---

## Intellectual Property and Patent Policy

Certain architectural concepts implemented in the CoSyn Runtime Wrapper may qualify for patent protection or defensive publication.

The project maintains a documented patent and defensive publication strategy.

See:

PATENTS.md

for details regarding:

- defensive publication strategy
- patent candidate categories
- contributor notice regarding patent inclusion
- commercial patent licensing boundaries

---

# Trademark Notice

CoSyn is a governance framework and runtime architecture created by the project author. The name and associated marks may be protected under trademark law.

---

# About

FastAPI + Redis governance middleware implementing the **CoSyn runtime governance pipeline**.

Deterministic ingress and egress governance gates on every LLM interaction.

Audit-traceable. Runtime-enforced. Governance-bound.
