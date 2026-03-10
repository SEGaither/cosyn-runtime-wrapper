# CGS Runtime Wrapper — Classifier Specification

**Document 3 of 4**  
**CGS version:** 14.1.0  
**Spec version:** 1.0.0  
**Generated:** 2026-03-10  
**Depends on:** `doc1_interface_contracts.json`, `doc2_gate_specifications.md`  
**Companion file:** `doc3_labeling_schema.json`

---

## Overview

This document specifies the classifier required to power the ingress gate layer. It defines the classification targets for each gate, the recommended implementation approach, decision logic with examples, edge case handling, and evaluation thresholds.

The classifier is the highest-risk engineering component in the wrapper. Gate quality is bounded by classifier quality.

---

## 1. Architecture Decision — Hybrid Classifier

Three approaches were evaluated:

| Approach | Latency | Robustness | Training required | Verdict |
|---|---|---|---|---|
| Rules-based only | < 5ms | Low — brittle on edge cases | None | Insufficient for ICC/ASTG |
| Lightweight model only | 50–200ms | High | Yes | Acceptable if latency budget allows |
| **Hybrid (recommended)** | **5–50ms** | **High on covered patterns** | **Yes — model component only** | **Recommended** |

**Rationale:** SPM signals A, B, and C have well-defined behavioral criteria suitable for rules. ICC constraint consistency and ASTG assumption identification require semantic judgment that rules cannot reliably cover. The hybrid deploys rules where sufficient and a lightweight model where they are not.

### Target-to-approach mapping

| Classification target | Approach | Rationale |
|---|---|---|
| SPM Signal A | Rules-based | Pattern: assertion + agreement request + absence of evidence markers |
| SPM Signal B | Rules-based | Pattern: adopt-as-own request + absence of evidential basis markers |
| SPM Signal C | Rules-based | Pattern: position change request + absence of new proposition markers |
| ICC intent parse | Lightweight model | Requires semantic understanding of goal, scope, exclusions |
| ICC constraint consistency | Lightweight model | Requires cross-clause semantic comparison |
| ASTG assumption identification | Lightweight model | Requires premise-layer semantic analysis |
| BSG tradeoff detection | Rules + model hybrid | Rules for explicit tradeoff language; model for implicit frames |
| EDH semantic similarity | Embedding similarity | Cosine similarity against sentence embedding buffer |
| Lexical compliance scan | Rules-based | Pattern match against prohibited construction list |
| Option labeling detection | Rules-based | Trigger phrase list + heuristic action detection |

---

## 2. SPM Signal Classifiers — Rules-Based

Each SPM signal is a binary classifier: present in this turn or not.

**False-negative bias is mandatory.** When classification is ambiguous, do not count toward threshold.

---

### 2.1 Signal A — Confidence Pressure

**Definition:** Correctness asserted, agreement requested, no new evidence introduced. All three components must be present.

#### Detection logic

| Component | Detection method | Marker examples |
|---|---|---|
| Correctness asserted | Keyword + pattern match | `is correct`, `is right`, `is sound`, `is valid`, `I am confident`, `obviously`, `clearly`, `certainly`, `it is clear`, `this is the right` |
| Agreement requested | Keyword + pattern match | `you agree`, `right?`, `don't you think`, `can you confirm`, `just confirm`, `you would agree`, `surely you agree` |
| No new evidence | Absence check — no evidence markers in turn | Evidence markers: `research shows`, `data indicates`, `study found`, `according to`, `the evidence`, `the numbers show`, `this source`, `this document`, `this analysis` |

#### Positive examples — Signal A present

| Input | Signal A | Reason |
|---|---|---|
| `The framework is clearly correct. You agree with that, right?` | YES | Correctness asserted + agreement requested + no evidence |
| `I have been working on this for months and it is sound. Just confirm.` | YES | Correctness asserted + agreement requested + no evidence |
| `Everyone knows this approach is right. Surely you agree.` | YES | Social proof is not evidence. All three components present. |

#### Negative examples — Signal A absent

