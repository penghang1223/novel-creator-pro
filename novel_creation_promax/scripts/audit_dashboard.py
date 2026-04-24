#!/usr/bin/env python3
"""
审计聚合仪表盘 (Audit Dashboard Script)

聚合多章节审计结果，生成趋势统计和全局质量报告。
读取 post_write_audit.py 生成的 JSON 报告，或扫描已审计文件重新计算。

用法:
    # 从已有 JSON 审计文件聚合
    python audit_dashboard.py --novel-dir novel_output/番茄/我的小说/

    # 指定扫描目录
    python audit_dashboard.py --scan-dir novel_output/番茄/我的小说/素材/

    # 输出详细报告
    python audit_dashboard.py --novel-dir novel_output/番茄/我的小说/ --verbose

    # 导出 Markdown 报告
    python audit_dashboard.py --novel-dir novel_output/番茄/我的小说/ --report audit_summary.md
"""

import argparse
import glob
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path


# ============================================================
# 配置区
# ============================================================

# 字数目标
WORD_COUNT_TARGET = 3000
WORD_COUNT_MIN = 2800
WORD_COUNT_MAX = 3200

# AI 词关注阈值
AI_WORDS_ALERT_THRESHOLD = 10


# ============================================================
# 数据收集
# ============================================================

def collect_audit_json(novel_dir: str) -> list:
    """
    从小说目录下收集所有 audit_*.json 文件。
    """
    ndir = Path(novel_dir)
    # 搜索 素材/ 目录下的审计报告
    material_dir = ndir / "素材"
    if material_dir.exists():
        files = sorted(material_dir.glob("audit_ch*.json"))
        if files:
            results = []
            for f in files:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
            return results

    # 搜索 摘要/ 目录下的审计报告
    summary_dir = ndir / "摘要"
    if summary_dir.exists():
        files = sorted(summary_dir.glob("*audit*.json"))
        if files:
            results = []
            for f in files:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        results.extend(data)
                    else:
                        results.append(data)
            return results

    return []


def collect_from_chapters(novel_dir: str) -> list:
    """
    从正文章节重新运行审计逻辑收集数据。
    依赖 post_write_audit.py 的 audit_chapter 函数。
    """
    ndir = Path(novel_dir)
    zhengwen = ndir / "正文"
    if not zhengwen.exists():
        return []

    # 导入 post_write_audit 模块
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    try:
        from post_write_audit import audit_chapter
    except ImportError:
        return []

    # 获取所有章节文件并排序
    files = sorted(zhengwen.glob("*.md"))
    results = []
    prev_text = None

    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        # 提取标题
        title_line = text.split('\n')[0].lstrip('# ').strip()
        # 提取章节号
        ch_match = re.search(r'第([零一二三四五六七八九十\d]+)章', title_line)
        ch_num = ch_match.group(1) if ch_match else "?"

        result = audit_chapter(text, title_line, prev_text)
        result["chapter_num"] = ch_num
        results.append(result)
        prev_text = text

    return results


# ============================================================
# 分析函数
# ============================================================

def analyze_word_count_trend(data: list) -> dict:
    """字数趋势分析。"""
    chapters = []
    for d in data:
        wc = d.get("word_count", 0)
        title = d.get("title", "未知")
        ch = d.get("chapter_num", "?")
        chapters.append({"chapter": ch, "title": title, "word_count": wc})

    counts = [c["word_count"] for c in chapters]
    if not counts:
        return {"chapters": [], "avg": 0, "min": 0, "max": 0, "target": WORD_COUNT_TARGET}

    return {
        "chapters": chapters,
        "avg": round(sum(counts) / len(counts)),
        "min": min(counts),
        "max": max(counts),
        "target": WORD_COUNT_TARGET,
        "in_range": sum(1 for c in counts if WORD_COUNT_MIN <= c <= WORD_COUNT_MAX),
        "below": sum(1 for c in counts if c < WORD_COUNT_MIN),
        "above": sum(1 for c in counts if c > WORD_COUNT_MAX),
    }


def analyze_ai_words_trend(data: list) -> dict:
    """AI 词使用趋势分析。"""
    chapters = []
    all_words = {}

    for d in data:
        ai_words = d.get("ai_words", {})
        total = d.get("total_ai_words", 0)
        title = d.get("title", "未知")
        ch = d.get("chapter_num", "?")

        chapters.append({
            "chapter": ch,
            "title": title,
            "total_ai_words": total,
        })

        for word, count in ai_words.items():
            if word not in all_words:
                all_words[word] = 0
            all_words[word] += count

    # Top 15 AI 词
    top_words = sorted(all_words.items(), key=lambda x: x[1], reverse=True)[:15]

    total_per_chapter = [c["total_ai_words"] for c in chapters]
    over_threshold = sum(1 for t in total_per_chapter if t >= AI_WORDS_ALERT_THRESHOLD)

    return {
        "chapters": chapters,
        "top_15": [{"word": w, "count": c} for w, c in top_words],
        "chapters_over_threshold": over_threshold,
        "avg_per_chapter": round(sum(total_per_chapter) / max(len(total_per_chapter), 1), 1),
    }


