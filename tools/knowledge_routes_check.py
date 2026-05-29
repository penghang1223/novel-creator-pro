#!/usr/bin/env python3
"""Validate machine-readable knowledge routes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.jsonio import load_json


def concrete_paths(payload: dict) -> list[str]:
    paths: list[str] = []
    for item in payload.get("required", []):
        path = item.get("path", "")
        if path:
            paths.append(path)
    for route in payload.get("routes", []):
        paths.extend(path for path in route.get("files", []) if path)
    for item in payload.get("evaluations", []):
        path = item.get("file", "")
        if path:
            paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 knowledge_base/_ROUTES.json 引用文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args()

    path = PROJECT_ROOT / "knowledge_base" / "_ROUTES.json"
    payload = load_json(path, {})
    if not isinstance(payload, dict):
        print(f"[FAIL] 无法读取: {path}", file=sys.stderr)
        return 1

    missing = []
    checked = 0
    templated = []
    for ref in concrete_paths(payload):
        if "{" in ref or "}" in ref:
            templated.append(ref)
            continue
        checked += 1
        if not (PROJECT_ROOT / ref).exists():
            missing.append(ref)

    report = {
        "routes_file": str(path),
        "checked": checked,
        "templated": templated,
        "missing": missing,
        "passed": not missing,
    }
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print("知识路由检查")
        print(f"checked={checked}, templated={len(templated)}, missing={len(missing)}")
        for item in missing:
            print(f"  [MISS] {item}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

