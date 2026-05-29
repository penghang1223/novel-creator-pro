"""Machine-readable knowledge routing and per-chapter pack assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonio import load_json, now_iso, save_json
from .paths import find_chapter_file, rel


def load_routes(project_root: Path) -> dict[str, Any]:
    return load_json(project_root / "knowledge_base" / "_ROUTES.json", {})


def _replace_vars(value: str, context: dict[str, Any]) -> str:
    result = value
    for key, item in context.items():
        result = result.replace("{" + key + "}", str(item))
    return result


def _path_exists(project_root: Path, path: str) -> bool:
    if "{" in path or "}" in path:
        return False
    return (project_root / path).exists()


def infer_genre(novel_dir: Path) -> str:
    state = load_json(novel_dir / "novel_state.json", {})
    if isinstance(state, dict):
        for key in ("genre", "type", "category"):
            value = state.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    bootstrap = load_json(novel_dir / "记忆" / "project_bootstrap.json", {})
    if isinstance(bootstrap, dict):
        for path in (
            ("project", "genre"),
            ("project", "category"),
            ("novel", "genre"),
        ):
            cursor: Any = bootstrap
            for key in path:
                cursor = cursor.get(key) if isinstance(cursor, dict) else None
            if isinstance(cursor, str) and cursor.strip():
                return cursor.strip()
    return ""


def build_knowledge_pack(
    *,
    project_root: Path,
    novel_dir: Path,
    chapter: int,
    title: str,
    platform: str = "",
    genre: str = "",
) -> dict[str, Any]:
    routes = load_routes(project_root)
    platform = platform or novel_dir.parent.name
    book_title = novel_dir.name
    previous_file = find_chapter_file(novel_dir, chapter - 1) if chapter > 1 else None
    genre = genre or infer_genre(novel_dir)
    context = {
        "平台": platform,
        "书名": book_title,
        "chapter": chapter,
        "chapter_3": f"{chapter:03d}",
        "previous_chapter_file": rel(previous_file, project_root) if previous_file else "",
        "genre": genre,
        "题材": genre,
        "title": title,
    }

    required = []
    for item in routes.get("required", []):
        path = _replace_vars(item.get("path", ""), context)
        required.append({**item, "path": path, "exists": _path_exists(project_root, path)})

    selected: list[dict[str, Any]] = []
    for route in routes.get("routes", []):
        key = route.get("key", "")
        select = False
        reason = ""
        if key == "chapter_one" and chapter == 1:
            select, reason = True, "第1章"
        elif key == "opening" and chapter <= 5:
            select, reason = True, "前5章"
        elif key == "genre" and genre:
            select, reason = True, f"题材={genre}"
        elif key == "dialogue" and any(token in title for token in ("对话", "交锋", "谈判", "质问")):
            select, reason = True, "标题命中对话/交锋"
        elif key == "high_pressure" and any(token in title for token in ("危机", "暴露", "反派", "杀", "逼", "崩")):
            select, reason = True, "标题命中高压场景"
        if not select:
            continue
        files = []
        for file_path in route.get("files", []):
            path = _replace_vars(file_path, context)
            files.append({"path": path, "exists": _path_exists(project_root, path)})
        selected.append({"key": key, "name": route.get("name", key), "reason": reason, "files": files})

    pack = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "chapter": chapter,
        "title": title,
        "novel_dir": rel(novel_dir, project_root),
        "context": context,
        "required": required,
        "selected_routes": selected,
        "available_routes": [
            {"key": route.get("key", ""), "name": route.get("name", ""), "trigger": route.get("trigger", "")}
            for route in routes.get("routes", [])
        ],
    }
    return pack


def save_knowledge_pack(pack: dict[str, Any], output: Path) -> None:
    save_json(output, pack)

