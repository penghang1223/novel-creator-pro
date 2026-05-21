"""Memory system API routes."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from config import MEMORY_SCRIPT, PROJECT_ROOT
from utils.paths import get_memory_dir

router = APIRouter(prefix="/api/novels/{platform}/{name:path}/memory", tags=["memory"])


@router.get("/stats")
def get_memory_stats(platform: str, name: str):
    """Get memory system statistics."""
    mem_dir = get_memory_dir(platform, name)
    if not mem_dir.exists():
        raise HTTPException(status_code=404, detail="Memory directory not found")

    stats = {}
    for layer in ["style_dna", "character", "plot", "context", "history"]:
        layer_dir = mem_dir / layer
        if layer_dir.exists():
            files = list(layer_dir.glob("*.json"))
            stats[layer] = len(files)
        else:
            stats[layer] = 0

    # Check entity graph
    eg_path = mem_dir / "entity_graph.json"
    if eg_path.exists():
        try:
            with open(eg_path, "r", encoding="utf-8-sig") as f:
                eg = json.load(f)
                stats["entity_graph"] = {
                    "entities": len(eg.get("entities", {})),
                    "edges": len(eg.get("edges", [])),
                }
        except (json.JSONDecodeError, IOError):
            stats["entity_graph"] = {"entities": 0, "edges": 0}

    return stats


@router.get("/query")
def query_memory(platform: str, name: str, type: str = "", filter: str = ""):
    """Query memory by type."""
    mem_dir = get_memory_dir(platform, name)
    if not mem_dir.exists():
        return []

    layer_dir = mem_dir / type
    if not layer_dir.exists():
        return []

    results = []
    for f in sorted(layer_dir.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
                data["_file"] = f.name
                results.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    return results


@router.get("/entity-graph")
def get_entity_graph(platform: str, name: str):
    """Get entity graph data."""
    eg_path = get_memory_dir(platform, name) / "entity_graph.json"
    if not eg_path.exists():
        return {"entities": {}, "edges": [], "next_entity_id": 1}
    with open(eg_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)
