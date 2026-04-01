import os
from groq import Groq
from agents.state import AgentState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert medical treatment planning AI assistant.
Synthesise all agent outputs to produce a comprehensive personalised treatment plan.

Output your response in this EXACT format:

## 💊 Treatment Plan

### First-Line Treatment
| Intervention | Details | Duration | Notes |
|-------------|---------|----------|-------|
| [med/therapy] | [dosage] | [duration] | [notes] |

### Supportive Care
- [Measure 1]
- [Measure 2]

### Alternative Options
1. **Option A**: [Description] — *Use if: [condition]*
2. **Option B**: [Description] — *Use if: [condition]*

### Lifestyle Modifications
- [Modification 1]
- [Modification 2]

### Follow-Up Plan
| Timeframe | Action |
|-----------|--------|
| 24-48 hrs | [action] |
| 1 week | [action] |
| 1 month | [action] |

### Emergency Warning Signs
- [Sign 1]
- [Sign 2]

⚠️ Must be reviewed by a licensed physician before implementation."""


def treatment_agent(state: AgentState) -> AgentState:
    patient = state["patient"]
    diagnosis = state.get("diagnosis_output", "")
    lab = state.get("lab_analysis_output", "")
    risk = state.get("risk_evaluation_output", "")

    user_message = f"""
PATIENT SUMMARY:
- Age: {patient.get('age')} | Gender: {patient.get('gender')}
- Weight: {patient.get('weight_kg')} kg | Height: {patient.get('height_cm')} cm
- Allergies: {', '.join(patient.get('allergies', [])) or 'None'}
- Current Medications: {', '.join(patient.get('current_medications', [])) or 'None'}

DIAGNOSIS OUTPUT:
{diagnosis}

LAB ANALYSIS OUTPUT:
{lab}

RISK EVALUATION OUTPUT:
{risk}

Please create a personalised risk-adjusted treatment plan.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        output = response.choices[0].message.content
    except Exception as e:
        output = f"Treatment Agent Error: {str(e)}"
        return {"treatment_output": output, "errors": [str(e)]}

    return {"treatment_output": output}