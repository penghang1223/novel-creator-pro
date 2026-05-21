"""Read/write chapter .md files and summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from models.chapter import ChapterContent, ChapterSummary
from utils.paths import (
    count_chinese_chars,
    extract_chapter_number,
    extract_chapter_title,
    get_chapters_dir,
    get_summaries_dir,
)


class ChapterService:
    """Service for reading and writing chapter files."""

    def get_chapter_content(self, platform: str, novel_name: str, ch_num: int) -> Optional[ChapterContent]:
        ch_dir = get_chapters_dir(platform, novel_name)
        if not ch_dir.exists():
            return None

        for ch_file in sorted(ch_dir.glob("第*.md")):
            if extract_chapter_number(ch_file.name) == ch_num:
                content = ch_file.read_text(encoding="utf-8")
                return ChapterContent(
                    chapter_number=ch_num,
                    title=extract_chapter_title(ch_file.name),
                    content=content,
                    word_count=count_chinese_chars(content),
                )
        return None

    def save_chapter_content(self, platform: str, novel_name: str, ch_num: int, content: str) -> bool:
        ch_dir = get_chapters_dir(platform, novel_name)
        if not ch_dir.exists():
            return False

        for ch_file in sorted(ch_dir.glob("第*.md")):
            if extract_chapter_number(ch_file.name) == ch_num:
                ch_file.write_text(content, encoding="utf-8")
                return True
        return False

    def get_chapter_summary(self, platform: str, novel_name: str, ch_num: int) -> dict[str, Any]:
        summary_dir = get_summaries_dir(platform, novel_name)
        summary_path = summary_dir / f"chapter_{ch_num:03d}_summary.json"
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        return {}

    def save_chapter_summary(self, platform: str, novel_name: str, ch_num: int, data: dict[str, Any]) -> bool:
        summary_dir = get_summaries_dir(platform, novel_name)
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path = summary_dir / f"chapter_{ch_num:03d}_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    def list_chapter_files(self, platform: str, novel_name: str) -> list[tuple[int, str, Path]]:
        """List all chapter files with (number, title, path)."""
        ch_dir = get_chapters_dir(platform, novel_name)
        if not ch_dir.exists():
            return []
        result = []
        for ch_file in sorted(ch_dir.glob("第*.md")):
            num = extract_chapter_number(ch_file.name)
            if num is not None:
                result.append((num, extract_chapter_title(ch_file.name), ch_file))
        return result
