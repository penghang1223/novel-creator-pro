#!/usr/bin/env python3
"""小说创作看板 HTTP 服务 — 零依赖，标准库 only"""

import http.server
import json
import os
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

PORT = 8080
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOVEL_OUTPUT = PROJECT_ROOT / "novel_output"
PORTFOLIO_FILE = Path(__file__).resolve().parent / "portfolio.json"
DASHBOARD_FILE = Path(__file__).resolve().parent / "dashboard.html"

SKIP_DIRS = {"素材", "短篇小说", ".DS_Store"}
IDEAS_DIR = PROJECT_ROOT / "knowledge_base" / "15_Ideas"
PROJECTS_DIR = PROJECT_ROOT / "knowledge_base" / "80_Projects"

import re


def scan_novels():
    """扫描 novel_output/ 下所有小说，读取 novel_state.json"""
    novels = []
    if not NOVEL_OUTPUT.exists():
        return novels

    for platform_dir in sorted(NOVEL_OUTPUT.iterdir()):
        if not platform_dir.is_dir() or platform_dir.name in SKIP_DIRS:
            continue
        platform = platform_dir.name

        for novel_dir in sorted(platform_dir.iterdir()):
            if not novel_dir.is_dir() or novel_dir.name.startswith("."):
                continue
            slug = novel_dir.name
            state_file = novel_dir / "novel_state.json"

            info = {
                "slug": slug,
                "platform": platform,
                "title": slug,
                "genre": "",
                "total_chapters": 0,
                "current_chapter": 0,
                "status": "未知",
                "word_count": 0,
            }

            # 读取 novel_state.json
            if state_file.exists():
                try:
                    with open(state_file, encoding="utf-8") as f:
                        data = json.load(f)
                    info["title"] = data.get("title") or slug
                    info["genre"] = data.get("genre", "")
                    info["status"] = data.get("status", "未知")
                    info["total_chapters"] = data.get("total_chapters", 0)
                    info["current_chapter"] = data.get("current_chapter", 0)
                    info["word_count"] = data.get("word_count", 0)
                except (json.JSONDecodeError, Exception):
                    pass

            # fallback: 数正文目录里的章节数
            chapters_dir = novel_dir / "正文"
            if chapters_dir.is_dir():
                chapter_files = [
                    f for f in chapters_dir.iterdir()
                    if f.suffix in (".md", ".txt")
                ]
                count = len(chapter_files)
                if info["current_chapter"] == 0:
                    info["current_chapter"] = count
                if info["total_chapters"] == 0:
                    info["total_chapters"] = max(count, 100)  # 默认目标100章

            novels.append(info)

    return novels


def scan_ideas():
    """扫描 knowledge_base/15_Ideas/ 下所有创意方案"""
    ideas = []
    if not IDEAS_DIR.exists():
        return ideas

    skip_files = {"README.md", "tools-reference.md"}

    for root, dirs, files in os.walk(IDEAS_DIR):
        # 跳过归档目录
        dirs[:] = [d for d in dirs if d not in ("惊鸿归档", "旧资料", ".obsidian")]
        for fname in sorted(files):
            if not fname.endswith(".md") or fname in skip_files:
                continue
            fpath = Path(root) / fname
            rel = fpath.relative_to(IDEAS_DIR)
            parts = rel.parts

            # 从路径推断平台
            platform = parts[0] if len(parts) > 1 else "未分类"
            if platform in ("其他", "惊鸿归档"):
                platform = "未分类"

            # 读文件提取标题和类型
            title = fname.replace(".md", "").replace("_完整小说创意方案", "").replace("_完整策划方案", "").replace("_完整策划", "")
            genre = ""

            try:
                with open(fpath, encoding="utf-8") as f:
                    lines = f.readlines()[:15]
                for line in lines:
                    line = line.strip()
                    if line.startswith("# 《") or line.startswith("#《"):
                        # 提取《书名》
                        m = re.search(r"《(.+?)》", line)
                        if m:
                            title = m.group(1)
                    elif line.startswith("# ") and not title:
                        title = line[2:].strip()[:30]
                    elif "类型：" in line or "题材" in line:
                        genre = line.split("：", 1)[-1].strip()[:30]
                    elif "目标平台：" in line:
                        p = line.split("：", 1)[-1].strip()
                        if p and platform == "未分类":
                            platform = p
            except Exception:
                pass

            ideas.append({
                "title": title,
                "platform": platform,
                "genre": genre,
                "file": str(fpath.relative_to(PROJECT_ROOT)),
                "stage": "创意",
            })

    return ideas


def scan_projects():
    """扫描 knowledge_base/80_Projects/ 获取项目信息"""
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for d in sorted(PROJECTS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        config_file = d / "_config.md"
        title = d.name
        genre = ""
        status = "创意"

        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    lines = f.readlines()[:20]
                for line in lines:
                    line = line.strip()
                    if line.startswith("# ") and not title:
                        title = line[2:].strip()
                    elif "题材" in line and "|" in line:
                        # 表格行: | 题材 | xxx |
                        parts = line.split("|")
                        if len(parts) >= 3:
                            genre = parts[2].strip()
                    elif "状态" in line and "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            s = parts[2].strip()
                            if "连载" in s or "写作" in s:
                                status = "写作中"
                            elif "完结" in s:
                                status = "完结"
                            elif "签约" in s:
                                status = "已发布"
            except Exception:
                pass

        projects.append({
            "slug": d.name,
            "title": title,
            "genre": genre,
            "status": status,
            "dir": str(d.relative_to(PROJECT_ROOT)),
        })

    return projects


def load_portfolio():
    """读取 portfolio.json"""
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"novels": [], "calendar": []}


def save_portfolio(data):
    """保存 portfolio.json"""
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/novels":
            self._json_response(scan_novels())
        elif path == "/api/ideas":
            self._json_response(scan_ideas())
        elif path == "/api/projects":
            self._json_response(scan_projects())
        elif path == "/api/portfolio":
            self._json_response(load_portfolio())
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/portfolio":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                save_portfolio(data)
                self._json_response({"ok": True})
            except Exception as e:
                self._json_response({"error": str(e)}, status=400)
        else:
            self.send_error(404)

    def _serve_html(self):
        if not DASHBOARD_FILE.exists():
            self.send_error(404, "dashboard.html not found")
            return
        with open(DASHBOARD_FILE, encoding="utf-8") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # 安静模式，不刷屏
        pass


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), DashboardHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"小说看板已启动: {url}")
    print(f"数据源: {NOVEL_OUTPUT}")
    print(f"按 Ctrl+C 停止")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()
