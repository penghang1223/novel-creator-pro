#!/usr/bin/env python3
"""Compatibility wrappers for shared pipeline helpers.

New code should import from ``novel_creation_promax.core``. This module remains
so older scripts that run from ``novel_creation_promax/scripts`` keep working.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.jsonio import load_json, now_iso, save_json
from novel_creation_promax.core.passport import init_passport, load_passport, passport_path, save_passport
from novel_creation_promax.core.paths import (
    count_chinese_chars,
    find_chapter_file,
    infer_chapter_number,
    list_chapter_files,
    rel,
)


def update_novel_state(
    novel_dir: Path,
    *,
    chapter: int | None = None,
    word_count: int | None = None,
    audit_report: str | None = None,
    audit_status: str | None = None,
    passport: str | None = None,
    publish_update: dict[str, Any] | None = None,
    revision_update: dict[str, Any] | None = None,
    pipeline_result: str | None = None,
) -> None:
    state_path = novel_dir / "novel_state.json"
    state = load_json(state_path, {})
    if not isinstance(state, dict):
        state = {}

    state.setdefault("revision_history", [])
    state.setdefault("audit_history", [])
    state.setdefault("publish_state", {})
    state.setdefault("chapters", {})

    if chapter is not None:
        state["current_chapter"] = max(int(state.get("current_chapter", 0) or 0), chapter)
        chapter_key = f"{chapter:03d}"
        ch_state = state["chapters"].setdefault(chapter_key, {})
        ch_state["updated_at"] = now_iso()
        if word_count is not None:
            ch_state["word_count"] = word_count
        if passport:
            ch_state["passport"] = passport
        if audit_report:
            ch_state["audit_report"] = audit_report
            ch_state["audit_status"] = audit_status or ""
        if pipeline_result:
            ch_state["pipeline_result"] = pipeline_result
            if pipeline_result == "pass":
                state["last_completed_chapter"] = max(int(state.get("last_completed_chapter", 0) or 0), chapter)
        if audit_status in {"pass", "passed"}:
            state["last_audit_chapter"] = max(int(state.get("last_audit_chapter", 0) or 0), chapter)

    if word_count is not None and chapter is not None:
        state["word_count"] = sum(
            int(item.get("word_count", 0) or 0)
            for item in state.get("chapters", {}).values()
            if isinstance(item, dict)
        )

    if audit_report:
        state["audit_history"].append(
            {
                "chapter": chapter,
                "report": audit_report,
                "status": audit_status or "",
                "updated_at": now_iso(),
            }
        )

    if publish_update:
        platform = publish_update.get("platform", "unknown")
        state["publish_state"].setdefault(platform, {})
        state["publish_state"][platform].update(publish_update)
        state["publish_state"][platform]["updated_at"] = now_iso()

    if revision_update:
        payload = dict(revision_update)
        payload.setdefault("updated_at", now_iso())
        state["revision_history"].append(payload)

    state["updated_at"] = now_iso()
    save_json(state_path, state)

