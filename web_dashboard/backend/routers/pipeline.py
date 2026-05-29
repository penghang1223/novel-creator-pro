"""Pipeline execution API routes — run scripts as subprocesses."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Optional
import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import MEMORY_SCRIPT, PROJECT_ROOT, SCRIPTS_DIR

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.paths import find_chapter_file

router = APIRouter(prefix="/api/novels/{platform}/{name:path}/pipeline", tags=["pipeline"])

# In-memory job registry
jobs: dict[str, dict[str, Any]] = {}
job_logs: dict[str, list[dict[str, str]]] = {}


class PipelineRequest(BaseModel):
    chapter: Optional[int] = None
    extra_args: list = []


def _get_novel_dir(platform: str, name: str) -> Path:
    return PROJECT_ROOT / "novel_output" / platform / name


def _get_chapter_file_from_dir(novel_dir: Path, ch_num: int) -> Optional[str]:
    if not ch_num:
        return None
    path = find_chapter_file(novel_dir, ch_num)
    return str(path) if path else None


def _add_log(job_id: str, level: str, message: str):
    import datetime
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "level": level,
        "message": message,
    }
    job_logs.setdefault(job_id, []).append(entry)


async def _run_script(job_id: str, cmd: list[str]):
    """Run a script as subprocess, capture output."""
    jobs[job_id]["status"] = "running"
    _add_log(job_id, "info", f"$ {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )

        async def read_stream(stream, prefix=""):
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    _add_log(job_id, "info" if not prefix else "error", f"{prefix}{text}")

        await asyncio.gather(
            read_stream(proc.stdout),
            read_stream(proc.stderr, "[stderr] "),
        )

        await proc.wait()
        jobs[job_id]["status"] = "completed" if proc.returncode == 0 else "failed"
        jobs[job_id]["exit_code"] = proc.returncode
        _add_log(job_id, "info", f"Process exited with code {proc.returncode}")

    except Exception as e:
        jobs[job_id]["status"] = "error"
        _add_log(job_id, "error", str(e))


def _build_command(action: str, novel_dir: Path, chapter: Optional[int], extra_args: list) -> Optional[list]:
    """Build the CLI command for a pipeline action."""
    import sys
    python = sys.executable
    scripts = SCRIPTS_DIR

    ch_file = None
    if chapter:
        ch_file = _get_chapter_file_from_dir(novel_dir, chapter)

    actions = {
        "write-pre": [python, str(scripts / "write_pipeline.py"), "pre", "--novel-dir", str(novel_dir)]
        + ([f"--chapter={chapter}", f"--title=第{chapter}章"] if chapter else []),

        "write-post": [python, str(scripts / "write_pipeline.py"), "post", "--novel-dir", str(novel_dir)]
        + ([f"--chapter={chapter}", f"--title=第{chapter}章"] if chapter else []),

        "pre-write-check": [python, str(scripts / "pre_write_check.py"), "--novel-dir", str(novel_dir)]
        + ([f"--chapter={chapter}"] if chapter else []),

        "gate-check": [python, str(scripts / "writing_gate.py")]
        + ([f"--chapter={ch_file}"] if ch_file else [])
        + ["--novel-dir", str(novel_dir)],

        "post-audit": [python, str(scripts / "post_write_audit.py")]
        + ([f"--chapter-file={ch_file}"] if ch_file else [])
        + ([f"--prev-file={_get_chapter_file_from_dir(novel_dir, chapter - 1)}"] if chapter and chapter > 1 else [])
        + ([f"--title=第{chapter}章"] if chapter else []),

        "style-check": [python, str(scripts / "style_calibrator.py")]
        + ([f"--input={ch_file}"] if ch_file else []),

        "character-check": [python, str(scripts / "character_consistency_checker.py")]
        + ([f"--input={ch_file}"] if ch_file else []),

        "plot-check": [python, str(scripts / "plot_continuity_checker.py"), "--check", str(chapter or 1)],

        "memory-sync": [python, str(MEMORY_SCRIPT), "sync-chapter"]
        + ([f"--input={novel_dir}/摘要/chapter_{chapter:03d}_summary.json"] if chapter else [])
        + [f"--memory-dir={novel_dir}/记忆"],

        "memory-pack": [python, str(MEMORY_SCRIPT), "chapter-pack"]
        + ([f"--chapter={chapter}"] if chapter else [])
        + [f"--memory-dir={novel_dir}/记忆"],

        "memory-stats": [python, str(MEMORY_SCRIPT), "stats", f"--memory-dir={novel_dir}/记忆"],

        "generate-cover": [python, str(scripts / "generate_cover.py"), "--auto", f"--output={novel_dir}/cover.jpg"],
    }

    cmd = actions.get(action)
    if cmd is None:
        return None

    if extra_args:
        cmd.extend(extra_args)

    return cmd


@router.post("/{action}")
async def run_pipeline_action(platform: str, name: str, action: str, body: Optional[PipelineRequest] = None):
    """Execute a pipeline action."""
    body = body or PipelineRequest()
    novel_dir = _get_novel_dir(platform, name)
    job_id = str(uuid.uuid4())[:8]

    cmd = _build_command(action, novel_dir, body.chapter, body.extra_args)
    if cmd is None:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    jobs[job_id] = {"id": job_id, "action": action, "status": "pending", "exit_code": None}
    job_logs[job_id] = []

    asyncio.create_task(_run_script(job_id, cmd))

    return {"job_id": job_id, "action": action}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get job status and logs."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        **jobs[job_id],
        "logs": job_logs.get(job_id, []),
    }


@router.get("/jobs")
def list_jobs():
    """List recent jobs."""
    return list(jobs.values())[-20:]
