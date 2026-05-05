#!/usr/bin/env python3
"""
写作门禁脚本 (Writing Gate) — Pass 1 → Pass 2 之间的轻量检查。

用法:
  python writing_gate.py --chapter "正文/第003章-xxx.md" --novel-dir "novel_output/七猫/小说名/"

退出码:
  0 = 通过，可以进入 Pass 2
  1 = 不通过，需要重写/修复
"""

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 词库（与 post_write_audit.py 保持一致）
# ============================================================

ABSOLUTE_BANNED = [
    "切面", "旁白", "镜头", "转场",  # 元叙事工艺术语
    "从而", "以此", "进一步凸显", "这表明", "这说明", "这反映了",
    "总而言之", "不言而喻", "他是一个",
]

# ============================================================
# 平台默认字数
# ============================================================

PLATFORM_DEFAULTS = {
    "番茄": (2800, 3200),
    "七猫": (2800, 3200),
    "起点": (2000, 4000),
    "知乎": (3000, 5000),
}


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    return sum(1 for c in text if '一' <= c <= '鿿')


def load_word_count_range(novel_dir: str) -> tuple:
    """从 novel_state.json 读取字数范围，未设置则按平台默认"""
    state_path = Path(novel_dir) / "novel_state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        if "word_count_range" in state:
            r = state["word_count_range"]
            return (r[0], r[1])
    # 按目录名推断平台
    for platform, default in PLATFORM_DEFAULTS.items():
        if platform in novel_dir:
            return default
    return (2800, 3200)  # 最终兜底


def check_word_count(text: str, novel_dir: str) -> tuple:
    """检查1：字数。返回 (passed, message)"""
    count = count_chinese_chars(text)
    lo, hi = load_word_count_range(novel_dir)
    if lo <= count <= hi:
        return True, f"字数 {count}（范围 {lo}-{hi}）✓"
    return False, f"字数 {count}（范围 {lo}-{hi}）✗ 需调整"


def check_chapter_boundary(text: str, novel_dir: str) -> tuple:
    """检查2：章节边界。检查章末是否包含下一章核心事件"""
    state_path = Path(novel_dir) / "novel_state.json"
    if not state_path.exists():
        return True, "无 novel_state.json，跳过边界检查"
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    hook = state.get("next_chapter_hook", "")
    if not hook:
        return True, "无 next_chapter_hook，跳过边界检查"
    # 取章末 500 字检查
    tail = text[-500:] if len(text) > 500 else text
    if hook in tail:
        return False, f"章末出现下一章核心事件「{hook[:20]}...」✗ 可能串章"
    return True, "章节边界 ✓"


def check_ping_pong(text: str) -> tuple:
    """检查3：乒乓球对话。连续 ≥5 行纯对话无描写"""
    lines = text.split("\n")
    max_consecutive = 0
    current = 0
    stripped_lines = [l.strip() for l in lines if l.strip()]
    for line in stripped_lines:
        # 判断是否为对话行（包含引号）
        is_dialogue = bool(re.search(r'["“”「」『』‘’‚‛]', line))
        if is_dialogue:
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    if max_consecutive > 5:
        return False, f"乒乓球对话：最长连续 {max_consecutive} 行纯对话 ✗（应 ≤5 行）"
    return True, f"乒乓球对话：最长连续 {max_consecutive} 行 ✓"


def check_absolute_banned(text: str) -> tuple:
    """检查4：绝对禁止词"""
    found = []
    for word in ABSOLUTE_BANNED:
        if word in text:
            found.append(word)
    if found:
        return False, f"绝对禁止词出现：{', '.join(found)} ✗"
    return True, "绝对禁止词 ✓"


def check_dialogue_ratio(text: str) -> tuple:
    """检查5：对话占比速检（WARN 级别，不阻断）"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return True, "空文件"
    dialogue_pattern = r'["“”「」『』‘’‚‛]'
    dialogue_lines = sum(1 for l in lines if re.search(dialogue_pattern, l))
    ratio = dialogue_lines / len(lines)
    if ratio < 0.25:
        return True, f"对话占比 {ratio:.1%} ⚠ 偏低（建议 ≥25%，不阻断）"
    return True, f"对话占比 {ratio:.1%} ✓"


def main():
    parser = argparse.ArgumentParser(description="写作门禁 — Pass 1 → Pass 2 轻量检查")
    parser.add_argument("--chapter", required=True, help="章节文件路径")
    parser.add_argument("--novel-dir", required=True, help="小说根目录")
    args = parser.parse_args()

    chapter_path = Path(args.chapter)
    if not chapter_path.exists():
        print(f"错误：文件不存在 {chapter_path}", file=sys.stderr)
        sys.exit(1)

    text = chapter_path.read_text(encoding="utf-8")

    checks = [
        ("字数检查", check_word_count(text, args.novel_dir)),
        ("章节边界", check_chapter_boundary(text, args.novel_dir)),
        ("乒乓球对话", check_ping_pong(text)),
        ("绝对禁止词", check_absolute_banned(text)),
        ("对话占比", check_dialogue_ratio(text)),
    ]

    all_passed = True
    print(f"\n{'='*50}")
    print(f"写作门禁检查 — {chapter_path.name}")
    print(f"{'='*50}")

    for name, (passed, msg) in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not passed:
            all_passed = False

    print(f"{'='*50}")
    if all_passed:
        print("结果：通过 ✓ 可以进入 Pass 2")
        sys.exit(0)
    else:
        print("结果：不通过 ✗ 需要修复后重跑")
        sys.exit(1)


if __name__ == "__main__":
    main()
