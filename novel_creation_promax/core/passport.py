"""Chapter passport helpers and pipeline status normalization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonio import load_json, now_iso, save_json
from .paths import count_chinese_chars, rel

PASS_VALUES = {"pass", "passed", "ok", "success", True}
FAIL_VALUES = {"fail", "failed", "blocked", "error", False}


def normalize_status(value: Any) -> str:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in PASS_VALUES:
            return "pass"
        if lowered in FAIL_VALUES:
            return "fail"
        if lowered in {"pending", "skipped", "warning"}:
            return lowered
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "pending"


def status_passed(value: Any) -> bool:
    return normalize_status(value) == "pass"


def passport_path(novel_dir: Path, chapter: int) -> Path:
    return novel_dir / "摘要" / f"chapter_{chapter:03d}_passport.json"


def init_passport(chapter: int, title: str, chapter_file: Path | None, novel_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.1",
        "chapter": chapter,
        "title": title or f"第{chapter}章",
        "chapter_file": rel(chapter_file, novel_dir) if chapter_file else "",
        "word_count": 0,
        "pipeline_result": "pending",
        "pipeline": {
            "knowledge_pack": "skipped",
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
            "knowledge_pack": "",
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


def ensure_passport_shape(passport: dict[str, Any], chapter: int, title: str, chapter_file: Path | None, novel_dir: Path) -> dict[str, Any]:
    base = init_passport(chapter, title, chapter_file, novel_dir)
    merged = {**base, **passport}
    merged["pipeline"] = {**base["pipeline"], **passport.get("pipeline", {})}
    merged["inputs"] = {**base["inputs"], **passport.get("inputs", {})}
    merged["changes"] = {**base["changes"], **passport.get("changes", {})}
    merged["publish"] = {**base["publish"], **passport.get("publish", {})}
    merged.setdefault("schema_version", "1.1")
    return merged


def load_passport(novel_dir: Path, chapter: int, title: str = "", chapter_file: Path | None = None) -> dict[str, Any]:
    path = passport_path(novel_dir, chapter)
    passport = load_json(path, {})
    if not isinstance(passport, dict):
        passport = {}
    passport = ensure_passport_shape(passport, chapter, title or f"第{chapter}章", chapter_file, novel_dir)
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


def passport_pipeline_passed(passport: dict[str, Any], required: list[str] | None = None) -> bool:
    pipeline = passport.get("pipeline", {})
    required = required or ["writing_gate", "post_write_audit", "normalizer", "truth_delta", "truth_sync"]
    return all(status_passed(pipeline.get(key)) for key in required)


def previous_chapter_audited(novel_dir: Path, chapter: int) -> tuple[bool, str]:
    if chapter <= 1:
        return True, "第一章无上一章审计门禁"
    prev = chapter - 1
    passport = load_json(passport_path(novel_dir, prev), {})
    if isinstance(passport, dict):
        pipeline = passport.get("pipeline", {})
        result = normalize_status(passport.get("pipeline_result"))
        if status_passed(pipeline.get("post_write_audit")) and result in {"pass", "pending"}:
            return True, f"第{prev}章 passport 审计通过"
        if status_passed(pipeline.get("post_write_audit")) and not passport.get("pipeline_result"):
            return True, f"第{prev}章旧版 passport 审计通过"
        if pipeline:
            return False, f"第{prev}章 passport 审计状态为 {pipeline.get('post_write_audit')}, pipeline_result={passport.get('pipeline_result')}"

    state = load_json(novel_dir / "novel_state.json", {})
    if isinstance(state, dict):
        chapters = state.get("chapters", {})
        prev_state = chapters.get(f"{prev:03d}") if isinstance(chapters, dict) else None
        if isinstance(prev_state, dict) and status_passed(prev_state.get("audit_status")):
            return True, f"第{prev}章 novel_state 审计通过"
        last_audit = state.get("last_audit_chapter")
        if isinstance(last_audit, int) and last_audit >= prev:
            return True, f"novel_state.last_audit_chapter={last_audit}"

    return False, f"第{prev}章缺少通过状态的 passport 审计记录"

