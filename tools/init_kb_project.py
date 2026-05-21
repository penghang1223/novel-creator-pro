#!/usr/bin/env python3
"""
init_kb_project.py — 为 knowledge_base/80_Projects/{编号_书名}/ 生成项目管理五件套骨架。

适用场景：
  - 已经在 novel_output/ 写了若干章，但 80_Projects/ 下要么没有项目目录，要么只有 _config.md
  - 用本脚本生成空模板，由人工补内容（避免 LLM 编造细节）

生成的文件:
  _config.md         （已存在则不动）
  项目索引.md
  伏笔追踪/总表.md
  角色状态/.gitkeep
  剧情节点/主线.md
  变更记录.md

用法:
  python tools/init_kb_project.py --title "她眼里有我的未来" --id 011
  python tools/init_kb_project.py --title "我能看到万物词条" --id 010 --platform 七猫 --genre 都市异能
  python tools/init_kb_project.py --auto    # 自动扫描所有缺骨架的项目并补齐
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_PROJECTS = PROJECT_ROOT / "knowledge_base" / "80_Projects"
NOVEL_OUTPUT = PROJECT_ROOT / "novel_output"

REQUIRED_SUBS = ["伏笔追踪", "角色状态", "剧情节点", "项目索引.md", "_config.md"]


def find_existing_dir(title: str, project_id: str | None) -> Path | None:
    """模糊匹配 knowledge_base/80_Projects/ 下含书名的目录。"""
    if not KB_PROJECTS.exists():
        return None
    for d in KB_PROJECTS.iterdir():
        if not d.is_dir():
            continue
        if title in d.name:
            return d
    return None


def find_novel_output(title: str) -> tuple[str | None, str | None]:
    """返回 (platform, dirname) 或 (None, None)。"""
    if not NOVEL_OUTPUT.exists():
        return None, None
    for plat in NOVEL_OUTPUT.iterdir():
        if not plat.is_dir():
            continue
        for n in plat.iterdir():
            if n.is_dir() and title in n.name:
                return plat.name, n.name
    return None, None


def render_config(title: str, platform: str, genre: str, output_dirname: str) -> str:
    return f"""# _config — {title}

## 基本信息

| 字段 | 值 |
|------|-----|
| 书名 | {title} |
| 题材 | {genre or "（待补）"} |
| 风格 | （待补） |
| 状态 | 连载中 |
| 总字数 | （待补） |
| 预计 | （待补） |
| 正文目录 | `../../novel_output/{platform or "?"}/{output_dirname or "?"}/正文/` |
| 大纲目录 | `../../novel_output/{platform or "?"}/{output_dirname or "?"}/` |

## 风格指南（本小说专用）

- （待补）

## 世界观速查

- （待补）

## 参考链接

- [[项目索引]]
- [[伏笔追踪/总表]]
- [[剧情节点/主线]]
"""


def render_index(title: str, platform: str, output_dirname: str) -> str:
    return f"""# {title} - 项目知识库

## 项目信息
- **书名**：{title}
- **平台**：{platform or "（待补）"}
- **题材**：（待补）
- **风格**：（待补）
- **当前进度**：（待补）
- **核心概念**：（待补）

## 知识库导航
- [[_config]]
- [[伏笔追踪/总表]]
- [[剧情节点/主线]]
- [[变更记录]]

## 角色档案
（待生成 `角色状态/{{角色名}}.md`）

## Canvas 文件
- [ ] 人物关系图.canvas
- [ ] 剧情时间线.canvas

## 关联目录
- 正文：`../../novel_output/{platform or "?"}/{output_dirname or "?"}/正文/`
- 记忆：`../../novel_output/{platform or "?"}/{output_dirname or "?"}/记忆/`
"""


def render_foreshadow(title: str) -> str:
    return f"""# 伏笔总表 — {title}

> 记录所有已埋设的伏笔，标注埋下章节、回收章节、当前状态。
> 状态图例：🔴 已埋未提 / 🟡 展开中 / ✅ 已回收 / ⚠️ 风险（超过 50 章未回收）

| 伏笔名 | 类型 | 埋下章节 | 回收章节 | 状态 | 说明 |
|--------|------|---------|---------|------|------|
| （待补） | 主线 | ch? | ch? | 🔴 | |

## 需要前文铺垫的伏笔

| 伏笔 | 问题 | 建议 |
|------|------|------|
| （待补） | | |

## 回收节奏检查

- [ ] 每 5-10 章扫一遍本表
- [ ] 🔴 + 🟡 状态 > 5 个 → 主线债务过重，下一卷需要回收
- [ ] 单个 🔴 超 50 章未升级状态 → 标 ⚠️ 风险
"""


def render_plot_node(title: str) -> str:
    return f"""# 主线节点 — {title}

