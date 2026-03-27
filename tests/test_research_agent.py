"""Tests for Autonomous Research Agent."""
import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.services.research_agent import ResearchMemory


def test_settings():
    assert settings.MAX_PAPERS == 10
    assert settings.MAX_SEARCH_RESULTS == 5
    assert settings.MAX_ITERATIONS == 8


def test_research_memory_create():
    mem = ResearchMemory()
    mem.create_session("s1", "What is GraphRAG?")
    session = mem.get_session("s1")
    assert session is not None
    assert session["question"] == "What is GraphRAG?"
    assert session["papers"] == []


def test_research_memory_add_paper():
    mem = ResearchMemory()
    mem.create_session("s1", "LLMs")
    mem.add_paper("s1", {"title": "Test Paper", "authors": ["A"], "abstract": "..."})
    session = mem.get_session("s1")
    assert len(session["papers"]) == 1
    assert session["papers"][0]["title"] == "Test Paper"


def test_research_memory_add_finding():
    mem = ResearchMemory()
    mem.create_session("s1", "Q")
    mem.add_finding("s1", "Finding 1")
    session = mem.get_session("s1")
    assert session["iterations"] == 1
    assert "Finding 1" in session["intermediate_findings"]


def test_research_memory_nonexistent():
    mem = ResearchMemory()
    assert mem.get_session("nonexistent") is None


@patch("app.services.research_agent.ChatOpenAI")
def test_decompose_query(mock_llm):
    import json
    mock_response = MagicMock()
    mock_response.content = json.dumps(["sub-query 1", "sub-query 2", "sub-query 3"])
    mock_llm.return_value.invoke.return_value = mock_response
    from app.services.research_agent import ResearchAgent
    agent = ResearchAgent()
    queries = agent._decompose_query("What are the latest advances in RAG?")
    assert isinstance(queries, list)
    assert len(queries) == 3


@pytest.mark.asyncio
async def test_api_health():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/api/v1/research/health")
    assert resp.status_code == 200