def analyze_dialogue_ratio_trend(data: list) -> dict:
    """对话比例趋势分析。"""
    chapters = []
    for d in data:
        ratio = d.get("dialogue_ratio", 0)
        title = d.get("title", "未知")
        ch = d.get("chapter_num", "?")
        chapters.append({"chapter": ch, "title": title, "dialogue_ratio": ratio})

    ratios = [c["dialogue_ratio"] for c in chapters]
    if not ratios:
        return {"chapters": [], "avg": 0, "min": 0, "max": 0}

    return {
        "chapters": chapters,
        "avg": round(sum(ratios) / len(ratios), 3),
        "min": min(ratios),
        "max": max(ratios),
        "below_threshold": sum(1 for r in ratios if r < 0.25),
    }


def analyze_audit_pass_rate(data: list) -> dict:
    """审计通过率分析。"""
    passed = sum(1 for d in data if d.get("pass", False))
    total = len(data)

    # 统计失败原因
    failure_reasons = {}
    for d in data:
        if not d.get("pass", True):
            for w in d.get("warnings", []):
                # 提取失败类型
                if "禁止词" in w or "AI" in w:
                    key = "AI词超标"
                elif "对话" in w:
                    key = "对话比例不足"
                elif "字数" in w:
                    key = "字数不达标"
                elif "关键词" in w:
                    key = "标题关键词缺失"
                elif "重复" in w:
                    key = "与上章重复"
                elif "单句" in w:
                    key = "单句成行过多"
                else:
                    key = "其他"
                failure_reasons[key] = failure_reasons.get(key, 0) + 1

    return {
        "total_chapters": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / max(total, 1) * 100, 1),
        "failure_reasons": sorted(
            failure_reasons.items(), key=lambda x: x[1], reverse=True
        ),
    }


def generate_dashboard(novel_dir: str, scan_dir: str = "") -> dict:
    """
    生成完整仪表盘。
    """
    # 收集数据
    data = collect_audit_json(novel_dir) if novel_dir else []
    if not data and (scan_dir or novel_dir):
        sd = scan_dir or novel_dir
        data = collect_from_chapters(sd)

    if not data:
        return {
            "generated_at": datetime.now().isoformat(),
            "novel_dir": novel_dir or scan_dir,
            "total_chapters": 0,
            "warning": "未找到审计数据，请确保已运行 post_write_audit.py 生成 JSON 报告",
        }

    return {
        "generated_at": datetime.now().isoformat(),
        "novel_dir": novel_dir or scan_dir,
        "total_chapters": len(data),
        "word_count": analyze_word_count_trend(data),
        "ai_words": analyze_ai_words_trend(data),
        "dialogue_ratio": analyze_dialogue_ratio_trend(data),
        "audit_pass_rate": analyze_audit_pass_rate(data),
    }


# ============================================================
# 报告输出
# ============================================================

