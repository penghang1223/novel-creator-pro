#!/usr/bin/env python3
"""
小说/短故事输出 → 番茄发布目录同步脚本

支持两种模式：
  - 小说连载：novel_output/番茄/书名/正文/*.md → auto_publish/fanqie_auto_publish/chapters/书名/*.txt
  - 短故事：  novel_output/006_短篇小说/NN_书名/正文/*.md → auto_publish/fanqie_auto_publish/short_chapters/书名/*.txt

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

sys.path.insert(0, str(Path(__file__).parent.parent / "novel_creation_promax" / "scripts"))
from pipeline_utils import (  # noqa: E402
    infer_chapter_number,
    load_passport,
    rel,
    save_passport,
    update_novel_state,
)

PROJECT_ROOT = Path(__file__).parent.parent
NOVEL_OUTPUT = PROJECT_ROOT / "novel_output"
FANQIE_NOVEL_ROOT = NOVEL_OUTPUT / "番茄"
FANQIE_CHAPTERS = PROJECT_ROOT / "auto_publish/fanqie_auto_publish" / "chapters"
FANQIE_SHORT_CHAPTERS = PROJECT_ROOT / "auto_publish/fanqie_auto_publish" / "short_chapters"
SHORT_STORY_DIRS = [
    NOVEL_OUTPUT / "006_短篇小说",
    NOVEL_OUTPUT / "短篇小说",
    NOVEL_OUTPUT / "知乎",
]


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


def safe_print(text: str = "") -> None:
    encoding = sys.stdout.encoding or "utf-8"
    print(str(text).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def mark_publish_state(novel_dir: Path, md_file: Path, txt_path: Path, *, short: bool = False) -> None:
    """Update chapter passport and novel_state.json after sync."""
    chapter = infer_chapter_number(md_file)
    if chapter is None:
        return
    title = md_file.stem
    passport = load_passport(novel_dir, chapter, title, md_file)
    passport.setdefault("publish", {})
    passport["publish"].update(
        {
            "platform": "fanqie",
            "status": "synced",
            "target_file": str(txt_path),
            "short": short,
            "synced_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_passport(novel_dir, chapter, passport)
    update_novel_state(
        novel_dir,
        chapter=chapter,
        word_count=passport.get("word_count"),
        passport=rel(novel_dir / "摘要" / f"chapter_{chapter:03d}_passport.json", novel_dir),
        publish_update={
            "platform": "fanqie",
            "last_synced_chapter": chapter,
            "last_synced_file": str(txt_path),
            "status": "synced",
            "short": short,
        },
    )


def _has_chapters(novel_dir: Path) -> bool:
    zhengwen_dir = novel_dir / "正文"
    return zhengwen_dir.is_dir() and any(zhengwen_dir.glob("*.md"))


def discover_novels():
    """Discover long-form novels, preferring novel_output/番茄/{书名}."""
    novels = []
    seen = set()
    if FANQIE_NOVEL_ROOT.exists():
        for novel_dir in sorted(FANQIE_NOVEL_ROOT.iterdir()):
            if novel_dir.is_dir() and _has_chapters(novel_dir):
                novels.append((novel_dir.name, len(list((novel_dir / "正文").glob("*.md"))), novel_dir))
                seen.add(novel_dir.resolve())

    if NOVEL_OUTPUT.exists():
        for novel_dir in sorted(NOVEL_OUTPUT.iterdir()):
            if not novel_dir.is_dir() or novel_dir.name in {"006_短篇小说", "短篇小说", "知乎"}:
                continue
            if novel_dir.resolve() in seen:
                continue
            if _has_chapters(novel_dir):
                novels.append((novel_dir.name, len(list((novel_dir / "正文").glob("*.md"))), novel_dir))
    return novels


def list_novels():
    """列出所有可同步到番茄的长篇小说。"""
    return [(name, count) for name, count, _ in discover_novels()]


def find_novel_dir(target_name: str) -> tuple[str, Path] | None:
    for name, _count, novel_dir in discover_novels():
        if target_name.lower() in name.lower():
            return name, novel_dir
    return None


def list_short_stories():
    """列出所有有正文章节的短故事。"""
    novels = []
    for root in SHORT_STORY_DIRS:
        if not root.exists():
            continue
        for story_dir in sorted(root.iterdir()):
            if not story_dir.is_dir() or not _has_chapters(story_dir):
                continue
            real_name = re.sub(r'^\d+_', '', story_dir.name)
            md_files = list((story_dir / "正文").glob("*.md"))
            novels.append((real_name, len(md_files), story_dir.name, story_dir))
    return novels


def find_short_story(target_name: str) -> tuple[str, str, Path] | None:
    for real_name, _count, folder_name, story_dir in list_short_stories():
        if target_name.lower() in real_name.lower() or target_name.lower() in folder_name.lower():
            return real_name, folder_name, story_dir
    return None


def sync_novel(novel_name: str, novel_dir: Path | None = None) -> int:
    """同步一本小说，返回新增/更新的章节数"""
    if novel_dir is None:
        found = find_novel_dir(novel_name)
        if not found:
            safe_print(f"  [FAIL] 未找到小说：{novel_name}")
            return 0
        novel_name, novel_dir = found
    zhengwen_dir = novel_dir / "正文"
    target_dir = FANQIE_CHAPTERS / novel_name

    if not zhengwen_dir.is_dir():
        safe_print(f"  [FAIL] 未找到正文目录: {zhengwen_dir}")
        return 0

    md_files = sorted(zhengwen_dir.glob("*.md"))
    if not md_files:
        safe_print("  [WARN] 没有 .md 章节文件")
        return 0

    os.makedirs(target_dir, exist_ok=True)

    synced = 0
    for md_file in md_files:
        filename = md_file.name
        txt_name = filename.replace(".md", ".txt")
        txt_path = target_dir / txt_name

        # 跳过已存在（已同步过）
        if txt_path.exists():
            uploaded_path = PROJECT_ROOT / "auto_publish/fanqie_auto_publish" / "uploaded" / novel_name / txt_name
            if uploaded_path.exists():
                continue

        text = md_to_text(md_file)
        if text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            mark_publish_state(novel_dir, md_file, txt_path, short=False)
            synced += 1
            safe_print(f"  [OK] {filename} -> {txt_name}")
        else:
            safe_print(f"  [WARN] {filename} 内容为空，跳过")

    return synced


def sync_short_story(real_name: str, folder_name: str, story_dir: Path | None = None) -> int:
    """同步一个短故事，返回新增章节数"""
    if story_dir is None:
        found = find_short_story(real_name or folder_name)
        if not found:
            safe_print(f"  [FAIL] 未找到短故事：{real_name or folder_name}")
            return 0
        real_name, folder_name, story_dir = found
    zhengwen_dir = story_dir / "正文"
    target_dir = FANQIE_SHORT_CHAPTERS / real_name

    if not zhengwen_dir.is_dir():
        safe_print(f"  [FAIL] 未找到正文目录: {zhengwen_dir}")
        return 0

    md_files = sorted(zhengwen_dir.glob("*.md"))
    if not md_files:
        safe_print("  [WARN] 没有 .md 章节文件")
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
            mark_publish_state(story_dir, md_file, txt_path, short=True)
            synced += 1
            safe_print(f"  [OK] {filename} -> {txt_name}")
        else:
            safe_print(f"  [WARN] {filename} 内容为空，跳过")

    return synced


def main():
    args = sys.argv[1:]
    is_short = "--short" in args
    is_list = "--list" in args

    # 移除标记参数，剩下的就是书名
    book_args = [a for a in args if a not in ("--short", "--list")]

    if is_list:
        if is_short:
            safe_print("短故事列表：\n")
            for real_name, count, _folder_name, _story_dir in list_short_stories():
                target = FANQIE_SHORT_CHAPTERS / real_name
                pending = len(list(target.glob("*.txt"))) if target.exists() else 0
                safe_print(f"  [BOOK] {real_name}  ({count} 章正文, {pending} 章待发)")
        else:
            safe_print("小说列表：\n")
            for name, count in list_novels():
                target = FANQIE_CHAPTERS / name
                pending = len(list(target.glob("*.txt"))) if target.exists() else 0
                safe_print(f"  [BOOK] {name}  ({count} 章正文, {pending} 章待发)")
        safe_print()
        return

    if book_args:
        # 同步指定书名
        target_name = book_args[0]

        if is_short:
            # 模糊匹配短故事
            matched = find_short_story(target_name)

            if matched:
                real_name, folder_name, story_dir = matched
                safe_print(f"[BOOK] 同步短故事：{real_name}\n")
                synced = sync_short_story(real_name, folder_name, story_dir)
                safe_print(f"\n[OK] 同步完成：{synced} 章已转换")
            else:
                safe_print(f"[FAIL] 未找到短故事：{target_name}")
        else:
            # 模糊匹配小说
            matched = find_novel_dir(target_name)

            if matched:
                name, novel_dir = matched
                safe_print(f"[BOOK] 同步小说：{name}\n")
                synced = sync_novel(name, novel_dir)
                safe_print(f"\n[OK] 同步完成：{synced} 章已转换")
            else:
                safe_print(f"[FAIL] 未找到小说：{target_name}")
    else:
        # 同步全部
        if is_short:
            safe_print("[SYNC] 扫描所有短故事...\n")
            total = 0
            for real_name, count, folder_name, story_dir in list_short_stories():
                synced = sync_short_story(real_name, folder_name, story_dir)
                if synced > 0:
                    safe_print(f"  -> {real_name}: {synced} 章")
                    total += synced
            safe_print(f"\n[OK] 全部同步完成：共 {total} 章")
        else:
            safe_print("[SYNC] 扫描所有小说...\n")
            total = 0
            for name, count, novel_dir in discover_novels():
                synced = sync_novel(name, novel_dir)
                if synced > 0:
                    safe_print(f"  -> {name}: {synced} 章")
                    total += synced
            safe_print(f"\n[OK] 全部同步完成：共 {total} 章")


if __name__ == "__main__":
    main()
