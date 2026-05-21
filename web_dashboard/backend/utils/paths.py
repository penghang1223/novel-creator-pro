"""Path resolution utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from config import OUTPUT_DIR


def get_novel_dir(platform: str, novel_name: str) -> Path:
    return OUTPUT_DIR / platform / novel_name


def get_chapters_dir(platform: str, novel_name: str) -> Path:
    return get_novel_dir(platform, novel_name) / "正文"


def get_summaries_dir(platform: str, novel_name: str) -> Path:
    return get_novel_dir(platform, novel_name) / "摘要"


def get_memory_dir(platform: str, novel_name: str) -> Path:
    return get_novel_dir(platform, novel_name) / "记忆"


def get_novel_state_path(platform: str, novel_name: str) -> Path:
    return get_novel_dir(platform, novel_name) / "novel_state.json"


def extract_chapter_number(filename: str) -> Optional[int]:
    """Extract chapter number from filename like '第005章-xxx.md'."""
    m = re.search(r"第(\d+)章", filename)
    if m:
        return int(m.group(1))
    return None


def extract_chapter_title(filename: str) -> str:
    """Extract title from filename like '第005章-觉醒.md'."""
    # Remove extension and chapter prefix
    name = Path(filename).stem
    m = re.match(r"第\d+章[-_]?\s*(.*)", name)
    if m and m.group(1):
        return m.group(1)
    return name


def count_chinese_chars(text: str) -> int:
    """Count Chinese characters + Chinese punctuation in text."""
    count = 0
    for ch in text:
        if "一" <= ch <= "鿿" or "　" <= ch <= "〿" or "＀" <= ch <= "￯":
            count += 1
    return count
