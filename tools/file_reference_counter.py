#!/usr/bin/env python3
"""
文件引用统计脚本

扫描项目中的所有 markdown 文件，统计每个文件被引用的次数。
支持 wikilink、markdown 链接等多种引用模式。

用法:
    python tools/file_reference_counter.py
    python tools/file_reference_counter.py --output report.json
    python tools/file_reference_counter.py --min-refs 2  # 只显示被引用≥2次的文件
    python tools/file_reference_counter.py --orphans     # 只显示未被引用的文件
    python tools/file_reference_counter.py --top 20      # 显示引用最多的20个文件
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 需要扫描的目录
SCAN_DIRS = [
    "knowledge_base",
    "novel_creation_promax",
    "tools",
    "scripts",
    "auto_publish",
]

# 排除的目录
EXCLUDE_DIRS = {
    "novel_output",
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "flux",
}

# 引用模式
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
MDLINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')


def safe_print(text):
    print(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))


def should_scan(path: Path) -> bool:
    """判断文件/目录是否应该被扫描。"""
    parts = path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return False
    return path.suffix.lower() == ".md"


def collect_md_files() -> list[Path]:
    """收集所有需要扫描的 markdown 文件。"""
    files = []
    for scan_dir in SCAN_DIRS:
        root = PROJECT_ROOT / scan_dir
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if should_scan(path):
                files.append(path)

    # 也扫描根目录的 markdown 文件
    for path in PROJECT_ROOT.glob("*.md"):
        if should_scan(path):
            files.append(path)

    return sorted(set(files))


def resolve_wikilink(ref: str, source_file: Path) -> Path | None:
    """解析 wikilink 为绝对路径。"""
    ref = ref.strip()
    if not ref:
        return None

    # 去除锚点
    if "#" in ref:
        ref = ref.split("#")[0]

    # 添加默认扩展名
    if not Path(ref).suffix:
        ref += ".md"

    # wikilink 通常是相对于知识库根目录或当前文件的
    # 先尝试相对于当前文件
    candidate = source_file.parent / ref
    if candidate.exists():
        return candidate.resolve()

    # 再尝试相对于项目根目录
    candidate = PROJECT_ROOT / ref
    if candidate.exists():
        return candidate.resolve()

    # 再尝试相对于知识库根目录
    candidate = PROJECT_ROOT / "knowledge_base" / ref
    if candidate.exists():
        return candidate.resolve()

    return None


def resolve_mdlink(ref: str, source_file: Path) -> Path | None:
    """解析 markdown 链接为绝对路径。"""
    ref = ref.strip()
    if not ref:
        return None

    # 排除外部链接
    if ref.startswith(("http://", "https://", "mailto:", "tel:")):
        return None

    # 排除纯锚点
    if ref.startswith("#"):
        return None

    # 排除模板变量
    if "{" in ref or "}" in ref:
        return None

    # 去除锚点
    if "#" in ref:
        ref = ref.split("#")[0]

    # 处理相对路径
    candidate = source_file.parent / ref
    if candidate.exists():
        return candidate.resolve()

    # 尝试相对于项目根目录
    candidate = PROJECT_ROOT / ref
    if candidate.exists():
        return candidate.resolve()

    return None


def extract_refs_from_file(file_path: Path) -> dict[str, list[str]]:
    """从文件中提取所有引用。"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}

    refs: dict[str, list[str]] = {
        "wikilink": [],
        "mdlink": [],
    }

    # 提取 wikilinks
    for match in WIKILINK_RE.finditer(content):
        ref = match.group(1).strip()
        resolved = resolve_wikilink(ref, file_path)
        if resolved:
            refs["wikilink"].append(str(resolved))

    # 提取 markdown links
    for match in MDLINK_RE.finditer(content):
        ref = match.group(2).strip()
        resolved = resolve_mdlink(ref, file_path)
        if resolved:
            refs["mdlink"].append(str(resolved))

    return refs


def build_reference_graph(files: list[Path]) -> dict:
    """构建引用图。"""
    # 所有文件集合
    all_files = {str(f.resolve()) for f in files}

    # 引用统计: target -> {count, sources: [{file, type, line}]}
    ref_stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0,
        "wikilink_count": 0,
        "mdlink_count": 0,
        "sources": [],
    })

    for file_path in files:
        refs = extract_refs_from_file(file_path)
        source_str = str(file_path.resolve())

        for ref_type, targets in refs.items():
            for target in targets:
                if target in all_files:
                    stats = ref_stats[target]
                    stats["count"] += 1
                    if ref_type == "wikilink":
                        stats["wikilink_count"] += 1
                    else:
                        stats["mdlink_count"] += 1
                    stats["sources"].append({
                        "file": source_str,
                        "type": ref_type,
                    })

    return {
        "all_files": sorted(all_files),
        "ref_stats": dict(ref_stats),
    }


