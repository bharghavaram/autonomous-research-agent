"""Autonomous Research Agent – API routes."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.research_agent import ResearchAgent, get_research_agent

router = APIRouter(prefix="/research", tags=["Autonomous Research"])

class ResearchRequest(BaseModel):
    question: str
    max_papers: Optional[int] = None

_sessions: dict = {}

@router.post("/conduct")
async def conduct_research(req: ResearchRequest, svc: ResearchAgent = Depends(get_research_agent)):
    if len(req.question.strip()) < 10:
        raise HTTPException(400, "Research question too short (min 10 chars)")
    return svc.conduct_research(req.question)

@router.get("/session/{session_id}")
async def get_session(session_id: str, svc: ResearchAgent = Depends(get_research_agent)):
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found")
    return session

@router.get("/health")
async def health():
    return {"status": "ok", "service": "Autonomous Research Agent – Self-directed Web + ArXiv Research"}
