#!/usr/bin/env python3
"""
写后自动审计脚本 (Post-Write Audit Script)

每章生成后必须运行此脚本，检测AI词、对话比例、标题关键词、重复度等指标。
任何检查不通过时，输出详细报告并建议修复。

用法:
    python post_write_audit.py --chapter-file "正文/第1章-xxx.md" --title "第1章 xxx"
    python post_write_audit.py --chapter-file "正文/第1章-xxx.md" --prev-file "正文/第0章-xxx.md" --title "第1章 xxx"
    python post_write_audit.py --scan-all --dir "正文/"  # 扫描目录下所有章节
"""

import argparse
import glob
import json
import re
import sys
from pathlib import Path

# ============================================================
# 配置区 — 可根据项目调整
# ============================================================

# 绝对禁止词 (写后必须为0)
ABSOLUTE_BANNED = {
    "像是": 0,
}

# 严格限制词 (单章上限 + 20章总量上限)
STRICT_LIMITED = {
    # 词汇: (单章上限, 20章总量上限)
    "突然": (1, 5),
    "微微": (1, 5),
    "沉默": (1, 5),
    "感觉": (1, 10),
    "嘴角": (1, 5),
    "天旋地转": (0, 2),
}

# 浓度红线
CONCENTRATION_PER_CHAPTER = 3  # 任何AI词单章 >= 3次 → 浓度超标
TOTAL_AI_WORDS_PER_CHAPTER = 10  # 全章AI词总数 >= 10 → AI味过重

# 字数红线（中文字符）
WORD_COUNT_MIN = 2800  # 每章最低中文字数
WORD_COUNT_MAX = 3200  # 每章最高中文字符
WORD_COUNT_TARGET = 3000

# 对话比例红线
DIALOGUE_RATIO_MIN = 0.25  # 网文对话比例 >= 25%

# 重复度红线
REPEAT_RATIO_MAX = 0.20  # 相邻章节开头重复度 <= 20%

# 单句成行红线
SINGLE_LINE_PARAGRAPH_MAX = 8  # 每章单句成行段落不得超过N个

# 标题关键词最小长度
TITLE_KEYWORD_MIN_LEN = 2

# ============================================================
# 审计函数
# ============================================================

def count_word(text: str, word: str) -> int:
    """统计词汇在文本中的出现次数。"""
    return text.count(word)


def count_true_similes(text: str) -> int:
    """
    统计真正的"像"比喻数量。
    排除: 像...一样(非比喻), 偶像, 想象, 好像, 不像, 像她自己 等非比喻用法。
    """
    # 先排除常见非比喻用法
    cleaned = text
    for pattern in [
        '偶像', '想象', '想像', '好像', '不像', '像自己', '像她', '像他',
        '像我', '像你', '像我们', '像他们', '像什么', '像这样', '像那样',
        '像......一样', '像……一样',
    ]:
        cleaned = cleaned.replace(pattern, 'XXX')
    # 统计剩余的"像"字（大概率是比喻）
    return cleaned.count('像')


def calc_dialogue_ratio(text: str) -> float:
    """
    计算对话比例。
    简单算法：统计中文引号内的字符数 / 总字符数。
    """
    # 匹配 "xxx" 和 「xxx」 和 "xxx" 中的内容
    dialogue_chars = 0
    # 中文双引号
    for match in re.finditer(r'"([^"]*)"', text):
        dialogue_chars += len(match.group(1))
    # 中文双引号另一种
    for match in re.finditer(r'"([^"]*)"', text):
        dialogue_chars += len(match.group(1))
    # 单引号
    for match in re.finditer(r"'([^']*)'", text):
        dialogue_chars += len(match.group(1))

    total_chars = len(text.replace('\n', '').replace(' ', ''))
    if total_chars == 0:
        return 0.0
    return dialogue_chars / total_chars


