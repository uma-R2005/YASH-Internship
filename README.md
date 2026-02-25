PDF Q&A Analyzer

AI-powered document intelligence — Upload any PDF and receive 8 distinct answers generated using 4 prompting techniques and 4 chunking strategies, with automated quality ranking.



PDF Q&A Analyzer

AI-powered document intelligence — Upload any PDF and receive 8 distinct answers generated using 4 prompting techniques and 4 chunking strategies, with automated quality ranking.




┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                       │
│              (Gradio — claude.ai dark theme)             │
└───────────────────────┬─────────────────────────────────┘
                        │ PDF + Question
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   TEXT EXTRACTION                        │
│              PyMuPDF (fitz) — full text                  │
└──────────┬────────────────────────────┬─────────────────┘
           │                            │
    PROMPTING PATH               CHUNKING PATH
    (first 3,500 chars)          (full document)
           │                            │
           ▼                            ▼
  ┌─────────────────┐       ┌───────────────────────┐
  │ 4 Prompt Styles │       │  4 Chunking Strategies │
  │ · Zero-Shot     │       │  · Fixed Size          │
  │ · Chain-of-Thot │       │  · Sentence            │
  │ · Role-Based    │       │  · Paragraph           │
  │ · Few-Shot      │       │  · Semantic            │
  └────────┬────────┘       └──────────┬────────────┘
           │                           │
           │                    ┌──────▼──────┐
           │                    │ Chunk Scorer │
           │                    │(stop-word    │
           │                    │ filtered     │
           │                    │ keyword       │
           │                    │ overlap)     │
           │                    └──────┬──────┘
           │                           │ Best chunks (≤3000 chars)
           │                           │ + Zero-Shot prompt
           └──────────┬────────────────┘
                      │ 8 prompts total
                      ▼
         ┌─────────────────────────┐
         │   OpenRouter LLM API    │
         │  meta-llama/llama-3.1-  │
         │    8b-instruct:free     │
         └──────────┬──────────────┘
                    │ 8 answers (sequential, 1.5s delay)
                    ▼
         ┌─────────────────────────┐
         │   Quality Scorer        │
         │ · Relevance   (3 pts)   │
         │ · Grounding   (3 pts)   │
         │ · Specificity (2 pts)   │
         │ · Conciseness (2 pts)   │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │   Ranked Comparison     │
         │   Table (HTML)          │
         └─────────────────────────┘



         Techniques Overview
📏 Chunking Techniques
Fixed-size: Splits text into overlapping character windows to preserve continuity.

Sentence-based: Groups sentences into windows with overlap, ensuring balanced context.

Paragraph-based: Uses natural paragraph breaks, sub-chunking oversized sections.

Semantic-based: Detects topic shifts using meaningful word overlap to form coherent chunks.

🎯 Prompting Techniques
Zero-shot: Directly asks the model to answer using only the document.

Chain-of-thought: Guides the model through explicit reasoning steps before the final answer.

Role-based: Frames the model as a professional analyst to encourage evidence-based responses.

Few-shot: Provides example Q&A pairs to shape consistent and structured answers.
