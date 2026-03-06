# 🕵️ Crime & Case Analyzer

*An AI-powered detective tool matching clues against a case database using MultiQuery Retrieval × CrossEncoder Reranking × ChromaDB.*

## What Is This?

Crime & Case Analyzer is an **AI-powered case matching platform** built with Streamlit and LangChain. It takes a detective clue as natural language input — a suspect description, location detail, or behavioral pattern — and retrieves the most relevant cases from a database using a multi-stage retrieval pipeline.

It makes the difference between **basic vector search and intelligent reranking** visible and actionable, not just theoretical.

---

## Features

- 🔍 **Natural Language Clue Input** — describe a suspect, scene, or pattern in plain English
- 🔄 **Multi-Query Expansion** — Flan-T5 generates 3 query variants to maximize recall
- 🧠 **Semantic Vector Search** — ChromaDB retrieves semantically similar cases using MiniLM embeddings
- 🎯 **CrossEncoder Reranking** — ms-marco-MiniLM-L-6-v2 reranks results by true relevance, not just similarity
- 📁 **Top 3 Case Cards** — results displayed with case ID, crime type badge, and full case details
- 💡 **Example Queries** — sidebar chips for instant detective scenarios
- 📊 **Case Type Dashboard** — overview of 10 cases across Robbery, Fraud, Theft, Arson, and Drugs
- ⚡ **Cached Pipeline** — models load once and stay in memory for fast repeated queries

---

Open `http://localhost:8501` in your browser, then:

1. **Enter a clue** — describe a suspect, location, time, or item in plain English
2. **Hit Analyze** — the pipeline expands your query, searches the case DB, and reranks results
3. **Read the case cards** — top 3 matching cases are returned with match rank and crime type
4. **Try sidebar chips** — pre-loaded example clues to explore different case patterns
5. **Switch queries** — run variations to see how the reranker shifts rankings

---

## How It Works

The analyzer runs every clue through a **3-stage retrieval pipeline** before returning results:

| Stage | Component | What It Does |
|---|---|---|
| **1. Query Expansion** | Flan-T5 + MultiQueryRetriever | Generates 3 query variants from your clue |
| **2. Vector Search** | ChromaDB + MiniLM embeddings | Retrieves top 10 semantically similar cases |
| **3. Reranking** | CrossEncoder ms-marco-MiniLM | Reranks all 10 by true query-document relevance, returns top 3 |

### Why 3 Stages?

| | Basic Search | This Pipeline |
|---|---|---|
| **Handles typos / paraphrases** | ❌ | ✅ (query expansion) |
| **Captures semantic meaning** | ✅ | ✅ (vector embeddings) |
| **Scores true relevance** | ❌ | ✅ (cross-encoder reranking) |
| **Result quality** | Medium | High |

### The Retrieval Pipeline

| Step | Model | Purpose |
|---|---|---|
| 🔄 **Query Expansion** | `google/flan-t5-base` | Rewrites clue into 3 diverse variants for broader recall |
| 📦 **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` | Converts cases and query into 384-dim semantic vectors |
| 🗄️ **Vector Store** | `ChromaDB` | Fast approximate nearest-neighbour search over all cases |
| 🎯 **Reranking** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Scores each (query, case) pair jointly — far more accurate than cosine alone |

### Case Database

10 real-style crime cases across 5 categories, each with suspect description, location, evidence, and status:

| Case | Type | Key Detail |
|---|---|---|
| #001 | Robbery | Dark hoodie, red duffle bag, harbor district, 11:45pm |
| #002 | Heist | Two masked suspects, crowbars, jewelry store, 2:30am |
| #003 | Smuggling | Group of 4, unmarked crates, Pier 12, midnight |
| #004 | Burglary | Back window entry, white sedan, Elm Street daytime |
| #005 | Arson | Tall male, dark jacket, accelerant traces, 1:00am |
| #006 | Assault | Dark hoodie, waterfront attack, 11:00pm, bag |
| #007 | Fraud | Forged documents, fake ID, City Central Bank |
| #008 | Theft | Signal jammers, high-end cars, multiple lots, 10pm–2am |
| #009 | Theft | Airport badge misuse, large bag on CCTV, midnight |
| #010 | Drugs | Harbor road factory, hoodie lookout, midnight operations |

### Example Queries and What They Match

| Clue | Best Matches | Why |
|---|---|---|
| `suspect in dark hoodie near docks at midnight` | #001, #010, #003 | Hoodie + dock + midnight pattern across multiple cases |
| `assault near waterfront at night` | #006 | Direct location and time match |
| `illegal goods moved near harbor` | #003, #010 | Smuggling + drugs near harbor |
| `vehicle stolen at night with jammer` | #008 | Signal jammer + nighttime theft exact match |
| `fraud using forged documents at bank` | #007 | Exact fraud pattern match |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io) |
| Orchestration | [LangChain](https://www.langchain.com/) |
| Vector Store | [ChromaDB](https://www.trychroma.com/) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Query Expansion LLM | `google/flan-t5-base` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Inference | HuggingFace Transformers (local, free — no API key needed) |
| Language | Python 3.8+ |

---

## Requirements
```
streamlit
langchain
langchain-chroma
langchain-community
langchain-huggingface
sentence-transformers
transformers
chromadb
torch
```


> Built to show that smart retrieval isn't just about finding similar text — it's about understanding what actually matches. 🕵️
