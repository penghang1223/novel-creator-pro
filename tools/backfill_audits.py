#!/usr/bin/env python3
"""
backfill_audits.py — 批量为已写章节补跑 post_write_audit。

适用于历史章节：novel_output/番茄/002_我发疯后… 已经写到第43章，但只跑过 ch22-32 的审计。
用本脚本一次性补完。

关键点：
  - 直接调用 post_write_audit.py，不走 write_pipeline.post，避免触发不需要的 style/character 检查
  - 自动跳过已存在 audit_chNNN.json 的章节（除非 --force）
  - 同时更新 novel_state.json.chapters[NNN].audit_status

用法:
  python tools/backfill_audits.py --novel-dir "novel_output/番茄/002_我发疯后全世界都正常了"
  python tools/backfill_audits.py --novel-dir "..." --from-chapter 1 --to-chapter 21
  python tools/backfill_audits.py --novel-dir "..." --force      # 已有也重跑
  python tools/backfill_audits.py --novel-dir "..." --dry-run    # 只打印计划，不执行
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "novel_creation_promax" / "scripts"
AUDIT_SCRIPT = SCRIPTS_DIR / "post_write_audit.py"

CH_PATTERNS = [
    re.compile(r"第0*(\d+)章"),
    re.compile(r"^0*(\d+)[_-]"),
    re.compile(r"chapter_0*(\d+)", re.IGNORECASE),
]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def infer_chapter(path: Path) -> int | None:
    name = path.stem
    for pat in CH_PATTERNS:
        m = pat.search(name)
        if m:
            return int(m.group(1))
    return None


def list_chapters(novel_dir: Path) -> list[tuple[int, Path]]:
    body = novel_dir / "正文"
    if not body.exists():
        return []
    items = []
    for p in body.glob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md", ".txt"}:
            continue
        n = infer_chapter(p)
        if n is not None:
            items.append((n, p))
    return sorted(items)


def find_chapter(items: list[tuple[int, Path]], n: int) -> Path | None:
    for ch, p in items:
        if ch == n:
            return p
    return None


def update_state(novel_dir: Path, chapter: int, audit_report: str, status: str) -> None:
    state_path = novel_dir / "novel_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    state.setdefault("chapters", {})
    state.setdefault("audit_history", [])
    key = f"{chapter:03d}"
    ch = state["chapters"].setdefault(key, {})
    ch["audit_report"] = audit_report
    ch["audit_status"] = status
    ch["updated_at"] = now_iso()
    state["audit_history"].append({
        "chapter": chapter,
        "report": audit_report,
        "status": status,
        "updated_at": now_iso(),
        "source": "backfill",
    })
    state["updated_at"] = now_iso()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_audit(novel_dir: Path, chapter: int, chapter_file: Path, prev_file: Path | None) -> tuple[int, Path]:
    audit_report = novel_dir / "素材" / f"audit_ch{chapter:03d}.json"
    audit_report.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(AUDIT_SCRIPT),
        "--chapter-file", str(chapter_file),
        "--title", chapter_file.stem,
        "--output", str(audit_report),
    ]
    if prev_file:
        cmd.extend(["--prev-file", str(prev_file)])
    state_path = novel_dir / "novel_state.json"
    if state_path.exists():
        cmd.extend(["--novel-state", str(state_path)])
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    return r.returncode, audit_report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--novel-dir", required=True)
    ap.add_argument("--from-chapter", type=int, default=1)
    ap.add_argument("--to-chapter", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="已有 audit 也重跑")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    novel_dir = Path(args.novel_dir)
    if not novel_dir.is_absolute():
        novel_dir = PROJECT_ROOT / novel_dir
    if not novel_dir.exists():
        print(f"[FATAL] 目录不存在: {novel_dir}", file=sys.stderr)
        return 2

    chapters = list_chapters(novel_dir)
    if not chapters:
        print("[FATAL] 没找到章节文件（正文/ 目录）", file=sys.stderr)
        return 2

    max_ch = chapters[-1][0]
    to_ch = args.to_chapter or max_ch
    targets = [(n, p) for n, p in chapters if args.from_chapter <= n <= to_ch]

    print(f"目标章节: {args.from_chapter}-{to_ch}，共 {len(targets)} 章。")
    print(f"小说目录: {novel_dir.relative_to(PROJECT_ROOT)}")

    skipped, ran, passed, failed = 0, 0, 0, 0
    for n, p in targets:
        audit_report = novel_dir / "素材" / f"audit_ch{n:03d}.json"
        if audit_report.exists() and not args.force:
            print(f"  [skip] 第{n}章 已有 audit → {audit_report.name}")
            skipped += 1
            continue
        prev = find_chapter(chapters, n - 1)
        print(f"  [run ] 第{n}章 {p.name}")
        if args.dry_run:
            ran += 1
            continue
        rc, report_path = run_audit(novel_dir, n, p, prev)
        status = "pass" if rc == 0 else "fail"
        update_state(novel_dir, n, str(report_path.relative_to(novel_dir)), status)
        ran += 1
        if rc == 0:
            passed += 1
        else:
            failed += 1

    print(f"\n汇总：跳过 {skipped}，执行 {ran}，通过 {passed}，失败 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
