#!/usr/bin/env python3
"""
七猫免费小说全自动发布脚本
基于 Playwright 浏览器自动化，支持逐章发布和存草稿

发布流程：
  1. 打开书籍管理页 → 找到目标书 → 点击"上传章节"
  2. 在编辑页填写标题 + 注入正文
  3. 点击"存为草稿"或"立即发布"
  4. 后续章节自动在编辑页继续（无需返回管理页）

连接已有浏览器（推荐）：
  python3 publish.py --book "书名" --draft --cdp http://localhost:9222

  需要先关闭 Chrome，然后用以下命令重新打开：
  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
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

# 七猫作家专区 URL
BASE_URL = "https://zuozhe.qimao.com"
BOOK_MANAGE_URL = f"{BASE_URL}/front/book-manage"
BOOK_UPLOAD_URL = f"{BASE_URL}/front/book-upload"


def natural_sort_key(path):
    """按章节号数字排序，避免 '第100章' 排在 '第11章' 前面"""
    basename = os.path.basename(path)
    m = re.search(r'第(\d+)章', basename)
    return int(m.group(1)) if m else 0


def close_modals(page, max_rounds=5):
    """关闭弹窗（七猫 Element UI 弹窗）

    七猫使用 localStorage 键 'zuozhe_upload_important-notice' 跳过"重要提醒"弹窗。
    首次使用时该弹窗会出现，后续不再弹出。
    """
    for _ in range(max_rounds):
        try:
            clicked = False
            # 关闭 Element UI dialog
            close_btns = page.locator(
                '.el-dialog__headerbtn, .el-message-box__headerbtn, '
                '[aria-label="Close"], .el-dialog__close'
            ).element_handles()
            for btn in close_btns:
                try:
                    if btn.is_visible():
                        btn.click(force=True)
                        page.wait_for_timeout(300)
                        clicked = True
                except Exception:
                    pass
            # 关闭文字按钮弹窗
            for txt in ["我知道了", "确定", "关闭", "好的", "明白了", "取消"]:
                try:
                    btn = page.get_by_text(txt).first
                    if btn.is_visible():
                        box = btn.bounding_box()
                        if box and 50 < box['y'] < 900:
                            btn.click(force=True)
                            page.wait_for_timeout(300)
                            clicked = True
                            break
                except Exception:
                    pass
            if not clicked:
                break
        except Exception:
            break


def find_book_and_get_upload_url(page, book_name):
    """在书籍管理页找到目标书，返回上传页面的 URL

    返回: upload_url (str) 或 None
    """
    print(f" -> 在书籍管理页寻找【{book_name}】...")

    # 等待页面加载
    page.wait_for_timeout(2000)
    close_modals(page)

    # 策略1: 找到包含书名的卡片，点击"上传章节"按钮
    try:
        # 找到所有包含书名的链接
        book_link = page.locator(f'a:has-text("{book_name}")').first
        if book_link.is_visible():
            # 找到同卡片下的"上传章节"按钮
            card = book_link.locator('xpath=ancestor::li | ancestor::div[contains(@class,"card")]').first
            upload_btn = card.get_by_text("上传章节").first
            if upload_btn.is_visible():
                print(f"    找到【上传章节】按钮")
                return "click_upload"  # 标记需要点击
    except Exception:
        pass

    # 策略2: 遍历所有书籍卡片
    try:
        all_cards = page.locator('ul > li, [class*="book-item"]').element_handles()
        for card in all_cards:
            try:
                card_text = card.evaluate('el => el.textContent')
                if book_name in card_text:
                    # 在这个卡片里找"上传章节"
                    upload_btn = card.evaluate_handle(
                        'el => el.querySelector("a") && [...el.querySelectorAll("a")].find(a => a.textContent.includes("上传章节"))'
                    )
                    if upload_btn:
                        upload_btn.click()
                        print(f"    通过卡片遍历找到并点击了【上传章节】")
                        return "clicked"
            except Exception:
                continue
    except Exception:
        pass

    return None


def inject_content(page, content):
    """注入正文到七猫富文本编辑器

    七猫使用 div.q-contenteditable.book 作为主编辑器
    """
    # 定位主编辑器
    editor = page.locator('div.q-contenteditable.book').first

    try:
        if not editor.is_visible():
            # 回退选择器
            editor = page.locator('[contenteditable="true"]').first
    except Exception:
        editor = page.locator('[contenteditable="true"]').first

    try:
        editor.click(force=True)
        page.wait_for_timeout(300)

        # 清空现有内容
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(200)

        # 通过 JS 直接设置 innerText（最可靠的方式）
        editor.evaluate("""(el, text) => {
            el.focus();
            el.innerText = text;
            // 触发 Vue 响应式更新
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }""", content[:50000])

        print(f"    已注入正文 ({len(content)} 字)")
        return True

    except Exception as e:
        print(f"  [警告] JS注入失败，尝试粘贴方式: {e}")
        # 回退：分段粘贴
        try:
            editor.click(force=True)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
            for chunk in chunks:
                page.evaluate("""(text) => {
                    navigator.clipboard.writeText(text);
                }""", chunk)
                page.keyboard.press("Control+V")
                page.wait_for_timeout(300)
            print(f"    已分段粘贴正文 ({len(content)} 字)")
            return True
        except Exception as e2:
            print(f"  [错误] 正文注入全部失败: {e2}")
            return False


def fill_title(page, chapter_title):
    """填写章节标题

    七猫标题输入框: input[placeholder="请输入章节名称，最多20个字"]
    """
    try:
        title_input = page.locator(
            'input[placeholder*="章节名称"], input[placeholder*="章节名"]'
        ).first

        if not title_input.is_visible():
            # 回退
            title_input = page.locator('input.el-input__inner').first

        title_input.click(force=True)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.wait_for_timeout(200)

        # 七猫标题最多20个字
        title_to_fill = chapter_title[:20] if chapter_title else ""
        title_input.fill(title_to_fill, force=True)
        print(f"    已填写标题: {title_to_fill}")
        return True
    except Exception as e:
        print(f"    [警告] 标题填写失败: {e}")
        return False


def handle_important_notice_dialog(page, timeout=15):
    """处理七猫"重要提醒"对话框

    点击发布/草稿后弹出的法规提醒，带5秒倒计时。
    按钮文字格式: "我已阅读并知晓(N)" 倒计时到0后变为 "我已阅读并知晓"
    """
    for _ in range(timeout):
        try:
            # 查找对话框中的确认按钮
            btn = page.locator('a:has-text("我已阅读并知晓")').first
            if btn.is_visible():
                text = btn.inner_text()
                # 检查倒计时是否结束（没有括号数字）
                if "(" not in text:
                    btn.click(force=True)
                    print(f"    已确认重要提醒")
                    page.wait_for_timeout(1000)
                    return True
        except Exception:
            pass
        page.wait_for_timeout(1000)

    # 超时强制点击
    try:
        btn = page.locator('a:has-text("我已阅读并知晓")').first
        if btn.is_visible():
            btn.click(force=True)
            print(f"    强制确认重要提醒（倒计时超时）")
            return True
    except Exception:
        pass
    return False


def click_publish_action(page, mode):
    """点击发布/草稿按钮

    七猫底部按钮:
      - 存为草稿: "存为草稿" 链接
      - 立即发布: "立即发布" 链接
      - 定时发布: "定时发布" 链接

    点击后会弹出"重要提醒"对话框（含5秒倒计时）
    """
    try:
        btn_text = "存为草稿" if mode == "draft" else "立即发布"
        btn = page.locator(f'a:has-text("{btn_text}")').first
        btn.click(force=True)
        print(f"    已点击 [{btn_text}]")
        page.wait_for_timeout(1000)

        # 处理"重要提醒"对话框
        handle_important_notice_dialog(page)

        # 等待页面跳转（成功后会跳到草稿箱或章节管理页）
        page.wait_for_timeout(3000)

        return "draft" if mode == "draft" else "published"
    except Exception as e:
        print(f"  [错误] 操作按钮点击失败: {e}")
        return None


def publish_chapters(book_name, txt_files, publish_mode, volume_dir, cdp_url=None):
    """小说章节发布流程

    Args:
        cdp_url: Chrome DevTools Protocol URL，如 "http://localhost:9222"
                 提供时连接到已有浏览器（共享登录态），否则启动新实例
    """
    with sync_playwright() as p:
        if cdp_url:
            print(f"\n>>> 连接到已有 Chrome 浏览器: {cdp_url}")
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
        else:
            print("\n>>> 准备启动浏览器...")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=STATE_FILE)
            page = context.new_page()

        success_count = 0
        first_chapter = True

        for idx, file_path in enumerate(txt_files):
            filename = os.path.basename(file_path)
            raw_title = os.path.splitext(filename)[0]

            m = re.search(r'第(\d+)章[\s_\-]*(.*)', raw_title)
            chapter_num = str(m.group(1)) if m else ""
            chapter_title = m.group(2).strip() if m else ""

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 从正文第一行提取标题
            if not chapter_title and lines:
                m2 = re.search(r'第.*?章[\s：:\-]*(.*)', lines[0].strip())
                if m2:
                    chapter_title = m2.group(1).strip()
            if not chapter_title:
                chapter_title = raw_title

            print(f"\n[{idx+1}/{len(txt_files)}] 第{chapter_num}章 '{chapter_title}'")

            # 去除正文第一行的章节标题
            if lines and re.search(r'第.*?章', lines[0].strip()):
                lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
            content = "".join(lines)

            # 验证字数（七猫按去除空白后的字符数计算）
            char_count = len(re.sub(r'\s+', '', content))
            if char_count < 1000:
                print(f"  [跳过] 正文不足1000字（当前{char_count}字），七猫最低要求")
                continue

            try:
                # 第一章需要从书籍管理页进入
                if first_chapter:
                    print(" -> 打开书籍管理页...")
                    page.goto(BOOK_MANAGE_URL, timeout=60000)
                    page.wait_for_timeout(3000)
                    close_modals(page)

                    result = find_book_and_get_upload_url(page, book_name)
                    if result is None:
                        raise Exception(f"未找到书籍: {book_name}")

                    # 点击"上传章节"
                    if result == "click_upload":
                        try:
                            # 再次精确点击
                            upload_links = page.locator('a:has-text("上传章节")').element_handles()
                            for link in upload_links:
                                try:
                                    if link.is_visible():
                                        link.click(force=True)
                                        break
                                except Exception:
                                    continue
                        except Exception:
                            pass

                    page.wait_for_timeout(3000)
                    close_modals(page)
                    first_chapter = False

                    # 检查是否进入了编辑页面
                    if "book-upload" not in page.url:
                        print("  [提示] 可能未进入编辑页，尝试直接导航...")
                        # 从当前URL提取book_id
                        try:
                            book_id = page.evaluate("""() => {
                                const links = document.querySelectorAll('a[href*="book-upload"]');
                                for (const link of links) {
                                    const match = link.href.match(/id=(\\d+)/);
                                    if (match) return match[1];
                                }
                                return null;
                            }""")
                            if book_id:
                                import urllib.parse
                                url = f"{BOOK_UPLOAD_URL}?id={book_id}&title={urllib.parse.quote(book_name)}"
                                page.goto(url, timeout=60000)
                                page.wait_for_timeout(3000)
                        except Exception:
                            pass

                # 填写标题
                print(" -> 填写标题...")
                fill_title(page, chapter_title)

                # 注入正文
                print(" -> 注入正文...")
                inject_content(page, content)

                # 等待自动保存（七猫会自动云端保存）
                page.wait_for_timeout(2000)

                # 发布或存草稿
                mode_label = "存草稿" if publish_mode == "draft" else "发布"
                print(f" -> {mode_label}...")
                result = click_publish_action(page, publish_mode)

                if result:
                    icon = "✅" if result == "draft" else "🎇"
                    print(f"  [{icon} {'草稿已保存' if result == 'draft' else '发布成功'}] 第{chapter_num}章")
                    success_count += 1

                    # 归档
                    dest_path = os.path.join(volume_dir, filename)
                    shutil.move(file_path, dest_path)

                    # 如果还有下一章，点击"新建草稿"继续（不重新打开浏览器）
                    if idx < len(txt_files) - 1:
                        try:
                            print(" -> 点击【新建草稿】继续下一章...")
                            new_draft_btn = page.locator('a:has-text("新建草稿")').first
                            new_draft_btn.click(force=True)
                            page.wait_for_timeout(3000)
                            close_modals(page)
                            first_chapter = False
                        except Exception as e:
                            print(f"  [提示] 新建草稿点击失败，下章将从管理页重新进入: {e}")
                            first_chapter = True
                else:
                    print(f"  [失败] 第{chapter_num}章")

                page.wait_for_timeout(2000)

            except Exception as e:
                print(f"!!! 处理第{chapter_num}章时出错: {e}")
                try:
                    page.screenshot(path=f"error_{chapter_num}.png", full_page=True)
                    print(f"    错误截图: error_{chapter_num}.png")
                except Exception:
                    pass
                # 出错后重置，下一轮从管理页重新进入
                first_chapter = True
                continue

        mode_word = "存草稿" if publish_mode == "draft" else "发布"
        print(f"\n{'=' * 60}")
        print(f"七猫自动{mode_word}完成！成功 {success_count}/{len(txt_files)} 章")
        print(f"{'=' * 60}")

        if not cdp_url:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description='七猫免费小说自动发布')
    parser.add_argument('--book', type=str, help='指定书名（模糊匹配）')
    parser.add_argument('--count', type=int, default=None, help='发布章节数量')
    parser.add_argument('--draft', action='store_true', help='存草稿模式')
    parser.add_argument('--cdp', type=str, default=None,
                        help='连接已有Chrome（CDP地址，如 http://localhost:9222）')
    args = parser.parse_args()

    if not args.cdp and not os.path.exists(STATE_FILE):
        print(f"找不到 {STATE_FILE}，请先运行: python3 login.py")
        print(f"或者使用 --cdp http://localhost:9222 连接已有Chrome浏览器")
        return

    # 扫描待发布章节
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
        print(f"\n[{CHAPTERS_DIR}/] 中没有找到待发章节！")
        print(f"请将章节文件放入 {CHAPTERS_DIR}/书名/ 目录下")
        print(f"文件名格式：第001章 章节标题.txt")
        return

    # 显示书籍列表
    print(f"\n{'=' * 60}")
    print(f"七猫自动发布")
    print(f"{'=' * 60}")
    for idx, (name, _, txts) in enumerate(book_dirs, 1):
        print(f"  [{idx}] {name}  （{len(txts)} 章待发）")
    print()

    # 选择书籍
    if args.book:
        found = False
        for name, sub_path, files in book_dirs:
            if args.book in name:
                book_name = name
                book_chapter_dir = sub_path
                txt_files = files
                found = True
                break
        if not found:
            print(f"[错误] 未找到包含 '{args.book}' 的小说")
            return
    else:
        try:
            choice = input(">>> 请选择序号：").strip()
        except EOFError:
            print("非交互模式，请使用 --book 参数指定书名")
            return
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(book_dirs):
                raise ValueError
        except ValueError:
            print("    [错误] 无效序号")
            return
        book_name, book_chapter_dir, txt_files = book_dirs[idx]

    # 限制发布数量
    total = len(txt_files)
    publish_count = min(args.count or total, total)
    txt_files = txt_files[:publish_count]

    mode_label = "存草稿" if args.draft else "直接发布"
    print(f"\n已选择：【{book_name}】，{mode_label} {len(txt_files)} 章")

    volume_dir = os.path.join(UPLOADED_DIR, book_name)
    os.makedirs(volume_dir, exist_ok=True)
    print(f"    归档至：{volume_dir}/\n")

    publish_chapters(
        book_name, txt_files,
        "draft" if args.draft else "publish", volume_dir,
        cdp_url=args.cdp
    )


if __name__ == "__main__":
    main()