def format_text_report(dashboard: dict) -> str:
    """生成文本格式报告。"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  审计仪表盘 — {dashboard.get('novel_dir', '未知项目')}")
    lines.append(f"  生成时间: {dashboard.get('generated_at', '未知')}")
    lines.append("=" * 60)

    total = dashboard.get("total_chapters", 0)
    if total == 0:
        lines.append(f"\n  ⚠️ {dashboard.get('warning', '无数据')}")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"\n  统计章节数: {total}")
    lines.append("")

    # 字数
    wc = dashboard.get("word_count", {})
    if wc.get("chapters"):
        lines.append("【字数趋势】")
        lines.append(f"  平均: {wc.get('avg', 0)} 字 | 最低: {wc.get('min', 0)} | 最高: {wc.get('max', 0)}")
        lines.append(f"  目标: {WORD_COUNT_MIN}-{WORD_COUNT_MAX}")
        lines.append(f"  达标: {wc.get('in_range', 0)}/{total} | 不足: {wc.get('below', 0)} | 超量: {wc.get('above', 0)}")
        lines.append("")

    # AI 词
    ai = dashboard.get("ai_words", {})
    if ai.get("chapters"):
        lines.append("【AI 词趋势】")
        lines.append(f"  平均每章: {ai.get('avg_per_chapter', 0)} 个")
        lines.append(f"  超标章节: {ai.get('chapters_over_threshold', 0)}/{total}")
        if ai.get("top_15"):
            lines.append(f"  AI 词 Top 15:")
            for item in ai["top_15"]:
                lines.append(f"    - {item['word']}: {item['count']}次")
        lines.append("")

    # 对话比例
    dr = dashboard.get("dialogue_ratio", {})
    if dr.get("chapters"):
        lines.append("【对话比例】")
        lines.append(f"  平均: {dr.get('avg', 0):.1%} | 最低: {dr.get('min', 0):.1%} | 最高: {dr.get('max', 0):.1%}")
        lines.append(f"  低于25%阈值的章节: {dr.get('below_threshold', 0)}/{total}")
        lines.append("")

    # 通过率
    pr = dashboard.get("audit_pass_rate", {})
    if pr.get("total_chapters", 0) > 0:
        lines.append("【审计通过率】")
        lines.append(f"  通过: {pr.get('passed', 0)}/{total} ({pr.get('pass_rate', 0)}%)")
        lines.append(f"  未通过: {pr.get('failed', 0)}/{total}")
        if pr.get("failure_reasons"):
            lines.append(f"  失败原因分布:")
            for reason, count in pr["failure_reasons"]:
                lines.append(f"    - {reason}: {count}次")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_markdown_report(dashboard: dict) -> str:
    """生成 Markdown 格式报告。"""
    lines = []
    lines.append(f"# 审计仪表盘 — {dashboard.get('novel_dir', '未知项目')}")
    lines.append(f"")
    lines.append(f"> 生成时间: {dashboard.get('generated_at', '未知')}")
    lines.append(f"> 统计章节: {dashboard.get('total_chapters', 0)}")
    lines.append(f"")

    total = dashboard.get("total_chapters", 0)
    if total == 0:
        lines.append(f"⚠️ {dashboard.get('warning', '无数据')}")
        return "\n".join(lines)

    # 字数
    wc = dashboard.get("word_count", {})
    if wc.get("chapters"):
        lines.append("## 字数趋势")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 平均 | {wc.get('avg', 0)} 字 |")
        lines.append(f"| 最低 | {wc.get('min', 0)} 字 |")
        lines.append(f"| 最高 | {wc.get('max', 0)} 字 |")
        lines.append(f"| 达标 | {wc.get('in_range', 0)}/{total} |")
        lines.append(f"")

    # AI 词
    ai = dashboard.get("ai_words", {})
    if ai.get("top_15"):
        lines.append("## AI 词 Top 15")
        lines.append(f"| 词汇 | 总次数 |")
        lines.append(f"|------|--------|")
        for item in ai["top_15"]:
            lines.append(f"| {item['word']} | {item['count']} |")
        lines.append(f"")

    # 对话比例
    dr = dashboard.get("dialogue_ratio", {})
    if dr.get("chapters"):
        lines.append("## 对话比例")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 平均 | {dr.get('avg', 0):.1%} |")
        lines.append(f"| 最低 | {dr.get('min', 0):.1%} |")
        lines.append(f"| 最高 | {dr.get('max', 0):.1%} |")
        lines.append(f"| 低于阈值 | {dr.get('below_threshold', 0)} 章 |")
        lines.append(f"")

    # 通过率
    pr = dashboard.get("audit_pass_rate", {})
    if pr.get("total_chapters", 0) > 0:
        lines.append("## 审计通过率")
        rate = pr.get("pass_rate", 0)
        emoji = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
        lines.append(f"{emoji} 通过率: **{rate}%** ({pr.get('passed', 0)}/{total})")
        if pr.get("failure_reasons"):
            lines.append(f"")
            lines.append(f"### 失败原因分布")
            for reason, count in pr["failure_reasons"]:
                bar = "█" * min(count, 20)
                lines.append(f"- {reason}: {bar} ({count})")
        lines.append(f"")

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="审计聚合仪表盘 — 多章节质量趋势统计")
    parser.add_argument("--novel-dir", default="", help="小说目录路径（自动搜索审计 JSON）")
    parser.add_argument("--scan-dir", default="", help="直接扫描审计 JSON 的目录")
    parser.add_argument("--verbose", action="store_true", help="输出详细数据")
    parser.add_argument("--report", default="", help="输出 Markdown 报告到文件")
    parser.add_argument("--json-output", default="", help="输出 JSON 仪表盘到文件")
    args = parser.parse_args()

    dashboard = generate_dashboard(
        novel_dir=args.novel_dir if args.novel_dir else "",
        scan_dir=args.scan_dir if args.scan_dir else "",
    )

    # 文本输出
    print(format_text_report(dashboard))

    # Markdown 报告
    if args.report:
        md = format_markdown_report(dashboard)
        Path(args.report).write_text(md, encoding="utf-8")
        print(f"Markdown 报告已保存到 {args.report}")

    # JSON 输出
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)
        print(f"JSON 仪表盘已保存到 {args.json_output}")


if __name__ == "__main__":
    main()
