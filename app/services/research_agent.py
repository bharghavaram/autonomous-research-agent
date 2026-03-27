"""
Autonomous Research Agent – Self-directed web browsing, ArXiv paper reading,
and research synthesis using LangChain ReAct + tool-use.
"""
import logging
import json
import uuid
import re
from datetime import datetime
from typing import Optional, List
import httpx
import arxiv
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are an autonomous AI research agent. Your goal is to:
1. Break down the research question into sub-queries
2. Search for relevant papers, articles, and web content
3. Synthesise findings into a comprehensive, well-cited research report
4. Identify knowledge gaps and suggest future research directions

Always think step-by-step (chain-of-thought) before taking actions.
Cite your sources and quantify claims wherever possible."""

SYNTHESIS_PROMPT = """You are a world-class research synthesiser.

RESEARCH QUESTION: {question}

PAPERS FOUND:
{papers}

WEB SOURCES:
{web_content}

PREVIOUS FINDINGS:
{previous_findings}

Create a comprehensive research report with:
# Executive Summary
# Key Findings (with citations)
# Methodology Overview
# Evidence Analysis
# Contradictions & Debates
# Knowledge Gaps
# Future Research Directions
# References

Be precise, cite specific papers/sources, and highlight breakthrough findings."""


class ResearchMemory:
    def __init__(self):
        self._sessions: dict = {}

    def create_session(self, session_id: str, question: str):
        self._sessions[session_id] = {
            "question": question,
            "papers": [],
            "web_sources": [],
            "intermediate_findings": [],
            "iterations": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

    def add_paper(self, session_id: str, paper: dict):
        if session_id in self._sessions:
            self._sessions[session_id]["papers"].append(paper)

    def add_web_source(self, session_id: str, source: dict):
        if session_id in self._sessions:
            self._sessions[session_id]["web_sources"].append(source)

    def add_finding(self, session_id: str, finding: str):
        if session_id in self._sessions:
            self._sessions[session_id]["intermediate_findings"].append(finding)
            self._sessions[session_id]["iterations"] += 1

    def get_session(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)


class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )
        self.memory = ResearchMemory()

    def _search_arxiv(self, query: str, max_results: int = None) -> List[dict]:
        max_results = max_results or settings.MAX_PAPERS
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            papers = []
            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors[:3]],
                    "abstract": result.summary[:500],
                    "url": result.entry_id,
                    "published": result.published.strftime("%Y-%m-%d"),
                    "categories": result.categories,
                })
            logger.info("Found %d ArXiv papers for: %s", len(papers), query)
            return papers
        except Exception as exc:
            logger.error("ArXiv search failed: %s", exc)
            return []

    def _search_web(self, query: str) -> List[dict]:
        results = []
        try:
            if settings.SERPAPI_KEY:
                resp = httpx.get(
                    "https://serpapi.com/search",
                    params={"q": query, "api_key": settings.SERPAPI_KEY, "num": settings.MAX_SEARCH_RESULTS},
                    timeout=10,
                )
                data = resp.json()
                for item in data.get("organic_results", [])[:settings.MAX_SEARCH_RESULTS]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    })
            else:
                # Fallback: DDG lite scrape
                resp = httpx.get(
                    "https://duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "ResearchAgent/1.0"},
                    timeout=10,
                )
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.select(".result__a")[:settings.MAX_SEARCH_RESULTS]:
                    results.append({
                        "title": a.get_text(strip=True),
                        "url": a.get("href", ""),
                        "snippet": "",
                    })
        except Exception as exc:
            logger.warning("Web search failed: %s", exc)
        return results

    def _decompose_query(self, question: str) -> List[str]:
        response = self.llm.invoke([
            SystemMessage(content="You are a research strategist. Break the question into 3-5 specific search sub-queries for ArXiv and web. Return only a JSON list of strings."),
            HumanMessage(content=f"Research question: {question}"),
        ])
        try:
            queries = json.loads(response.content)
            return queries if isinstance(queries, list) else [question]
        except Exception:
            return [question]

    def _extract_key_findings(self, papers: List[dict], web_sources: List[dict]) -> str:
        papers_text = "\n".join([f"- [{p['published']}] {p['title']} ({', '.join(p['authors'])}): {p['abstract']}" for p in papers[:8]])
        web_text = "\n".join([f"- {s['title']}: {s['snippet']}" for s in web_sources[:5]])
        response = self.llm.invoke([
            SystemMessage(content="Extract the 5 most important findings from these research sources. Be specific and cite titles."),
            HumanMessage(content=f"Papers:\n{papers_text}\n\nWeb Sources:\n{web_text}"),
        ])
        return response.content

    def conduct_research(self, question: str) -> dict:
        session_id = str(uuid.uuid4())
        self.memory.create_session(session_id, question)
        logger.info("Research session %s: %s", session_id, question)

        # Step 1: Decompose query
        sub_queries = self._decompose_query(question)
        logger.info("Sub-queries: %s", sub_queries)

        # Step 2: Gather papers and web sources
        all_papers = []
        all_web = []
        for query in sub_queries[:3]:
            papers = self._search_arxiv(query, max_results=settings.MAX_PAPERS // len(sub_queries))
            web = self._search_web(query)
            all_papers.extend(papers)
            all_web.extend(web)
            for p in papers:
                self.memory.add_paper(session_id, p)
            for w in web:
                self.memory.add_web_source(session_id, w)

        # Deduplicate
        seen_titles = set()
        unique_papers = []
        for p in all_papers:
            if p["title"] not in seen_titles:
                seen_titles.add(p["title"])
                unique_papers.append(p)

        # Step 3: Extract intermediate findings
        findings = self._extract_key_findings(unique_papers, all_web)
        self.memory.add_finding(session_id, findings)

        # Step 4: Synthesise comprehensive report
        papers_formatted = "\n".join([
            f"[{i+1}] {p['title']} – {', '.join(p['authors'])} ({p['published']})\n    {p['abstract']}"
            for i, p in enumerate(unique_papers[:10])
        ])
        web_formatted = "\n".join([f"- {s['title']}: {s['snippet']}" for s in all_web[:5]])

        report_response = self.llm.invoke([HumanMessage(
            content=SYNTHESIS_PROMPT.format(
                question=question,
                papers=papers_formatted or "No papers found.",
                web_content=web_formatted or "No web content.",
                previous_findings=findings,
            )
        )])

        session = self.memory.get_session(session_id)
        return {
            "session_id": session_id,
            "question": question,
            "report": report_response.content,
            "stats": {
                "sub_queries": sub_queries,
                "papers_found": len(unique_papers),
                "web_sources": len(all_web),
                "iterations": session["iterations"],
            },
            "sources": {
                "papers": unique_papers[:10],
                "web": all_web[:5],
            },
        }

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.memory.get_session(session_id)


_agent: Optional[ResearchAgent] = None
def get_research_agent() -> ResearchAgent:
    global _agent
    if _agent is None:
        _agent = ResearchAgent()
    return _agent
