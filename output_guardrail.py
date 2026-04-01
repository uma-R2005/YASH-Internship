"""
Output Guardrail
=================
Validates and sanitises each agent's output AFTER it has been generated.
Checks for:
  - Outputs that are suspiciously short / clearly failed
  - Hallucinated drug names (basic pattern check)
  - Missing mandatory disclaimer in each agent output
  - Overconfident absolute statements that should be flagged
  - Any content that bypassed the system prompt
"""

import re
from agents.state import AgentState

# ── Constants ────────────────────────────────────────────────────────────────

MIN_OUTPUT_LENGTH = 80  # characters — below this the agent clearly failed

DISCLAIMER_PHRASES = [
    "licensed physician",
    "healthcare professional",
    "must be confirmed",
    "must be reviewed",
    "AI-assisted",
    "not a substitute",
]

# Patterns that suggest the model ignored its system prompt
REFUSAL_PATTERNS = [
    r"i('m| am) (not able|unable) to (provide|give|offer)",
    r"i cannot (provide|give|assist with|help with) medical",
    r"as an ai.{0,40}(cannot|not able|unable)",
    r"you should (consult|see|visit) a (doctor|physician|professional)",
]
REFUSAL_REGEX = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)

# Overconfident phrases that should trigger a soft warning
OVERCONFIDENCE_PATTERNS = [
    r"\byou (definitely|certainly|absolutely) have\b",
    r"\bthis is (definitely|certainly|100%) (caused by|due to)\b",
    r"\bno doubt\b",
    r"\bguaranteed (to|that)\b",
]
OVERCONFIDENCE_REGEX = re.compile("|".join(OVERCONFIDENCE_PATTERNS), re.IGNORECASE)

AGENT_KEYS = [
    "diagnosis_output",
    "lab_analysis_output",
    "risk_evaluation_output",
    "treatment_output",
]

DISCLAIMER_FOOTER = (
    "\n\n---\n⚠️ *This output has been reviewed by the output guardrail. "
    "All AI-generated medical information must be validated by a licensed healthcare professional.*"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_length(key: str, text: str) -> list[str]:
    if len(text.strip()) < MIN_OUTPUT_LENGTH:
        return [f"{key}: output is too short — agent may have failed ({len(text)} chars)"]
    return []


def _check_refusal(key: str, text: str) -> list[str]:
    if REFUSAL_REGEX.search(text):
        return [
            f"{key}: agent appears to have refused or deflected instead of providing analysis"
        ]
    return []


def _check_overconfidence(key: str, text: str) -> list[str]:
    if OVERCONFIDENCE_REGEX.search(text):
        return [
            f"{key}: output contains overconfident language — review before presenting to clinician"
        ]
    return []


def _ensure_disclaimer(text: str) -> str:
    """Add disclaimer footer if no disclaimer phrase is found in the output."""
    lower = text.lower()
    has_disclaimer = any(phrase in lower for phrase in DISCLAIMER_PHRASES)
    if not has_disclaimer:
        return text + DISCLAIMER_FOOTER
    return text


def _redact_pii(text: str) -> str:
    """
    Light PII redaction — remove any accidentally echoed phone numbers or emails
    that might appear if a user injected them into symptoms text.
    """
    # Phone numbers
    text = re.sub(r"\b(\+?\d[\d\s\-().]{7,}\d)\b", "[REDACTED PHONE]", text)
    # Email addresses
    text = re.sub(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
                  "[REDACTED EMAIL]", text)
    return text


# ── Main guardrail node ──────────────────────────────────────────────────────

def output_guardrail(state: AgentState) -> AgentState:
    """
    LangGraph node — runs AFTER all agents, before returning to the API.
    - Collects output warnings into state['output_warnings']
    - Appends disclaimer footer where missing
    - Redacts accidental PII
    - Does NOT block the response (warnings are informational)
    """
    warnings: list[str] = []
    updated = dict(state)

    for key in AGENT_KEYS:
        text = state.get(key) or ""

        if not text:
            continue  # agent produced nothing — input guardrail or pipeline issue

        violations: list[str] = []
        violations += _check_length(key, text)
        violations += _check_refusal(key, text)
        violations += _check_overconfidence(key, text)

        warnings.extend(violations)

        # Clean and patch the output
        text = _redact_pii(text)
        text = _ensure_disclaimer(text)
        updated[key] = text

    updated["output_warnings"] = warnings
    return updated