#!/usr/bin/env python3
"""
文件引用计数更新脚本
扫描 novel_output/{小说名}/摘要/ 下所有 chapter_*_summary.json，
汇总 knowledge_references 字段，更新 file_reference_count.json。

用法:
  python .claude/memory/references/update_reference_count.py --novel-dir "novel_output/番茄/被裁员后我觉醒了神级投资系统"
"""

import argparse
import json
import os
import glob
from datetime import datetime


def scan_summaries(novel_dir):
    """扫描所有章节摘要JSON，提取引用记录"""
    summary_dir = os.path.join(novel_dir, "摘要")
    if not os.path.exists(summary_dir):
        print(f"摘要目录不存在: {summary_dir}")
        return {}

    references = {}  # file_path -> {count, chapters, categories}

    for f in sorted(glob.glob(os.path.join(summary_dir, "chapter_*_summary.json"))):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  跳过 {f}: {e}")
            continue

        chapter = data.get("chapter", 0)
        refs = data.get("knowledge_references", [])

        for ref in refs:
            path = ref.get("file", "")
            if not path:
                continue
            if path not in references:
                references[path] = {"count": 0, "chapters": [], "categories": []}
            references[path]["count"] += 1
            if chapter not in references[path]["chapters"]:
                references[path]["chapters"].append(chapter)
            cat = ref.get("purpose", "unknown")
            if cat not in references[path]["categories"]:
                references[path]["categories"].append(cat)

    return references


def update_count_file(count_file, scanned_refs, novel_name):
    """合并扫描结果到引用计数文件"""
    if os.path.exists(count_file):
        with open(count_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        data = {
            "project": novel_name,
            "last_updated": "",
            "description": "文件引用计数",
            "files": {}
        }

    data["project"] = novel_name
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # 合并扫描到的引用
    for path, info in scanned_refs.items():
        if path not in data["files"]:
            data["files"][path] = {
                "count": 0,
                "chapters": [],
                "categories": [],
                "role": "auto-detected"
            }
        # 用扫描结果覆盖
        data["files"][path]["count"] = info["count"]
        data["files"][path]["chapters"] = sorted(info["chapters"])
        data["files"][path]["categories"] = info["categories"]

    # 手动添加的未被摘要引用但重要的文件保持不变
    # 如果文件不在扫描结果中但已在count文件中，保留但不更新

    # 按引用次数降序排列
    sorted_files = dict(sorted(
        data["files"].items(),
        key=lambda x: x[1]["count"],
        reverse=True
    ))
    data["files"] = sorted_files

    with open(count_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    return data


def print_report(data):
    """打印引用统计报告"""
    print(f"\n{'='*60}")
    print(f"  文件引用统计 — {data['project']}")
    print(f"  更新时间: {data['last_updated']}")
    print(f"{'='*60}\n")

    hot = []   # count >= 2
    warm = []  # count == 1
    cold = []  # count == 0

    for path, info in data["files"].items():
        entry = (path, info["count"], info.get("role", ""))
        if info["count"] >= 2:
            hot.append(entry)
        elif info["count"] == 1:
            warm.append(entry)
        else:
            cold.append(entry)

    if hot:
        print("  [高频] 每章都引用:")
        for path, count, role in hot:
            print(f"    {count}次  {path}  ({role})")
        print()

    if warm:
        print("  [中频] 偶尔引用:")
        for path, count, role in warm:
            print(f"    {count}次  {path}  ({role})")
        print()

    if cold:
        print("  [未引用] 从未被引用（排查是否需要或应清理）:")
        for path, count, role in cold:
            print(f"    {count}次  {path}  ({role})")
        print()

    total = len(data["files"])
    hot_pct = len(hot) / total * 100 if total else 0
    cold_pct = len(cold) / total * 100 if total else 0
    print(f"  总计: {total} 个文件 | 高频: {len(hot)}({hot_pct:.0f}%) | 未引用: {len(cold)}({cold_pct:.0f}%)")


def main():
    parser = argparse.ArgumentParser(description="更新文件引用计数")
    parser.add_argument("--novel-dir", required=True, help="小说项目目录")
    parser.add_argument("--count-file", default=None, help="引用计数文件路径")
    args = parser.parse_args()

    novel_dir = args.novel_dir
    if args.count_file:
        count_file = args.count_file
    else:
        count_file = os.path.join(".claude", "memory", "references", "file_reference_count.json")

    # 从目录名推断小说名
    novel_name = os.path.basename(os.path.normpath(novel_dir))

    print(f"扫描目录: {novel_dir}")
    scanned = scan_summaries(novel_dir)
    print(f"扫描到 {len(scanned)} 个被引用的文件")

    data = update_count_file(count_file, scanned, novel_name)
    print(f"已更新: {count_file}")

    print_report(data)


if __name__ == "__main__":
    main()
