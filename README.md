# 🎯 Placement Preparation Bot



*A React Prompting-powered mock interview engine across 4 modes × 8 companies.*


## What Is This?

PlacementBot is an **AI-powered placement preparation platform** built with Streamlit and Groq. It simulates the exact interview style of your target company — asking questions that mirror real hiring patterns, evaluating every answer with a strict 3-step feedback loop, and generating a full performance report at the end.

It makes the impact of **how you answer** visible and actionable, not just theoretical.

---

## Features

- 👤 **Student Profile** — personalizes every session to your branch, CGPA, skills, and year
- 🏢 **8 Companies** — TCS, Infosys, Wipro, Capgemini, Accenture, Amazon, Google, Microsoft
- 🎮 **4 Prep Modes** — DSA, HR, Company Simulation, Resume Review
- 🎯 **Company-Specific Openers** — Capgemini pseudocode test, Amazon Leadership Principles, TCS NQT pattern, and more
- 🔄 **React Prompting Engine** — every AI response follows REACT → ANALYZE → PROMPT
- 📊 **Full Performance Report** — topic scores, strengths, weak areas, 3-day study plan, readiness score out of 10
- ⬇️ **Downloadable Report** — export your session as a `.txt` file

---

## Installation

### Prerequisites

- Python 3.8+
- A free API key from [console.groq.com](https://console.groq.com)


Open `http://localhost:8501` in your browser, then:

1. **Fill your profile** — name, branch, CGPA, skills, year
2. **Pick a mode** — DSA, HR, Company, or Resume
3. **Select your target company** — see its rounds, focus areas, and tips in the sidebar
4. **Hit Start** — the bot opens with a company-matched Round 1 question
5. **Answer questions** — get instant REACT → ANALYZE → PROMPT feedback after each one
6. **End or auto-complete** — your full performance report generates automatically

---

## How It Works

The bot runs a **personalized interview simulation** on every session:

| | Prompting Mode | Company Mode |
|---|---|---|
| **What changes** | The evaluation lens (DSA / HR / Resume) | The question bank and round style |
| **What stays fixed** | The React Prompting 3-step loop | The feedback structure |
| **Purpose** | Measure depth in a specific skill area | Mirror the exact company hiring pattern |

### The 4 Prep Modes

| Mode | Questions | What It Evaluates |
|---|---|---|
| 🧠 **DSA** | 12 | Algorithmic thinking, time/space complexity, problem-solving approach |
| 🎤 **HR** | 8 | STAR format, clarity, confidence, cultural fit |
| 🏢 **Company** | 10 | Exact round simulation for your target company |
| 📄 **Resume** | 7 | Impact metrics, action verbs, recruiter appeal |

### The React Prompting Loop

Every AI response — regardless of mode or company — follows this strict 3-step structure:

| Step | What Happens |
|---|---|
| ⚡ **REACT** | Honest one-line evaluation of your answer |
| 🔍 **ANALYZE** | Identifies the exact gap vs. what the company expects |
| 🎯 **PROMPT** | Asks one sharp follow-up question — never gives away the answer |

### Company Intelligence

Each company has a dedicated question bank with seeds across DSA, HR, Coding, and Aptitude — injected into the system prompt so every session feels distinct:

| Company | Difficulty | Special Pattern |
|---|---|---|
| TCS | Easy–Medium | NQT output prediction, basic coding |
| Infosys | Medium | Recursion, trees, logical puzzles |
| Wipro | Easy–Medium | Array/string ops, quantitative aptitude |
| Capgemini | Medium | Pseudocode test → game aptitude → spoken English → Technical |
| Accenture | Easy | Communication, basic DSA, attention to detail |
| Amazon | Hard | LeetCode Medium/Hard paired with a Leadership Principle every round |
| Google | Very Hard | Advanced DP, graphs, system design, scale |
| Microsoft | Hard | OOP, design patterns, binary trees, DP on strings |

### Performance Report (out of 10)

At session end, a full report is generated across 4 dimensions:

| Signal | Score | What It Measures |
|---|---|---|
| **Communication** | /10 | Clarity, structure, and articulation of answers |
| **Confidence** | /10 | Decisiveness and depth without excessive hedging |
| **Relevance** | /10 | How well answers matched what the company actually looks for |
| **Company Readiness** | /10 | Overall fit for the target company's hiring bar |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io) |
| LLM Inference | [Groq API](https://console.groq.com) (Free Tier) |
| Language Model | Llama 3.1 8B Instant |
| Env Management | `python-dotenv` |
| Language | Python 3.8+ |

---

## Requirements
```
streamlit
groq
python-dotenv
```

---

## Limitations

- **Question banks are seeds** — company questions are injected as topic seeds; the LLM expands them using its training knowledge, not live data
- **No vector search** — context retrieval is prompt-based, not embedding-based
- **English only** — all prompts and evaluation are optimized for English responses
- **Report is a proxy** — the readiness score measures linguistic and structural signals, not ground-truth correctness

---

> Built for students, by someone who knows the grind. Good luck with your placements! 🚀
