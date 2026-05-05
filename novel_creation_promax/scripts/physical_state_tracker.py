#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物理状态追踪器 — 从章节文本自动提取物理状态（金钱/地点/时间），
支持跨章节一致性对比。

用法:
    # 提取本章物理状态
    python scripts/physical_state_tracker.py --chapter-file novel_output/番茄/小说/正文/ch001.md

    # 对比上一章状态
    python scripts/physical_state_tracker.py --chapter-file ch002.md --prev-state ch001_state.json

    # 输出状态文件（供下一章对比）
    python scripts/physical_state_tracker.py --chapter-file ch001.md --output ch001_state.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract_physical_state(text: str) -> dict:
    """从章节文本自动提取物理状态。"""
    # 金钱
    money_pattern = re.compile(r'(\d+)\s*(块|元|万|千|角|分)')
    money = money_pattern.findall(text)

    # 地点
    location_pattern = re.compile(
        r'(?:在|到|去|回|来|走向|坐在|站在|躺在|蹲在)([一-鿿]{2,8}(?:楼|室|厅|院|街|路|店|馆|所|房|台|场|边|前|后|里|外|旁))'
    )
    locations = list(set(location_pattern.findall(text)))

    # 时间
    time_pattern = re.compile(
        r'(?:现在|当时|此刻|已经|过了|等了|直到|直到)([一-鿿0-9]{2,10}(?:钟|小时|天|分钟|秒|点|时))'
    )
    times = list(set(time_pattern.findall(text)))

    return {
        "money": [{"amount": int(m[0]), "unit": m[1]} for m in money],
        "locations": locations,
        "time_refs": times,
    }


def validate_consistency(current: dict, previous: dict) -> list:
    """对比当前章和上一章的物理状态，检测矛盾。"""
    issues = []

    # 金钱大幅变化
    if previous.get("money") and current.get("money"):
        prev_total = sum(
            m["amount"] * (10000 if m["unit"] == "万" else 1000 if m["unit"] == "千" else 1)
            for m in previous["money"] if m["unit"] in ("块", "元", "万", "千")
        )
        curr_total = sum(
            m["amount"] * (10000 if m["unit"] == "万" else 1000 if m["unit"] == "千" else 1)
            for m in current["money"] if m["unit"] in ("块", "元", "万", "千")
        )
        if prev_total > 0 and curr_total > 0:
            change_ratio = abs(curr_total - prev_total) / prev_total
            if change_ratio > 0.5:
                issues.append(
                    f"⚠️ 金额变化较大: 上章{prev_total}元 → 本章{curr_total}元 (变化{change_ratio:.0%})"
                )

    return issues


def main():
    parser = argparse.ArgumentParser(description="物理状态追踪器")
    parser.add_argument("--chapter-file", required=True, help="章节文件路径")
    parser.add_argument("--prev-state", default="", help="上一章状态文件(JSON)")
    parser.add_argument("--output", default="", help="输出状态文件(JSON)")
    args = parser.parse_args()

    text = Path(args.chapter_file).read_text(encoding="utf-8")
    state = extract_physical_state(text)

    # 输出当前状态
    print(json.dumps(state, ensure_ascii=False, indent=2))

    # 跨章对比
    if args.prev_state:
        prev = json.loads(Path(args.prev_state).read_text(encoding="utf-8"))
        issues = validate_consistency(state, prev)
        if issues:
            print("\n" + "\n".join(issues), file=sys.stderr)

    # 保存状态文件
    if args.output:
        Path(args.output).write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n状态已保存: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