def make_relative(path_str: str) -> str:
    """将绝对路径转为相对于项目根目录的路径。"""
    try:
        p = Path(path_str)
        return str(p.relative_to(PROJECT_ROOT))
    except ValueError:
        return path_str


def print_report(graph: dict, args: argparse.Namespace) -> None:
    """打印引用统计报告。"""
    all_files = graph["all_files"]
    ref_stats = graph["ref_stats"]

    # 分类文件
    referenced = []
    unreferenced = []

    for f in all_files:
        rel = make_relative(f)
        if f in ref_stats:
            stats = ref_stats[f]
            referenced.append((rel, stats["count"], stats["wikilink_count"], stats["mdlink_count"]))
        else:
            unreferenced.append(rel)

    # 按引用次数降序
    referenced.sort(key=lambda x: (-x[1], x[0]))

    print("=" * 70)
    print("文件引用统计报告")
    print("=" * 70)
    print(f"\n总计 markdown 文件: {len(all_files)}")
    print(f"被引用文件: {len(referenced)}")
    print(f"未被引用文件: {len(unreferenced)}")
    print()

    # 过滤
    if args.orphans:
        # 只显示未被引用的
        print("-" * 70)
        print("未被引用的文件 (orphans)")
        print("-" * 70)
        for rel in sorted(unreferenced):
            safe_print(f"  {rel}")
        print(f"\n共 {len(unreferenced)} 个未被引用的文件")
        return

    if args.min_refs is not None:
        referenced = [x for x in referenced if x[1] >= args.min_refs]

    if args.top:
        referenced = referenced[:args.top]

    # 被引用文件列表
    print("-" * 70)
    print(f"{'引用次数':>8} {'wikilink':>8} {'mdlink':>8} | 文件路径")
    print("-" * 70)
    for rel, count, wcount, mcount in referenced:
        safe_print(f"{count:>8} {wcount:>8} {mcount:>8} | {rel}")

    if not args.min_refs and not args.top:
        # 显示未被引用的文件（简要）
        if unreferenced:
            print()
            print("-" * 70)
            print(f"未被引用的文件 ({len(unreferenced)} 个)")
            print("-" * 70)
            for rel in sorted(unreferenced)[:50]:
                safe_print(f"  {rel}")
            if len(unreferenced) > 50:
                print(f"  ... 还有 {len(unreferenced) - 50} 个")

    print()
    print("=" * 70)


def save_json_report(graph: dict, output_path: Path) -> None:
    """保存 JSON 格式的详细报告。"""
    all_files = graph["all_files"]
    ref_stats = graph["ref_stats"]

    report = {
        "summary": {
            "total_files": len(all_files),
            "referenced_files": len(ref_stats),
            "unreferenced_files": len(all_files) - len(ref_stats),
        },
        "referenced": [],
        "unreferenced": [],
    }

    for f in all_files:
        rel = make_relative(f)
        if f in ref_stats:
            stats = ref_stats[f]
            report["referenced"].append({
                "file": rel,
                "total_refs": stats["count"],
                "wikilink_refs": stats["wikilink_count"],
                "mdlink_refs": stats["mdlink_count"],
                "sources": [{"file": make_relative(s["file"]), "type": s["type"]} for s in stats["sources"]],
            })
        else:
            report["unreferenced"].append(rel)

    # 按引用次数排序
    report["referenced"].sort(key=lambda x: -x["total_refs"])
    report["unreferenced"].sort()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    safe_print(f"\n报告已保存: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="文件引用统计")
    parser.add_argument("--output", "-o", help="输出 JSON 报告路径")
    parser.add_argument("--min-refs", type=int, help="只显示被引用≥N次的文件")
    parser.add_argument("--orphans", action="store_true", help="只显示未被引用的文件")
    parser.add_argument("--top", type=int, help="显示引用最多的 N 个文件")
    args = parser.parse_args()

    safe_print("扫描 markdown 文件中...")
    files = collect_md_files()
    safe_print(f"找到 {len(files)} 个 markdown 文件")

    safe_print("分析引用关系中...")
    graph = build_reference_graph(files)

    print_report(graph, args)

    if args.output:
        save_json_report(graph, Path(args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
