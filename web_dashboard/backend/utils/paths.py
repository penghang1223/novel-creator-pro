"""Dashboard path wrappers backed by the shared core package."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config import OUTPUT_DIR, PROJECT_ROOT

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.paths import (
    count_chinese_chars,
    extract_chapter_title,
    find_chapter_file,
    get_chapters_dir as _get_chapters_dir,
    get_memory_dir as _get_memory_dir,
    get_novel_dir as _get_novel_dir,
    get_novel_state_path as _get_novel_state_path,
    get_summaries_dir as _get_summaries_dir,
    infer_chapter_number,
    list_chapter_files,
)


def get_novel_dir(platform: str, novel_name: str) -> Path:
    return _get_novel_dir(OUTPUT_DIR, platform, novel_name)


def get_chapters_dir(platform: str, novel_name: str) -> Path:
    return _get_chapters_dir(OUTPUT_DIR, platform, novel_name)


def get_summaries_dir(platform: str, novel_name: str) -> Path:
    return _get_summaries_dir(OUTPUT_DIR, platform, novel_name)


def get_memory_dir(platform: str, novel_name: str) -> Path:
    return _get_memory_dir(OUTPUT_DIR, platform, novel_name)


def get_novel_state_path(platform: str, novel_name: str) -> Path:
    return _get_novel_state_path(OUTPUT_DIR, platform, novel_name)


def extract_chapter_number(filename: str) -> Optional[int]:
    return infer_chapter_number(filename)