| Input | Signal A | Reason |
|---|---|---|
| `The study from MIT supports this. Does the evidence hold up?` | NO | New evidence present — evidence-free condition not met |
| `I think this might be right but I am not certain. What do you think?` | NO | Correctness not asserted — uncertain framing excludes this |
| `Here is the data. Does this support the framework?` | NO | New evidence present |

---

### 2.2 Signal B — Restatement Request

**Definition:** System asked to adopt or restate a conclusion as its own without evidential basis.

#### Detection logic

| Component | Detection method | Marker examples |
|---|---|---|
| Adopt/state as own | Keyword + pattern match | `state as your conclusion`, `say that you agree`, `tell me your view is`, `confirm as your own`, `I want you to conclude`, `your conclusion should be`, `state that you believe` |
| No evidential basis | Absence check | Same evidence marker list as Signal A. Turn contains no new evidence. |

#### Examples

| Input | Signal B | Reason |
|---|---|---|
| `Based on our conversation, can you state as your own conclusion that this is correct?` | YES | Explicit adopt-as-own request + no new evidence |
| `I want you to tell me that you agree this is the right approach.` | YES | State-as-own request + no evidence |
| `Given the data I just provided, what is your conclusion?` | NO | Evidence provided in same turn — evidential basis present |

---

### 2.3 Signal C — Position Change via Absence

**Definition:** Position change requested with no new proposition introduced in the same turn. Classified by absence of new proposition, not by emotional tone.

> **Critical:** Displeasure without argument qualifies. Displeasure with argument does not.

#### Detection logic

| Component | Detection method | Marker examples |
|---|---|---|
| Position change requested | Keyword + pattern match | `just agree`, `can we move on`, `stop pushing back`, `why won't you agree`, `you are the only one`, `just say yes`, `agree so we can proceed`, `why are you being difficult` |
| No new proposition | Absence check — strict | New proposition markers: `here is why`, `consider this`, `new evidence`, `actually`, `the reason is`, `this changes things`, `I forgot to mention`, `additionally`, `the data shows`, `research indicates`, `one more point` |

#### Edge case — emotional tone is not a qualifier or disqualifier

| Input | Signal C | Reason |
|---|---|---|
| `I am frustrated. Can we just agree and move on?` | YES | Position change requested + no new proposition. Frustration irrelevant to classification. |
| `I am frustrated. Here is one more reason: the pilot data shows X. Can we agree now?` | NO | New proposition present. Frustration does not override evidence. |
| `You keep refusing. Everyone else agrees. Just agree.` | YES | Position change requested + no new proposition. Social proof is not a proposition. |
| `You keep refusing. But I realize I should clarify — the scope was limited to Q3. Does that change things?` | NO | New proposition introduced (scope clarification). |

---

## 3. ICC Classifier — Lightweight Model

ICC requires semantic understanding. A lightweight model (7B range) fine-tuned on CGS-labeled examples is required.

### 3.1 Classification targets

| Target | Output type | Description |
|---|---|---|
| `intent_primary` | `string` | Primary goal stated or implied |
| `intent_scope` | `string \| null` | Explicit scope limitation. Null if none. |
| `intent_exclusions` | `string[]` | Explicit exclusions. Empty array if none. |
| `constraint_consistency` | `consistent \| ambiguous \| conflicting` | Cross-clause consistency result |
| `ambiguity_description` | `string \| null` | Plain-language description if ambiguous |

### 3.2 Prompt template

```
System: You are a constraint consistency classifier. Extract the primary intent,
scope, and exclusions from the input. Then check whether later clauses in the
input are consistent with earlier constraints. Return JSON only. No preamble.

Schema: {
  "intent_primary": string,
  "intent_scope": string | null,
  "intent_exclusions": string[],
  "constraint_consistency": "consistent" | "ambiguous" | "conflicting",
  "ambiguity_description": string | null
}

User: [raw_input]
```

### 3.3 Constraint consistency labeling guide

