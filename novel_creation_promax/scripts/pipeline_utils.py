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


def resolve_novel_path(template: str, novel_dir: Path, **extra: str | int) -> str:
    """将路径模板中的占位符替换为实际值。

    支持的变量：
        {平台}     — 从 novel_dir 推断（novel_output/{平台}/{书名}）
        {书名}     — 从 novel_dir 推断
        {章节号}   — extra["chapter"]，格式化为三位数字
        {卷号}     — extra["volume"]，格式化为两位数字
        {小说目录} — novel_dir 的相对路径

    用法：
        resolve_novel_path("{平台}/{书名}/正文/ch{章节号}.md", novel_dir, chapter=3)
    """
    novel_rel = rel(novel_dir, PROJECT_ROOT)
    parts = novel_rel.split("/")
    platform = parts[1] if len(parts) > 1 else ""
    book_name = parts[2] if len(parts) > 2 else ""

    result = template.replace("{平台}", platform).replace("{书名}", book_name)
    result = result.replace("{小说目录}", str(novel_rel))

    if "chapter" in extra:
        ch = int(extra["chapter"])
        result = result.replace("{章节号}", f"{ch:03d}")
        result = result.replace("{章节号_raw}", str(ch))
    if "volume" in extra:
        result = result.replace("{卷号}", f"{int(extra['volume']):02d}")

    return result


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

    # --- resume_point: 断点续跑标记 ---
    if chapter is not None:
        resume: dict[str, Any] = {"chapter": chapter, "updated_at": now_iso()}
        if pipeline_result == "pass":
            # 本章完成，下一步是写下一章的 pre
            resume["action"] = "pre"
            resume["next_chapter"] = chapter + 1
            resume["hint"] = f"第{chapter}章已完成，可写第{chapter + 1}章"
        elif pipeline_result == "fail":
            # 本章 post 未通过，需要修复后重跑 post
            resume["action"] = "post"
            resume["next_chapter"] = chapter
            resume["hint"] = f"第{chapter}章审计未通过，需修复后重跑 post"
        else:
            # pre 阶段完成，下一步是写正文然后跑 post
            resume["action"] = "write_then_post"
            resume["next_chapter"] = chapter
            resume["hint"] = f"第{chapter}章 pre 已完成，写完正文后跑 post"
        state["resume_point"] = resume

    state["updated_at"] = now_iso()
    save_json(state_path, state)