> 记录主线大事件的章节定位与因果链。每个卷末必须有 1 个大节点。

## 卷一

| 章节 | 节点名 | 说明 | 引发 | 后果 |
|------|--------|------|------|------|
| ch? | （待补） | | | |

## 卷二

（待补）

## 关键转折点（跨卷）

- （待补）

## 节点偏离记录

> 任何偏离主线节点的章节必须在此登记，附理由。

| 章节 | 原节点 | 实际写法 | 理由 |
|------|--------|----------|------|
| - | - | - | - |
"""


def render_change_log(title: str) -> str:
    return f"""# 变更记录 — {title}

> 改主线/人物/能力/卷结构时必须先在此登记，说清原因和影响范围。
> 未经登记的偏离 = 失误，可要求重写。

| 日期 | 变更类型 | 变更前 | 变更后 | 影响章节 | 理由 | 决策人 |
|------|---------|--------|--------|---------|------|--------|
| - | - | - | - | - | - | - |

## 变更类型规范

- **主线**：动主线节点、卷末大事件
- **人物**：动核心角色的关键设定、动机、关系
- **能力**：动主角/反派的能力系统、等级、规则
- **卷结构**：动卷的划分、章节归属、节奏
- **设定**：动世界观、组织、地理等关键设定
"""


def ensure_file(path: Path, content: str, *, force: bool = False) -> str:
    if path.exists() and not force:
        return "skip"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "create"


def init_one(title: str, project_id: str | None, platform_hint: str | None, genre: str, force: bool) -> dict:
    plat, output_dirname = find_novel_output(title)
    platform = platform_hint or plat or ""
    existing = find_existing_dir(title, project_id)
    if existing:
        target = existing
    else:
        dirname = f"{project_id}_{title}" if project_id else title
        target = KB_PROJECTS / dirname
    target.mkdir(parents=True, exist_ok=True)
    (target / "角色状态").mkdir(exist_ok=True)
    (target / "伏笔追踪").mkdir(exist_ok=True)
    (target / "剧情节点").mkdir(exist_ok=True)

    keep = target / "角色状态" / ".gitkeep"
    if not keep.exists():
        keep.touch()

    results = {
        "_config.md": ensure_file(target / "_config.md", render_config(title, platform, genre, output_dirname or ""), force=force),
        "项目索引.md": ensure_file(target / "项目索引.md", render_index(title, platform, output_dirname or ""), force=force),
        "伏笔追踪/总表.md": ensure_file(target / "伏笔追踪" / "总表.md", render_foreshadow(title), force=force),
        "剧情节点/主线.md": ensure_file(target / "剧情节点" / "主线.md", render_plot_node(title), force=force),
        "变更记录.md": ensure_file(target / "变更记录.md", render_change_log(title), force=force),
    }
    return {"path": str(target.relative_to(PROJECT_ROOT)), "files": results}


def scan_shell_projects() -> list[tuple[str, str | None]]:
    """返回 [(title, id), ...] 缺骨架的项目。"""
    out = []
    if not KB_PROJECTS.exists():
        return out
    for d in KB_PROJECTS.iterdir():
        if not d.is_dir():
            continue
        completeness = sum(1 for sub in REQUIRED_SUBS if (d / sub).exists())
        if completeness < 4:
            m = re.match(r"^(\d{3})[_-](.+)$", d.name)
            if m:
                out.append((m.group(2), m.group(1)))
            else:
                out.append((d.name, None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", help="书名")
    ap.add_argument("--id", dest="project_id", help="项目编号（如 010）")
    ap.add_argument("--platform", default="", help="平台名（番茄/七猫/起点等）")
    ap.add_argument("--genre", default="", help="题材")
    ap.add_argument("--force", action="store_true", help="已存在文件也覆写")
    ap.add_argument("--auto", action="store_true", help="自动扫描所有缺骨架的项目")
    args = ap.parse_args()

    if args.auto:
        shells = scan_shell_projects()
        if not shells:
            print("没有发现缺骨架的项目。")
            return 0
        print(f"发现 {len(shells)} 个空壳项目：")
        for title, pid in shells:
            print(f"  - {pid or '???'}_{title}")
        print()
        for title, pid in shells:
            res = init_one(title, pid, None, "", args.force)
            print(f"[{res['path']}]")
            for k, v in res["files"].items():
                print(f"  {v:6}  {k}")
        return 0

    if not args.title:
        print("[FATAL] 必须指定 --title 或 --auto", file=sys.stderr)
        return 2

    res = init_one(args.title, args.project_id, args.platform, args.genre, args.force)
    print(f"[{res['path']}]")
    for k, v in res["files"].items():
        print(f"  {v:6}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
