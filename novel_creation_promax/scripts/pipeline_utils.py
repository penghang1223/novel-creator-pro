#!/usr/bin/env python3
"""Shared helpers for novel Pro Max pipeline scripts."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_chinese_chars(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def find_chapter_file(novel_dir: Path, chapter: int) -> Path | None:
    body_dir = novel_dir / "正文"
    if not body_dir.exists():
        return None
    patterns = [
        f"第{chapter:03d}章*",
        f"第{chapter}章*",
        f"{chapter:03d}_*",
        f"chapter_{chapter:03d}*",
        f"chapter_{chapter}*",
    ]
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(body_dir.glob(pattern))
    matches = sorted({p for p in matches if p.is_file() and p.suffix.lower() in {".md", ".txt"}})
    return matches[0] if matches else None


def infer_chapter_number(path: Path) -> int | None:
    name = path.stem
    patterns = [
        r"第0*(\d+)章",
        r"^0*(\d+)[_-]",
        r"chapter_0*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def list_chapter_files(novel_dir: Path) -> list[tuple[int, Path]]:
    body_dir = novel_dir / "正文"
    if not body_dir.exists():
        return []
    items: list[tuple[int, Path]] = []
    for path in body_dir.glob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue
        chapter = infer_chapter_number(path)
        if chapter is not None:
            items.append((chapter, path))
    return sorted(items, key=lambda item: (item[0], item[1].name))


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def passport_path(novel_dir: Path, chapter: int) -> Path:
    return novel_dir / "摘要" / f"chapter_{chapter:03d}_passport.json"


def init_passport(chapter: int, title: str, chapter_file: Path | None, novel_dir: Path) -> dict[str, Any]:
    return {
        "chapter": chapter,
        "title": title or f"第{chapter}章",
        "chapter_file": rel(chapter_file, novel_dir) if chapter_file else "",
        "word_count": 0,
        "pipeline": {
            "memory_pack": "skipped",
            "truth_compile": "skipped",
            "truth_delta_template": "skipped",
            "pre_write_check": "skipped",
            "writing_gate": "skipped",
            "post_write_audit": "skipped",
            "normalizer": "skipped",
            "truth_delta_extract": "pending",
            "truth_delta": "pending",
            "truth_sync": "pending",
            "style_calibration": "skipped",
            "character_consistency": "skipped",
            "memory_sync": "pending",
        },
        "inputs": {
            "memory_pack": "",
            "rule_stack": "",
            "truth_brief": "",
            "truth_delta": "",
            "truth_delta_candidates": "",
            "truth_delta_candidates_review": "",
            "truth_delta_report": "",
            "truth_apply_report": "",
            "normalizer_report": "",
            "normalizer_task": "",
            "pre_check_report": "",
            "audit_report": "",
            "style_report": "",
            "character_report": "",
        },
        "changes": {
            "character_state_changes": [],
            "new_foreshadowing": [],
            "resolved_foreshadowing": [],
            "world_state_changes": [],
        },
        "publish": {
            "platform": "",
            "status": "not_synced",
            "target_file": "",
            "synced_at": "",
        },
        "updated_at": now_iso(),
    }


def load_passport(novel_dir: Path, chapter: int, title: str = "", chapter_file: Path | None = None) -> dict[str, Any]:
    path = passport_path(novel_dir, chapter)
    passport = load_json(path, init_passport(chapter, title or f"第{chapter}章", chapter_file, novel_dir))
    if chapter_file:
        passport["chapter_file"] = rel(chapter_file, novel_dir)
        try:
            passport["word_count"] = count_chinese_chars(chapter_file.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            passport["word_count"] = 0
    passport["updated_at"] = now_iso()
    return passport


def save_passport(novel_dir: Path, chapter: int, passport: dict[str, Any]) -> None:
    save_json(passport_path(novel_dir, chapter), passport)


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
