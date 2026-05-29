#!/usr/bin/env python3
"""
Scan novel output directories and knowledge_base/80_Projects for naming drift.

This tool is read-only by default. It reports likely matches, missing project
records, and ID mismatches so humans can decide whether to rename or merge
project folders. Use tools/build_project_registry.py to write the generated
registry file.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.project_registry import (
    analyze,
    collect_output_entries,
    collect_project_entries,
)


def safe_print(text: str = "") -> None:
    print(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))


def print_report(outputs, projects, items) -> None:
    safe_print("=" * 72)
    safe_print("80_Projects 编号/命名对齐检查")
    safe_print("=" * 72)
    safe_print(f"novel_output 项目数: {len(outputs)}")
    safe_print(f"80_Projects 项目数: {len(projects)}")
    safe_print(f"发现需人工确认项: {len(items)}")
    safe_print()

    for kind in ("id_mismatch", "possible_match", "missing_project", "orphan_project"):
        group = [item for item in items if item.kind == kind]
        if not group:
            continue
        safe_print(f"[{kind}] {len(group)}")
        for item in group:
            safe_print(f"  - {item.message}")
            if item.output:
                safe_print(f"    output : {item.output.path}")
            if item.project:
                safe_print(f"    project: {item.project.path}")
            if item.score is not None:
                safe_print(f"    score  : {item.score:.2f}")
        safe_print()

    if not items:
        safe_print("未发现编号或命名漂移。")


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查 novel_output 与 80_Projects 的项目编号/命名漂移")
    parser.add_argument("--json", action="store_true", help="输出 JSON，便于后续脚本处理")
    parser.add_argument("--include-short", action="store_true", help="纳入 novel_output/短篇小说（默认忽略，避免长篇项目治理噪音）")
    args = parser.parse_args()

    outputs = collect_output_entries(PROJECT_ROOT, include_short=args.include_short)
    projects = collect_project_entries(PROJECT_ROOT)
    items = analyze(outputs, projects)

    if args.json:
        payload = {
            "summary": {
                "novel_output_count": len(outputs),
                "project_count": len(projects),
                "issue_count": len(items),
            },
            "items": [
                {
                    "kind": item.kind,
                    "message": item.message,
                    "output": asdict(item.output) if item.output else None,
                    "project": asdict(item.project) if item.project else None,
                    "score": item.score,
                }
                for item in items
            ],
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print_report(outputs, projects, items)

    return 1 if items else 0


if __name__ == "__main__":
    raise SystemExit(main())

