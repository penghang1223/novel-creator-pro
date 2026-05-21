#!/usr/bin/env python3
"""Hard audit pipeline for novel chapters."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline_utils import (
    count_chinese_chars,
    find_chapter_file,
    list_chapter_files,
    load_json,
    load_passport,
    rel,
    save_passport,
    update_novel_state,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "novel_creation_promax" / "scripts"


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def run(cmd: list[str], label: str) -> dict[str, Any]:
    print(f"\n{'=' * 64}")
    print(label)
    print(" ".join(cmd))
    print("=" * 64)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return {
        "status": "pass" if result.returncode == 0 else "fail",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def title_from_file(path: Path, fallback: str) -> str:
    try:
        first = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        return first or fallback
    except (UnicodeDecodeError, IndexError):
        return fallback


def audit_one(novel_dir: Path, chapter: int, *, title: str = "") -> bool:
    chapter_file = find_chapter_file(novel_dir, chapter)
    if not chapter_file:
        print(f"未找到第{chapter}章正文文件", file=sys.stderr)
        return False

    title = title or title_from_file(chapter_file, f"第{chapter}章")
    passport = load_passport(novel_dir, chapter, title, chapter_file)

    gate = run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "writing_gate.py"),
            "--chapter",
            str(chapter_file),
            "--novel-dir",
            str(novel_dir),
        ],
        f"第{chapter}章 Writing Gate",
    )
    passport["pipeline"]["writing_gate"] = gate["status"]

    audit_report = novel_dir / "素材" / f"audit_ch{chapter:03d}.json"
    audit_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "post_write_audit.py"),
        "--chapter-file",
        str(chapter_file),
        "--title",
        title,
        "--output",
        str(audit_report),
    ]
    prev = find_chapter_file(novel_dir, chapter - 1) if chapter > 1 else None
    if prev:
        audit_cmd.extend(["--prev-file", str(prev)])
    novel_state = novel_dir / "novel_state.json"
    if novel_state.exists():
        audit_cmd.extend(["--novel-state", str(novel_state)])
    audit = run(audit_cmd, f"第{chapter}章 写后审计")
    passport["pipeline"]["post_write_audit"] = audit["status"]
    passport["inputs"]["audit_report"] = rel(audit_report, novel_dir)

    word_count = count_chinese_chars(chapter_file.read_text(encoding="utf-8"))
    passport["word_count"] = word_count
    save_passport(novel_dir, chapter, passport)
    update_novel_state(
        novel_dir,
        chapter=chapter,
        word_count=word_count,
        audit_report=rel(audit_report, novel_dir),
        audit_status=audit["status"],
        passport=rel(novel_dir / "摘要" / f"chapter_{chapter:03d}_passport.json", novel_dir),
    )

    return gate["returncode"] == 0 and audit["returncode"] == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="小说章节硬审计流水线")
    parser.add_argument("--novel-dir", required=True, help="小说项目目录")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chapter", type=int, help="章节号")
    group.add_argument("--all", action="store_true", help="审计所有章节")
    parser.add_argument("--title", default="", help="章节标题，仅 --chapter 时使用")
    args = parser.parse_args()

    novel_dir = resolve_path(args.novel_dir)
    (novel_dir / "素材").mkdir(parents=True, exist_ok=True)
    (novel_dir / "摘要").mkdir(parents=True, exist_ok=True)

    if args.chapter:
        return 0 if audit_one(novel_dir, args.chapter, title=args.title) else 1

    ok = True
    chapters = list_chapter_files(novel_dir)
    if not chapters:
        print(f"未找到章节文件: {novel_dir / '正文'}", file=sys.stderr)
        return 1
    for chapter, _path in chapters:
        ok = audit_one(novel_dir, chapter) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
