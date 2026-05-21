"""WebSocket endpoint for real-time log streaming."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from routers.pipeline import job_logs, jobs

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Stream job logs in real-time via WebSocket."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            job_id = msg.get("job_id")

            if not job_id or job_id not in jobs:
                await websocket.send_json({"type": "error", "message": "Invalid job_id"})
                continue

            last_sent = 0
            while True:
                logs = job_logs.get(job_id, [])
                if len(logs) > last_sent:
                    for entry in logs[last_sent:]:
                        await websocket.send_json({"type": "log", **entry})
                    last_sent = len(logs)

                status = jobs[job_id]["status"]
                if status in ("completed", "failed", "error"):
                    await websocket.send_json({
                        "type": "done",
                        "status": status,
                        "exit_code": jobs[job_id].get("exit_code"),
                    })
                    break

                await asyncio.sleep(0.3)

    except WebSocketDisconnect:
        pass
