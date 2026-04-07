"""
main.py — Pipeline Orchestrator
────────────────────────────────────────────
Wires all 4 agents together into a pipeline.

How to run:
  1. Drop resume PDFs into:  data/resumes/incoming/
  2. Run:  python main.py

Flow:
  Agent 1 → scans incoming folder
      ↓
  Agent 2 → scores each resume with Groq LLM
      ↓
  ┌── shortlist ──────────────────────┐
  │  Agent 3 → books interview slot  │
  │  Agent 4 → sends invite email    │
  └───────────────────────────────────┘
  ┌── reject ─────────────────────────┐
  │  Agent 4 → sends rejection email │
  └───────────────────────────────────┘
"""

import agents.agent1_intake       as agent1
import agents.agent2_screener     as agent2
import agents.agent3_scheduler    as agent3
import agents.agent4_communicator as agent4


def run_pipeline():
    print("\n" + "="*55)
    print("  🤖 HR RECRUITMENT PIPELINE STARTED")
    print("="*55)

    # ── Agent 1: Scan folder for resumes ─────────────────
    applications = agent1.run()

    if not applications:
        print("\n💡 Tip: Add resume PDFs to data/resumes/incoming/")
        print("   Example: john_doe_python_developer_john@gmail.com.pdf\n")
        return

    results = {"shortlist": 0, "reject": 0}

    for application in applications:

        print(f"\n{'─'*55}")
        print(f"  Processing: {application['name']} → {application['job_role']}")
        print(f"{'─'*55}")

        # ── Agent 2: Score the resume ─────────────────────
        application = agent2.run(application)

        # ── Agent 3: Book slot (shortlisted only) ─────────
        if application.get("recommendation") == "shortlist":
            application = agent3.run(application)

        # ── Agent 4: Send email + log outcome ─────────────
        application = agent4.run(application)

        # ── Move resume to processed folder ───────────────
        agent1.mark_processed(application["resume_path"])

        # ── Summary for this candidate ────────────────────
        recommendation = application.get("recommendation", "reject")
        results[recommendation] += 1

        print(f"\n  ✔ DONE | {application['name']}")
        print(f"    Score:    {application.get('score', 'N/A')}/100")
        print(f"    Decision: {recommendation.upper()}")
        if recommendation == "shortlist":
            print(f"    Interview: {application.get('interview_slot', 'N/A')}")
        print(f"    Email sent: {'Yes' if application.get('email_sent') else 'No'}")

    # ── Final Summary ─────────────────────────────────────
    total = results["shortlist"] + results["reject"]
    print(f"\n{'='*55}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Total processed : {total}")
    print(f"  Shortlisted     : {results['shortlist']}")
    print(f"  Rejected        : {results['reject']}")
    print(f"  Logs saved in   : data/logs/")
    print(f"  Schedule saved  : data/schedules/interviews.csv")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    run_pipeline()