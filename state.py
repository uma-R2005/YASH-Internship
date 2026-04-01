from typing import TypedDict, Optional, Annotated
import operator


class PatientInput(TypedDict):
    age: int
    gender: str
    weight_kg: float
    height_cm: float
    existing_conditions: list[str]
    current_medications: list[str]
    symptoms_text: str
    symptoms_selected: list[str]
    temperature_f: Optional[float]
    blood_pressure: Optional[str]
    heart_rate: Optional[int]
    spo2: Optional[float]
    lab_reports: list[dict]
    past_illnesses: str
    surgeries: str
    allergies: list[str]
    smoking: Optional[str]
    alcohol: Optional[str]
    activity_level: Optional[str]


class AgentState(TypedDict):
    patient: PatientInput

    # ── Agent outputs ──────────────────────────────────────────────────────
    diagnosis_output: Optional[str]
    lab_analysis_output: Optional[str]
    risk_evaluation_output: Optional[str]
    treatment_output: Optional[str]
    final_report: Optional[str]

    # ── Guardrail fields ───────────────────────────────────────────────────
    # input_errors  : fatal violations — pipeline skips agents if non-empty
    # output_warnings: non-fatal flags — returned to client for display
    input_errors: Annotated[list[str], operator.add]
    output_warnings: Annotated[list[str], operator.add]

    # ── Legacy error accumulator ───────────────────────────────────────────
    errors: Annotated[list[str], operator.add]