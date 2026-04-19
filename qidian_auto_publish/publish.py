#!/usr/bin/env python3
"""
起点中文网（阅文作家专区）全自动发布脚本
支持：小说逐章发布
"""
import argparse
import os
import glob
import time
import shutil
import re
from playwright.sync_api import sync_playwright

STATE_FILE = "state.json"
CHAPTERS_DIR = "chapters"
UPLOADED_DIR = "uploaded"
WRITER_URL = "https://write.qq.com/portal/home"


def natural_sort_key(path):
    """按章节号数字排序，避免 '第100章' 排在 '第11章' 前面"""
    basename = os.path.basename(path)
    m = re.search(r'第(\d+)章', basename)
    return int(m.group(1)) if m else 0


def close_modals(page, max_rounds=10):
    """关闭弹窗"""
    for _ in range(max_rounds):
        try:
            clicked = False
            for txt in ["我知道了", "确定", "关闭", "跳过", "x", "X", "取消"]:
                btns = page.get_by_text(txt).element_handles()
                for btn in btns:
                    box = btn.bounding_box()
                    if box and 50 < box['y'] < 900:
                        try:
                            btn.click(force=True)
                            page.wait_for_timeout(500)
                            clicked = True
                            break
                        except Exception:
                            pass
                if clicked:
                    break
            if not clicked:
                break
        except Exception:
            break


def find_book_entry(page, book_name):
    """在阅文作家专区找到对应书籍"""
    print(f" -> 寻找【{book_name}】...")

    # 策略1: 从书籍列表卡片中查找
    try:
        cards = page.locator('div').filter(has_text=book_name)
        count = cards.count()
        for i in range(count - 1, -1, -1):
            card = cards.nth(i)
            try:
                if card.is_visible():
                    # 查找"章节管理"、"写作"、"发布"等按钮
                    for btn_text in ["写作", "发布", "章节", "编辑", "管理"]:
                        try:
                            btn = card.get_by_text(btn_text).first
                            if btn.is_visible():
                                btn.click(force=True)
                                print(f"    点击了 '{btn_text}' 按钮")
                                return True, page
                        except Exception:
                            pass
                    # 直接点击卡片
                    card.click(force=True)
                    print(f"    点击了书籍卡片")
                    return True, page
            except Exception:
                continue
    except Exception:
        pass

    # 策略2: 从书籍列表链接中查找
    try:
        links = page.locator('a[href*="book"], a[href*="novel"]').element_handles()
        for link in links:
            parent = link.evaluate('el => el.closest("[class*=book], [class*=card]")?.outerHTML || ""')
            if book_name in parent:
                link.click(force=True)
                print(f"    通过链接找到书籍")
                return True, page
    except Exception:
        pass

    return False, page


def publish_chapters(book_name, txt_files, book_chapter_dir, publish_mode, volume_dir):
    """小说章节发布流程"""
    print("\n>>> 准备启动浏览器...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        success_count = 0

        for file_path in txt_files:
            filename = os.path.basename(file_path)
            raw_title = os.path.splitext(filename)[0]

            m = re.search(r'第(\d+)章[\s_\-]*(.*)', raw_title)
            chapter_num = str(m.group(1)) if m else ""
            chapter_title = m.group(2).strip() if m else ""

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 从正文第一行提取标题（如果文件名里没有）
            if not chapter_title and lines:
                m2 = re.search(r'第.*?章[\s：:\-]*(.*)', lines[0].strip())
                if m2:
                    chapter_title = m2.group(1).strip()
            if not chapter_title:
                chapter_title = raw_title

            print(f"\n[{success_count+1}/{len(txt_files)}] 正在处理: 第{chapter_num}章 '{chapter_title}'")

            # 去除正文第一行的章节标题（避免重复）
            if lines and re.search(r'第.*?章', lines[0].strip()):
                lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]

            content = "".join(lines)

            try:
                print(" -> 跳转作家后台...")
                page.goto(WRITER_URL, timeout=60000)
                page.wait_for_timeout(4000)

                # 关闭弹窗
                print(" -> 关闭弹窗...")
                close_modals(page)
                page.wait_for_timeout(1000)

                # 找到书籍
                found, editor_page = find_book_entry(page, book_name)
                if not found:
                    raise Exception(f"未找到书籍: {book_name}")

                page.wait_for_timeout(3000)

                # 填写章节内容
                print(" -> 填写章节信息...")

                # 填写标题
                try:
                    title_input = page.locator('input[placeholder*="标题"], input[placeholder*="章节名"], input[type="text"]').first
                    if title_input.is_visible():
                        title_input.click(force=True)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)
                        title_input.fill(f"第{chapter_num}章 {chapter_title}", force=True)
                        print(f"    已填写标题")
                except Exception as e:
                    print(f"    [警告] 标题填写失败: {e}")

                # 注入正文
                print(" -> 注入正文...")
                try:
                    # 尝试多种编辑器选择器
                    editors = [
                        page.locator('.ql-editor').first,
                        page.locator('.ProseMirror').first,
                        page.locator('[contenteditable="true"]').first,
                        page.locator('textarea').first,
                        page.locator('.editor').first,
                        page.locator('.writing-area').first,
                    ]

                    editor = None
                    for ed in editors:
                        try:
                            if ed.is_visible():
                                editor = ed
                                break
                        except Exception:
                            continue

                    if editor:
                        editor.click(force=True)
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(200)

                        # 粘贴内容（更可靠的方式）
                        page.evaluate(f"""() => {{
                            navigator.clipboard.writeText(`{content[:10000]}`);
                        }}""")
                        page.keyboard.press("Control+V")
                        page.wait_for_timeout(1000)

                        print(f"    已注入正文 ({len(content)} 字)")
                    else:
                        print("  [警告] 未找到编辑器")

                except Exception as e:
                    print(f"  [警告] 正文注入失败: {e}")

                # 发布或存草稿
                if publish_mode == "draft":
                    print(" -> 点击【存草稿】...")
                    try:
                        draft_btn = page.get_by_text("存草稿").first
                        draft_btn.click(force=True)
                        page.wait_for_timeout(2000)
                        print(f"  [✅ 草稿已保存] 第{chapter_num}章")
                        success_count += 1
                    except Exception as e:
                        print(f"  [警告] 存草稿失败: {e}")
                else:
                    print(" -> 点击【发布/下一步】...")
                    try:
                        next_btn = page.get_by_text("下一步").first
                        if next_btn.is_visible():
                            next_btn.click(force=True)
                            page.wait_for_timeout(2000)

                        publish_btn = page.get_by_text("发布").first
                        if publish_btn.is_visible():
                            publish_btn.click(force=True)
                            page.wait_for_timeout(3000)

                        print(f"  [🎇 发布成功] 第{chapter_num}章 '{chapter_title}'")
                        success_count += 1
                    except Exception as e:
                        print(f"  [警告] 发布失败: {e}")

                page.wait_for_timeout(2000)

                # 归档
                dest_path = os.path.join(volume_dir, filename)
                shutil.move(file_path, dest_path)

            except Exception as e:
                print(f"!!! 处理 '第{chapter_num}章 {chapter_title}' 时出错: {e}")
                try:
                    page.screenshot(path=f"error_{chapter_num}.png", full_page=True)
                except Exception:
                    pass
                break

        mode_label = "存草稿" if publish_mode == "draft" else "发布"
        print(f"\n{'=' * 60}")
        print(f"全自动{mode_label}流程结束。本次共成功 {success_count} 章！")
        print(f"{'=' * 60}")

        browser.close()


