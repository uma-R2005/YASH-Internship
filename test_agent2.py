"""
Test Agent 2 (Screener) with a mock resume — no PDF needed.
Run: python tests/test_agent2.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.agent2_screener import score_resume

SAMPLE_RESUME = """
John Doe
Email: john.doe@email.com | Phone: +91-9876543210

SKILLS
- Python, FastAPI, REST APIs, SQL, PostgreSQL
- Docker, Git, AWS (EC2, S3)
- 3 years of experience in backend development

EXPERIENCE
Software Developer — TechCorp (2021–2024)
- Built REST APIs using FastAPI serving 50k+ requests/day
- Managed PostgreSQL databases and wrote complex queries
- Deployed services using Docker on AWS EC2

EDUCATION
B.Tech in Computer Science — JNTU Hyderabad (2021)
"""


def test_screening():
    print("Testing Agent 2 - Screener with sample resume...\n")
    result = score_resume(SAMPLE_RESUME, "python_developer")

    print(f"Score:     {result['score']}/100")
    print(f"Strengths: {result['strengths']}")
    print(f"Gaps:      {result['gaps']}")
    print(f"Summary:   {result['summary']}")

    assert isinstance(result["score"], int), "Score must be an integer"
    assert 0 <= result["score"] <= 100,      "Score must be between 0 and 100"
    assert isinstance(result["strengths"], list)
    assert isinstance(result["gaps"], list)

    print("\n✅ All assertions passed!")


if __name__ == "__main__":
    test_screening()
