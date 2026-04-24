#!/usr/bin/env python3
"""
写前检查脚本 (Pre-Write Check Script)

每章正文写作前必须运行，执行 9 问必答 + 5 项写前检查。
输出结构化检查报告，供 AI 和人工审核。

用法:
    python pre_write_check.py \
        --novel-dir novel_output/番茄/我的小说/ \
        --chapter 5 \
        --title "第5章 神秘来客"

    # 从细纲读取章节信息
    python pre_write_check.py \
        --novel-dir novel_output/番茄/我的小说/ \
        --chapter 5 \
        --outline-file 细纲/volume_1.json

    # 指定 AI 词黑名单文件
    python pre_write_check.py \
        --novel-dir novel_output/番茄/我的小说/ \
        --chapter 5 \
        --banned-words knowledge_base/50_Quality/闭环质量控制.md
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ============================================================
# 配置区
# ============================================================

# 9 问必答系统 — 每题分值
QUESTIONS = [
    {"id": 1, "name": "章节位置", "weight": 10,
     "desc": "本章在全书/本卷中的位置和作用"},
    {"id": 2, "name": "情节团", "weight": 10,
     "desc": "本章要推进的具体情节团"},
    {"id": 3, "name": "悬念承接", "weight": 15,
     "desc": "上章悬念如何承接"},
    {"id": 4, "name": "伏笔处理", "weight": 10,
     "desc": "本章要处理/埋设的伏笔"},
    {"id": 5, "name": "核心事件", "weight": 20,
     "desc": "用1句话描述本章核心推进事件"},
    {"id": 6, "name": "爽点设计", "weight": 10,
     "desc": "本章的爽点或情绪爆点"},
    {"id": 7, "name": "角色状态", "weight": 10,
     "desc": "出场角色的当前状态变化"},
    {"id": 8, "name": "场景设定", "weight": 5,
     "desc": "本章场景和时间线"},
    {"id": 9, "name": "结尾悬念", "weight": 10,
     "desc": "本章结尾要留下的悬念"},
]

PASS_THRESHOLD = 70  # 9问总分≥70分方可写作


# ============================================================
# 检查函数
# ============================================================

def load_banned_words(banned_file: str) -> list:
    """
    从闭环质量控制文档或纯文本文件加载 AI 禁止词。
    支持两种格式:
    1. Markdown 文件中的列表行（- xxx / * xxx / 1. xxx）
    2. 纯文本，每行一个词
    """
    words = []
    try:
        text = Path(banned_file).read_text(encoding="utf-8")
        # 提取 Markdown 列表项
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("-", "*", "|")) or re.match(r"^\d+\.", line):
                # 去掉列表标记
                cleaned = re.sub(r"^[-*|]\s*|\d+\.\s*", "", line).strip()
                # 去掉引号
                cleaned = cleaned.strip('"').strip("'").strip('「').strip('」')
                if cleaned and len(cleaned) >= 2:
                    words.append(cleaned)
    except FileNotFoundError:
        # 如果文件不存在，使用默认禁止词
        words = ["像是"]
    return words


def check_previous_chapter_exists(novel_dir: str, chapter: int) -> dict:
    """
    检查上一章是否存在（防止无上下文写作）。
    返回上一章文件路径和开头 200 字。
    """
    ndir = Path(novel_dir)
    zhengwen = ndir / "正文"
    if not zhengwen.exists():
        return {"exists": False, "path": None, "first_200": "", "warning": "正文目录不存在"}

    # 查找上一章文件
    prev_num = chapter - 1
    if prev_num <= 0:
        return {"exists": True, "path": None, "first_200": "", "warning": "第1章，无上章"}

    # 匹配模式: 第N章-标题.md 或 第N章 标题.md 或 N_标题.md
    patterns = [
        f"第{prev_num}章*.md",
        f"第{prev_num:02d}章*.md",
        f"{prev_num:03d}_*.md",
        f"{prev_num}_*.md",
    ]
    for pat in patterns:
        matches = list(zhengwen.glob(pat))
        if matches:
            prev_text = matches[0].read_text(encoding="utf-8")
            # 跳过 frontmatter / 标题行
            content = re.sub(r'^---.*?---\n', '', prev_text, flags=re.DOTALL)
            content = re.sub(r'^#.*\n', '', content, count=1)
            return {
                "exists": True,
                "path": str(matches[0]),
                "first_200": content[:200],
                "warning": None,
            }

    return {"exists": False, "path": None, "first_200": "",
            "warning": f"未找到第{prev_num}章文件"}


def check_memory_pack(novel_dir: str, chapter: int) -> dict:
    """
    检查章节记忆包是否存在。
    优先读 JSON 记忆包，其次读记忆目录。
    """
    ndir = Path(novel_dir)
    memory_dir = ndir / "记忆"
    if not memory_dir.exists():
        return {"exists": False, "path": None, "warning": "记忆目录不存在，跳过"}

    # 查找记忆包
    pack_name = f"chapter_{chapter}_pack.json"
    pack_file = memory_dir / pack_name
    if pack_file.exists():
        with open(pack_file, "r", encoding="utf-8") as f:
            pack_data = json.load(f)
        return {
            "exists": True,
            "path": str(pack_file),
            "data": pack_data,
            "warning": None,
        }

    # 检查是否有通用记忆文件
    memory_files = list(memory_dir.glob("*.json"))
    if memory_files:
        return {
            "exists": True,
            "path": str(memory_files[0]),
            "data": None,
            "warning": f"未找到专用记忆包 {pack_name}，使用通用记忆",
        }

    return {"exists": False, "path": None, "warning": "无记忆文件"}


def check_outline_chapter(outline_file: str, chapter: int) -> dict:
    """
    从细纲文件提取章节信息。
    支持 JSON 格式的细纲。
    """
    try:
        with open(outline_file, "r", encoding="utf-8") as f:
            outline = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"exists": False, "data": None, "warning": "细纲文件不存在或格式错误"}

    # 尝试从 outline 中找到对应章节
    chapters = outline.get("chapters", outline.get("outline", []))
    if isinstance(chapters, list) and len(chapters) >= chapter:
        ch_data = chapters[chapter - 1]
        return {"exists": True, "data": ch_data, "warning": None}

    # 尝试按 key 查找
    key = f"chapter_{chapter}"
    if key in outline:
        return {"exists": True, "data": outline[key], "warning": None}

    return {"exists": False, "data": None, "warning": f"细纲中未找到第{chapter}章"}


def extract_title_keywords(title: str) -> list:
    """
    从章节标题提取关键词（>=2字的中文词）。
    """
    clean = re.sub(r'^第[零一二三四五六七八九十\d]+章\s*', '', title.strip())
    keywords = re.findall(r'[一-龥]{2,}', clean)
    stop = {'之', '的', '了', '在', '是', '有', '和', '与', '及'}
    return [kw for kw in keywords if kw not in stop]


def check_first_300_conflict_keywords() -> list:
    """
    返回前300字冲突/悬念检测用的关键词列表。
    """
    return [
        '突然', '猛然', '冷不丁', '砰', '轰', '喊', '叫', '冲', '跑',
        '追', '逃', '打', '杀', '破', '碎', '裂', '撞', '跌', '闪',
        '但是', '然而', '却', '可是', '没想到', '竟然', '居然',
        '"', '"', "’", '?', '？', '！',
    ]


# ============================================================
# 主检查流程
# ============================================================

def run_pre_write_check(
    novel_dir: str,
    chapter: int,
    title: str = "",
    outline_file: str = "",
    banned_words_file: str = "",
    answers: dict = None,
) -> dict:
    """
    执行完整写前检查。

    Args:
        novel_dir: 小说目录路径
        chapter: 章节号
        title: 章节标题
        outline_file: 细纲文件路径
        banned_words_file: AI禁止词文件路径
        answers: 9问答案 {"1": "答案文本", "2": "答案文本", ...}

    Returns:
        检查报告字典
    """
    report = {
        "chapter": chapter,
        "title": title or f"第{chapter}章",
        "score": 0,
        "pass": False,
        "nine_questions": [],
        "five_checks": [],
        "warnings": [],
        "info": {},
    }

    ndir = Path(novel_dir)

    # ---- 9 问必答 ----
    total_score = 0
    if answers:
        for q in QUESTIONS:
            qid = str(q["id"])
            answer = answers.get(qid, "").strip()
            score = 0
            if answer and len(answer) >= 5:
                score = q["weight"]
            elif answer and len(answer) > 0:
                score = q["weight"] // 2  # 答案太短给一半分
            total_score += score
            report["nine_questions"].append({
                "id": q["id"],
                "name": q["name"],
                "weight": q["weight"],
                "answer": answer,
                "score": score,
            })
    else:
        # 无答案时标记为待填写
        for q in QUESTIONS:
            report["nine_questions"].append({
                "id": q["id"],
                "name": q["name"],
                "weight": q["weight"],
                "answer": "",
                "score": 0,
                "status": "待填写",
            })

    report["score"] = total_score
    report["pass"] = total_score >= PASS_THRESHOLD

    # ---- 5 项写前检查 ----
    checks = []

    # Check 1: AI 词黑名单加载
    if banned_words_file:
        banned = load_banned_words(banned_words_file)
        checks.append({
            "name": "AI词黑名单已加载",
            "pass": len(banned) > 0,
            "detail": f"已加载 {len(banned)} 个禁止词: {', '.join(banned[:10])}{'...' if len(banned) > 10 else ''}",
        })
    else:
        # 默认从知识库读取
        default_path = Path(__file__).parent.parent.parent / "knowledge_base" / "50_Quality" / "闭环质量控制.md"
        if default_path.exists():
            banned = load_banned_words(str(default_path))
            checks.append({
                "name": "AI词黑名单已加载",
                "pass": len(banned) > 0,
                "detail": f"从知识库加载 {len(banned)} 个禁止词",
            })
        else:
            checks.append({
                "name": "AI词黑名单已加载",
                "pass": False,
                "detail": "未指定禁止词文件，使用默认: ['像是']",
            })

    # Check 2: 上一章已读取
    prev_info = check_previous_chapter_exists(novel_dir, chapter)
    if prev_info["exists"]:
        checks.append({
            "name": "上一章已读取",
            "pass": True,
            "detail": prev_info.get("warning", f"已读取: {prev_info.get('path', 'N/A')}"),
        })
        report["info"]["prev_chapter_path"] = prev_info.get("path")
    else:
        checks.append({
            "name": "上一章已读取",
            "pass": False,
            "detail": prev_info.get("warning", "上一章不存在"),
        })

    # Check 3: 记忆包已加载
    mem_info = check_memory_pack(novel_dir, chapter)
    if mem_info["exists"]:
        checks.append({
            "name": "记忆包已加载",
            "pass": True,
            "detail": mem_info.get("warning", f"已加载: {mem_info.get('path')}"),
        })
    else:
        checks.append({
            "name": "记忆包已加载",
            "pass": False,
            "detail": mem_info.get("warning", "无记忆文件"),
        })

    # Check 4: 标题关键词已提取
    keywords = extract_title_keywords(title)
    if keywords:
        checks.append({
            "name": "标题关键词已提取",
            "pass": True,
            "detail": f"提取到 {len(keywords)} 个关键词: {', '.join(keywords)}",
        })
    else:
        checks.append({
            "name": "标题关键词已提取",
            "pass": True,  # 标题可能没有有效关键词，写作时注意即可
            "detail": "标题无有效关键词，写作时注意标题匹配",
        })
    report["info"]["title_keywords"] = keywords

    # Check 5: 细纲章节信息
    if outline_file:
        outline_info = check_outline_chapter(outline_file, chapter)
        if outline_info["exists"]:
            checks.append({
                "name": "细纲章节信息已确认",
                "pass": True,
                "detail": f"已从细纲读取第{chapter}章信息",
            })
            report["info"]["outline_data"] = outline_info["data"]
        else:
            checks.append({
                "name": "细纲章节信息已确认",
                "pass": False,
                "detail": outline_info.get("warning", "细纲信息缺失"),
            })

    report["five_checks"] = checks

    # 汇总警告
    all_pass_count = sum(1 for c in checks if c["pass"])
    if all_pass_count < len(checks):
        failed = [c["name"] for c in checks if not c["pass"]]
        report["warnings"].append(f"写前检查未全部通过: {', '.join(failed)}")

    return report


def format_report(report: dict) -> str:
    """格式化写前检查报告。"""
    lines = []
    lines.append("=" * 50)
    lines.append(f"  写前检查报告 — {report['title']}")
    lines.append("=" * 50)
    lines.append("")

    # 9 问评分
    lines.append("【9问必答系统】")
    total = report["score"]
    status = "✅" if report["pass"] else "❌"
    lines.append(f"  总分: {status} {total}/100 (通过线: {PASS_THRESHOLD})")
    lines.append("")
    for q in report["nine_questions"]:
        q_status = "✅" if q["score"] > 0 else "❌"
        answer_preview = q.get("answer", "")[:40] or "(未填写)"
        lines.append(f"  Q{q['id']} {q['name']} ({q['weight']}分): {q_status} {q['score']}分")
        if answer_preview != "(未填写)":
            lines.append(f"      → {answer_preview}")
    lines.append("")

    # 5 项检查
    lines.append("【写前5项检查】")
    for c in report["five_checks"]:
        c_status = "✅" if c["pass"] else "❌"
        lines.append(f"  {c_status} {c['name']}: {c['detail']}")
    lines.append("")

    # 最终结论
    if report["pass"]:
        lines.append("=" * 50)
        lines.append(f"  ✅ 写前检查通过，可以开始写正文！")
        lines.append("=" * 50)
    else:
        lines.append("=" * 50)
        lines.append(f"  ❌ 9问总分 {report['score']} 分 (需≥{PASS_THRESHOLD}分)")
        lines.append(f"  请完善以上答案后再开始写作")
        lines.append("=" * 50)

    if report["warnings"]:
        lines.append("")
        lines.append("【注意事项】")
        for w in report["warnings"]:
            lines.append(f"  ⚠️ {w}")

    lines.append("")
    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="写前检查脚本 — 9问必答 + 5项写前检查")
    parser.add_argument("--novel-dir", required=True, help="小说目录路径")
    parser.add_argument("--chapter", required=True, type=int, help="章节号")
    parser.add_argument("--title", default="", help="章节标题")
    parser.add_argument("--outline-file", default="", help="细纲文件路径(JSON)")
    parser.add_argument("--banned-words", default="", help="AI禁止词文件路径")
    parser.add_argument("--answers", default="",
                        help="9问答案(JSON格式: {\"1\":\"答案\",\"2\":\"答案\",...})")
    parser.add_argument("--output", help="输出检查报告到JSON文件")
    args = parser.parse_args()

    answers = {}
    if args.answers:
        try:
            answers = json.loads(args.answers)
        except json.JSONDecodeError:
            print(f"警告: --answers JSON 解析失败: {args.answers}")

    report = run_pre_write_check(
        novel_dir=args.novel_dir,
        chapter=args.chapter,
        title=args.title,
        outline_file=args.outline_file,
        banned_words_file=args.banned_words,
        answers=answers,
    )

    print(format_report(report))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"检查报告已保存到 {args.output}")

    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
