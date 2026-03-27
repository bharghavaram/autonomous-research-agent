"""Autonomous Research Agent – FastAPI Application Entry Point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.research import router as research_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s – %(message)s")

app = FastAPI(
    title="Autonomous Research Agent",
    description="Self-directed AI research agent that autonomously browses the web, reads ArXiv papers, synthesises multi-source findings, and generates comprehensive research reports using chain-of-thought reasoning.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "Autonomous Research Agent",
        "version": "1.0.0",
        "description": "Self-directed Web + ArXiv Research Synthesis",
        "docs": "/docs",
        "capabilities": [
            "Query decomposition into sub-research tracks",
            "ArXiv paper search & abstract extraction",
            "Web content retrieval & parsing",
            "Chain-of-thought multi-hop reasoning",
            "Structured research report generation",
            "Session memory for multi-turn research",
        ],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