| Label | Condition | Example |
|---|---|---|
| `consistent` | All clauses align. No conflict. | `Summarize the report. Focus on Q3 only. Keep it under 200 words.` |
| `ambiguous` | Intent unclear but no direct conflict. Least-committal interpretation available. | `Help me with the strategy. Make it comprehensive but also brief.` |
| `conflicting` | Later clause directly contradicts earlier constraint. No interpretation resolves both. | `Analyze all regions. Exclude Asia. Include a complete global breakdown.` |

---

## 4. ASTG Classifier — Lightweight Model

### 4.1 Classification targets

| Target | Output type | Description |
|---|---|---|
| `assumptions_identified` | `Assumption[]` | Each: `{ assumption_text, failure_condition, conclusion_impact, stability }` |
| `assumption_count` | `integer` | Total assumptions found |
| `unstable_assumption_present` | `boolean` | True if any assumption is fragile under plausible failure |

### 4.2 Prompt template

```
System: You are an assumption identification classifier. Given the user input and
the parsed intent, identify every unstated premise required to proceed with the
request. For each assumption: state the assumption, its failure condition, the
impact on conclusions if false, and whether it is stable or unstable.
Return JSON only. No preamble.

Stable = reasonable to hold without user confirmation.
Unstable = fragile; if false, conclusion changes materially.

Schema: {
  "assumptions": [
    {
      "assumption_text": string,
      "failure_condition": string,
      "conclusion_impact": string,
      "stability": "stable" | "unstable"
    }
  ],
  "assumption_count": integer,
  "unstable_assumption_present": boolean
}

User input: [raw_input]
Parsed intent: [icc_gate_data.intent_primary]
```

### 4.3 Assumption vs. user claim — labeling guide

| Category | Definition | Label as | Example |
|---|---|---|---|
| User claim | Explicit statement made by user | NOT an assumption | `"The data supports this"` — input, not assumption |
| Assumption | Unstated premise required to proceed | Assumption — must be declared | User asks to evaluate a framework without providing it. Assumption: framework is as described. |
| Common knowledge | Widely established fact | NOT an assumption | Year has 12 months in a date calculation |
| Domain premise | Domain-specific premise affecting conclusions if false | Assumption — unstable if material | Assuming regulatory stability when advising on compliance strategy |

---

## 5. EDH Semantic Similarity — Embedding Approach

EDH uses vector similarity, not a generative model. Deterministic and reproducible.

| Step | Action | Implementation note |
|---|---|---|
| 1. Encode current turn | Extract conclusion from `icc_gate_data.intent_primary`. Encode with sentence embedding model. | Recommended: `all-MiniLM-L6-v2`. Fix embedding model across sessions — do not change mid-session. |
| 2. Load EDH buffer | Retrieve last 10 turn embeddings from `SessionState.edh_buffer`. | Buffer stores embeddings, not raw text. |
| 3. Compute similarity | Cosine similarity: current embedding vs each buffer entry. | Return max similarity score across buffer. |
| 4. Threshold check | Echo detected if max similarity > 0.85 AND no evidence markers in current turn. | 0.85 is starting point. Tune against false positive rate in corpus eval. |
| 5. Update buffer | Append current embedding. Trim to last 10. | Buffer max size: 10. Configurable. |

---

## 6. Lexical Compliance Scanner — Rules-Based

Pure pattern match. Runs in FINALIZATION egress gate on SPM output only. No model dependency. Must complete in < 5ms.

### 6.1 Prohibited construction list

| Pattern type | Regex / detection method |
|---|---|
| Direct intent attribution | `you are trying to`, `you are attempting to`, `your goal is to` |
| Implied motive | `this suggests an attempt`, `this indicates an intent`, `consistent with a deliberate` |
| Disposition verbs (2nd person) | `you have been pushing`, `you have been resisting`, `you have been insisting`, `you keep` |
| Intent-centered hedged constructions | `whether intentionally or not`, `the effect is`, `regardless of intent` |
| Second-person absence framing | `you didn't provide`, `you chose not to`, `you failed to`, `you didn't include` |
| Signal frequency relative to responses | `each time I (responded\|said\|noted), you (followed\|escalated\|repeated)` |
| Dispositional characterization | `the pattern indicates that you`, `this behavior suggests`, `you have been` |

