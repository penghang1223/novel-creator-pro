#!/usr/bin/env python3
"""Lightweight knowledge-base governance report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.knowledge_lint import scan_markdown_status


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描 knowledge_base markdown 状态 frontmatter")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    report = scan_markdown_status(PROJECT_ROOT / "knowledge_base")
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print("知识库状态巡检")
        print(f"total={report['total']}")
        for key, count in report["summary"].items():
            print(f"{key}={count}")
        print("提示：unspecified 多不代表错误，但 active/deprecated/archive frontmatter 越完整，路由治理越稳。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

