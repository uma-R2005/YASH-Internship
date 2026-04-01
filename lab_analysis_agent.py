import os
from groq import Groq
from agents.state import AgentState

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert medical lab analyst AI assistant.
Recommend and interpret lab tests based on the patient's clinical presentation.

Output your response in this EXACT format:

## 🧪 Lab Analysis

### Recommended Tests
| Test | Reason | Priority |
|------|--------|----------|
| [test] | [why needed] | Urgent / Routine |

### Expected Findings
| Parameter | Expected | Clinical Significance |
|-----------|----------|-----------------------|
| [param] | [range] | [significance] |

### Clinical Interpretation
[2-3 sentences about what labs would likely show]

### Critical Values to Watch
- [Value 1]
- [Value 2]

⚠️ No actual lab reports uploaded. Recommendations based on clinical presentation only."""


def lab_analysis_agent(state: AgentState) -> AgentState:
    patient = state["patient"]

    user_message = f"""
Patient:
- Age: {patient.get('age')} | Gender: {patient.get('gender')}
- Conditions: {', '.join(patient.get('existing_conditions', [])) or 'None'}
- Symptoms: {patient.get('symptoms_text', 'Not provided')}
- Vitals: BP {patient.get('blood_pressure', 'N/A')} | HR {patient.get('heart_rate', 'N/A')} | SpO2 {patient.get('spo2', 'N/A')}%
- Medications: {', '.join(patient.get('current_medications', [])) or 'None'}

Please recommend and interpret relevant lab investigations.
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
        output = f"Lab Analysis Agent Error: {str(e)}"
        return {"lab_analysis_output": output, "errors": [str(e)]}

    return {"lab_analysis_output": output}