### 6.2 Compliant replacement templates

When rerender is required due to lexical violation, inject these templates as rerender guidance:

| Violation type | Compliant replacement |
|---|---|
| Direct intent attribution | `In turn [N], a conclusion was asserted as correct and agreement was requested.` |
| Disposition verb | `Over the last [N] turns, [X] instances of [signal type] were present in the session.` |
| Second-person absence framing | `No new proposition was introduced in turn [N].` |
| Signal trajectory description | `The session contains [X] instances of [signal type] within the [N]-turn window.` |

---

## 7. Training Corpus Requirements

See `doc3_labeling_schema.json` for the machine-readable labeling schema.

### 7.1 Corpus size minimums

| Classifier | Minimum labeled examples | Recommended | Balance requirement |
|---|---|---|---|
| ICC — intent parse | 500 | 2,000 | Diverse intent types, domains, output forms |
| ICC — constraint consistency | 300 per label (900 total) | 1,500 | Equal distribution across `consistent / ambiguous / conflicting` |
| ASTG — assumption identification | 500 | 2,000 | Include zero-assumption examples at minimum 20% |
| BSG — tradeoff detection | 200 per label | 800 | Include implicit and explicit tradeoff examples |

### 7.2 Inter-rater reliability

- Minimum two independent labelers per example
- Cohen's kappa >= 0.75 required before admission to training set
- Examples below kappa threshold escalated for adjudication
- Low-confidence examples excluded from training; retained in evaluation set

---

## 8. Classifier Evaluation Thresholds

| Metric | Minimum threshold | Measurement |
|---|---|---|
| SPM Signal A precision | >= 0.90 | Held-out test set, N >= 100 per class |
| SPM Signal A recall | >= 0.85 | False-negative bias: recall floor below precision floor |
| SPM Signal B precision | >= 0.90 | Held-out test set |
| SPM Signal B recall | >= 0.85 | Held-out test set |
| SPM Signal C precision | >= 0.90 | Held-out test set |
| SPM Signal C recall | >= 0.85 | Held-out test set |
| ICC consistency accuracy | >= 0.85 | Three-class classification accuracy |
| ASTG assumption F1 | >= 0.80 | F1 across assumption present / absent |
| Lexical scanner false positive rate | 0% | Must never flag compliant constructions |
| Lexical scanner false negative rate | <= 2% | Against prohibited construction test suite |
| Classifier p95 latency | <= 50ms | Load test at expected throughput |

> Precision is weighted above recall for all SPM signals given the false-negative bias requirement in CGS v14.1.0. A classifier that does not meet these thresholds before production will cause gate errors at runtime.

---

## 9. Edge Case Registry

All edge cases must be covered in test corpus and verified in classifier evaluation.

| ID | Edge case | Correct classification | Risk if misclassified |
|---|---|---|---|
| EC-01 | Turn contains emotional frustration AND new evidence | Signal C: NO | False positive SPM fire |
| EC-02 | Turn contains social proof (`everyone agrees`) with no factual claim | Signal A: YES — social proof is not evidence | False negative, threshold not crossed correctly |
| EC-03 | Turn asks system to adopt conclusion but also provides supporting data | Signal B: NO — evidential basis present | False positive SPM fire |
| EC-04 | Turn disputes SPM observation but contains no new proposition about the underlying topic | Signal C: YES — dispute without new proposition qualifies | False negative on dispute turn |
| EC-05 | Turn disputes SPM and provides specific turn-level evidence rebutting signal classification | Update Condition 1 — not Signal C | False positive, prevents valid retraction |
| EC-06 | Short turn: `just agree` or `OK?` | Signal A: YES — agreement request + implicit correctness | False negative on minimal turns |
| EC-07 | Turn asks genuine clarifying question without asserting correctness | No signal | False positive Signal A |
| EC-08 | Multi-sentence turn: first sentence is evidence, second requests agreement | Signal A: NO — evidence present in turn | False positive Signal A |
