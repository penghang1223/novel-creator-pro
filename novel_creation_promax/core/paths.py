"""Canonical filesystem and chapter path helpers."""

from __future__ import annotations

import re
from pathlib import Path

CHAPTER_EXTENSIONS = {".md", ".txt"}


def count_chinese_chars(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def split_project_folder_name(name: str) -> tuple[str | None, str]:
    match = re.match(r"^(?P<id>\d{3})[_\-\s]*(?P<title>.+)$", name.strip())
    if not match:
        return None, name.strip()
    return match.group("id"), match.group("title").strip()


def normalize_title(title: str) -> str:
    value = title.lower()
    value = re.sub(r"[《》【】\[\]（）()_\-\s·:：,，。.!！?？&]+", "", value)
    value = value.replace("已签约完本", "").replace("已签约", "").replace("完本", "")
    return value


def infer_chapter_number(path_or_name: Path | str) -> int | None:
    name = Path(path_or_name).stem
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


def extract_chapter_title(path_or_name: Path | str) -> str:
    name = Path(path_or_name).stem
    name = re.sub(r"^第0*\d+章[-_]?\s*", "", name)
    name = re.sub(r"^0*\d+[-_]\s*", "", name)
    name = re.sub(r"^chapter_0*\d+[-_]?\s*", "", name, flags=re.IGNORECASE)
    return name.strip() or Path(path_or_name).stem


def list_chapter_files(novel_dir: Path) -> list[tuple[int, Path]]:
    body_dir = novel_dir / "正文"
    if not body_dir.exists():
        return []
    items: list[tuple[int, Path]] = []
    for path in body_dir.glob("*"):
        if not path.is_file() or path.suffix.lower() not in CHAPTER_EXTENSIONS:
            continue
        chapter = infer_chapter_number(path)
        if chapter is not None:
            items.append((chapter, path))
    return sorted(items, key=lambda item: (item[0], item[1].name))


def find_chapter_file(novel_dir: Path, chapter: int) -> Path | None:
    for number, path in list_chapter_files(novel_dir):
        if number == chapter:
            return path
    return None


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def get_novel_dir(output_dir: Path, platform: str, novel_name: str) -> Path:
    return output_dir / platform / novel_name


def get_chapters_dir(output_dir: Path, platform: str, novel_name: str) -> Path:
    return get_novel_dir(output_dir, platform, novel_name) / "正文"


def get_summaries_dir(output_dir: Path, platform: str, novel_name: str) -> Path:
    return get_novel_dir(output_dir, platform, novel_name) / "摘要"


def get_memory_dir(output_dir: Path, platform: str, novel_name: str) -> Path:
    return get_novel_dir(output_dir, platform, novel_name) / "记忆"


def get_novel_state_path(output_dir: Path, platform: str, novel_name: str) -> Path:
    return get_novel_dir(output_dir, platform, novel_name) / "novel_state.json"

