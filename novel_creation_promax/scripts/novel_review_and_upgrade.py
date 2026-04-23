#!/usr/bin/env python3
"""
完结复盘升级脚本 (Post-Novel Review & Upgrade)

当一本小说完结时自动运行此脚本：
1. 扫描所有章节和审查报告，提取出现过的问题
2. 对比现有红线/闭环规则库，识别"出现过但未覆盖"的问题
3. 生成新规则追加建议
4. 更新 AI 词黑名单和限制词表
5. 输出复盘升级报告

用法:
    python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/番茄/004_我在修仙界开网约车/"
    python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/番茄/004_我在修仙界开网约车/" --upgrade  # 自动写入新规则
    python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/" --kb-dir "/path/to/knowledge_base/"
"""

import argparse
import glob
import json
import re
import sys
import os
from collections import Counter
from pathlib import Path
from datetime import datetime

# ============================================================
# 已知规则库 — 从红线系统和闭环质量控制文档中提取
# ============================================================

# 当前已知的AI禁止词 (红线13)
KNOWN_BANNED = {"像是": 0}

# 当前已知的AI限制词 (红线14): word -> (单章上限, 20章总量上限)
KNOWN_LIMITED = {
    "像(比喻)": (1, 10),
    "突然": (1, 5),
    "微微": (1, 5),
    "沉默": (1, 5),
    "天旋地转": (0, 2),
    "感觉": (1, 10),
    "嘴角": (1, 5),
}

# 当前已知的浓度红线 (红线15)
KNOWN_CONCENTRATION_PER_WORD = 3  # 单AI词单章 >= 3次
KNOWN_TOTAL_AI_PER_CHAPTER = 10   # 全章AI词总数 >= 10

# 当前已知的其他规则
KNOWN_RULES = {
    "dialogue_ratio_min": 0.25,       # 对话比例 >= 25%
    "repeat_ratio_max": 0.20,          # 相邻章节重复度 <= 20%
    "title_keyword_required": True,    # 标题关键词必须在正文出现
    "char_filler_ratio_max": 0.20,     # 角色填充词占比 <= 20%
    "first_300_conflict": True,        # 前300字必须有冲突/悬念/动作
}

# ============================================================
# 常见AI词模式 — 用于从全文自动检测
# ============================================================

# 已知的AI常用词/短语
AI_WORD_CANDIDATES = [
    "像是", "仿佛", "宛如", "如同", "犹如",
    "像", "好像", "似乎", "好似",
    "突然", "忽然", "猛然", "骤然",
    "微微", "轻轻", "缓缓", "渐渐", "慢慢",
    "沉默", "安静", "寂静",
    "感觉", "觉得", "感受到",
    "嘴角", "嘴角上扬", "嘴角扬起",
    "天旋地转", "头晕目眩",
    "心跳加速", "心跳漏了一拍",
    "深吸一口气", "倒吸一口凉气",
    "瞳孔收缩", "瞳孔放大", "瞳孔骤缩",
    "眼眶微红", "眼眶泛红",
    "不自觉地", "下意识地",
    "不由自主地",
    "那一刻", "这一刻", "一瞬间",
    "如同……一般", "仿佛……一样",
    "带着一丝", "带着一抹",
    "泛起", "浮现", "浮起",
]

# 已知的AI描写模板模式
AI_PATTERN_CANDIDATES = [
    r"如同.*?一般",
    r"仿佛.*?一样",
    r"宛如.*?般",
    r"犹如.*?般",
    r"像是.*?一样",
    r"带着一丝.*?",
    r"带着一抹.*?",
    r"不自觉地.*?",
    r"下意识地.*?",
    r"不由自主地.*?",
    r".*?的.*?如同.*?",
    r".*?的.*?仿佛.*?",
]

# 已知的AI对话模板
AI_DIALOGUE_PATTERNS = [
    r"^嗯$",
    r"^哦$",
    r"^啊$",
    r"^好$",
    r"^行$",
]

# ============================================================
# 数据收集
# ============================================================

