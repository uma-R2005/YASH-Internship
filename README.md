# 🔍 SearchLab — E-commerce Search Engine

*A search relevance playground comparing 3 ranking algorithms × real Cohere embeddings × AI-powered explanations.*

## What Is This?

SearchLab is an **interactive search engine demo** built with Vanilla JS and a local backend. It lets you search a product catalog using three fundamentally different ranking strategies — and explains *why* each product ranked where it did, using a live LLM.

It makes the difference between **keyword, semantic, and hybrid search** visible and tangible, not just theoretical.

---

## Features

- 🟠 **Keyword Search (TF-IDF)** — exact token matching, rare terms score higher
- 🟢 **Semantic Search (Cosine)** — real 1024-dim Cohere embeddings, meaning-based matching
- 🟣 **Hybrid Search (RRF)** — Reciprocal Rank Fusion merges both rank lists, scale-free
- 📊 **Live Score Bars** — visualize TF-IDF, Cosine, and RRF scores on every product card
- 🏷️ **Matched Keyword Tags** — see exactly which tokens fired in keyword mode
- 🤖 **AI Ranking Explanations** — click any product card for a natural-language breakdown of its score, powered by **Groq llama-3.3-70b**
- 💡 **Suggested Queries** — quick-start chips that demonstrate where each mode wins or fails
- 📐 **Formula Legend** — live-highlighted algorithm cards that update with your active mode

---

## Installation

### Prerequisites

- A free API key from [cohere.com](https://cohere.com)
- A free API key from [console.groq.com](https://console.groq.com)
- Python 3.8+ (for the backend server)

Open `http://localhost:3000` in your browser, then:

1. **Type a query** — or click a suggestion chip to start
2. **Pick a mode** — Keyword, Semantic, or Hybrid
3. **Hit Search** — the Cohere API embeds your query in real time
4. **Read the results** — score bars, rank badges, and matched tokens appear on every card
5. **Click any card** — get an instant LLM explanation of why it ranked there
6. **Switch modes** — run the same query in all three modes to see how rankings change

---

## How It Works

SearchLab runs the **same query through three parallel ranking pipelines** and lets you compare the outputs directly:

| | Keyword Mode | Semantic Mode | Hybrid Mode |
|---|---|---|---|
| **Signal used** | Token frequency | Vector similarity | Both combined |
| **What it's good at** | Exact brand/product names | Conceptual queries | Balanced retrieval |
| **Blind spot** | Synonyms and paraphrases | Rare or specific terms | Tuning the fusion weight |
| **Score shown** | TF-IDF | Cosine (0–1) | RRF score |

### The 3 Ranking Algorithms

| Algorithm | Formula | What It Measures |
|---|---|---|
| 🟠 **TF-IDF** | `score = Σ (freq(w,doc)/len(doc)) × (log(N/df(w)) + 1)` | Token match quality; rare matching terms score higher |
| 🟢 **Cosine Similarity** | `sim(Q,D) = (Q·D) / (|Q| × |D|)` | Angular distance between 1024-dim Cohere embedding vectors |
| 🟣 **RRF** | `RRF(d) = Σ 1/(k + rank_i(d)),  k = 60` | Rank-level fusion — robust to score scale differences |

### The AI Explanation Flow

Every time you click a product card, the following happens:

| Step | What Happens |
|---|---|
| 📤 **Payload sent** | Product scores, rank, query, mode, and full result list |
| ⚡ **LLM called** | Groq llama-3.3-70b receives the full context |
| 🔍 **Explanation returned** | Natural-language reasoning for why this product ranked here |

### Query Behaviour by Mode

Each suggested query is chosen to highlight a specific algorithm's strength or weakness:

| Query | Best Mode | Why |
|---|---|---|
| `nike` | Keyword | Exact brand token — TF-IDF nails it |
| `comfortable jogging shoes` | Semantic | No exact match needed — embeddings understand intent |
| `wireless audio` | Hybrid | Category query — both signals contribute |
| `budget laptop` | Semantic | "Budget" is a concept, not a product keyword |
| `lightweight outdoor bag` | Hybrid | Multi-attribute query benefits from rank fusion |
| `skin care moisturizer` | Semantic | Synonym-heavy — cosine handles it cleanly |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JS |
| Fonts | Syne, DM Mono, DM Sans (Google Fonts) |
| Embeddings | [Cohere](https://cohere.com/) `embed-english-light-v3.0` (1024-dim) |
| LLM Explanations | [Groq](https://groq.com/) `llama-3.3-70b` |
| Backend | Python (local API at `localhost:8000`) |

---


> Built to make search relevance tangible — because the best way to understand an algorithm is to watch it win and lose. 🔍
