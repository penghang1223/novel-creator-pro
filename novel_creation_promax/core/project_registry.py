"""Project registry builder for novel_output and knowledge_base/80_Projects."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .jsonio import load_json, now_iso, read_text, save_json
from .paths import normalize_title, rel, split_project_folder_name

IGNORED_OUTPUT_DIRS = {"素材", "covers", "archive", "uploaded", "short_uploaded"}
DEFAULT_IGNORED_PLATFORMS = {"短篇小说"}


@dataclass(frozen=True)
class ProjectEntry:
    source: str
    path: str
    name: str
    title: str
    norm_title: str
    project_id: str | None = None
    platform: str | None = None


@dataclass(frozen=True)
class DriftItem:
    kind: str
    message: str
    output: ProjectEntry | None = None
    project: ProjectEntry | None = None
    score: float | None = None


def stable_uid(norm_title: str) -> str:
    digest = hashlib.sha1(norm_title.encode("utf-8")).hexdigest()[:10]
    return f"proj_{digest}"


def read_json_title(path: Path) -> tuple[str | None, str | None]:
    data = load_json(path, {})
    if not isinstance(data, dict):
        return None, None
    title = data.get("title")
    novel_id = data.get("novel_id")
    project_id = split_project_folder_name(str(novel_id))[0] if novel_id else None
    return (str(title).strip() if title else None), project_id


def read_config_title(path: Path) -> str | None:
    content = read_text(path)
    if not content:
        return None
    patterns = [
        r"\|\s*书名\s*\|\s*([^|\n]+?)\s*\|",
        r"^#\s*_config\s*[—-]\s*(.+?)\s*$",
        r"^\s*-\s*\*\*书名\*\*[:：]\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def collect_output_entries(project_root: Path, include_short: bool = False) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    output_dir = project_root / "novel_output"
    if not output_dir.exists():
        return entries
    for platform_dir in sorted(path for path in output_dir.iterdir() if path.is_dir()):
        if platform_dir.name in IGNORED_OUTPUT_DIRS:
            continue
        if not include_short and platform_dir.name in DEFAULT_IGNORED_PLATFORMS:
            continue
        for novel_dir in sorted(path for path in platform_dir.iterdir() if path.is_dir()):
            if novel_dir.name in IGNORED_OUTPUT_DIRS:
                continue
            project_id, title = split_project_folder_name(novel_dir.name)
            entries.append(
                ProjectEntry(
                    source="novel_output",
                    path=rel(novel_dir, project_root),
                    name=novel_dir.name,
                    title=title,
                    norm_title=normalize_title(title),
                    project_id=project_id,
                    platform=platform_dir.name,
                )
            )
    return entries


def collect_project_entries(project_root: Path) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    projects_dir = project_root / "knowledge_base" / "80_Projects"
    if not projects_dir.exists():
        return entries
    for project_dir in sorted(path for path in projects_dir.iterdir() if path.is_dir()):
        folder_id, folder_title = split_project_folder_name(project_dir.name)
        meta_title, meta_id = read_json_title(project_dir / "meta.json")
        config_title = read_config_title(project_dir / "_config.md")
        title = meta_title or config_title or folder_title
        project_id = meta_id or folder_id
        entries.append(
            ProjectEntry(
                source="80_Projects",
                path=rel(project_dir, project_root),
                name=project_dir.name,
                title=title,
                norm_title=normalize_title(title),
                project_id=project_id,
            )
        )
    return entries


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return min(len(left), len(right)) / max(len(left), len(right))
    return SequenceMatcher(None, left, right).ratio()


def best_project_for(output: ProjectEntry, projects: list[ProjectEntry]) -> tuple[ProjectEntry | None, float]:
    if not projects:
        return None, 0.0
    scored = [(project, similarity(output.norm_title, project.norm_title)) for project in projects]
    return max(scored, key=lambda item: item[1])


def analyze(outputs: list[ProjectEntry], projects: list[ProjectEntry]) -> list[DriftItem]:
    items: list[DriftItem] = []
    matched_project_paths: set[str] = set()
    projects_by_title: dict[str, list[ProjectEntry]] = {}
    for project in projects:
        projects_by_title.setdefault(project.norm_title, []).append(project)

    for output in outputs:
        exact_projects = projects_by_title.get(output.norm_title, [])
        if exact_projects:
            project = exact_projects[0]
            matched_project_paths.add(project.path)
            if output.project_id != project.project_id:
                items.append(
                    DriftItem(
                        kind="id_mismatch",
                        message=f"同名项目编号不一致: output={output.project_id or '无编号'} project={project.project_id or '无编号'}",
                        output=output,
                        project=project,
                        score=1.0,
                    )
                )
            continue

        candidate, score = best_project_for(output, projects)
        if candidate and score >= 0.62:
            matched_project_paths.add(candidate.path)
            items.append(
                DriftItem(
                    kind="possible_match",
                    message=f"未精确匹配，但疑似同一项目，相似度 {score:.2f}",
                    output=output,
                    project=candidate,
                    score=score,
                )
            )
        else:
            items.append(
                DriftItem(
                    kind="missing_project",
                    message="novel_output 中存在，但 80_Projects 未找到对应项目",
                    output=output,
                    project=candidate,
                    score=score if candidate else None,
                )
            )

    output_norms = {entry.norm_title for entry in outputs}
    for project in projects:
        if project.path in matched_project_paths or project.norm_title in output_norms:
            continue
        candidate_outputs = [(output, similarity(project.norm_title, output.norm_title)) for output in outputs]
        candidate_output, score = max(candidate_outputs, key=lambda item: item[1]) if candidate_outputs else (None, 0.0)
        items.append(
            DriftItem(
                kind="orphan_project",
                message="80_Projects 中存在，但 novel_output 未找到精确对应目录",
                output=candidate_output if score >= 0.62 else None,
                project=project,
                score=score if score >= 0.62 else None,
            )
        )
    return items


def build_registry(project_root: Path, include_short: bool = False) -> dict:
    outputs = collect_output_entries(project_root, include_short=include_short)
    projects = collect_project_entries(project_root)
    issues = analyze(outputs, projects)
    by_norm: dict[str, dict] = {}
    for output in outputs:
        entry = by_norm.setdefault(
            output.norm_title,
            {
                "uid": stable_uid(output.norm_title),
                "canonical_title": output.title,
                "normalized_title": output.norm_title,
                "project_id": output.project_id,
                "platforms": [],
                "output_dirs": [],
                "project_dirs": [],
                "aliases": sorted({output.name, output.title}),
            },
        )
        entry["platforms"].append(output.platform)
        entry["output_dirs"].append(output.path)
        entry["aliases"] = sorted(set(entry["aliases"]) | {output.name, output.title})
    for project in projects:
        entry = by_norm.setdefault(
            project.norm_title,
            {
                "uid": stable_uid(project.norm_title),
                "canonical_title": project.title,
                "normalized_title": project.norm_title,
                "project_id": project.project_id,
                "platforms": [],
                "output_dirs": [],
                "project_dirs": [],
                "aliases": sorted({project.name, project.title}),
            },
        )
        entry["project_dirs"].append(project.path)
        entry["aliases"] = sorted(set(entry["aliases"]) | {project.name, project.title})
        if not entry.get("project_id") and project.project_id:
            entry["project_id"] = project.project_id

    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "summary": {
            "project_count": len(by_norm),
            "novel_output_count": len(outputs),
            "knowledge_project_count": len(projects),
            "issue_count": len(issues),
        },
        "projects": sorted(by_norm.values(), key=lambda item: item["canonical_title"]),
        "issues": [
            {
                "kind": item.kind,
                "message": item.message,
                "output": asdict(item.output) if item.output else None,
                "project": asdict(item.project) if item.project else None,
                "score": item.score,
            }
            for item in issues
        ],
    }


def registry_path(project_root: Path) -> Path:
    return project_root / "knowledge_base" / "80_Projects" / "_PROJECT_REGISTRY.json"


def save_registry(project_root: Path, include_short: bool = False) -> dict:
    registry = build_registry(project_root, include_short=include_short)
    save_json(registry_path(project_root), registry)
    return registry