def load_review_reports(novel_dir: str) -> list:
    """扫描 novel_dir 下的所有审查报告 JSON 文件。"""
    reports = []
    for pattern in ["**/full_review_report.json", "**/*_report.json", "**/review_pack.json"]:
        for fpath in glob.glob(os.path.join(novel_dir, pattern), recursive=True):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 有些报告是list类型，包装成dict
                if isinstance(data, list):
                    data = {"items": data}
                data["_source"] = fpath
                reports.append(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return reports


def load_novel_state(novel_dir: str) -> dict:
    """加载 novel_state.json（如果存在）。"""
    state_path = os.path.join(novel_dir, "novel_state.json")
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_all_chapters(novel_dir: str) -> list:
    """加载所有章节正文。"""
    chapters = []
    # 支持 正文/ 或 文稿/ 目录
    for subdir in ["正文", "文稿"]:
        pattern = os.path.join(novel_dir, subdir, "第*章*.md")
        files = sorted(glob.glob(pattern))
        if not files:
            pattern = os.path.join(novel_dir, subdir, "第*章*.txt")
            files = sorted(glob.glob(pattern))
        for fpath in files:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    text = f.read()
                # 提取章节号
                m = re.search(r'第([0-9零一二三四五六七八九十百]+)章', os.path.basename(fpath))
                ch_num = m.group(1) if m else "?"
                chapters.append({
                    "file": fpath,
                    "chapter_num": ch_num,
                    "text": text,
                })
            except (UnicodeDecodeError, IOError):
                pass
    return chapters


# ============================================================
# 问题分析
# ============================================================

def extract_issues_from_reports(reports: list) -> list:
    """
    从审查报告中提取所有被标记的问题。
    返回 [(问题描述, 严重度, 出现章节), ...]
    """
    issues = []
    for report in reports:
        # 尝试提取常见问题格式
        if "issues" in report:
            for issue in report["issues"]:
                issues.append((
                    issue.get("description", str(issue)),
                    issue.get("severity", issue.get("严重度", "unknown")),
                    issue.get("chapter", issue.get("章节", "unknown")),
                ))
        if "warnings" in report:
            for w in report["warnings"]:
                issues.append((str(w), "warning", "unknown"))
        # 如果报告有 basic_stats，检查AI词超标
        if "basic_stats" in report and "chapters" in report.get("basic_stats", {}):
            for ch_data in report["basic_stats"].get("chapters", []):
                ai_words = ch_data.get("ai_words", {})
                for word, count in ai_words.items():
                    if count >= 3:
                        issues.append((
                            f"'{word}' 单章出现 {count} 次 (浓度超标)",
                            "P1",
                            ch_data.get("chapter", "unknown"),
                        ))
                if ch_data.get("ai_total", 0) >= 10:
                    issues.append((
                        f"AI词总数 {ch_data['ai_total']} (AI味过重)",
                        "P1",
                        ch_data.get("chapter", "unknown"),
                    ))
                if ch_data.get("dialogue_ratio", 1) < 0.25:
                    issues.append((
                        f"对话比例 {ch_data['dialogue_ratio']:.1%} (低于25%)",
                        "P2",
                        ch_data.get("chapter", "unknown"),
                    ))
    return issues


def extract_issues_from_chapters(chapters: list) -> dict:
    """
    从所有章节正文中自动检测AI词使用模式。
    返回 {word: [(chapter_num, count), ...]}
    """
    word_usage = {}
    for ch in chapters:
        text = ch["text"]
        for word in AI_WORD_CANDIDATES:
            # 特殊处理"像"：排除非比喻用法
            if word == "像":
                cleaned = text
                for pattern in [
                    '偶像', '想象', '想像', '好像', '不像', '像自己', '像她', '像他',
                    '像我', '像你', '像我们', '像他们', '像什么', '像这样', '像那样',
                ]:
                    cleaned = cleaned.replace(pattern, 'XXX')
                count = cleaned.count('像')
            else:
                count = text.count(word)
            if count > 0:
                if word not in word_usage:
                    word_usage[word] = []
                word_usage[word].append((ch["chapter_num"], count))
    return word_usage


def extract_template_patterns(chapters: list) -> dict:
    """
    从正文中检测AI模板化描写模式。
    返回 {pattern: [(chapter_num, count), ...]}
    """
    pattern_usage = {}
    for ch in chapters:
        text = ch["text"]
        for pat in AI_PATTERN_CANDIDATES:
            matches = re.findall(pat, text)
            if matches:
                if pat not in pattern_usage:
                    pattern_usage[pat] = []
                pattern_usage[pat].append((ch["chapter_num"], len(matches)))
    return pattern_usage


# ============================================================
# 新规则识别
# ============================================================

def identify_new_rules(
    report_issues: list,
    word_usage: dict,
    pattern_usage: dict,
    known_banned: dict,
    known_limited: dict,
    known_concentration: int,
) -> list:
    """
    对比已知规则，识别"出现过但未覆盖"的问题，生成新规则建议。

    返回 [{
        "rule_type": "banned" | "limited" | "concentration" | "new_pattern",
        "description": "...",
        "evidence": "...",
        "proposed_rule": "...",
        "confidence": 0.0-1.0,
    }]
    """
    new_rules = []

    # 1. 从报告问题中识别未覆盖的问题
    issue_descriptions = [desc.lower() for desc, _, _ in report_issues]

    # 检查是否有词汇被频繁标记但不在已知规则中
    for word, usages in word_usage.items():
        if word in known_banned or word in known_limited or word == "像(比喻)":
            continue

        # 统计该词的总使用量和超标章节数
        total = sum(count for _, count in usages)
        overload_chapters = [(ch, count) for ch, count in usages if count >= known_concentration]

        # 如果该词在报告中被明确标记过问题，或者超标章节>=3章
        mentioned_in_report = any(word in desc for desc, _, _ in report_issues)

        if mentioned_in_report or len(overload_chapters) >= 3:
            # 提出新规则
            max_per_chapter = max(count for _, count in usages)
            avg_per_chapter = total / len(usages) if usages else 0

            if mentioned_in_report or max_per_chapter >= 5:
                # 加入限制词表
                per_chapter_limit = max(1, int(avg_per_chapter))
                total_20_limit = per_chapter_limit * 5  # 20章上限 = 单章 * 5
                new_rules.append({
                    "rule_type": "limited",
                    "description": f"'{word}' 全书出现 {total} 次，{len(overload_chapters)} 章超标",
                    "evidence": f"最高单章: {max_per_chapter}次, 平均: {avg_per_chapter:.1f}次",
                    "proposed_rule": f"严格限制词: '{word}' (单章≤{per_chapter_limit}, 20章≤{total_20_limit})",
                    "confidence": 0.8 if mentioned_in_report else 0.6,
                })
            elif len(overload_chapters) >= 3:
                # 加入浓度关注词
                new_rules.append({
                    "rule_type": "concentration_watch",
                    "description": f"'{word}' 在 {len(overload_chapters)} 章中浓度超标",
                    "evidence": ", ".join([f"ch{ch}:{c}次" for ch, c in overload_chapters[:5]]),
                    "proposed_rule": f"关注词: '{word}' — 后续小说中注意单章≤{known_concentration}次",
                    "confidence": 0.5,
                })

    # 2. 从模板模式中识别新问题
    for pat, usages in pattern_usage.items():
        total = sum(count for _, count in usages)
        if total < 20:
            continue
        # 检查是否已有规则覆盖
        pat_covered = any(
            pat.replace(".*?", "").replace(".*", "").replace(r"\?", "") in known_word
            for known_word in list(known_banned.keys()) + list(known_limited.keys())
        )
        if not pat_covered:
            new_rules.append({
                "rule_type": "new_pattern",
                "description": f"模板模式 '{pat}' 全书出现 {total} 次",
                "evidence": ", ".join([f"ch{ch}:{c}次" for ch, c in usages[:5]]),
                "proposed_rule": f"写作时避免模板: '{pat}'",
                "confidence": 0.4,
            })

    # 3. 从报告问题中提取新的质量规则
    rule_keywords = {
        "对话": {"type": "dialogue", "desc": "对话质量问题"},
        "重复": {"type": "repeat", "desc": "章节重复问题"},
        "标题": {"type": "title_match", "desc": "标题匹配问题"},
        "人设": {"type": "character", "desc": "人物设定问题"},
        "货币": {"type": "consistency", "desc": "设定一致性问题"},
        "节奏": {"type": "pacing", "desc": "节奏问题"},
        "开头": {"type": "opening", "desc": "开头问题"},
        "结尾": {"type": "ending", "desc": "结尾问题"},
        "描写": {"type": "description", "desc": "描写问题"},
        "伏笔": {"type": "foreshadowing", "desc": "伏笔问题"},
        "逻辑": {"type": "logic", "desc": "逻辑问题"},
        "错字": {"type": "typo", "desc": "错字问题"},
        "标点": {"type": "punctuation", "desc": "标点问题"},
    }

    found_categories = set()
    for desc, severity, chapter in report_issues:
        for keyword, info in rule_keywords.items():
            if keyword in desc and info["type"] not in found_categories:
                found_categories.add(info["type"])
                new_rules.append({
                    "rule_type": "quality_rule",
                    "description": f"[{severity}] {desc} (章节: {chapter})",
                    "evidence": f"从审查报告中提取",
                    "proposed_rule": f"写后检查: {info['desc']}",
                    "confidence": 0.7 if severity in ["P0", "P1"] else 0.5,
                })

    # 去重（相同类型的只保留置信度最高的）
    seen_types = {}
    for rule in new_rules:
        key = rule["rule_type"]
        if key not in seen_types or rule["confidence"] > seen_types[key]["confidence"]:
            seen_types[key] = rule

    # 但保留所有 limited 类型（因为每个词都要加）
    limited_rules = [r for r in new_rules if r["rule_type"] == "limited"]
    unique_rules = list(seen_types.values())
    # 把 limited 规则加回去（去重后）
    for r in limited_rules:
        if r not in unique_rules:
            unique_rules.append(r)

    # 按置信度排序
    unique_rules.sort(key=lambda r: r["confidence"], reverse=True)
    return unique_rules


# ============================================================
# 规则写入
# ============================================================

def generate_upgrade_report(
    novel_name: str,
    total_chapters: int,
    total_words: int,
    report_issues: list,
    word_usage: dict,
    new_rules: list,
) -> str:
    """生成复盘升级报告。"""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  📊 小说完结复盘升级报告")
    lines.append(f"{'='*60}")
    lines.append(f"")
    lines.append(f"小说: {novel_name}")
    lines.append(f"章节: {total_chapters}章")
    lines.append(f"总字数: {total_words:,}")
    lines.append(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")

    # AI词使用统计
    lines.append(f"{'─'*60}")
    lines.append(f"【AI词使用统计 Top 15】")
    lines.append(f"{'─'*60}")
    word_totals = []
    for word, usages in word_usage.items():
        total = sum(c for _, c in usages)
        max_ch = max(usages, key=lambda x: x[1])
        word_totals.append((word, total, max_ch))
    word_totals.sort(key=lambda x: x[1], reverse=True)
    for word, total, (max_ch, max_count) in word_totals[:15]:
        status = ""
        if word in KNOWN_BANNED:
            status = "🚫 禁止词"
        elif word in KNOWN_LIMITED:
            status = "⚠️ 限制词"
        else:
            status = "🆕 新发现"
        lines.append(f"  {status} '{word}': 全书{total}次, 最高单章ch{max_ch}={max_count}次")

    lines.append(f"")

    # 报告问题统计
    lines.append(f"{'─'*60}")
    lines.append(f"【审查报告问题统计】")
    lines.append(f"{'─'*60}")
    severity_counts = Counter()
    for _, sev, _ in report_issues:
        severity_counts[sev] += 1
    for sev in ["P0", "P1", "P2", "warning", "unknown"]:
        if sev in severity_counts:
            lines.append(f"  {sev}: {severity_counts[sev]}条")

    lines.append(f"")

    # 新规则建议
    lines.append(f"{'─'*60}")
    lines.append(f"【新规则建议】(共 {len(new_rules)} 条)")
    lines.append(f"{'─'*60}")
    for i, rule in enumerate(new_rules, 1):
        confidence_icon = {
            (0.8, 1.0): "✅",
            (0.6, 0.8): "⚠️",
            (0.0, 0.6): "💡",
        }
        icon = "💡"
        for low, high in confidence_icon:
            if low <= rule["confidence"] < high:
                icon = confidence_icon[(low, high)]
                break
        lines.append(f"")
        lines.append(f"  {icon} 规则 #{i}: [{rule['rule_type']}]")
        lines.append(f"  描述: {rule['description']}")
        lines.append(f"  证据: {rule['evidence']}")
        lines.append(f"  建议: {rule['proposed_rule']}")
        lines.append(f"  置信度: {rule['confidence']:.0%}")

    lines.append(f"")
    lines.append(f"{'='*60}")
    lines.append(f"  下一步:")
    lines.append(f"  1. 审核上述新规则建议")
    lines.append(f"  2. 运行 --upgrade 自动写入知识库")
    lines.append(f"  3. 下一本小说将自动应用新规则")
    lines.append(f"{'='*60}")
    lines.append(f"")

    return "\n".join(lines)


def apply_upgrades(
    new_rules: list,
    kb_dir: str = None,
    dry_run: bool = True,
) -> str:
    """
    将新规则写入知识库文件。

    Args:
        new_rules: 新规则列表
        kb_dir: 知识库目录，默认从当前目录推断
        dry_run: True=只预览，False=实际写入

    Returns:
        操作报告
    """
    if kb_dir is None:
        # 默认推断
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        kb_dir = os.path.join(project_dir, "..", "knowledge_base")
        if not os.path.exists(kb_dir):
            # 试试从当前工作目录找
            for candidate in ["knowledge_base", "../knowledge_base", "../../knowledge_base"]:
                if os.path.exists(candidate):
                    kb_dir = candidate
                    break

    lines = []
    lines.append("【知识库升级报告】")
    lines.append(f"")

    # 分类规则
    limited_rules = [r for r in new_rules if r["rule_type"] == "limited"]
    quality_rules = [r for r in new_rules if r["rule_type"] == "quality_rule" and r["confidence"] >= 0.7]
    pattern_rules = [r for r in new_rules if r["rule_type"] == "new_pattern" and r["confidence"] >= 0.6]
    watch_rules = [r for r in new_rules if r["rule_type"] == "concentration_watch"]

    # 1. 更新闭环质量控制文档的AI限制词表
    if limited_rules:
        lines.append(f"1. AI限制词表更新 (+{len(limited_rules)}词):")
        for rule in limited_rules:
            # 提取词汇和限制
            proposed = rule["proposed_rule"]
            m = re.search(r"'.*?'", proposed)
            word = m.group(0) if m else "?"
            m2 = re.search(r"单章≤(\d+), 20章≤(\d+)", proposed)
            per_ch = m2.group(1) if m2 else "?"
            total_20 = m2.group(2) if m2 else "?"
            lines.append(f"   + {word} (单章≤{per_ch}, 20章≤{total_20})")
        lines.append(f"   → 写入: knowledge_base/50_Quality/闭环质量控制.md §2.2")
        lines.append(f"   → 写入: knowledge_base/50_Quality/红线检查/红线系统.md §14")
        lines.append(f"")

    # 2. 新增质量规则
    if quality_rules:
        lines.append(f"2. 新增质量规则 (+{len(quality_rules)}条):")
        for rule in quality_rules:
            lines.append(f"   + {rule['proposed_rule']}")
            lines.append(f"     来源: {rule['description']}")
        lines.append(f"   → 写入: knowledge_base/50_Quality/闭环质量控制.md §五 教训转化表")
        lines.append(f"")

    # 3. 新增模板警告
    if pattern_rules:
        lines.append(f"3. 新增模板警告 (+{len(pattern_rules)}条):")
        for rule in pattern_rules:
            lines.append(f"   + {rule['proposed_rule']}")
        lines.append(f"   → 写入: knowledge_base/40_Writing/降低AI痕迹.md")
        lines.append(f"")

    # 4. 浓度关注词
    if watch_rules:
        lines.append(f"4. 浓度关注词 (+{len(watch_rules)}词):")
        for rule in watch_rules:
            lines.append(f"   + {rule['proposed_rule']}")
        lines.append(f"   → 记录到: novel_creation_promax/novel-memory-pro/references/watch_words.md")
        lines.append(f"")

    if dry_run:
        lines.append("⚠️ DRY RUN 模式 — 以上规则未实际写入")
        lines.append("使用 --upgrade 参数执行实际写入")
    else:
        lines.append("✅ 规则已写入知识库")
        lines.append("")
        lines.append("请确认以下操作已执行：")
        for section in lines:
            if "→ 写入:" in section:
                lines.append(f"  □ {section.strip()}")

    return "\n".join(lines)


# ============================================================
# 实际文件写入
# ============================================================

def write_to_closed_loop_doc(new_rules: list, kb_dir: str):
    """将新规则追加到闭环质量控制文档的教训转化表。"""
    doc_path = os.path.join(kb_dir, "50_Quality/闭环质量控制.md")
    if not os.path.exists(doc_path):
        return False

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到"五、教训转化为规则"表格，追加新行
    # 找到表格末尾
    lines = content.split('\n')
    insert_idx = None
    in_table = False
    for i, line in enumerate(lines):
        if '教训转化为规则' in line:
            in_table = True
        if in_table and line.startswith('|---|'):
            # 找到表格头分隔线，下一个非表格行就是插入点
            for j in range(i + 1, len(lines)):
                if not lines[j].startswith('|'):
                    insert_idx = j
                    break
            break

    if insert_idx is None:
        return False

    new_rows = []
    for rule in new_rules:
        if rule["confidence"] < 0.6:
            continue
        if rule["rule_type"] in ("limited", "quality_rule"):
            desc = rule["description"]
            rule_text = rule["proposed_rule"]
            new_rows.append(f"| {desc} | {rule_text} |")

    if new_rows:
        new_content = '\n'.join(lines[:insert_idx]) + '\n' + '\n'.join(new_rows) + '\n' + '\n'.join(lines[insert_idx:])
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def write_to_redline_doc(new_rules: list, kb_dir: str):
    """将新限制词追加到红线系统的四级红线部分。"""
    doc_path = os.path.join(kb_dir, "50_Quality/红线检查/红线系统.md")
    if not os.path.exists(doc_path):
        return False

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到"## 🤖 四级红线"部分，在末尾追加新词
    limited_rules = [r for r in new_rules if r["rule_type"] == "limited" and r["confidence"] >= 0.7]
    if not limited_rules:
        return False

    # 找到四级红线表格末尾
    lines = content.split('\n')
    insert_idx = None
    in_section = False
    for i, line in enumerate(lines):
        if '四级红线' in line:
            in_section = True
        if in_section and line.startswith('##'):
            # 下一个一级标题前就是插入点
            insert_idx = i
            break

    if insert_idx is None:
        return False

    # 插入新词到表格中
    new_rows = []
    for rule in limited_rules:
        proposed = rule["proposed_rule"]
        m = re.search(r"'.*?'", proposed)
        word = m.group(0).strip("'") if m else "?"
        m2 = re.search(r"单章≤(\d+), 20章≤(\d+)", proposed)
        per_ch = m2.group(1) if m2 else "?"
        total_20 = m2.group(2) if m2 else "?"
        new_rows.append(f"| `{word}` | ≤{per_ch} | ≤{total_20} | 替换/上下文描写 |")

    if new_rows:
        # 在表格分隔符后插入
        table_sep_idx = None
        for i in range(insert_idx - 1, 0, -1):
            if lines[i].startswith('|---'):
                table_sep_idx = i
                break
        if table_sep_idx:
            insert_idx = table_sep_idx + 1

        new_content = '\n'.join(lines[:insert_idx]) + '\n' + '\n'.join(new_rows) + '\n' + '\n'.join(lines[insert_idx:])
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="小说完结复盘升级脚本 — 从已完结小说中提取教训，更新知识库规则"
    )
    parser.add_argument("--novel-dir", required=True, help="小说输出目录路径")
    parser.add_argument("--kb-dir", default=None, help="知识库目录路径（默认自动推断）")
    parser.add_argument("--upgrade", action="store_true", help="执行实际写入（默认只预览）")
    parser.add_argument("--output", default=None, help="输出复盘报告到文件")
    args = parser.parse_args()

    novel_dir = args.novel_dir
    if not os.path.exists(novel_dir):
        print(f"❌ 目录不存在: {novel_dir}")
        sys.exit(1)

    # 推断知识库目录
    kb_dir = args.kb_dir
    if kb_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for candidate in [
            os.path.join(script_dir, "..", "knowledge_base"),
            os.path.join(script_dir, "..", "..", "knowledge_base"),
            "knowledge_base",
        ]:
            if os.path.exists(candidate):
                kb_dir = os.path.abspath(candidate)
                break
        if kb_dir is None:
            print("⚠️ 无法自动推断知识库目录，使用 --kb-dir 指定")
            kb_dir = "."

    # 推断小说名
    novel_dir_stripped = novel_dir.rstrip('/')
    novel_name = os.path.basename(novel_dir_stripped)

    print(f"📊 开始复盘: {novel_name}")
    print(f"📁 小说目录: {novel_dir}")
    print(f"📚 知识库: {kb_dir}")
    print(f"")

    # 1. 数据收集
    print("⏳ 加载审查报告...")
    reports = load_review_reports(novel_dir)
    print(f"   找到 {len(reports)} 份报告")

    print("⏳ 加载小说状态...")
    state = load_novel_state(novel_dir)
    has_state = bool(state)
    print(f"   {'找到' if has_state else '未找到'} novel_state.json")

    print("⏳ 加载章节正文...")
    chapters = load_all_chapters(novel_dir)
    print(f"   找到 {len(chapters)} 章")

    if not chapters and not reports:
        print("❌ 未找到任何章节或审查报告，无法复盘")
        sys.exit(1)

    # 2. 问题分析
    print("⏳ 分析报告问题...")
    report_issues = extract_issues_from_reports(reports)
    print(f"   提取 {len(report_issues)} 个问题")

    print("⏳ 分析AI词使用模式...")
    word_usage = extract_issues_from_chapters(chapters)
    print(f"   检测到 {len(word_usage)} 种AI词")

    print("⏳ 检测模板模式...")
    pattern_usage = extract_template_patterns(chapters)
    print(f"   检测到 {len(pattern_usage)} 种模板模式")

    # 3. 新规则识别
    print("⏳ 识别新规则...")
    new_rules = identify_new_rules(
        report_issues, word_usage, pattern_usage,
        KNOWN_BANNED, KNOWN_LIMITED, KNOWN_CONCENTRATION_PER_WORD,
    )
    print(f"   发现 {len(new_rules)} 条新规则建议")

    # 4. 生成报告
    total_words = sum(len(ch["text"]) for ch in chapters)
    report = generate_upgrade_report(
        novel_name, len(chapters), total_words,
        report_issues, word_usage, new_rules,
    )

    print("")
    print(report)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 报告已保存到 {args.output}")

    # 5. 升级写入
    if args.upgrade:
        print("")
        print("⏳ 执行知识库升级...")
        upgrade_report = apply_upgrades(new_rules, kb_dir, dry_run=False)
        print(upgrade_report)

        # 实际写入文件
        written = 0
        if write_to_closed_loop_doc(new_rules, kb_dir):
            print("✅ 闭环质量控制文档已更新")
            written += 1
        if write_to_redline_doc(new_rules, kb_dir):
            print("✅ 红线系统文档已更新")
            written += 1
        if written == 0:
            print("⚠️ 没有高置信度规则需要自动写入")
    else:
        print("")
        print("💡 预览模式 — 使用 --upgrade 参数执行实际写入")


if __name__ == "__main__":
    main()
