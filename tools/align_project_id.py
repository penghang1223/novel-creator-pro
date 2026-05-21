#!/usr/bin/env python3
"""
align_project_id.py — 检测 novel_output/ 与 knowledge_base/80_Projects/ 之间的项目编号/书名漂移。

只读检测，不自动修改任何文件。输出一份对齐建议。

判定逻辑:
  novel_output/{平台}/{编号_书名} 是"事实"（已经在写正文）。
  80_Projects/{编号_书名} 是"管理"（角色/伏笔/剧情）。
  两边应该一一对应；如果编号或书名不一致就报警。

用法:
  python tools/align_project_id.py
  python tools/align_project_id.py --json    # 输出 JSON 给后续自动化用
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOVEL_OUTPUT = PROJECT_ROOT / "novel_output"
KB_PROJECTS = PROJECT_ROOT / "knowledge_base" / "80_Projects"

NUMBERED_PREFIX = re.compile(r"^(\d{3})[_-](.+)$")


def parse_dirname(name: str) -> tuple[str | None, str]:
    """把 '002_我发疯…' 拆成 (编号, 书名)。无编号返回 (None, 原名)。"""
    m = NUMBERED_PREFIX.match(name)
    if m:
        return m.group(1), m.group(2)
    return None, name


def scan_novel_output() -> dict[str, dict]:
    """返回 {书名: {id, platform, dirname, path}}"""
    result: dict[str, dict] = {}
    if not NOVEL_OUTPUT.exists():
        return result
    for platform_dir in NOVEL_OUTPUT.iterdir():
        if not platform_dir.is_dir():
            continue
        for novel_dir in platform_dir.iterdir():
            if not novel_dir.is_dir():
                continue
            # 必须看起来像本书：有正文/或novel_state.json
            if not (novel_dir / "正文").exists() and not (novel_dir / "novel_state.json").exists():
                continue
            nid, title = parse_dirname(novel_dir.name)
            key = title
            result[key] = {
                "id": nid,
                "platform": platform_dir.name,
                "dirname": novel_dir.name,
                "path": str(novel_dir.relative_to(PROJECT_ROOT)),
            }
    return result


def scan_kb_projects() -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not KB_PROJECTS.exists():
        return result
    for proj_dir in KB_PROJECTS.iterdir():
        if not proj_dir.is_dir():
            continue
        nid, title = parse_dirname(proj_dir.name)
        # 完整度判定：有伏笔追踪/角色状态/剧情节点都有则算完整
        completeness = sum(
            1
            for sub in ["伏笔追踪", "角色状态", "剧情节点", "项目索引.md", "_config.md"]
            if (proj_dir / sub).exists()
        )
        result[title] = {
            "id": nid,
            "dirname": proj_dir.name,
            "path": str(proj_dir.relative_to(PROJECT_ROOT)),
            "completeness": f"{completeness}/5",
            "complete": completeness >= 4,
        }
    return result


def diff(novels: dict[str, dict], kb: dict[str, dict]) -> dict:
    report = {
        "id_mismatch": [],       # 同书两边编号不同
        "missing_in_kb": [],     # novel_output 有，80_Projects 无
        "missing_in_output": [], # 80_Projects 有，novel_output 无
        "shell_projects": [],    # 80_Projects 完整度 < 4/5
    }
    all_titles = set(novels.keys()) | set(kb.keys())
    for title in sorted(all_titles):
        n = novels.get(title)
        k = kb.get(title)
        if n and not k:
            report["missing_in_kb"].append({
                "title": title,
                "novel_output": n,
            })
        elif k and not n:
            report["missing_in_output"].append({
                "title": title,
                "kb": k,
            })
        elif n and k:
            if n["id"] and k["id"] and n["id"] != k["id"]:
                report["id_mismatch"].append({
                    "title": title,
                    "novel_output_id": n["id"],
                    "kb_id": k["id"],
                    "novel_output_path": n["path"],
                    "kb_path": k["path"],
                })
            if not k["complete"]:
                report["shell_projects"].append({
                    "title": title,
                    "completeness": k["completeness"],
                    "kb_path": k["path"],
                })
    return report


def print_human(report: dict) -> None:
    def section(title: str, items: list, fmt) -> None:
        if not items:
            print(f"\n[OK] {title}: 无")
            return
        print(f"\n[!!] {title}: {len(items)} 项")
        for it in items:
            print("  -", fmt(it))

    section(
        "编号漂移（同书两边编号不同）",
        report["id_mismatch"],
        lambda it: f"{it['title']}: novel_output={it['novel_output_id']} ⇄ 80_Projects={it['kb_id']}\n      ({it['novel_output_path']}  vs  {it['kb_path']})",
    )
    section(
        "80_Projects 缺失（已在写但没建项目管理）",
        report["missing_in_kb"],
        lambda it: f"{it['title']}: 在 {it['novel_output'].get('platform')} 写了 → 缺 80_Projects/{it['novel_output'].get('id') or '???'}_{it['title']}/",
    )
    section(
        "novel_output 缺失（有项目管理但没动笔）",
        report["missing_in_output"],
        lambda it: f"{it['title']}: {it['kb'].get('path')}（可能是历史归档或废案）",
    )
    section(
        "空壳项目（80_Projects 完整度不足 4/5）",
        report["shell_projects"],
        lambda it: f"{it['title']}: {it['completeness']}  →  {it['kb_path']}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="项目编号对齐检测")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    novels = scan_novel_output()
    kb = scan_kb_projects()
    report = diff(novels, kb)

    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(f"扫描完成：novel_output {len(novels)} 本，80_Projects {len(kb)} 个")
        print_human(report)

    has_issue = any(report[k] for k in ["id_mismatch", "missing_in_kb", "shell_projects"])
    return 1 if has_issue else 0


if __name__ == "__main__":
    sys.exit(main())
