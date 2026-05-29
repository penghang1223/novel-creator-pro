#!/usr/bin/env python3
"""Build knowledge_base/80_Projects/_PROJECT_REGISTRY.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.project_registry import save_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="生成项目注册表（novel_output ⇄ 80_Projects）")
    parser.add_argument("--include-short", action="store_true", help="纳入 novel_output/短篇小说")
    parser.add_argument("--print", action="store_true", dest="print_json", help="同时打印 JSON")
    args = parser.parse_args()

    registry = save_registry(PROJECT_ROOT, include_short=args.include_short)
    path = PROJECT_ROOT / "knowledge_base" / "80_Projects" / "_PROJECT_REGISTRY.json"
    if args.print_json:
        json.dump(registry, sys.stdout, ensure_ascii=False, indent=2)
        print()
    print(f"项目注册表已生成: {path}")
    print(
        "summary: "
        f"projects={registry['summary']['project_count']}, "
        f"outputs={registry['summary']['novel_output_count']}, "
        f"80_Projects={registry['summary']['knowledge_project_count']}, "
        f"issues={registry['summary']['issue_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

