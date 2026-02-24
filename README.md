# 🤖 Domo RFP Intelligence Bot

A Streamlit-based Document Intelligence App that processes RFP PDFs, builds a FAISS vector database, and enables interactive Q&A powered by Mistral-7B with external Wikipedia knowledge validation.  
It supports multi-language responses, accuracy scoring (ROUGE), and dynamic section filtering.

---

## 📂 Project Structure

- apy.py → Streamlit front‑end
  - Custom UI with gradients, chat bubbles, stat cards
  - Tabs for Chat, Summary, Key Info, Deadlines, Analytics
  - Upload PDFs → process → query with RAG
  - ROUGE scoring for accuracy checks
  - Multi-language support (English, French, Spanish, German, Hindi, Arabic)
  - Export chat history (TXT/CSV)

- bot.py → Bot loader
  - Loads FAISS index from storage/
  - Connects HuggingFace Mistral-7B-Instruct-v0.2
  - Custom HuggingFace embedding wrapper (HFEmbedding)
  - Returns a query engine (no chat engine, no reranker, no memory)

- ingest.py → Ingestion pipeline
  - Reads PDFs with SimpleDirectoryReader
  - Splits into chunks using SentenceSplitter
  - Embeds text with HuggingFace (all-MiniLM-L6-v2)
  - Persists FAISS index to storage/
  - Includes retry logic for embedding API calls

---

## 🚀 Features

- PDF Ingestion & Vectorization  
  Chunking with overlap for context preservation  
  FAISS vector store persistence  
  HuggingFace embeddings with retry logic  

- Interactive Chat  
  PDF-based RAG answers (Mistral-7B)  
  External Wikipedia KB validation  
  ROUGE accuracy scoring (Mistral vs. Web sources)  

- Dynamic Section Filtering  
  Restrict queries to specific RFP sections (e.g., Section 5, Section 6)  

- Key Info Extraction  
  Deadlines, contacts, FTE requirements, pricing model, project duration  

- Multi-language Support  
  Responses in English, French, Spanish, German, Hindi, Arabic  

- Analytics & Export  
  Track queries, response times, and section usage  
  Export chat history as TXT or CSV  

