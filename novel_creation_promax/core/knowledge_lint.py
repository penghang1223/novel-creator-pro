"""Knowledge-base lint helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonio import read_text


def parse_frontmatter_status(text: str) -> str:
    if not text.startswith("---"):
        return "unspecified"
    end = text.find("\n---", 3)
    if end == -1:
        return "unspecified"
    frontmatter = text[3:end]
    for line in frontmatter.splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip() or "unspecified"
    return "unspecified"


def scan_markdown_status(root: Path) -> dict[str, Any]:
    files = sorted(path for path in root.rglob("*.md") if ".git" not in path.parts and "node_modules" not in path.parts)
    summary = {"active": 0, "deprecated": 0, "archive": 0, "unspecified": 0, "other": 0}
    examples: dict[str, list[str]] = {key: [] for key in summary}
    for path in files:
        status = parse_frontmatter_status(read_text(path))
        bucket = status if status in summary else "other"
        summary[bucket] += 1
        if len(examples[bucket]) < 10:
            examples[bucket].append(path.as_posix())
    return {"total": len(files), "summary": summary, "examples": examples}