def main():
    parser = argparse.ArgumentParser(description='起点中文网自动发布')
    parser.add_argument('--book', type=str, help='指定书名（自动选择）')
    parser.add_argument('--count', type=int, default=None, help='发布章节数量')
    parser.add_argument('--draft', action='store_true', help='存草稿模式')
    args = parser.parse_args()

    if not os.path.exists(STATE_FILE):
        print(f"找不到登录状态文件 {STATE_FILE}，请先运行 login.py 进行登录！")
        return

    root_txt_files = glob.glob(os.path.join(CHAPTERS_DIR, "*.txt"))
    if root_txt_files:
        print(f"\n[提示] {CHAPTERS_DIR}/ 根目录下有散落的 txt 文件，请放入子目录。")
        return

    book_dirs = []
    if os.path.isdir(CHAPTERS_DIR):
        for name in sorted(os.listdir(CHAPTERS_DIR)):
            sub_path = os.path.join(CHAPTERS_DIR, name)
            if os.path.isdir(sub_path):
                txts = glob.glob(os.path.join(sub_path, "*.txt"))
                if txts:
                    book_dirs.append((name, sub_path, sorted(txts, key=natural_sort_key)))

    if not book_dirs:
        print(f"\n[{CHAPTERS_DIR}] 中没有找到待发章节！")
        return

    print(f"\n{'=' * 60}")
    print(f"全自动发文（起点模式）")
    print(f"{'=' * 60}")
    for idx, (name, _, txts) in enumerate(book_dirs, 1):
        print(f"  [{idx}] {name}  （{len(txts)} 章待发）")
    print()

    if args.book:
        found = False
        for name, sub_path, files in book_dirs:
            if args.book in name:
                book_name_filter = name
                book_chapter_dir = sub_path
                txt_files = files
                found = True
                break
        if not found:
            print(f"[错误] 未找到包含 '{args.book}' 的小说")
            return
    else:
        choice = input(">>> 请选择序号：").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(book_dirs):
                raise ValueError
        except ValueError:
            print("    [错误] 无效序号")
            return
        book_name_filter, book_chapter_dir, txt_files = book_dirs[idx]

    total = len(txt_files)
    publish_count = args.count if args.count else total
    if publish_count > total:
        publish_count = total

    txt_files = txt_files[:publish_count]
    mode_label = "存草稿" if args.draft else "直接发布"
    print(f"\n已选择：【{book_name_filter}】，{mode_label} {len(txt_files)} 章")

    volume_dir = os.path.join(UPLOADED_DIR, book_name_filter)
    os.makedirs(volume_dir, exist_ok=True)
    print(f"    文件归档至：{volume_dir}/\n")

    publish_chapters(
        book_name_filter, txt_files, book_chapter_dir,
        "draft" if args.draft else "publish", volume_dir
    )


if __name__ == "__main__":
    main()
