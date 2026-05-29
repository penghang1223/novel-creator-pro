#!/usr/bin/env python3
"""
项目自检脚本

检查项：
  1. 必读记忆文件存在性
  2. 核心脚本路径可执行性
  3. 密钥是否误提交到 git
  4. README 示例是否违反禁词（"默"字人名）
  5. novel_output 是否正确忽略
  6. AGENTS.md 路径漂移（.Codex 残留）
  7. SKILL.md 命令路径正确性
  8. 临时脚本是否还在根目录
  9. 发布目录结构完整性
  10. SKILL.md frontmatter 格式
  11. 引用文件存在性
  12. 功能编号一致性（CLAUDE.md vs SKILL.md）
  13. agents/openai.yaml 存在性
  14. novel_creation_promax skill 自检

用法:
    python tools/health_check.py
"""

import os
import re
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.jsonio import load_json
from novel_creation_promax.core.knowledge_routes import load_routes
from novel_creation_promax.core.project_registry import build_registry

ERRORS = []
WARNINGS = []


def error(msg):
    ERRORS.append(msg)
    print(f"  [FAIL] {msg}")


def warning(msg):
    WARNINGS.append(msg)
    print(f"  [WARN] {msg}")


def ok(msg):
    print(f"  [OK]   {msg}")


def safe_print(text):
    print(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))


def check_memory_files():
    print("\n[1/17] 必读记忆文件")
    files = [
        "MEMORY.md",
        ".claude/memory/decisions/preferences.md",
        ".claude/memory/active_novels/progress.md",
        ".claude/memory/feedback/corrections.md",
        ".claude/memory/feedback/no-mer-names.md",
    ]
    for f in files:
        path = PROJECT_ROOT / f
        if path.exists():
            ok(f"{f}")
        else:
            error(f"缺失: {f}")


def check_scripts():
    print("\n[2/17] 核心脚本可执行性")
    scripts = [
        "novel_creation_promax/scripts/generate_cover.py",
        "novel_creation_promax/scripts/pre_write_check.py",
        "novel_creation_promax/scripts/post_write_audit.py",
        "novel_creation_promax/scripts/audit_pipeline.py",
        "novel_creation_promax/scripts/project_bootstrap_pipeline.py",
        "novel_creation_promax/scripts/write_pipeline.py",
        "novel_creation_promax/scripts/skill_health_check.py",
        "novel_creation_promax/scripts/name_generator.py",
        "novel_creation_promax/novel-memory-pro/scripts/memory_manager.py",
        "novel_creation_promax/scripts/style_dna_extractor.py",
        "novel_creation_promax/scripts/style_calibrator.py",
        "novel_creation_promax/scripts/plot_continuity_checker.py",
        "scripts/sync_to_fanqie.py",
        "tools/file_reference_counter.py",
        "tools/align_project_id.py",
        "tools/build_project_registry.py",
        "tools/knowledge_routes_check.py",
        "tools/knowledge_lint.py",
    ]
    for s in scripts:
        path = PROJECT_ROOT / s
        if path.exists():
            ok(f"{s}")
        else:
            error(f"缺失: {s}")


