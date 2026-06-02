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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline_utils import (
    count_chinese_chars,
    find_chapter_file,
    load_json,
    load_passport,
    now_iso,
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
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.knowledge_routes import build_knowledge_pack, save_knowledge_pack
from novel_creation_promax.core.passport import previous_chapter_audited

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

    放行条件：
    1. chapter == 1（第一章无前置）
    2. 第 N-1 章 passport 或 novel_state 记录明确为 audit pass
    3. allow_override=True（由 --override-prev-audit 触发，跳过本检查）
    """
    if chapter <= 1:
        return True
    if allow_override:
        print(f"[WARN] --override-prev-audit 已启用，跳过第{chapter-1}章审计门禁。", file=sys.stderr)
        return True

    ok, detail = previous_chapter_audited(novel_dir, chapter)
    if ok:
        print(f"[OK] {detail}")
        return True

    prev = chapter - 1

    print(
        f"[BLOCKED] {detail}，禁止写第{chapter}章。",
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


def build_and_save_knowledge_pack(novel_dir: Path, chapter: int, title: str, passport: dict[str, Any]) -> bool:
    pack_path = novel_dir / "摘要" / f"chapter_{chapter:03d}_knowledge_pack.json"
    try:
        pack = build_knowledge_pack(
            project_root=PROJECT_ROOT,
            novel_dir=novel_dir,
            chapter=chapter,
            title=title,
        )
        save_knowledge_pack(pack, pack_path)
    except Exception as exc:
        passport["pipeline"]["knowledge_pack"] = "fail"
        print(f"[FAIL] 生成知识包失败: {exc}", file=sys.stderr)
        return False

    missing_required = [item["path"] for item in pack.get("required", []) if item.get("path") and not item.get("exists")]
    passport["pipeline"]["knowledge_pack"] = "warning" if missing_required else "pass"
    passport["inputs"]["knowledge_pack"] = rel(pack_path, novel_dir)
    print(f"[OK] 已生成章节知识包: {pack_path}")
    if missing_required:
        print("[WARN] 知识包必读项未全部落到具体文件/目录：")
        for item in missing_required:
            print(f"  - {item}")
    return True


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


# ============================================================
# P3: 章节骨架生成
# ============================================================

def generate_chapter_skeleton(
    novel_dir: Path,
    chapter: int,
    title: str,
) -> Path | None:
    """写正文前生成章节骨架，包含锚点/冲突/记忆更新清单。

    从细纲、上一章摘要、人物档案中提取信息，生成结构化骨架供写作参考。
    """
    skeleton_path = novel_dir / "素材" / f"skeleton_ch{chapter:03d}.md"
    lines = [f"# 第{chapter}章 骨架 — {title}", ""]

    # 1. 读取细纲
    outline_dir = novel_dir / "细纲"
    outline_content = ""
    if outline_dir.exists():
        for f in sorted(outline_dir.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            # 尝试找到本章对应的细纲段落
            patterns = [
                rf"第{chapter}章",
                rf"第{chapter}节",
                rf"chapter[ _]?{chapter}",
            ]
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    # 提取到下一个章节标题之间的内容
                    next_ch = re.search(r"第\d+[章节]", text[match.end():])
                    end = match.end() + next_ch.start() if next_ch else len(text)
                    outline_content = text[match.start():end].strip()
                    break
            if outline_content:
                break

    if outline_content:
        lines.append("## 细纲要点")
        lines.append(outline_content[:1000])
        lines.append("")
    else:
        lines.append("## 细纲要点")
        lines.append("> ⚠️ 未找到本章细纲，请参考总大纲。")
        lines.append("")

    # 2. 上一章摘要
    prev_summary_path = novel_dir / "摘要" / f"chapter_{chapter - 1:03d}_summary.json"
    if prev_summary_path.exists():
        prev = load_json(prev_summary_path, {})
        if isinstance(prev, dict):
            lines.append("## 上一章回顾")
            summary = prev.get("summary", prev.get("plot_summary", ""))
            if summary:
                lines.append(f"- **摘要**: {summary}")
            key_events = prev.get("key_events", [])
            if key_events:
                lines.append(f"- **关键事件**: {', '.join(str(e) for e in key_events)}")
            cliffhanger = prev.get("cliffhanger", prev.get("hook", ""))
            if cliffhanger:
                lines.append(f"- **悬念/钩子**: {cliffhanger}")
            lines.append("")

    # 3. 活跃角色状态
    memory_dir = novel_dir / "记忆"
    characters_file = find_characters_file(novel_dir)
    if characters_file:
        chars_data = load_json(characters_file, {})
        if isinstance(chars_data, dict):
            memories = chars_data.get("memories", [])
            active_chars: list[str] = []
            for mem in memories:
                data = mem.get("data", {}) if isinstance(mem, dict) else {}
                if isinstance(data, dict) and data.get("basic_info"):
                    name = data["basic_info"].get("name", "")
                    if name:
                        active_chars.append(name)
            if active_chars:
                lines.append("## 活跃角色")
                for name in active_chars[:10]:
                    lines.append(f"- {name}")
                lines.append("")

    # 4. 写作约束清单
    lines.append("## 写作约束清单")
    lines.append("")
    lines.append("### 开篇锚点（选择一种）")
    lines.append("- [ ] 动作开场：角色正在做某事")
    lines.append("- [ ] 对话开场：角色正在说某话")
    lines.append("- [ ] 环境开场：场景描写引入")
    lines.append("- [ ] 心理开场：角色内心活动")
    lines.append("- [ ] 悬念开场：抛出问题/异常")
    lines.append("")

    lines.append("### 核心冲突")
    lines.append("- [ ] 本章核心冲突已明确：______")
    lines.append("- [ ] 冲突在前300字已出现")
    lines.append("- [ ] 冲突有推进（不是原地打转）")
    lines.append("")

    lines.append("### 结尾目标（选择一种）")
    lines.append("- [ ] 悬念钩子：留下未解问题")
    lines.append("- [ ] 打脸前奏：即将反击/逆转")
    lines.append("- [ ] 新冲突引入：更大的问题出现")
    lines.append("- [ ] 情感高潮：角色情感爆发")
    lines.append("- [ ] 信息炸弹：揭示关键信息")
    lines.append("")

    lines.append("### 记忆更新清单")
    lines.append("- [ ] 角色状态变化已记录")
    lines.append("- [ ] 新出现的地点/势力已记录")
    lines.append("- [ ] 伏笔设置/回收已标注")
    lines.append("- [ ] 物理状态（钱/物品/位置）已更新")
    lines.append("")

    lines.append("### 写中自检（每300-500字）")
    lines.append("- [ ] 有没有无聊的段落？")
    lines.append("- [ ] 有没有重复的内容？")
    lines.append("- [ ] 有没有推进剧情？")
    lines.append("- [ ] 对话比例是否健康（≥25%）？")
    lines.append("- [ ] 人物行为是否符合设定？")
    lines.append("")

    skeleton_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 章节骨架已生成: {skeleton_path}")
    return skeleton_path


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
    knowledge_ok = build_and_save_knowledge_pack(novel_dir, chapter, title, passport)
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

    # 生成章节骨架
    generate_chapter_skeleton(novel_dir, chapter, title)

    return (
        knowledge_ok
        and
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
    required_ok = base_ok and truth_delta_ok
    passport["pipeline_result"] = "pass" if required_ok else "fail"
    save_passport(novel_dir, chapter, passport)
    update_novel_state(
        novel_dir,
        chapter=chapter,
        word_count=passport.get("word_count"),
        audit_report=passport["inputs"].get("audit_report"),
        audit_status=passport["pipeline"].get("post_write_audit"),
        passport=rel(passport_file, novel_dir),
        pipeline_result=passport.get("pipeline_result"),
    )

    # 审计失败时自动生成修复计划
    if not required_ok:
        print("\n[INFO] 审计未通过，自动生成修复计划...")
        generate_fix_plan(novel_dir, chapter, title)
    else:
        # 审计通过时检查是否触发阶段治理
        governance_check(novel_dir, chapter)

    return required_ok


def generate_fix_plan(novel_dir: Path, chapter: int, title: str) -> dict[str, Any] | None:
    """分析审计报告，生成结构化修复计划。

    返回 fix_plan dict，同时保存为 JSON + Markdown。
    如果审计已通过，返回 None。
    """
    audit_report_path = novel_dir / "素材" / f"audit_ch{chapter:03d}.json"
    if not audit_report_path.exists():
        print(f"[WARN] 未找到审计报告: {audit_report_path}", file=sys.stderr)
        return None

    audit = load_json(audit_report_path, {})
    if not isinstance(audit, dict):
        return None

    # 检查是否已通过
    overall = audit.get("overall_status", audit.get("status", ""))
    if overall in {"pass", "passed"}:
        print("[OK] 审计已通过，无需生成修复计划。")
        return None

    fix_actions: list[dict[str, Any]] = []

    # 1. AI 词问题
    ai_words = audit.get("ai_words", audit.get("banned_words", {}))
    if isinstance(ai_words, dict):
        found = ai_words.get("found", ai_words.get("detected", []))
        if isinstance(found, list) and found:
            fix_actions.append({
                "category": "ai_words",
                "priority": "high",
                "description": f"清除 {len(found)} 个 AI 词/禁用词",
                "details": found[:20],  # 最多列出20个
                "instruction": "逐个替换：用具体动作/感官描写替代抽象词汇。参照'每段三刀'法则，每段至少3处具体化修改。",
            })

    # 2. 对话比例问题
    dialogue = audit.get("dialogue_ratio", {})
    if isinstance(dialogue, dict):
        ratio = dialogue.get("ratio", dialogue.get("value", 0))
        threshold = dialogue.get("threshold", 0.25)
        if isinstance(ratio, (int, float)) and ratio < threshold:
            fix_actions.append({
                "category": "dialogue_ratio",
                "priority": "medium",
                "description": f"对话比例 {ratio:.1%} 低于阈值 {threshold:.0%}",
                "instruction": "将部分叙述转为对话：用角色交流替代信息传递段落，增加对话轮次。",
            })

    # 3. 风格漂移
    style_drift = audit.get("style_drift", audit.get("style_calibration", {}))
    if isinstance(style_drift, dict):
        drift_score = style_drift.get("drift_score", style_drift.get("score", 0))
        if isinstance(drift_score, (int, float)) and drift_score > 0.3:
            fix_actions.append({
                "category": "style_drift",
                "priority": "medium",
                "description": f"风格漂移分数 {drift_score:.2f} 偏高",
                "instruction": "回归基准风格：检查句式是否偏离 DNA，高频词是否被替换为同义词，语气是否一致。",
            })

    # 4. 人物一致性
    character = audit.get("character_consistency", audit.get("ooc_check", {}))
    if isinstance(character, dict):
        issues = character.get("issues", character.get("ooc_detected", []))
        if isinstance(issues, list) and issues:
            fix_actions.append({
                "category": "ooc",
                "priority": "high",
                "description": f"检测到 {len(issues)} 处人物不一致",
                "details": issues[:10],
                "instruction": "对照人物档案修正：检查行为动机、说话风格、能力边界是否符合设定。",
            })

    # 5. 字数问题
    word_count = audit.get("word_count", {})
    if isinstance(word_count, dict):
        count = word_count.get("count", word_count.get("value", 0))
        min_count = word_count.get("min", 2000)
        if isinstance(count, (int, float)) and count < min_count:
            deficit = int(min_count - count)
            fix_actions.append({
                "category": "word_count",
                "priority": "low",
                "description": f"字数 {int(count)} 不足，差 {deficit} 字",
                "instruction": f"补充 {deficit} 字：在场景描写/心理活动/对话轮次中自然扩充，不要注水。",
            })

    # 6. 乒乓球句
    pingpong = audit.get("pingpong_sentences", audit.get("dialogue_pingpong", []))
    if isinstance(pingpong, list) and pingpong:
        fix_actions.append({
            "category": "pingpong",
            "priority": "medium",
            "description": f"检测到 {len(pingpong)} 处乒乓球短句",
            "instruction": "在对话之间插入动作锚点、环境描写、心理活动，打破连续对话的单调感。",
        })

    # 7. Gate 问题
    gate = audit.get("writing_gate", {})
    if isinstance(gate, dict) and gate.get("status") == "fail":
        gate_issues = gate.get("issues", [])
        if gate_issues:
            fix_actions.append({
                "category": "gate",
                "priority": "high",
                "description": f"Writing Gate 未通过: {len(gate_issues)} 项问题",
                "details": gate_issues[:10],
                "instruction": "逐项修复 Gate 检测到的问题。",
            })

    if not fix_actions:
        print("[WARN] 审计未通过但未识别到具体问题，建议人工检查审计报告。")
        return None

    # 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    fix_actions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 9))

    fix_plan: dict[str, Any] = {
        "chapter": chapter,
        "title": title,
        "audit_report": rel(audit_report_path, novel_dir),
        "generated_at": now_iso(),
        "total_issues": len(fix_actions),
        "high_priority": sum(1 for a in fix_actions if a.get("priority") == "high"),
        "actions": fix_actions,
    }

    # 保存 JSON
    fix_json_path = novel_dir / "素材" / f"fix_plan_ch{chapter:03d}.json"
    save_json(fix_json_path, fix_plan)
    print(f"[OK] 修复计划已生成: {fix_json_path}")

    # 保存可读 Markdown
    fix_md_path = novel_dir / "素材" / f"fix_plan_ch{chapter:03d}.md"
    md_lines = [
        f"# 第{chapter}章 修复计划",
        f"\n> 生成时间: {fix_plan['generated_at']}",
        f"> 共 {fix_plan['total_issues']} 项问题（高优 {fix_plan['high_priority']} 项）\n",
    ]
    for i, action in enumerate(fix_actions, 1):
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(action.get("priority", ""), "⚪")
        md_lines.append(f"## {icon} {i}. {action['description']}")
        md_lines.append(f"\n**修复指令**: {action['instruction']}")
        if action.get("details"):
            md_lines.append("\n**涉及项**:")
            for detail in action["details"][:10]:
                md_lines.append(f"  - {detail}")
        md_lines.append("")

    fix_md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[OK] 可读修复计划: {fix_md_path}")

    return fix_plan


def stage_fix(novel_dir: Path, chapter: int, title: str) -> bool:
    """审计修复阶段：分析审计失败原因，生成修复计划。"""
    fix_plan = generate_fix_plan(novel_dir, chapter, title)
    if fix_plan is None:
        return True  # 审计已通过或无法生成计划

    # 更新 passport
    passport = load_passport(novel_dir, chapter, title, find_chapter_file(novel_dir, chapter))
    passport["pipeline"]["fix_plan"] = "generated"
    passport["inputs"]["fix_plan"] = f"素材/fix_plan_ch{chapter:03d}.json"
    save_passport(novel_dir, chapter, passport)

    print(f"\n{'=' * 50}")
    print(f"修复计划摘要:")
    print(f"  总问题数: {fix_plan['total_issues']}")
    print(f"  高优先级: {fix_plan['high_priority']}")
    for action in fix_plan["actions"]:
        icon = {"high": "!!", "medium": "!", "low": "-"}.get(action.get("priority", ""), "?")
        print(f"  [{icon}] {action['description']}")
    print(f"{'=' * 50}")
    print(f"\n下一步: 根据修复计划修改正文，然后重跑 post:")
    print(f"  python write_pipeline.py post --novel-dir \"{novel_dir}\" --chapter {chapter} --title \"{title}\"")

    return False


# ============================================================
# P1: 阶段治理审计（每 N 章自动触发）
# ============================================================

GOVERNANCE_INTERVAL = 20  # 每20章触发一次


def governance_check(novel_dir: Path, chapter: int) -> bool:
    """阶段治理审计：每 N 章触发一次全量审计，生成趋势报告。

    检查：
    1. 累计字数/章节趋势
    2. 审计通过率趋势
    3. AI 词/对话比/风格漂移的跨章趋势
    4. 角色出场频率变化
    5. 质量滑坡预警
    """
    if chapter < GOVERNANCE_INTERVAL or chapter % GOVERNANCE_INTERVAL != 0:
        return True  # 不触发

    print(f"\n{'=' * 60}")
    print(f"[GOVERNANCE] 第{chapter}章 — 触发阶段治理审计（每{GOVERNANCE_INTERVAL}章）")
    print(f"{'=' * 60}")

    # 加载所有章节审计报告
    audit_dir = novel_dir / "素材"
    audit_reports: list[dict[str, Any]] = []
    for ch_num in range(1, chapter + 1):
        report_path = audit_dir / f"audit_ch{ch_num:03d}.json"
        if report_path.exists():
            report = load_json(report_path, {})
            if isinstance(report, dict):
                report["_chapter"] = ch_num
                audit_reports.append(report)

    if len(audit_reports) < 5:
        print(f"[INFO] 审计报告不足5份（当前{len(audit_reports)}份），跳过趋势分析。")
        return True

    # --- 趋势分析 ---
    trends: dict[str, Any] = {"chapter": chapter, "analyzed_chapters": len(audit_reports)}

    # 1. 审计通过率
    pass_count = sum(
        1 for r in audit_reports
        if r.get("overall_status", r.get("status", "")) in {"pass", "passed"}
    )
    trends["audit_pass_rate"] = round(pass_count / len(audit_reports), 3)

    # 2. AI 词趋势
    ai_trend: list[dict[str, Any]] = []
    for r in audit_reports:
        ai = r.get("ai_words", r.get("banned_words", {}))
        if isinstance(ai, dict):
            found = ai.get("found", ai.get("detected", []))
            count = len(found) if isinstance(found, list) else 0
            ai_trend.append({"chapter": r["_chapter"], "ai_word_count": count})
    trends["ai_words_trend"] = ai_trend

    # 3. 对话比例趋势
    dialogue_trend: list[dict[str, Any]] = []
    for r in audit_reports:
        d = r.get("dialogue_ratio", {})
        if isinstance(d, dict):
            ratio = d.get("ratio", d.get("value", 0))
            if isinstance(ratio, (int, float)):
                dialogue_trend.append({"chapter": r["_chapter"], "ratio": round(ratio, 3)})
    trends["dialogue_ratio_trend"] = dialogue_trend

    # 4. 字数趋势
    word_trend: list[dict[str, Any]] = []
    for r in audit_reports:
        wc = r.get("word_count", {})
        if isinstance(wc, dict):
            count = wc.get("count", wc.get("value", 0))
            if isinstance(count, (int, float)):
                word_trend.append({"chapter": r["_chapter"], "word_count": int(count)})
    trends["word_count_trend"] = word_trend

    # --- 滑坡检测 ---
    warnings: list[str] = []

    # 最近5章通过率
    recent = audit_reports[-5:]
    recent_pass = sum(
        1 for r in recent
        if r.get("overall_status", r.get("status", "")) in {"pass", "passed"}
    )
    if recent_pass < 3:
        warnings.append(f"⚠️ 最近5章审计通过率 {recent_pass}/5，质量滑坡风险")

    # AI 词回升
    if len(ai_trend) >= 10:
        first_half = [x["ai_word_count"] for x in ai_trend[:len(ai_trend) // 2]]
        second_half = [x["ai_word_count"] for x in ai_trend[len(ai_trend) // 2:]]
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        if avg_second > avg_first * 1.5 and avg_second > 3:
            warnings.append(f"⚠️ AI 词密度回升: 前半 {avg_first:.1f} → 后半 {avg_second:.1f}")

    # 对话比例异常
    if dialogue_trend:
        recent_dialogue = [x["ratio"] for x in dialogue_trend[-5:]]
        avg_recent = sum(recent_dialogue) / len(recent_dialogue)
        if avg_recent < 0.15:
            warnings.append(f"⚠️ 最近5章对话比例 {avg_recent:.0%} 过低，可能变成纯叙述")
        elif avg_recent > 0.60:
            warnings.append(f"⚠️ 最近5章对话比例 {avg_recent:.0%} 过高，可能缺乏描写")

    # 字数缩水
    if word_trend and len(word_trend) >= 5:
        recent_words = [x["word_count"] for x in word_trend[-5:]]
        avg_recent = sum(recent_words) / len(recent_words)
        overall_avg = sum(x["word_count"] for x in word_trend) / len(word_trend)
        if avg_recent < overall_avg * 0.7:
            warnings.append(f"⚠️ 最近5章平均字数 {avg_recent:.0f}，低于整体均值 {overall_avg:.0f} 的 70%")

    trends["warnings"] = warnings

    # --- 保存报告 ---
    gov_report_path = novel_dir / "素材" / f"governance_ch{chapter:03d}.json"
    save_json(gov_report_path, trends)

    # 可读报告
    gov_md_path = novel_dir / "素材" / f"governance_ch{chapter:03d}.md"
    md_lines = [
        f"# 阶段治理报告 — 第{chapter}章",
        f"\n> 分析范围: 第1-{chapter}章 ({len(audit_reports)} 份审计报告)",
        f"> 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 核心指标",
        f"- 审计通过率: **{trends['audit_pass_rate']:.0%}**",
    ]

    if word_trend:
        total_words = sum(x["word_count"] for x in word_trend)
        md_lines.append(f"- 累计字数: **{total_words:,}**")
        md_lines.append(f"- 章均字数: **{total_words // len(word_trend):,}**")

    if dialogue_trend:
        avg_d = sum(x["ratio"] for x in dialogue_trend) / len(dialogue_trend)
        md_lines.append(f"- 平均对话比例: **{avg_d:.0%}**")

    if warnings:
        md_lines.append("\n## 预警")
        for w in warnings:
            md_lines.append(f"- {w}")
    else:
        md_lines.append("\n## 预警\n- 无预警，质量稳定 ✅")

    # 趋势摘要
    if ai_trend:
        md_lines.append("\n## AI 词趋势")
        for item in ai_trend[-10:]:
            bar = "█" * min(item["ai_word_count"], 20)
            md_lines.append(f"  第{item['chapter']:3d}章: {bar} {item['ai_word_count']}")

    gov_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n[GOVERNANCE] 报告已保存:")
    print(f"  JSON: {gov_report_path}")
    print(f"  Markdown: {gov_md_path}")

    if warnings:
        print(f"\n[GOVERNANCE] ⚠️ {len(warnings)} 项预警:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("\n[GOVERNANCE] ✅ 质量稳定，无预警")

    return len(warnings) == 0


def stage_act_summary(novel_dir: Path, volume: int, memory_dir: Path) -> bool:
    """聚合指定卷的所有章节摘要，生成卷级摘要并更新 novel_state.json。"""
    import json

    summary_files = sorted((novel_dir / "摘要").glob("chapter_*_summary.json"))
    if not summary_files:
        print("[WARN] 未找到任何章节摘要，跳过卷级摘要生成。", file=sys.stderr)
        return False

    chapters_data: list[dict[str, Any]] = []
    total_words = 0
    for sf in summary_files:
        data = load_json(sf, {})
        if not isinstance(data, dict):
            continue
        ch_num = data.get("chapter_number") or data.get("chapter")
        if ch_num is None:
            # 从文件名推断
            import re
            m = re.search(r"chapter_(\d+)_summary", sf.name)
            ch_num = int(m.group(1)) if m else 0
        chapters_data.append({
            "chapter": int(ch_num),
            "title": data.get("title", ""),
            "summary": data.get("summary", data.get("plot_summary", "")),
            "key_events": data.get("key_events", []),
            "word_count": data.get("word_count", 0),
        })
        total_words += int(data.get("word_count", 0) or 0)

    if not chapters_data:
        print("[WARN] 章节摘要数据为空，跳过。", file=sys.stderr)
        return False

    # 生成卷级摘要
    act_summary: dict[str, Any] = {
        "volume": volume,
        "chapter_count": len(chapters_data),
        "total_word_count": total_words,
        "chapters": chapters_data,
        "generated_at": now_iso(),
    }

    # 尝试提取卷级主题（从章节摘要中聚合）
    all_events: list[str] = []
    for ch in chapters_data:
        events = ch.get("key_events", [])
        if isinstance(events, list):
            all_events.extend(str(e) for e in events)
    if all_events:
        act_summary["aggregated_key_events"] = all_events

    act_path = novel_dir / "摘要" / f"act_{volume:02d}_summary.json"
    save_json(act_path, act_summary)
    print(f"[OK] 卷级摘要已生成: {act_path}")

    # 更新 novel_state.json
    state_path = novel_dir / "novel_state.json"
    state = load_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("act_summaries", {})
    state["act_summaries"][f"vol_{volume:02d}"] = {
        "path": rel(act_path, novel_dir),
        "chapter_count": len(chapters_data),
        "total_word_count": total_words,
        "updated_at": act_summary["generated_at"],
    }
    state["updated_at"] = act_summary["generated_at"]
    save_json(state_path, state)
    print(f"[OK] novel_state.json 已更新卷 {volume} 摘要引用")

    # 同步到记忆系统
    memory_script = PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "scripts" / "memory_manager.py"
    if memory_script.exists() and memory_dir.exists():
        # 把卷级摘要也作为"章节"同步，chapter号用 volume*1000 标记
        sync_cmd = [
            sys.executable,
            str(memory_script),
            "sync-chapter",
            "--input",
            str(act_path),
            "--memory-dir",
            str(memory_dir),
        ]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(sync_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJECT_ROOT, env=env)
        if result.returncode == 0:
            print("[OK] 卷级摘要已同步到记忆系统")
        else:
            print(f"[WARN] 卷级摘要同步到记忆系统失败: {result.stderr}", file=sys.stderr)

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="小说章节写作流水线")
    parser.add_argument("stage", choices=["pre", "post", "all", "fix", "act-summary"], help="pre=写前, post=写后, all=两者都跑, fix=生成修复计划, act-summary=卷级摘要")
    parser.add_argument("--novel-dir", required=True, help="小说项目目录")
    parser.add_argument("--chapter", type=int, default=0, help="章节号（pre/post/all 必填）")
    parser.add_argument("--title", default="", help="章节标题")
    parser.add_argument("--memory-dir", default="", help="记忆目录，默认 <novel-dir>/记忆")
    parser.add_argument("--answers-file", default="", help="9问答案 JSON 文件")
    parser.add_argument("--volume", type=int, default=0, help="卷号（act-summary 必填）")
    parser.add_argument("--allow-missing-memory", action="store_true", help="记忆包生成失败时不阻断 pre 阶段")
    parser.add_argument(
        "--override-prev-audit",
        action="store_true",
        help="跳过'上一章必须 audit pass'门禁（仅限补审计/历史章节补流程）",
    )
    args = parser.parse_args()

    if args.stage == "act-summary":
        if not args.volume:
            print("[ERROR] act-summary 需要指定 --volume", file=sys.stderr)
            return 1
        novel_dir = Path(args.novel_dir) if Path(args.novel_dir).is_absolute() else PROJECT_ROOT / args.novel_dir
        memory_dir = Path(args.memory_dir) if args.memory_dir else novel_dir / "记忆"
        return 0 if stage_act_summary(novel_dir, args.volume, memory_dir) else 1

    if args.stage in {"pre", "post", "all", "fix"} and not args.chapter:
        print("[ERROR] pre/post/all/fix 需要指定 --chapter", file=sys.stderr)
        return 1

    if args.stage == "fix":
        novel_dir = resolve_path(args.novel_dir)
        title = args.title or f"第{args.chapter}章"
        return 0 if stage_fix(novel_dir, args.chapter, title) else 1

    ok = True
    if args.stage in {"pre", "all"}:
        ok = stage_pre(args) and ok
    if args.stage in {"post", "all"}:
        ok = stage_post(args) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
