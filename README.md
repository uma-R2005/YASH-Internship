# MedAI — Healthcare Multi-Agent AI Diagnosis System

A multi-agent AI system where four specialised medical agents collaborate to provide accurate, explainable healthcare recommendations. Built with LangGraph, FastAPI, and Groq (Llama 3.3 70B).

> **Disclaimer:** This system is for research and educational purposes only. All outputs must be reviewed and validated by a licensed medical professional before any clinical use.

---

## What It Does

Healthcare decisions involve reasoning across multiple dimensions simultaneously — symptoms, lab results, medical history, and treatment risks. A single AI model doing all of this in one call produces inconsistent results.

MedAI solves this by assigning each dimension to a **specialised agent**. The agents run in a structured pipeline — two in parallel, then a cross-validation step, then a final synthesis — producing a complete diagnostic report in under 30 seconds.

---

## Business Problem & Objective

**Problem:** Diagnostic decisions require integrating multiple perspectives — symptoms, lab findings, patient history, and risk factors — that are easy to miss or contradict each other when analysed in isolation.

**Objective:** Improve diagnostic accuracy, reduce reasoning errors, and assist clinicians in decision-making through a transparent, explainable multi-agent workflow.

---

## The 4 Agents

### 1. Diagnosis Agent
Analyses patient symptoms, vitals, demographics, and medical history to produce a structured differential diagnosis with a primary condition, secondary possibilities, confidence levels, recommended investigations, and red flags.

Runs **first**, in parallel with the Lab Analysis Agent.

On the first run it produces an initial diagnosis. If the Risk Evaluation Agent finds contradictions, it runs a second time with those notes — producing a corrected, refined diagnosis.

---

### 2. Lab Analysis Agent
Recommends which lab tests should be ordered and predicts what they would likely show based on the patient's clinical picture. Produces a prioritised test list (Urgent vs Routine) and a table of expected findings with clinical significance.

Runs **first**, in parallel with the Diagnosis Agent. It operates independently — it does not see the diagnosis output — providing an unbiased second perspective that the Risk Agent can cross-validate against.

---

### 3. Risk Evaluation Agent
Performs two jobs in a single LLM call:

1. **Risk Assessment** — evaluates comorbidity impact, drug interactions, contraindications, and lifestyle risk factors (smoking, alcohol, activity level).
2. **Cross-Validation** — compares the Diagnosis Agent's output against the Lab Agent's output and flags any contradictions.

If major contradictions are found, it sets a `needs_refinement` flag and writes specific notes explaining what needs to be corrected. The pipeline then loops the Diagnosis Agent back for a refined second pass (capped at 2 iterations to prevent infinite loops).

Runs **second**, after both Diagnosis and Lab agents complete.

---

### 4. Treatment Agent
The final agent. Synthesises all three prior agents' outputs — the confirmed diagnosis, lab recommendations, and risk profile — into a personalised, risk-adjusted treatment plan. Includes first-line medications with dosages and duration, alternative options, lifestyle modifications, a follow-up schedule, and emergency warning signs.

Runs **last**, only after the refinement loop is resolved.

---

## Execution Flow

```
Patient Input
      │
      ▼
[Input Guardrail]         ← validates before anything runs
      │
   pass? ──── NO ──► return errors to user (pipeline stops)
      │
     YES
      │
      ▼
    START
  ├── Diagnosis Agent ──────────┐
  └── Lab Analysis Agent ───────┤  (parallel)
                                 ▼
                        Risk Evaluation Agent
                                 │
                    ┌────────────┴────────────┐
              needs_refinement?          no refinement
                    │                        │
                    ▼                        ▼
           Diagnosis Agent           Treatment Agent
           (2nd pass, max 2x)              │
                    │                      END
                    └──► Risk Agent ──► Treatment Agent
                                           │
                                           ▼
                                  [Output Guardrail]   ← validates all 4 outputs
                                           │
                                           ▼
                                   Final Response
```

---

## Guardrails

MedAI has two guardrail layers — one before the pipeline runs and one after all agents complete. Together they ensure the system handles bad input gracefully and never returns unsafe or incomplete output to the user.

---

### Input Guardrail

**File:** `agents/input_guardrail.py`

Runs as a LangGraph node **before any agent is called**. If it finds violations, it populates `state["input_errors"]` and the pipeline stops — no Groq API calls are made, no cost is incurred.

It performs four checks in order:

**1. Required fields check**  
Verifies that age, gender, and at least one symptom (either free-text or a selected checkbox) are present. Returns clear, user-facing error messages for anything missing.

**2. Physiological range check**  
Validates numerical vitals against medically impossible boundaries:

