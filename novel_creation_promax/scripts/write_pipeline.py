#!/usr/bin/env python3
"""
写作流水线

把章节写作的确定性门禁收束到一个入口：
pre  = 章节前检查 + 记忆包
post = gate + 写后审计 + 风格/OOC可选检查 + chapter passport
all  = pre + post（适合章节文件已存在时）
"""

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
    load_json,
    load_passport,
    passport_path,
    rel,
    save_json,
    save_passport,
    update_novel_state,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "novel_creation_promax" / "scripts"
MEMORY_SCRIPT = PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "scripts" / "memory_manager.py"
TRUTH_SCRIPT = SCRIPTS_DIR / "story_truth_manager.py"
PASS_THRESHOLD = 70


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def ensure_bootstrap_gate(novel_dir: Path) -> bool:
    state_path = novel_dir / "novel_state.json"
    state = load_json(state_path, {})
    gate = state.get("workflow_gate") if isinstance(state, dict) else None
    if isinstance(gate, dict) and gate.get("can_write_chapter") is True:
        return True

    report = gate.get("bootstrap_report") if isinstance(gate, dict) else ""
    print("[BLOCKED] 新书立项门禁未通过，禁止进入正文写作流水线。", file=sys.stderr)
    if report:
        print(f"[INFO] 当前门禁报告: {novel_dir / report}", file=sys.stderr)
    print(
        "[NEXT] 先运行: python novel_creation_promax/scripts/project_bootstrap_pipeline.py "
        f"seal --novel-dir \"{novel_dir}\"",
        file=sys.stderr,
    )
    return False


def ensure_prev_chapter_audited(novel_dir: Path, chapter: int, *, allow_override: bool = False) -> bool:
    """前置审计门禁：写第 N 章前，第 N-1 章必须已跑过 post_write_audit 并 pass。

    放行条件（任一即可）:
    1. chapter == 1（第一章无前置）
    2. novel_state.chapters[N-1].audit_status == "pass"
    3. 素材/audit_chN-1.json 或 audit_ch(N-1:03d).json 存在
    4. allow_override=True（由 --override-prev-audit 触发，跳过本检查）
    """
    if chapter <= 1:
        return True
    if allow_override:
        print(f"[WARN] --override-prev-audit 已启用，跳过第{chapter-1}章审计门禁。", file=sys.stderr)
        return True

    prev = chapter - 1
    state = load_json(novel_dir / "novel_state.json", {})
    chapters = state.get("chapters", {}) if isinstance(state, dict) else {}
    prev_state = chapters.get(f"{prev:03d}") if isinstance(chapters, dict) else None
    if isinstance(prev_state, dict) and prev_state.get("audit_status") == "pass":
        return True

    candidates = [
        novel_dir / "素材" / f"audit_ch{prev:03d}.json",
        novel_dir / "素材" / f"audit_ch{prev}.json",
    ]
    if any(p.exists() for p in candidates):
        return True

    print(
        f"[BLOCKED] 第{prev}章未通过 post_write_audit，禁止写第{chapter}章。",
        file=sys.stderr,
    )
    print(
        "[NEXT] 先跑: python novel_creation_promax/scripts/write_pipeline.py post "
        f"--novel-dir \"{novel_dir}\" --chapter {prev}",
        file=sys.stderr,
    )
    print(
        "[BYPASS] 紧急情况可加 --override-prev-audit 跳过本检查（仅限补审计场景）。",
        file=sys.stderr,
    )
    return False


def ensure_dirs(novel_dir: Path) -> None:
    for name in ["摘要", "素材", "记忆"]:
        (novel_dir / name).mkdir(parents=True, exist_ok=True)


def ensure_truth_files(novel_dir: Path) -> bool:
    report_path = novel_dir / "素材" / "truth_files_gate.json"
    result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "validate",
            "--novel-dir",
            str(novel_dir),
            "--output",
            str(report_path),
        ],
        "真相文件校验",
    )
    return result["returncode"] == 0


def compile_truth_inputs(novel_dir: Path, chapter: int, title: str, passport: dict[str, Any]) -> bool:
    rule_stack = novel_dir / "摘要" / f"chapter_{chapter:03d}_rule_stack.json"
    truth_brief = novel_dir / "素材" / f"chapter_{chapter:03d}_truth_brief.md"
    result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "compile",
            "--novel-dir",
            str(novel_dir),
            "--chapter",
            str(chapter),
            "--title",
            title,
            "--output",
            str(rule_stack),
            "--brief-output",
            str(truth_brief),
        ],
        "编译章节真相约束",
    )
    passport["pipeline"]["truth_compile"] = result["status"]
    passport["inputs"]["rule_stack"] = rel(rule_stack, novel_dir)
    passport["inputs"]["truth_brief"] = rel(truth_brief, novel_dir)
    return result["returncode"] == 0


