"""FastAPI main entry point for the novel creation web dashboard."""

import sys
from pathlib import Path

# Add project root to path so we can import existing scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "novel_creation_promax" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "scripts"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import CORS_ORIGINS
from routers import chapters, memory, novels, pipeline, ws

app = FastAPI(
    title="小说创作 Pro Max - Web Dashboard",
    description="可视化工作流面板 for 中文网文创作系统",
    version="1.0.0",
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(novels.router)
app.include_router(chapters.router)
app.include_router(pipeline.router)
app.include_router(memory.router)
app.include_router(ws.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "project_root": str(PROJECT_ROOT)}


# Serve frontend build in production
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