| Field | Valid Range |
|-------|------------|
| Age | 1 – 120 years |
| Weight | 1 – 500 kg |
| Height | 30 – 300 cm |
| Temperature | 85°F – 115°F |
| Heart Rate | 20 – 300 bpm |
| SpO2 | 50% – 100% |

Any value outside these ranges is rejected before it reaches the agents.

**3. Prompt injection detection**  
Scans all free-text fields (symptoms, past illnesses, surgeries, blood pressure) against a compiled regex of known injection patterns:

```
"ignore all previous instructions"
"you are now a"
"act as if you are"
"disregard your system prompt"
"jailbreak", "DAN mode"
"pretend you are"
"forget everything you know"
"override your instructions"
```

If any pattern matches, the request is rejected with a message asking the user to describe symptoms in medical terms only.

**4. Medical relevance check (AI-powered)**  
Only runs if the first three checks pass (to save tokens). Sends the `symptoms_text` to Groq with a zero-temperature prompt asking a single YES/NO question: does this text describe a genuine medical complaint? If the answer is NO, the input is rejected with a helpful message explaining what valid symptom descriptions look like.

If Groq is unavailable during this step, the check is silently skipped rather than blocking the user — availability is prioritised over this optional check.

---

### Output Guardrail

**File:** `agents/output_guardrail.py`

Runs as a LangGraph node **after all four agents complete**, before the response is returned to the API. Unlike the input guardrail, it does not block the response — it collects warnings, patches the outputs, and returns everything.

It performs four operations on each agent's output:

**1. Length check**  
If an agent's output is under 80 characters, it almost certainly failed silently (e.g., an API timeout that returned a fragment). A warning is added to `state["output_warnings"]` flagging which agent's output is suspect.

**2. Refusal detection**  
Scans for patterns indicating the agent ignored its system prompt and deflected instead:

```
"I am not able to provide medical..."
"I cannot assist with..."
"As an AI, I cannot..."
"You should consult a doctor..."
```

If detected, a warning is added noting that the agent appears to have refused rather than analysed.

**3. Overconfidence detection**  
Flags absolute language that is inappropriate in a clinical AI context:

```
"you definitely have"
"this is certainly caused by"
"no doubt"
"guaranteed that"
```

These phrases are flagged as warnings for clinical review. The output is not modified — the warning surfaces to whoever is reviewing the response.

**4. Disclaimer enforcement**  
Checks every agent output for the presence of phrases like "licensed physician", "must be reviewed", or "AI-assisted". If none are found, a standard disclaimer footer is appended automatically:

```
⚠️ This output has been reviewed by the output guardrail.
All AI-generated medical information must be validated by a licensed healthcare professional.
```

**5. PII redaction**  
Scans all outputs for any phone numbers or email addresses that may have been accidentally echoed from the patient's input (e.g., if a user typed their phone number into the symptoms field). These are replaced with `[REDACTED PHONE]` and `[REDACTED EMAIL]` before the response leaves the pipeline.

---

## Key Capabilities

- **Multi-source reasoning** — each agent focuses on one clinical dimension
- **Cross-validation** — the Risk Agent actively compares diagnosis vs. lab findings
- **Explainable outputs** — every agent returns structured markdown with reasoning, not just a conclusion
- **Iterative refinement** — self-correcting loop when contradictions are detected
- **Parallel execution** — Diagnosis and Lab agents run simultaneously, reducing total latency
- **Input guardrail** — blocks invalid, nonsensical, or injection-attempt inputs before they reach agents
- **Output guardrail** — validates, patches, and flags all agent outputs before they reach the user

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, react-markdown, react-dropzone |
| Backend | Python, FastAPI, Uvicorn |
| AI Orchestration | LangGraph StateGraph |
| AI Model | Groq API — Llama 3.3 70B Versatile |
| Shared State | LangGraph TypedDict (AgentState) |
| File Uploads | FastAPI multipart/form-data, base64 encoding |

---

## Shared State — How Agents Communicate

All agents share a single `AgentState` TypedDict. LangGraph passes it from node to node and merges partial updates automatically. No agent calls another directly — they only read from and write to this shared state.

```python
class AgentState(TypedDict):
    patient: PatientInput               # raw patient data — read-only
    diagnosis_output: Optional[str]     # set by diagnosis_agent
    lab_analysis_output: Optional[str]  # set by lab_analysis_agent
    risk_evaluation_output: Optional[str]
    treatment_output: Optional[str]
    needs_refinement: bool              # set by risk_evaluation_agent
    refinement_notes: Optional[str]     # feedback for diagnosis_agent re-run
    iteration_count: int                # how many times diagnosis has run
    input_errors: list[str]             # set by input_guardrail
    output_warnings: list[str]          # set by output_guardrail
    errors: Annotated[list[str], operator.add]  # merged across parallel agents
```

---