def check_secrets_in_git():
    print("\n[3/17] 密钥误提交检查")
    tracked_files = ["config.toml", "cc-connect-config.toml"]
    for f in tracked_files:
        result = subprocess.run(
            ["git", "ls-files", f],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.stdout.strip():
            error(f"{f} 仍在 git 跟踪中（含明文密钥）")
        else:
            ok(f"{f} 已取消跟踪")


def check_readme_banned_words():
    print("\n[4/17] README 禁词检查")
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        error("README.md 不存在")
        return

    content = readme.read_text(encoding="utf-8")
    # 检查是否包含"默"字作为人名的一部分
    # 简单检查：引号/书名号内或作为独立词出现的"默"
    patterns = [
        r'["\'][^"\']*默[^"\']*["\']',  # 引号内
        r'叫\s*\w*默\w*',               # "叫 xxx默xxx"
        r'主角叫[^，。\n]*默',           # "主角叫...默"
    ]
    found = False
    for pat in patterns:
        matches = re.findall(pat, content)
        for m in matches:
            if "默" in m:
                warning(f"README 中疑似含'默'字人名: {m}")
                found = True
    if not found:
        ok("README 未检测到含'默'字人名")


def check_gitignore():
    print("\n[5/17] .gitignore 检查")
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        error(".gitignore 不存在")
        return

    content = gitignore.read_text(encoding="utf-8")
    required = ["novel_output/", ".env", ".env.*", "config.toml", "cc-connect-config.toml"]
    for item in required:
        if item in content:
            ok(f"{item} 已忽略")
        else:
            error(f"{item} 未在 .gitignore 中")


def check_agents_paths():
    print("\n[6/17] AGENTS.md 路径漂移检查")
    agents = PROJECT_ROOT / "AGENTS.md"
    if not agents.exists():
        error("AGENTS.md 不存在")
        return

    content = agents.read_text(encoding="utf-8")
    if ".Codex" in content:
        error("AGENTS.md 中仍有 .Codex 路径残留")
    else:
        ok("AGENTS.md 无 .Codex 残留")


def check_skill_paths():
    print("\n[7/17] SKILL.md 命令路径检查")
    skill = PROJECT_ROOT / "novel_creation_promax" / "SKILL.md"
    if not skill.exists():
        error("SKILL.md 不存在")
        return

    content = skill.read_text(encoding="utf-8")
    # 检查是否还有错误路径（不以 novel_creation_promax/ 开头的 scripts/xxx.py）
    bad_patterns = [
        r'python scripts/(?!sync_to_fanqie)',
        r'`scripts/[^`]+\.py`',
    ]
    found = False
    for pat in bad_patterns:
        matches = re.findall(pat, content)
        for m in matches:
            warning(f"SKILL.md 中疑似错误路径: {m}")
            found = True
    if not found:
        ok("SKILL.md 命令路径正确")


def check_root_temp_scripts():
    print("\n[8/17] 根目录临时脚本检查")
    temp_patterns = ["debug_*.py", "tmp_*.py"]
    found = False
    for pat in temp_patterns:
        for f in PROJECT_ROOT.glob(pat):
            error(f"根目录存在临时脚本: {f.name}")
            found = True
    if not found:
        ok("根目录无临时脚本")


def check_publish_dirs():
    print("\n[9/17] 发布目录结构检查")
    platforms = ["auto_publish/fanqie_auto_publish", "auto_publish/qidian_auto_publish", "auto_publish/zhihu_auto_publish", "auto_publish/qimao_auto_publish"]
    for p in platforms:
        path = PROJECT_ROOT / p
        if not path.exists():
            error(f"{p}/ 目录不存在")
            continue
        if not path.is_dir():
            error(f"{p} 不是目录（可能是损坏的链接）")
            continue
        readme = path / "README.md"
        if readme.exists():
            ok(f"{p}/ 结构正常")
        else:
            warning(f"{p}/ 缺少 README.md")

    # 检查 publish_system 是否还存在
    ps = PROJECT_ROOT / "publish_system"
    if ps.exists():
        warning("publish_system/ 目录仍存在（建议删除或合并）")
    else:
        ok("publish_system/ 已清理")


def check_frontmatter():
    print("\n[10/17] SKILL.md frontmatter 格式")
    skill = PROJECT_ROOT / "novel_creation_promax" / "SKILL.md"
    if not skill.exists():
        error("SKILL.md 不存在")
        return

    content = skill.read_text(encoding="utf-8")
    if content.startswith("---"):
        ok("SKILL.md frontmatter 格式正确（有 --- 包裹）")
    else:
        error("SKILL.md frontmatter 缺少 --- 包裹")

    # 也检查 novel-memory-pro/SKILL.md
    mm_skill = PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "SKILL.md"
    if mm_skill.exists():
        mm_content = mm_skill.read_text(encoding="utf-8")
        if mm_content.startswith("---"):
            ok("novel-memory-pro/SKILL.md frontmatter 格式正确")
        else:
            error("novel-memory-pro/SKILL.md frontmatter 缺少 --- 包裹")


def check_references():
    print("\n[11/17] 引用文件存在性检查")
    skill = PROJECT_ROOT / "novel_creation_promax" / "SKILL.md"
    if not skill.exists():
        error("SKILL.md 不存在")
        return

    content = skill.read_text(encoding="utf-8")
    refs = set()
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", content):
        refs.add(match.group(1))
    for match in re.finditer(r"`([^`\n]+)`", content):
        value = match.group(1)
        if value.startswith("python "):
            continue
        if value.startswith(("novel_creation_promax/", "references/", "docs/", "assets/", "novel-memory-pro/", "review-skill/", "knowledge_base/")):
            refs.add(value)

    missing = 0
    checked = 0
    for ref_path in sorted(refs):
        if '{' in ref_path or '*' in ref_path or "..." in ref_path:
            continue
        if ref_path.startswith(("http://", "https://")):
            continue
        if ref_path in {"novel_state.json"}:
            continue
        if ref_path.startswith("novel_creation_promax/"):
            full_path = PROJECT_ROOT / ref_path
        elif ref_path.startswith(("references/", "docs/", "assets/", "novel-memory-pro/", "review-skill/")):
            full_path = PROJECT_ROOT / "novel_creation_promax" / ref_path
        elif ref_path.startswith("knowledge_base/"):
            full_path = PROJECT_ROOT / ref_path
        else:
            continue
        checked += 1
        if not full_path.exists():
            warning(f"引用文件不存在: {ref_path}")
            missing += 1

    if missing == 0:
        ok(f"所有 {checked} 个引用文件检查通过")
    else:
        ok(f"引用检查完成: {checked - missing}/{checked} 存在")


def check_numbering_consistency():
    print("\n[12/17] 功能编号一致性检查")
    claude = PROJECT_ROOT / "CLAUDE.md"
    skill = PROJECT_ROOT / "novel_creation_promax" / "SKILL.md"

    if not claude.exists() or not skill.exists():
        error("CLAUDE.md 或 SKILL.md 不存在")
        return

    claude_content = claude.read_text(encoding="utf-8")
    skill_content = skill.read_text(encoding="utf-8")

    # 提取关键功能的编号
    # CLAUDE.md: "正文润色 [N]"
    claude_match = re.search(r'正文润色 \[(\d+)\].*审稿评估 \[(\d+)\].*短篇创作 \[(\d+)\]', claude_content)
    # SKILL.md: "[N] 正文润色"
    skill_match = re.search(r'\[(\d+)\].*正文润色', skill_content)

    if claude_match and skill_match:
        claude_nums = (int(claude_match.group(1)), int(claude_match.group(2)), int(claude_match.group(3)))
        skill_num = int(skill_match.group(1))
        if claude_nums[0] == skill_num:
            ok(f"正文润色编号一致: [{skill_num}]")
        else:
            error(f"正文润色编号不一致: CLAUDE.md=[{claude_nums[0]}], SKILL.md=[{skill_num}]")
    else:
        warning("无法提取功能编号进行对比")


def check_agents_yaml():
    print("\n[13/17] agents/openai.yaml 检查")
    agents_yaml = PROJECT_ROOT / "novel_creation_promax" / "agents" / "openai.yaml"
    if agents_yaml.exists():
        ok("agents/openai.yaml 存在")
    else:
        warning("agents/openai.yaml 不存在（如需注册 Codex skill 建议补充）")


def check_skill_health_script():
    print("\n[14/17] novel_creation_promax skill 自检")
    script = PROJECT_ROOT / "novel_creation_promax" / "scripts" / "skill_health_check.py"
    if not script.exists():
        error("novel_creation_promax/scripts/skill_health_check.py 不存在")
        return
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.stdout:
        safe_print(result.stdout)
    if result.stderr:
        print(result.stderr.encode(sys.stderr.encoding or "utf-8", errors="replace").decode(sys.stderr.encoding or "utf-8", errors="replace"), file=sys.stderr)
    if result.returncode == 0:
        ok("skill 自检通过")
    else:
        error(f"skill 自检失败（exit {result.returncode}）")


def check_core_package():
    print("\n[15/17] core 共享包检查")
    required = [
        "novel_creation_promax/core/__init__.py",
        "novel_creation_promax/core/jsonio.py",
        "novel_creation_promax/core/paths.py",
        "novel_creation_promax/core/passport.py",
        "novel_creation_promax/core/knowledge_routes.py",
        "novel_creation_promax/core/project_registry.py",
    ]
    for item in required:
        if (PROJECT_ROOT / item).exists():
            ok(item)
        else:
            error(f"缺失: {item}")


def check_knowledge_routes():
    print("\n[16/17] 机器可读知识路由检查")
    routes = load_routes(PROJECT_ROOT)
    if not routes:
        error("knowledge_base/_ROUTES.json 不存在或无法读取")
        return
    missing = []
    checked = 0
    for item in routes.get("required", []):
        path = item.get("path", "")
        if not path or "{" in path or "}" in path:
            continue
        checked += 1
        if not (PROJECT_ROOT / path).exists():
            missing.append(path)
    for route in routes.get("routes", []):
        for path in route.get("files", []):
            if "{" in path or "}" in path:
                continue
            checked += 1
            if not (PROJECT_ROOT / path).exists():
                missing.append(path)
    for item in routes.get("evaluations", []):
        path = item.get("file", "")
        if path:
            checked += 1
            if not (PROJECT_ROOT / path).exists():
                missing.append(path)
    if missing:
        for path in missing:
            error(f"知识路由引用不存在: {path}")
    else:
        ok(f"知识路由引用检查通过（{checked} 项）")


def check_project_registry_builder():
    print("\n[17/17] 项目注册表生成检查")
    registry = build_registry(PROJECT_ROOT)
    summary = registry.get("summary", {})
    if summary.get("project_count", 0) > 0:
        ok(
            "registry 可生成: "
            f"projects={summary.get('project_count')}, "
            f"outputs={summary.get('novel_output_count')}, "
            f"80_Projects={summary.get('knowledge_project_count')}, "
            f"issues={summary.get('issue_count')}"
        )
    else:
        warning("registry 生成结果为空")


def main():
    print("=" * 50)
    print("小说创作 Pro Max — 项目健康检查")
    print("=" * 50)

    check_memory_files()
    check_scripts()
    check_secrets_in_git()
    check_readme_banned_words()
    check_gitignore()
    check_agents_paths()
    check_skill_paths()
    check_root_temp_scripts()
    check_publish_dirs()
    check_frontmatter()
    check_references()
    check_numbering_consistency()
    check_agents_yaml()
    check_skill_health_script()
    check_core_package()
    check_knowledge_routes()
    check_project_registry_builder()

    print("\n" + "=" * 50)
    print(f"结果: {len(ERRORS)} 错误, {len(WARNINGS)} 警告")
    if ERRORS:
        print("\n错误项:")
        for e in ERRORS:
            print(f"  - {e}")
    if WARNINGS:
        print("\n警告项:")
        for w in WARNINGS:
            print(f"  - {w}")
    print("=" * 50)

    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
