#!/usr/bin/env python3
"""
小说/短故事输出 → 番茄发布目录同步脚本

支持两种模式：
  - 小说连载：novel_output/书名/正文/*.md → fanqie_auto_publish/chapters/书名/*.txt
  - 短故事：  novel_output/006_短篇小说/NN_书名/正文/*.md → fanqie_auto_publish/short_chapters/书名/*.txt

用法:
    python sync_to_fanqie.py                          # 同步所有小说
    python sync_to_fanqie.py --short                  # 同步所有短故事
    python sync_to_fanqie.py "书名"                   # 同步指定小说
    python sync_to_fanqie.py --short "书名"           # 同步指定短故事
    python sync_to_fanqie.py --list                   # 列出所有可同步的小说
    python sync_to_fanqie.py --short --list           # 列出所有可同步的短故事
"""
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
NOVEL_OUTPUT = PROJECT_ROOT / "novel_output"
FANQIE_CHAPTERS = PROJECT_ROOT / "fanqie_auto_publish" / "chapters"
FANQIE_SHORT_CHAPTERS = PROJECT_ROOT / "fanqie_auto_publish" / "short_chapters"
SHORT_STORY_DIR = NOVEL_OUTPUT / "006_短篇小说"


def md_to_text(md_path):
    """将 .md 章节文件转为纯文本内容（去掉 markdown 标题和分隔线）"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    clean_lines = []
    skipped_header = False
    skipped_sep = False
    for line in lines:
        if not skipped_header and line.startswith("# "):
            skipped_header = True
            continue
        if not skipped_sep and line.strip() == "---":
            skipped_sep = True
            continue
        clean_lines.append(line)

    return "\n".join(clean_lines).strip()


def list_novels():
    """列出 novel_output 下所有有正文章节的小说（不含006_短篇小说）"""
    novels = []
    if not NOVEL_OUTPUT.exists():
        return novels

    for name in sorted(os.listdir(NOVEL_OUTPUT)):
        if name.startswith("006_短篇小说"):
            continue
        novel_dir = NOVEL_OUTPUT / name
        if not novel_dir.is_dir():
            continue
        zhengwen_dir = novel_dir / "正文"
        if zhengwen_dir.is_dir():
            md_files = list(zhengwen_dir.glob("*.md"))
            if md_files:
                novels.append((name, len(md_files)))
    return novels


def list_short_stories():
    """列出 006_短篇小说 下所有有正文章节的短故事"""
    stories = []
    if not SHORT_STORY_DIR.exists():
        return stories

    for name in sorted(os.listdir(SHORT_STORY_DIR)):
        story_dir = SHORT_STORY_DIR / name
        if not story_dir.is_dir():
            continue
        # 提取真实书名（去掉前面的编号前缀，如 "007_"）
        real_name = re.sub(r'^\d+_', '', name)
        zhengwen_dir = story_dir / "正文"
        if zhengwen_dir.is_dir():
            md_files = list(zhengwen_dir.glob("*.md"))
            if md_files:
                stories.append((real_name, len(md_files), name))
    return stories


def sync_novel(novel_name: str) -> int:
    """同步一本小说，返回新增/更新的章节数"""
    novel_dir = NOVEL_OUTPUT / novel_name
    zhengwen_dir = novel_dir / "正文"
    target_dir = FANQIE_CHAPTERS / novel_name

    if not zhengwen_dir.is_dir():
        print(f"  ❌ 未找到正文目录: {zhengwen_dir}")
        return 0

    md_files = sorted(zhengwen_dir.glob("*.md"))
    if not md_files:
        print(f"  ⚠️ 没有 .md 章节文件")
        return 0

    os.makedirs(target_dir, exist_ok=True)

    synced = 0
    for md_file in md_files:
        filename = md_file.name
        txt_name = filename.replace(".md", ".txt")
        txt_path = target_dir / txt_name

        # 跳过已存在（已同步过）
        if txt_path.exists():
            uploaded_path = PROJECT_ROOT / "fanqie_auto_publish" / "uploaded" / novel_name / txt_name
            if uploaded_path.exists():
                continue

        text = md_to_text(md_file)
        if text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            synced += 1
            print(f"  ✅ {filename} → {txt_name}")
        else:
            print(f"  ⚠️ {filename} 内容为空，跳过")

    return synced


def sync_short_story(real_name: str, folder_name: str) -> int:
    """同步一个短故事，返回新增章节数"""
    story_dir = SHORT_STORY_DIR / folder_name
    zhengwen_dir = story_dir / "正文"
    target_dir = FANQIE_SHORT_CHAPTERS / real_name

    if not zhengwen_dir.is_dir():
        print(f"  ❌ 未找到正文目录: {zhengwen_dir}")
        return 0

    md_files = sorted(zhengwen_dir.glob("*.md"))
    if not md_files:
        print(f"  ⚠️ 没有 .md 章节文件")
        return 0

    os.makedirs(target_dir, exist_ok=True)

    synced = 0
    for md_file in md_files:
        filename = md_file.name
        # 文件名中的 _ 替换为 - （如 第1章_标题.md -> 第1章-标题.txt）
        txt_name = filename.replace(".md", ".txt").replace("_", "-", 1)
        txt_path = target_dir / txt_name

        if txt_path.exists():
            uploaded_path = FANQIE_SHORT_CHAPTERS / "uploaded" / real_name / txt_name
            if uploaded_path.exists():
                continue

        text = md_to_text(md_file)
        if text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            synced += 1
            print(f"  ✅ {filename} → {txt_name}")
        else:
            print(f"  ⚠️ {filename} 内容为空，跳过")

    return synced


def main():
    args = sys.argv[1:]
    is_short = "--short" in args
    is_list = "--list" in args

    # 移除标记参数，剩下的就是书名
    book_args = [a for a in args if a not in ("--short", "--list")]

    if is_list:
        if is_short:
            print("短故事列表：\n")
            for real_name, count, _ in list_short_stories():
                target = FANQIE_SHORT_CHAPTERS / real_name
                pending = len(list(target.glob("*.txt"))) if target.exists() else 0
                print(f"  📚 {real_name}  （{count} 章正文, {pending} 章待发）")
        else:
            print("小说列表：\n")
            for name, count in list_novels():
                target = FANQIE_CHAPTERS / name
                pending = len(list(target.glob("*.txt"))) if target.exists() else 0
                print(f"  📚 {name}  （{count} 章正文, {pending} 章待发）")
        print()
        return

    if book_args:
        # 同步指定书名
        target_name = book_args[0]

        if is_short:
            # 模糊匹配短故事
            matched = None
            for real_name, count, folder_name in list_short_stories():
                if target_name.lower() in real_name.lower() or target_name.lower() in folder_name.lower():
                    matched = (real_name, folder_name)
                    break

            if matched:
                real_name, folder_name = matched
                print(f"📚 同步短故事：{real_name}\n")
                synced = sync_short_story(real_name, folder_name)
                print(f"\n✅ 同步完成：{synced} 章已转换")
            else:
                print(f"❌ 未找到短故事：{target_name}")
        else:
            # 模糊匹配小说
            matched = None
            for name, count in list_novels():
                if target_name.lower() in name.lower():
                    matched = name
                    break

            if matched:
                print(f"📚 同步小说：{matched}\n")
                synced = sync_novel(matched)
                print(f"\n✅ 同步完成：{synced} 章已转换")
            else:
                print(f"❌ 未找到小说：{target_name}")
    else:
        # 同步全部
        if is_short:
            print("🔄 扫描所有短故事...\n")
            total = 0
            for real_name, count, folder_name in list_short_stories():
                synced = sync_short_story(real_name, folder_name)
                if synced > 0:
                    print(f"  → {real_name}: {synced} 章")
                    total += synced
            print(f"\n✅ 全部同步完成：共 {total} 章")
        else:
            print("🔄 扫描所有小说...\n")
            total = 0
            for name, count in list_novels():
                synced = sync_novel(name)
                if synced > 0:
                    print(f"  → {name}: {synced} 章")
                    total += synced
            print(f"\n✅ 全部同步完成：共 {total} 章")


if __name__ == "__main__":
    main()
