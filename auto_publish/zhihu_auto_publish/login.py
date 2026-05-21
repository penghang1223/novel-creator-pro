#!/usr/bin/env python3
"""
知乎盐选登录脚本
通过知乎账号登录，保存Cookie到state.json
"""
import json
import time
import sys
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://www.zhihu.com/signin"
STATE_FILE = "state.json"


def main():
    print("=" * 60)
    print("知乎盐选登录工具")
    print("=" * 60)
    print("\n请在弹出的浏览器中登录知乎账号")
    print("支持手机号/邮箱/扫码等方式登录")
    print("登录成功并进入创作中心后按回车继续...")
    input("\n按回车键开始...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("\n正在跳转到登录页面...")
        page.goto(LOGIN_URL, timeout=60000)
        page.wait_for_timeout(3000)

        # 检查是否已经登录
        current_url = page.url
        if "signin" not in current_url.lower() and "zhihu.com" in current_url:
            print("检测到可能已经登录，尝试保存状态...")
            try:
                storage = context.storage_state()
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(storage, f, ensure_ascii=False, indent=2)
                print(f"[✅ 登录状态已保存到 {STATE_FILE}]")
                browser.close()
                return
            except Exception as e:
                print(f"保存状态失败: {e}")

        # 等待登录完成
        print("\n等待登录...")
        print("提示：如果页面没有自动弹出登录，请手动点击登录按钮")

        # 尝试点击登录按钮
        try:
            login_btn = page.get_by_text("登录").first
            if login_btn.is_visible():
                login_btn.click(force=True)
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # 等待登录成功（URL变化或出现特定元素）
        max_wait = 300  # 5分钟
        waited = 0
        while waited < max_wait:
            try:
                # 检查是否登录成功
                current_url = page.url
                if "signin" not in current_url.lower() and "zhihu.com" in current_url:
                    # 检查是否有用户相关元素
                    if page.locator('[class*="UserLink"], [class*="author"], [class*="user-info"]').first.is_visible():
                        print("\n登录成功！")
                        break
            except Exception:
                pass

            time.sleep(2)
            waited += 2
            if waited % 30 == 0:
                print(f"等待中...（已等待{waited}秒，按Ctrl+C取消）")

        if waited >= max_wait:
            print("超时，请重试")
            browser.close()
            return

        # 保存登录状态
        print("\n正在保存登录状态...")
        try:
            storage = context.storage_state()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=2)
            print(f"[✅ 登录状态已保存到 {STATE_FILE}]")
        except Exception as e:
            print(f"保存状态失败: {e}")

        browser.close()


if __name__ == "__main__":
    main()
