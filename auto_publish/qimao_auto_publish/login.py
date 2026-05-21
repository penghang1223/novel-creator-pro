#!/usr/bin/env python3
"""
七猫作家专区登录脚本
支持手机验证码登录和账号密码登录，保存Cookie到state.json
"""
import os
import json
import time
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://zuozhe.qimao.com/front/register-login/login"
STATE_FILE = "state.json"


def main():
    print("=" * 60)
    print("七猫作家专区登录工具")
    print("=" * 60)

    if os.path.exists(STATE_FILE):
        print(f"\n检测到已有 {STATE_FILE}，本次将加载上次的登录状态。")
        print("如果状态已过期，可在浏览器中重新登录后保存。")

    print("\n请在弹出的浏览器中登录七猫作家账号")
    print("支持：手机号登录（验证码）/ 账号密码登录")
    print("登录成功并进入作家专区首页后，回到终端按回车继续...")
    try:
        input("\n按回车键启动浏览器...")
    except EOFError:
        print("\n（非交互模式，自动启动浏览器...）")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if os.path.exists(STATE_FILE):
            context = browser.new_context(storage_state=STATE_FILE)
        else:
            context = browser.new_context()

        page = context.new_page()

        print("\n正在打开七猫作家专区...")
        try:
            page.goto(LOGIN_URL, timeout=60000)
        except Exception as e:
            print(f"打开网页遇到问题，请检查网络: {e}")
            print("浏览器仍然保持打开，您可以手动在地址栏输入 https://zuozhe.qimao.com")

        # 检查是否已经登录（被重定向到首页）
        page.wait_for_timeout(3000)
        current_url = page.url
        if "login" not in current_url.lower():
            print("检测到可能已经登录，直接保存状态...")
            try:
                storage = context.storage_state()
                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(storage, f, ensure_ascii=False, indent=2)
                print(f"[✅ 登录状态已保存到 {STATE_FILE}]")
                browser.close()
                return
            except Exception as e:
                print(f"保存状态失败: {e}")

        # 等待用户手动登录
        print("\n" + "=" * 50)
        print("浏览器已打开七猫作家登录页面。")
        print("请完成以下操作：")
        print("  1. 选择登录方式（手机号登录 / 账号密码登录）")
        print("  2. 输入手机号和验证码（或密码）")
        print("  3. 勾选底部协议复选框")
        print("  4. 点击【立即登录】")
        print("  5. 确认进入作家专区首页后，回到这里按回车")
        print("=" * 50)

        # 自动轮询检测登录状态
        max_wait = 300  # 5分钟
        waited = 0
        input_ready = False

        print(f"\n等待登录中（最长{max_wait}秒，也可随时按回车跳过等待）...")

        # 在后台检测登录状态
        import threading
        def check_login():
            nonlocal waited, input_ready
            while waited < max_wait:
                try:
                    current_url = page.url
                    if "login" not in current_url.lower() and "zuozhe.qimao.com" in current_url:
                        # 登录成功，URL不再包含login
                        print("\n检测到登录成功！")
                        input_ready = True
                        return
                except Exception:
                    pass
                time.sleep(2)
                waited += 2
                if waited % 30 == 0 and not input_ready:
                    print(f"等待中...（已等待{waited}秒）")

        checker = threading.Thread(target=check_login, daemon=True)
        checker.start()

        # 等待用户回车或自动检测到登录
        try:
            input()
        except EOFError:
            # 非交互模式，等待自动检测
            checker.join(timeout=max_wait)

        # 保存登录状态
        print("\n正在保存登录状态...")
        try:
            storage = context.storage_state()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=2)
            print(f"[✅ 登录状态已保存到 {STATE_FILE}]")
            print("以后运行自动发布脚本时，会自动加载这个文件，无需再次手动登录。")
        except Exception as e:
            print(f"保存状态失败: {e}")

        browser.close()


if __name__ == "__main__":
    main()