def create_truth_delta_template(novel_dir: Path, chapter: int, title: str, passport: dict[str, Any]) -> bool:
    result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "delta-template",
            "--novel-dir",
            str(novel_dir),
            "--chapter",
            str(chapter),
            "--title",
            title,
        ],
        "创建章节 truth delta 模板",
    )
    delta_file = novel_dir / "摘要" / f"chapter_{chapter:03d}_truth_delta.json"
    passport["pipeline"]["truth_delta_template"] = result["status"]
    passport["inputs"]["truth_delta"] = rel(delta_file, novel_dir)
    return result["returncode"] == 0


def validate_and_apply_truth_delta(
    novel_dir: Path,
    chapter: int,
    title: str,
    passport: dict[str, Any],
    *,
    apply_changes: bool,
) -> bool:
    chapter_file = find_chapter_file(novel_dir, chapter)
    if chapter_file:
        candidates_report = novel_dir / "素材" / f"truth_delta_candidates_ch{chapter:03d}.json"
        candidates_review = novel_dir / "素材" / f"truth_delta_candidates_ch{chapter:03d}.md"
        extract_result = run_command(
            [
                sys.executable,
                str(TRUTH_SCRIPT),
                "extract-delta",
                "--novel-dir",
                str(novel_dir),
                "--chapter",
                str(chapter),
                "--title",
                title,
                "--chapter-file",
                str(chapter_file),
                "--output",
                str(candidates_report),
                "--markdown-output",
                str(candidates_review),
                "--patch-delta",
            ],
            "提取 truth delta 候选事实",
        )
        passport["pipeline"]["truth_delta_extract"] = extract_result["status"]
        passport["inputs"]["truth_delta_candidates"] = rel(candidates_report, novel_dir)
        passport["inputs"]["truth_delta_candidates_review"] = rel(candidates_review, novel_dir)
        if extract_result["returncode"] != 0:
            return False

    delta_report = novel_dir / "素材" / f"truth_delta_ch{chapter:03d}.json"
    validate_result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "validate-delta",
            "--novel-dir",
            str(novel_dir),
            "--chapter",
            str(chapter),
            "--title",
            title,
            "--output",
            str(delta_report),
            "--create-template",
        ],
        "校验章节 truth delta",
    )
    passport["pipeline"]["truth_delta"] = validate_result["status"]
    passport["inputs"]["truth_delta_report"] = rel(delta_report, novel_dir)
    if validate_result["returncode"] != 0:
        return False
    if not apply_changes:
        passport["pipeline"]["truth_sync"] = "blocked"
        print("章节基础审计未全部通过，truth delta 已校验但暂不同步到真相文件。")
        return False

    apply_report = novel_dir / "素材" / f"truth_apply_ch{chapter:03d}.json"
    apply_result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "apply-delta",
            "--novel-dir",
            str(novel_dir),
            "--chapter",
            str(chapter),
            "--output",
            str(apply_report),
        ],
        "同步章节事实到真相文件",
    )
    passport["pipeline"]["truth_sync"] = apply_result["status"]
    passport["inputs"]["truth_apply_report"] = rel(apply_report, novel_dir)
    return apply_result["returncode"] == 0


def run_normalizer(novel_dir: Path, chapter: int, title: str, chapter_file: Path, passport: dict[str, Any]) -> bool:
    json_report = novel_dir / "素材" / f"normalizer_ch{chapter:03d}.json"
    md_report = novel_dir / "素材" / f"chapter_{chapter:03d}_normalizer_task.md"
    result = run_command(
        [
            sys.executable,
            str(TRUTH_SCRIPT),
            "normalize",
            "--novel-dir",
            str(novel_dir),
            "--chapter",
            str(chapter),
            "--title",
            title,
            "--chapter-file",
            str(chapter_file),
            "--json-output",
            str(json_report),
            "--output",
            str(md_report),
        ],
        "字数归一化检查",
    )
    passport["pipeline"]["normalizer"] = result["status"]
    passport["inputs"]["normalizer_report"] = rel(json_report, novel_dir)
    if result["returncode"] != 0:
        passport["inputs"]["normalizer_task"] = rel(md_report, novel_dir)
    return result["returncode"] == 0