def check_title_keywords(text: str, title: str) -> list:
    """
    提取标题中的关键词(>=2字的核心词)，检查是否在正文中出现。
    返回未匹配的关键词列表。
    """
    # 移除"第X章"前缀
    clean_title = re.sub(r'^第[零一二三四五六七八九十\d]+章\s*', '', title.strip())
    # 提取>=2字的连续中文词
    keywords = re.findall(r'[\u4e00-\u9fa5]{%d,}' % TITLE_KEYWORD_MIN_LEN, clean_title)
    # 过滤掉常见的非关键词
    stop_words = {'之', '的', '了', '在', '是', '有', '和', '与', '及'}
    keywords = [kw for kw in keywords if kw not in stop_words]

    missing = []
    for kw in keywords:
        if kw not in text:
            missing.append(kw)
    return missing


def calc_repeat_ratio(text1: str, text2: str, window: int = 200) -> float:
    """
    计算两段文本开头window字符的相似度。
    使用简单的字符重叠率。
    """
    s1 = text1[:window]
    s2 = text2[:window]
    if not s1 or not s2:
        return 0.0

    # 计算最长公共子序列长度
    def lcs_len(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if a[i] == b[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
        return dp[m][n]

    lcs = lcs_len(s1, s2)
    return lcs / max(len(s1), len(s2))


def check_first_300_chars(text: str) -> bool:
    """
    检查前300字是否有冲突/悬念/动作。
    简单启发式：前300字是否包含动作词、对话、悬念词。
    """
    first_300 = text[:300]
    # 检查是否有对话
    has_dialogue = bool(re.search(r'[""""].*?["""]', first_300))
    # 检查是否有动作/冲突词
    action_words = ['突然', '猛然', '冷不丁', '砰', '轰', '喊', '叫', '冲', '跑',
                    '追', '逃', '打', '杀', '破', '碎', '裂', '撞', '跌', '闪']
    has_action = any(w in first_300 for w in action_words)
    # 检查是否有悬念词
    suspense_words = ['但是', '然而', '却', '可是', '没想到', '竟然', '居然', '?', '？']
    has_suspense = any(w in first_300 for w in suspense_words)

    return has_dialogue or has_action or has_suspense


def count_single_line_paragraphs(text: str) -> int:
    """
    统计单句成行的段落数量。
    单句成行 = 一行只有一句话（不含标点分隔的多句话）就换行。
    用于检测"诗歌体"文风——每句话单独成行，阅读体验差。
    """
    # 跳过标题行（以#开头）和空行
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('#')]
    count = 0
    for line in lines:
        # 统计句子结束标点
        endings = len(re.findall(r'[。！？；]', line))
        # 如果一行只有1个或0个结束标点，且长度较短（<30字），算单句成行
        if endings <= 1 and len(re.findall(r'[\u4e00-\u9fff]', line)) < 30:
            count += 1
    return count


# ============================================================

def audit_chapter(chapter_text: str, title: str, prev_text: str = None) -> dict:
    """
    对单个章节执行完整审计。

    Args:
        chapter_text: 章节正文
        title: 章节标题
        prev_text: 上一章节正文（用于重复检测）

    Returns:
        审计结果字典
    """
    results = {
        "title": title,
        "word_count": len(re.findall(r'[\u4e00-\u9fff]', chapter_text)),  # 仅统计中文字符
        "ai_words": {},
        "dialogue_ratio": 0.0,
        "title_keywords": [],
        "missing_keywords": [],
        "repeat_ratio": 0.0,
        "first_300_ok": True,
        "single_line_count": 0,
        "concentration_issues": [],
        "total_ai_words": 0,
        "pass": True,
        "warnings": [],
    }

    # 1. AI词统计
    for word, limit in ABSOLUTE_BANNED.items():
        count = count_word(chapter_text, word)
        results["ai_words"][word] = count
        results["total_ai_words"] += count
        if count > limit:
            results["pass"] = False
            results["warnings"].append(f"❌ 绝对禁止词 '{word}' 出现 {count} 次 (要求: {limit})")

    for word, (per_chapter, total_20) in STRICT_LIMITED.items():
        count = count_word(chapter_text, word)
        results["ai_words"][word] = count
        results["total_ai_words"] += count
        if count > per_chapter:
            results["pass"] = False
            results["warnings"].append(f"❌ '{word}' 单章出现 {count} 次 (上限: {per_chapter})")

    # 特殊处理 "像" 比喻
    simile_count = count_true_similes(chapter_text)
    results["ai_words"]["像(比喻)"] = simile_count
    results["total_ai_words"] += simile_count
    if simile_count > 1:
        results["pass"] = False
        results["warnings"].append(f"❌ '像'比喻出现 {simile_count} 次 (单章上限: 1)")

    # 浓度检测
    for word, count in results["ai_words"].items():
        if count >= CONCENTRATION_PER_CHAPTER:
            results["concentration_issues"].append(f"⚠️ '{word}' 浓度超标: {count}次 (阈值: {CONCENTRATION_PER_CHAPTER})")

    if results["total_ai_words"] >= TOTAL_AI_WORDS_PER_CHAPTER:
        results["pass"] = False
        results["warnings"].append(f"❌ AI词总数 {results['total_ai_words']} (阈值: {TOTAL_AI_WORDS_PER_CHAPTER})，AI味过重")

    # 2. 字数检查（中文字符）
    wc = results["word_count"]
    if wc < WORD_COUNT_MIN:
        results["pass"] = False
        results["warnings"].append(f"❌ 字数 {wc} (最低: {WORD_COUNT_MIN}，目标: {WORD_COUNT_TARGET})")
    elif wc > WORD_COUNT_MAX:
        results["pass"] = False
        results["warnings"].append(f"❌ 字数 {wc} (最高: {WORD_COUNT_MAX}，目标: {WORD_COUNT_TARGET})")

    # 3. 对话比例
    results["dialogue_ratio"] = calc_dialogue_ratio(chapter_text)
    if results["dialogue_ratio"] < DIALOGUE_RATIO_MIN:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 对话比例 {results['dialogue_ratio']:.1%} (最低: {DIALOGUE_RATIO_MIN:.0%})"
        )

    # 4. 标题关键词匹配
    results["title_keywords"] = re.findall(
        r'[\u4e00-\u9fa5]{%d,}' % TITLE_KEYWORD_MIN_LEN,
        re.sub(r'^第[零一二三四五六七八九十\d]+章\s*', '', title.strip())
    )
    results["missing_keywords"] = check_title_keywords(chapter_text, title)
    if results["missing_keywords"]:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 标题关键词不在正文中: {', '.join(results['missing_keywords'])}"
        )

    # 5. 重复检测
    if prev_text:
        results["repeat_ratio"] = calc_repeat_ratio(chapter_text, prev_text)
        if results["repeat_ratio"] > REPEAT_RATIO_MAX:
            results["pass"] = False
            results["warnings"].append(
                f"❌ 与上一章开头重复度 {results['repeat_ratio']:.1%} (最高: {REPEAT_RATIO_MAX:.0%})"
            )

    # 6. 前300字检查
    results["first_300_ok"] = check_first_300_chars(chapter_text)
    if not results["first_300_ok"]:
        results["warnings"].append("⚠️ 前300字未检测到冲突/悬念/动作，建议增强开头吸引力")

    # 7. 单句成行检查
    results["single_line_count"] = count_single_line_paragraphs(chapter_text)
    if results["single_line_count"] > SINGLE_LINE_PARAGRAPH_MAX:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 单句成行段落 {results['single_line_count']} 次 (最高: {SINGLE_LINE_PARAGRAPH_MAX})，文风过于碎片化"
        )

    return results


