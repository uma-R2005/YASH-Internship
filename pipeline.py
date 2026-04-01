from langgraph.graph import StateGraph, START, END
from agents.state import AgentState
from agents.diagnosis_agent import diagnosis_agent
from agents.lab_analysis_agent import lab_analysis_agent
from agents.risk_evaluation_agent import risk_evaluation_agent
from agents.treatment_agent import treatment_agent
from agents.input_guardrail import input_guardrail
from agents.output_guardrail import output_guardrail


# ── Conditional routing after input guardrail ────────────────────────────────

def route_after_input_check(state: AgentState) -> str:
    """
    If the input guardrail found violations, skip straight to END
    (output_guardrail also won't run — nothing to sanitise).
    Otherwise proceed to the agent pipeline.
    """
    if state.get("input_errors"):
        return "blocked"
    return "proceed"


# ── Graph builder ────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────────────────────────────────
    graph.add_node("input_guardrail",    input_guardrail)
    graph.add_node("diagnosis_agent",    diagnosis_agent)
    graph.add_node("lab_analysis_agent", lab_analysis_agent)
    graph.add_node("risk_evaluation_agent", risk_evaluation_agent)
    graph.add_node("treatment_agent",    treatment_agent)
    graph.add_node("output_guardrail",   output_guardrail)

    # ── Entry: always run input guardrail first ────────────────────────────
    graph.add_edge(START, "input_guardrail")

    # ── Conditional branch after input check ──────────────────────────────
    graph.add_conditional_edges(
        "input_guardrail",
        route_after_input_check,
        {
            "proceed": "diagnosis_agent",   # valid input → run agents
            "blocked": END,                 # invalid input → return immediately
        },
    )

    # ── Agent pipeline (sequential to avoid state conflicts) ───────────────
    graph.add_edge("diagnosis_agent",    "lab_analysis_agent")
    graph.add_edge("lab_analysis_agent", "risk_evaluation_agent")
    graph.add_edge("risk_evaluation_agent", "treatment_agent")

    # ── Output guardrail runs after all agents ─────────────────────────────
    graph.add_edge("treatment_agent",    "output_guardrail")
    graph.add_edge("output_guardrail",   END)

    return graph.compile()


healthcare_graph = build_graph()


# ── Public runner ────────────────────────────────────────────────────────────

async def run_pipeline(patient_data: dict) -> dict:
    initial_state: AgentState = {
        "patient":                patient_data,
        "diagnosis_output":       None,
        "lab_analysis_output":    None,
        "risk_evaluation_output": None,
        "treatment_output":       None,
        "final_report":           None,
        "input_errors":           [],
        "output_warnings":        [],
        "errors":                 [],
    }

    result = await healthcare_graph.ainvoke(initial_state)

    input_errors   = result.get("input_errors",   [])
    output_warnings = result.get("output_warnings", [])

    # If input was blocked, return structured error immediately
    if input_errors:
        return {
            "blocked":         True,
            "input_errors":    input_errors,
            "diagnosis":       None,
            "lab_analysis":    None,
            "risk_evaluation": None,
            "treatment":       None,
            "errors":          [],
            "output_warnings": [],
        }

    return {
        "blocked":         False,
        "input_errors":    [],
        "output_warnings": output_warnings,
        "diagnosis":       result.get("diagnosis_output",       ""),
        "lab_analysis":    result.get("lab_analysis_output",    ""),
        "risk_evaluation": result.get("risk_evaluation_output", ""),
        "treatment":       result.get("treatment_output",       ""),
        "errors":          result.get("errors",                 []),
    }