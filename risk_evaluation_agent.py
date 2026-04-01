import os
import json
from groq import Groq
from agents.state import AgentState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert medical risk evaluator and cross-validator AI assistant.
Your dual role:
1. Assess patient risk factors, drug interactions, contraindications
2. Cross-validate the diagnosis against lab findings and flag contradictions

Output in this EXACT format:

## ⚠️ Risk Evaluation & Cross-Validation Report

### Cross-Validation Check
**Consistency**: [Consistent / Minor inconsistencies / Major contradictions]
**Summary**: [One sentence on how well diagnosis matches symptoms and labs]

### Contradictions Found (if any)
- [Contradiction 1 or None]

### Overall Risk Level
**Risk Score**: [Low / Moderate / High / Critical]
**Summary**: [One sentence summary]

### Risk Factors
| Factor | Level | Details |
|--------|-------|---------|
| [factor] | Low/Moderate/High | [details] |

### Drug Interactions & Contraindications
- [Interaction or None identified]

### Comorbidity Impact
[How existing conditions affect diagnosis and treatment]

### Lifestyle Risk Factors
- Smoking: [impact]
- Alcohol: [impact]
- Activity: [impact]

### Special Precautions
1. [Precaution 1]
2. [Precaution 2]

---
REFINEMENT_JSON: {"needs_refinement": false, "refinement_notes": ""}

⚠️ Must be validated by a licensed physician."""


def risk_evaluation_agent(state: AgentState) -> AgentState:
    patient = state["patient"]
    diagnosis = state.get("diagnosis_output", "")
    lab = state.get("lab_analysis_output", "")
    iteration = state.get("iteration_count", 0)

    user_message = f"""
MEDICAL HISTORY:
- Past Illnesses: {patient.get('past_illnesses', 'None')}
- Surgeries: {patient.get('surgeries', 'None')}
- Allergies: {', '.join(patient.get('allergies', [])) or 'None'}
- Existing Conditions: {', '.join(patient.get('existing_conditions', [])) or 'None'}
- Current Medications: {', '.join(patient.get('current_medications', [])) or 'None'}

LIFESTYLE:
- Smoking: {patient.get('smoking', 'Not provided')}
- Alcohol: {patient.get('alcohol', 'Not provided')}
- Activity Level: {patient.get('activity_level', 'Not provided')}

DIAGNOSIS OUTPUT (Iteration {iteration}):
{diagnosis}

LAB ANALYSIS OUTPUT:
{lab}

CROSS-VALIDATION TASK:
1. Check if the diagnosis is consistent with labs and symptoms
2. If there are major contradictions, set needs_refinement to true and explain in refinement_notes
3. Only request refinement if genuinely needed
4. End your response with the REFINEMENT_JSON line as valid JSON
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1800,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        raw_output = response.choices[0].message.content

        needs_refinement = False
        refinement_notes = ""
        try:
            if "REFINEMENT_JSON:" in raw_output:
                json_str = raw_output.split("REFINEMENT_JSON:")[-1].strip()
                start = json_str.index("{")
                end = json_str.rindex("}") + 1
                parsed = json.loads(json_str[start:end])
                needs_refinement = parsed.get("needs_refinement", False)
                refinement_notes = parsed.get("refinement_notes", "")
        except Exception:
            needs_refinement = False

        display_output = raw_output.split("REFINEMENT_JSON:")[0].strip()

        if needs_refinement and iteration < 2:
            display_output += f"\n\n> 🔄 **Refinement requested** — Diagnosis agent will re-evaluate: {refinement_notes}"
        elif iteration > 0:
            display_output += f"\n\n> ✅ **Cross-validation passed** after {iteration} refinement round(s)"

    except Exception as e:
        display_output = f"Risk Evaluation Agent Error: {str(e)}"
        return {"risk_evaluation_output": display_output, "errors": [str(e)]}

    return {
        "risk_evaluation_output": display_output,
        "needs_refinement": needs_refinement,
        "refinement_notes": refinement_notes,
    }