def format_report(results: dict) -> str:
    """格式化审计报告。"""
    lines = []
    lines.append(f"{'='*50}")
    lines.append(f"  写后审计报告 — {results['title']}")
    lines.append(f"{'='*50}")
    wc = results["word_count"]
    wc_status = "✅" if WORD_COUNT_MIN <= wc <= WORD_COUNT_MAX else "❌"
    lines.append(f"【字数】{wc_status} {wc} 中文字符 (范围: {WORD_COUNT_MIN}-{WORD_COUNT_MAX})")
    lines.append(f"")

    # AI词统计
    lines.append(f"【AI词统计】")
    for word, count in results["ai_words"].items():
        status = "✅" if count <= 1 else "⚠️"
        lines.append(f"  {status} {word}: {count}次")
    lines.append(f"  AI词总数: {results['total_ai_words']}")

    if results["concentration_issues"]:
        lines.append(f"  浓度问题:")
        for issue in results["concentration_issues"]:
            lines.append(f"    {issue}")

    lines.append(f"")
    lines.append(f"【对话比例】")
    ratio = results["dialogue_ratio"]
    status = "✅" if ratio >= DIALOGUE_RATIO_MIN else "❌"
    lines.append(f"  {status} {ratio:.1%} (目标: ≥{DIALOGUE_RATIO_MIN:.0%})")

    lines.append(f"")
    lines.append(f"【标题关键词】")
    if results["title_keywords"]:
        for kw in results["title_keywords"]:
            found = kw not in results["missing_keywords"]
            status = "✅" if found else "❌"
            lines.append(f"  {status} '{kw}': {'正文中出现' if found else '未找到'}")
    else:
        lines.append(f"  (无关键词可检测)")

    lines.append(f"")
    lines.append(f"【重复检测】")
    if results["repeat_ratio"] > 0:
        status = "✅" if results["repeat_ratio"] <= REPEAT_RATIO_MAX else "❌"
        lines.append(f"  {status} 与上一章开头重复度: {results['repeat_ratio']:.1%}")
    else:
        lines.append(f"  (无上一章，跳过)")

    lines.append(f"")
    lines.append(f"【开头检查】")
    status = "✅" if results["first_300_ok"] else "⚠️"
    lines.append(f"  {status} 前300字{'有冲突/悬念/动作' if results['first_300_ok'] else '缺少冲突/悬念/动作'}")

    lines.append(f"")
    lines.append(f"【单句成行】")
    slc = results["single_line_count"]
    status = "✅" if slc <= SINGLE_LINE_PARAGRAPH_MAX else "❌"
    lines.append(f"  {status} 单句成行段落: {slc} 次 (最高: {SINGLE_LINE_PARAGRAPH_MAX})")

    lines.append(f"")
    if results["pass"]:
        lines.append(f"{'='*50}")
        lines.append(f"  ✅ 审计通过！")
        lines.append(f"{'='*50}")
    else:
        lines.append(f"{'='*50}")
        lines.append(f"  ❌ 审计未通过，以下问题需要修复:")
        lines.append(f"{'='*50}")
        for w in results["warnings"]:
            lines.append(f"  {w}")
    lines.append(f"")

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="写后自动审计脚本")
    parser.add_argument("--chapter-file", help="章节文件路径")
    parser.add_argument("--prev-file", help="上一章节文件路径（用于重复检测）")
    parser.add_argument("--title", help="章节标题")
    parser.add_argument("--scan-all", action="store_true", help="扫描目录下所有章节")
    parser.add_argument("--dir", default="正文/", help="章节目录（配合 --scan-all 使用）")
    parser.add_argument("--output", help="输出审计报告到JSON文件")
    args = parser.parse_args()

    if args.scan_all:
        # 扫描目录下所有 .md 文件
        files = sorted(glob.glob(f"{args.dir}/*.md"))
        if not files:
            print(f"未在 {args.dir} 下找到 .md 文件")
            sys.exit(1)

        all_results = []
        prev_text = None
        for fpath in files:
            with open(fpath, 'r', encoding='utf-8') as f:
                text = f.read()
            # 提取标题（第一行）
            title_line = text.split('\n')[0].lstrip('# ').strip()
            results = audit_chapter(text, title_line, prev_text)
            all_results.append(results)
            print(format_report(results))
            prev_text = text

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"审计报告已保存到 {args.output}")

    elif args.chapter_file:
        with open(args.chapter_file, 'r', encoding='utf-8') as f:
            text = f.read()

        prev_text = None
        if args.prev_file:
            with open(args.prev_file, 'r', encoding='utf-8') as f:
                prev_text = f.read()

        title = args.title or "未知章节"
        results = audit_chapter(text, title, prev_text)
        print(format_report(results))

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"审计报告已保存到 {args.output}")

        sys.exit(0 if results["pass"] else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
