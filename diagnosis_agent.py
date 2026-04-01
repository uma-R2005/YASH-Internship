import os
from groq import Groq
from agents.state import AgentState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert clinical diagnosis AI assistant.
Analyse patient symptoms, vitals, and basic information to produce a structured differential diagnosis.
If refinement notes are provided, address those contradictions explicitly.

Output your response in this EXACT format:

## 🔬 Differential Diagnosis

### Primary Diagnosis
**Condition**: [Most likely diagnosis]
**Confidence**: [High / Medium / Low]
**Reasoning**: [Clinical reasoning in 2-3 sentences]

### Secondary Diagnoses
1. **[Condition]** — [Brief reasoning] (Confidence: H/M/L)
2. **[Condition]** — [Brief reasoning] (Confidence: H/M/L)
3. **[Condition]** — [Brief reasoning] (Confidence: H/M/L)

### Key Symptoms Identified
- [Symptom 1]
- [Symptom 2]

### Recommended Investigations
- [Test 1]
- [Test 2]

### Red Flags (if any)
- [Any urgent warning signs or None identified]

### Refinement Status
[If this is a refined diagnosis, explain what was corrected. If first run, write: Initial diagnosis.]

⚠️ AI-assisted analysis only. Must be confirmed by a licensed physician."""


def diagnosis_agent(state: AgentState) -> AgentState:
    patient = state["patient"]
    refinement_notes = state.get("refinement_notes", "")
    iteration = state.get("iteration_count", 0)

    refinement_section = ""
    if refinement_notes and iteration > 0:
        refinement_section = f"""

⚠️ REFINEMENT REQUEST (Iteration {iteration}):
The risk evaluation agent flagged these contradictions — address them:
{refinement_notes}
"""

    user_message = f"""
Patient Profile:
- Age: {patient.get('age')} | Gender: {patient.get('gender')}
- Weight: {patient.get('weight_kg')} kg | Height: {patient.get('height_cm')} cm
- Existing Conditions: {', '.join(patient.get('existing_conditions', [])) or 'None'}
- Current Medications: {', '.join(patient.get('current_medications', [])) or 'None'}

Symptoms:
{patient.get('symptoms_text', '')}
{('Selected: ' + ', '.join(patient.get('symptoms_selected', []))) if patient.get('symptoms_selected') else ''}

Vitals:
- Temperature: {patient.get('temperature_f', 'Not provided')} F
- Blood Pressure: {patient.get('blood_pressure', 'Not provided')}
- Heart Rate: {patient.get('heart_rate', 'Not provided')} bpm
- SpO2: {patient.get('spo2', 'Not provided')}%
{refinement_section}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        output = response.choices[0].message.content
    except Exception as e:
        output = f"Diagnosis Agent Error: {str(e)}"
        return {"diagnosis_output": output, "iteration_count": iteration, "errors": [str(e)]}

    return {"diagnosis_output": output, "iteration_count": iteration + 1}