def run_command(cmd: list[str], description: str) -> dict[str, Any]:
    print(f"\n{'=' * 64}")
    print(description)
    print(" ".join(cmd))
    print("=" * 64)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=PROJECT_ROOT,
        env=env,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    status = "pass" if result.returncode == 0 else "fail"
    print(f"{description}: {status} (exit {result.returncode})")
    return {
        "status": status,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": cmd,
    }


def pre_check_score(report_path: Path) -> int | None:
    report = load_json(report_path, {})
    score = report.get("score")
    return score if isinstance(score, int) else None


def find_style_dna(novel_dir: Path) -> Path | None:
    candidates = [
        novel_dir / "记忆" / "style_dna_baseline.json",
        novel_dir / "记忆" / "style_dna.json",
        novel_dir / "style_dna.json",
    ]
    return next((p for p in candidates if p.exists()), None)


def find_characters_file(novel_dir: Path) -> Path | None:
    memory_dir = novel_dir / "记忆"
    for pattern in ["characters.json", "character_*.json", "人物*.json"]:
        matches = sorted(memory_dir.glob(pattern)) if memory_dir.exists() else []
        if matches:
            return matches[0]
    return None


def stage_pre(args: argparse.Namespace) -> bool:
    novel_dir = resolve_path(args.novel_dir)
    if not ensure_bootstrap_gate(novel_dir):
        return False
    if not ensure_prev_chapter_audited(
        novel_dir, args.chapter, allow_override=args.override_prev_audit
    ):
        return False
    ensure_dirs(novel_dir)
    if not ensure_truth_files(novel_dir):
        return False
    memory_dir = resolve_path(args.memory_dir) if args.memory_dir else novel_dir / "记忆"
    chapter = args.chapter
    title = args.title or f"第{chapter}章"

    chapter_file = find_chapter_file(novel_dir, chapter)
    passport = load_passport(novel_dir, chapter, title, chapter_file)
    truth_ok = compile_truth_inputs(novel_dir, chapter, title, passport)
    delta_template_ok = create_truth_delta_template(novel_dir, chapter, title, passport)

    pack_path = novel_dir / "摘要" / f"chapter_{chapter:03d}_pack.json"
    cmd = [
        sys.executable,
        str(MEMORY_SCRIPT),
        "chapter-pack",
        "--chapter",
        str(chapter),
        "--memory-dir",
        str(memory_dir),
        "--output",
        str(pack_path),
    ]
    pack_result = run_command(cmd, "生成章节记忆包")
    passport["pipeline"]["memory_pack"] = pack_result["status"]
    if pack_path.exists():
        passport["inputs"]["memory_pack"] = rel(pack_path, novel_dir)

    pre_report = novel_dir / "素材" / f"pre_check_ch{chapter:03d}.json"
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "pre_write_check.py"),
        "--novel-dir",
        str(novel_dir),
        "--chapter",
        str(chapter),
        "--title",
        title,
        "--memory-dir",
        str(memory_dir),
        "--output",
        str(pre_report),
    ]
    if args.answers_file:
        cmd.extend(["--answers-file", str(resolve_path(args.answers_file))])
    pre_result = run_command(cmd, "9问必答检查")
    score = pre_check_score(pre_report)
    passport["pipeline"]["pre_write_check"] = pre_result["status"]
    passport["inputs"]["pre_check_report"] = rel(pre_report, novel_dir)
    passport["pre_write_score"] = score

    if chapter_file and chapter_file.exists():
        text = chapter_file.read_text(encoding="utf-8")
        passport["word_count"] = count_chinese_chars(text)
        passport["chapter_file"] = rel(chapter_file, novel_dir)

    save_passport(novel_dir, chapter, passport)
    return (
        truth_ok
        and delta_template_ok
        and pre_result["returncode"] == 0
        and (pack_result["returncode"] == 0 or args.allow_missing_memory)
    )


