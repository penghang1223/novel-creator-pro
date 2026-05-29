"""Read/write chapter .md files and summaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from config import PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.chapter import ChapterContent, ChapterSummary
from utils.paths import (
    count_chinese_chars,
    extract_chapter_title,
    find_chapter_file,
    get_novel_dir,
    get_summaries_dir,
    list_chapter_files,
)


class ChapterService:
    """Service for reading and writing chapter files."""

    def get_chapter_content(self, platform: str, novel_name: str, ch_num: int) -> Optional[ChapterContent]:
        ch_dir = get_chapters_dir(platform, novel_name)
        novel_dir = get_novel_dir(platform, novel_name)
        ch_file = find_chapter_file(novel_dir, ch_num)
        if not ch_file:
            return None

        content = ch_file.read_text(encoding="utf-8")
        return ChapterContent(
            chapter_number=ch_num,
            title=extract_chapter_title(ch_file.name),
            content=content,
            word_count=count_chinese_chars(content),
        )

    def save_chapter_content(self, platform: str, novel_name: str, ch_num: int, content: str) -> bool:
        novel_dir = get_novel_dir(platform, novel_name)
        ch_file = find_chapter_file(novel_dir, ch_num)
        if not ch_file:
            return False

        ch_file.write_text(content, encoding="utf-8")
        return True

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
        result = []
        for num, ch_file in list_chapter_files(get_novel_dir(platform, novel_name)):
            result.append((num, extract_chapter_title(ch_file.name), ch_file))
        return result
