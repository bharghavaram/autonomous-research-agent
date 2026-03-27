> **📅 Project Period:** Sep 2025 – Oct 2025 &nbsp;|&nbsp; **Status:** Completed &nbsp;|&nbsp; **Author:** [Bharghava Ram Vemuri](https://github.com/bharghavaram)

# Autonomous Research Agent

> Self-directed AI research agent that browses the web, reads ArXiv papers, and generates comprehensive research reports

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)](https://openai.com)

## Overview

An autonomous AI agent that **independently conducts research** on any topic. Given a research question, it decomposes the problem, searches ArXiv for academic papers, retrieves web sources, synthesises findings with chain-of-thought reasoning, and produces a structured research report — all without human intervention.

## Research Workflow

```
Research Question
        ↓
Query Decomposition (GPT-4o → 3-5 sub-queries)
        ↓
  ┌─────────────────────────┐
  │  ArXiv Search           │ → 10 papers per sub-query
  │  Web Search (SerpAPI/DDG)│ → 5 results per sub-query
  └─────────────────────────┘
        ↓
Intermediate Finding Extraction
        ↓
Synthesis Report Generation (GPT-4o)
        ↓
Structured Research Report
```

## Key Features

- **Autonomous query decomposition** – breaks complex questions into targeted sub-queries
- **ArXiv integration** – searches and parses academic papers with full metadata
- **Web search** – SerpAPI (primary) with DuckDuckGo fallback
- **Session memory** – stores intermediate findings across research iterations
- **Chain-of-thought reasoning** – multi-step evidence synthesis
- **Structured output** – Executive Summary, Key Findings, Evidence Analysis, Knowledge Gaps, References

## Quick Start

```bash
git clone https://github.com/bharghavaram/autonomous-research-agent
cd autonomous-research-agent
pip install -r requirements.txt
cp .env.example .env    # Add OPENAI_API_KEY
uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/research/conduct` | Start autonomous research |
| GET | `/api/v1/research/session/{id}` | Get session findings |
| GET | `/api/v1/research/health` | Health check |

### Example: Conduct Research

```bash
curl -X POST "http://localhost:8000/api/v1/research/conduct" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the latest advances in mixture-of-experts LLM architectures?"}'
```

### Example Response

```json
{
  "session_id": "uuid",
  "question": "...",
  "report": "# Executive Summary\n...\n# Key Findings\n...",
  "stats": {
    "sub_queries": ["sub-q1", "sub-q2", "sub-q3"],
    "papers_found": 18,
    "web_sources": 10,
    "iterations": 2
  },
  "sources": {
    "papers": [...],
    "web": [...]
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required for reasoning and synthesis |
| `SERPAPI_KEY` | Web search (optional – falls back to DuckDuckGo) |
| `MAX_PAPERS` | Max ArXiv papers per session (default: 10) |