def stage_post(args: argparse.Namespace) -> bool:
    novel_dir = resolve_path(args.novel_dir)
    if not ensure_bootstrap_gate(novel_dir):
        return False
    ensure_dirs(novel_dir)
    if not ensure_truth_files(novel_dir):
        return False
    chapter = args.chapter
    title = args.title or f"第{chapter}章"
    chapter_file = find_chapter_file(novel_dir, chapter)
    if not chapter_file:
        print(f"未找到第{chapter}章正文文件", file=sys.stderr)
        return False

    passport_file = passport_path(novel_dir, chapter)
    passport = load_passport(novel_dir, chapter, title, chapter_file)
    passport["chapter_file"] = rel(chapter_file, novel_dir)
    chapter_text = chapter_file.read_text(encoding="utf-8")
    passport["word_count"] = count_chinese_chars(chapter_text)

    gate_result = run_command(
        [
            sys.executable,
            str(SCRIPTS_DIR / "writing_gate.py"),
            "--chapter",
            str(chapter_file),
            "--novel-dir",
            str(novel_dir),
        ],
        "Writing Gate 检查",
    )
    passport["pipeline"]["writing_gate"] = gate_result["status"]

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
    prev_file = find_chapter_file(novel_dir, chapter - 1) if chapter > 1 else None
    if prev_file:
        audit_cmd.extend(["--prev-file", str(prev_file)])
    novel_state = novel_dir / "novel_state.json"
    if novel_state.exists():
        audit_cmd.extend(["--novel-state", str(novel_state)])

    audit_result = run_command(audit_cmd, "写后审计")
    passport["pipeline"]["post_write_audit"] = audit_result["status"]
    passport["inputs"]["audit_report"] = rel(audit_report, novel_dir)

    style_dna = find_style_dna(novel_dir)
    if style_dna:
        style_report = novel_dir / "素材" / f"style_ch{chapter:03d}.json"
        style_result = run_command(
            [
                sys.executable,
                str(SCRIPTS_DIR / "style_calibrator.py"),
                "--input",
                str(chapter_file),
                "--style-dna",
                str(style_dna),
                "--output",
                str(style_report),
            ],
            "风格校准",
        )
        passport["pipeline"]["style_calibration"] = style_result["status"]
        passport["inputs"]["style_report"] = rel(style_report, novel_dir)
    else:
        print("未找到 style DNA，跳过风格校准")

    characters_file = find_characters_file(novel_dir)
    if characters_file:
        character_report = novel_dir / "素材" / f"character_ch{chapter:03d}.json"
        character_result = run_command(
            [
                sys.executable,
                str(SCRIPTS_DIR / "character_consistency_checker.py"),
                "--input",
                str(chapter_file),
                "--characters",
                str(characters_file),
                "--output",
                str(character_report),
            ],
            "人物一致性检查",
        )
        passport["pipeline"]["character_consistency"] = character_result["status"]
        passport["inputs"]["character_report"] = rel(character_report, novel_dir)
    else:
        print("未找到人物档案，跳过人物一致性检查")

    summary_file = novel_dir / "摘要" / f"chapter_{chapter:03d}_summary.json"
    if summary_file.exists():
        memory_dir = resolve_path(args.memory_dir) if args.memory_dir else novel_dir / "记忆"
        sync_result = run_command(
            [
                sys.executable,
                str(MEMORY_SCRIPT),
                "sync-chapter",
                "--input",
                str(summary_file),
                "--memory-dir",
                str(memory_dir),
            ],
            "章节摘要回填",
        )
        passport["pipeline"]["memory_sync"] = sync_result["status"]
    else:
        passport["pipeline"]["memory_sync"] = "pending"
        print(f"未找到章节摘要，记忆回填保持 pending: {summary_file}")

    save_passport(novel_dir, chapter, passport)
    normalizer_ok = run_normalizer(novel_dir, chapter, title, chapter_file, passport)
    base_ok = gate_result["returncode"] == 0 and audit_result["returncode"] == 0 and normalizer_ok
    truth_delta_ok = validate_and_apply_truth_delta(
        novel_dir,
        chapter,
        title,
        passport,
        apply_changes=base_ok,
    )
    save_passport(novel_dir, chapter, passport)
    update_novel_state(
        novel_dir,
        chapter=chapter,
        word_count=passport.get("word_count"),
        audit_report=passport["inputs"].get("audit_report"),
        audit_status=passport["pipeline"].get("post_write_audit"),
        passport=rel(passport_file, novel_dir),
    )

    required_ok = base_ok and truth_delta_ok
    return required_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="小说章节写作流水线")
    parser.add_argument("stage", choices=["pre", "post", "all"], help="pre=写前, post=写后, all=两者都跑")
    parser.add_argument("--novel-dir", required=True, help="小说项目目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--title", default="", help="章节标题")
    parser.add_argument("--memory-dir", default="", help="记忆目录，默认 <novel-dir>/记忆")
    parser.add_argument("--answers-file", default="", help="9问答案 JSON 文件")
    parser.add_argument("--allow-missing-memory", action="store_true", help="记忆包生成失败时不阻断 pre 阶段")
    parser.add_argument(
        "--override-prev-audit",
        action="store_true",
        help="跳过'上一章必须 audit pass'门禁（仅限补审计/历史章节补流程）",
    )
    args = parser.parse_args()

    ok = True
    if args.stage in {"pre", "all"}:
        ok = stage_pre(args) and ok
    if args.stage in {"post", "all"}:
        ok = stage_post(args) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
