#!/usr/bin/env python3
"""
知识摄入脚本 (Knowledge Ingest Script)

将外部文章/教程/案例分析摄入到知识库，自动生成知识卡片、分类归档。

用法:
    # 从 URL 抓取（配合 --url）
    python ingest.py --url "https://example.com/article" \
        --title "爆款开头写法" \
        --topic writing

    # 从本地文件摄入
    python ingest.py --file /path/to/article.md \
        --title "黄金三章技巧" \
        --topic writing

    # 自动分类（根据内容关键词推测类别）
    python ingest.py --file /path/to/article.md --auto-classify

    # 生成反思问题
    python ingest.py --url "https://example.com/article" \
        --title "爽点设计" \
        --topic writing \
        --with-questions
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


# ============================================================
# 配置区
# ============================================================

KB_ROOT = Path(__file__).parent.parent.parent / "knowledge_base"
FLUX_DIR = KB_ROOT / "flux" / "raw_articles"
SPACE_FOUND = KB_ROOT / "space" / "found"

# 内容分类映射
CATEGORY_MAP = {
    # 题材相关关键词 → 10_WorldBuilding
    "都市": "10_WorldBuilding",
    "科幻": "10_WorldBuilding",
    "仙侠": "10_WorldBuilding",
    "修仙": "10_WorldBuilding",
    "玄幻": "10_WorldBuilding",
    "奇幻": "10_WorldBuilding",
    "悬疑": "10_WorldBuilding",
    "推理": "10_WorldBuilding",
    "言情": "10_WorldBuilding",
    "女频": "10_WorldBuilding",
    "历史": "10_WorldBuilding",
    "大女主": "10_WorldBuilding",
    "无限流": "10_WorldBuilding",
    "惊悚": "10_WorldBuilding",
    "灵异": "10_WorldBuilding",
    "百合": "10_WorldBuilding",
    "游戏": "10_WorldBuilding",
    # 角色相关 → 20_Characters
    "角色": "20_Characters",
    "人物": "20_Characters",
    "命名": "20_Characters",
    "人设": "20_Characters",
    "反派": "20_Characters",
    # 剧情结构 → 30_Plot
    "大纲": "30_Plot",
    "剧情": "30_Plot",
    "伏笔": "30_Plot",
    "节奏": "30_Plot",
    "结构": "30_Plot",
    # 写作技巧 → 40_Writing
    "写作": "40_Writing",
    "开头": "40_Writing",
    "爽点": "40_Writing",
    "风格": "40_Writing",
    "描写": "40_Writing",
    "对话": "40_Writing",
    "AI": "40_Writing",
    "简介": "40_Writing",
    "书名": "40_Writing",
    # 质量评估 → 50_Quality
    "质量": "50_Quality",
    "红线": "50_Quality",
    "检查": "50_Quality",
    "评估": "50_Quality",
    # 平台规则 → 60_Platform
    "番茄": "60_Platform",
    "起点": "60_Platform",
    "晋江": "60_Platform",
    "七猫": "60_Platform",
    "飞卢": "60_Platform",
    "知乎": "60_Platform",
    # 语料 → 70_Corpus
    "毒舌": "70_Corpus",
    "神回复": "70_Corpus",
    "语料": "70_Corpus",
}

# 按主题关键词反推 PARA 分类
TOPIC_TO_PARA = {
    "worldbuilding": "10_WorldBuilding",
    "题材": "10_WorldBuilding",
    "character": "20_Characters",
    "角色": "20_Characters",
    "人物": "20_Characters",
    "plot": "30_Plot",
    "剧情": "30_Plot",
    "伏笔": "30_Plot",
    "writing": "40_Writing",
    "写作": "40_Writing",
    "quality": "50_Quality",
    "质量": "50_Quality",
    "platform": "60_Platform",
    "平台": "60_Platform",
    "corpus": "70_Corpus",
    "语料": "70_Corpus",
}


# ============================================================
# 函数
# ============================================================

def sanitize_filename(name: str) -> str:
    """清理文件名为安全的短标题。"""
    name = re.sub(r'[\\/:*?"<>|\n\r]', '', name)
    name = name[:50]  # 限制长度
    if not name:
        name = "untitled"
    return name


def auto_classify(text: str) -> str:
    """
    根据文本关键词自动分类到 PARA 目录。
    返回类别编号如 "40_Writing"。
    """
    scores = {}
    for keyword, category in CATEGORY_MAP.items():
        count = text.count(keyword)
        if count > 0:
            scores[category] = scores.get(category, 0) + count

    if scores:
        return max(scores, key=scores.get)
    return "00_Inbox"  # 分类不确定，放入收件箱


def generate_reflection_questions(title: str, summary: str) -> list:
    """
    生成 3 个思考问题：连接层、挑战层、行动层。
    """
    questions = []
    if title:
        questions.append(
            f"【连接】这篇文章的技法，和我们已有的 "
            f"knowledge_base 中哪些知识可以关联/合并？"
        )
        questions.append(
            f"【挑战】如果 {title} 的方法在实际写作中效果不好，"
            f"可能的根本原因是什么？"
        )
        questions.append(
            f"【行动】本周内可以用 {title} 中的哪个具体技法，"
            f"写一段 500 字的练笔来验证？"
        )
    return questions


def create_knowledge_card(
    title: str,
    summary: str,
    key_points: list,
    source_url: str = "",
    author: str = "",
    category: str = "00_Inbox",
    with_questions: bool = True,
) -> str:
    """
    生成知识卡片 Markdown 内容。
    格式参考 knowledge_base/space/_templates/knowledge_card.md。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    slug = sanitize_filename(title)

    lines = [
        f"# {title}",
        "",
        "---",
        f"created: {today}",
        f"source: {source_url or '本地导入'}",
        f"author: {author or '未知'}",
        f"category: {category}",
        "---",
        "",
        "## 摘要",
        summary,
        "",
    ]

    if key_points:
        lines.append("## 关键要点")
        for i, pt in enumerate(key_points, 1):
            lines.append(f"{i}. {pt}")
        lines.append("")

    if with_questions:
        questions = generate_reflection_questions(title, summary)
        lines.append("## 思考问题")
        for q in questions:
            lines.append(f"- {q}")
        lines.append("")

    lines.append("## 实践记录")
    lines.append("_（在实际使用后补充）_")
    lines.append("")

    return "\n".join(lines), slug


def save_knowledge_card(content: str, slug: str, category: str) -> str:
    """
    保存知识卡片到知识库。
    返回文件路径。
    """
    target_dir = KB_ROOT / category
    if not target_dir.exists():
        target_dir = KB_ROOT / "00_Inbox"

    # 生成唯一文件名
    today = datetime.now().strftime("%Y%m%d")
    filename = f"{today}_{slug}.md"
    filepath = target_dir / filename

    # 如果文件已存在，添加序号
    counter = 1
    while filepath.exists():
        filename = f"{today}_{slug}_{counter}.md"
        filepath = target_dir / filename
        counter += 1

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def save_raw_content(content: str, slug: str) -> str:
    """
    保存原始内容到 flux 目录。
    """
    FLUX_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    filename = f"{today}_{slug}_raw.md"
    filepath = FLUX_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def ingest(
    title: str,
    content: str,
    source_url: str = "",
    author: str = "",
    topic: str = "",
    auto_classify_flag: bool = False,
    with_questions: bool = True,
) -> dict:
    """
    完整摄入流程。

    Args:
        title: 文章标题
        content: 文章正文（Markdown）
        source_url: 来源 URL
        author: 作者
        topic: 指定分类主题
        auto_classify_flag: 是否自动分类
        with_questions: 是否生成反思问题

    Returns:
        摄入结果字典
    """
    # 1. 保存原始内容
    slug = sanitize_filename(title)
    raw_path = save_raw_content(content, slug)

    # 2. 自动分类
    if topic and topic in TOPIC_TO_PARA:
        category = TOPIC_TO_PARA[topic]
    elif auto_classify_flag:
        category = auto_classify(content)
    elif topic:
        # 尝试精确匹配
        category = None
        for kw, cat in CATEGORY_MAP.items():
            if kw in topic:
                category = cat
                break
        category = category or "00_Inbox"
    else:
        category = auto_classify(content)

    # 3. 提取关键要点（简单启发式：提取前 10 个以 ## 开头的标题
    # 或前 500 字作为摘要）
    headings = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    key_points = headings[:8] if headings else []

    # 摘要 = 前 500 字（去掉 frontmatter）
    clean_content = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)
    clean_content = re.sub(r'^# .+\n', '', clean_content, count=1)
    summary = clean_content[:500].strip()
    if len(clean_content) > 500:
        summary += "..."

    # 4. 生成知识卡片
    card_content, card_slug = create_knowledge_card(
        title=title,
        summary=summary,
        key_points=key_points,
        source_url=source_url,
        author=author,
        category=category,
        with_questions=with_questions,
    )

    # 5. 保存
    card_path = save_knowledge_card(card_content, card_slug, category)

    return {
        "title": title,
        "slug": slug,
        "category": category,
        "raw_path": raw_path,
        "card_path": card_path,
        "key_points_count": len(key_points),
        "summary_len": len(summary),
    }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="知识摄入脚本 — 自动分类、生成知识卡片、归档")
    parser.add_argument("--url", default="", help="文章 URL")
    parser.add_argument("--file", default="", help="本地文件路径")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--topic", default="", help="指定分类（writing/plot/character 等）")
    parser.add_argument("--author", default="", help="作者")
    parser.add_argument("--auto-classify", action="store_true",
                        help="根据内容关键词自动分类")
    parser.add_argument("--no-questions", action="store_true",
                        help="不生成反思问题")
    parser.add_argument("--output", help="输出摄入报告到 JSON")
    args = parser.parse_args()

    # 读取内容
    content = ""
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.url:
        # URL 抓取需要额外处理，这里提示用户使用 WebFetch
        print(f"URL 模式：请先用 WebFetch 抓取 {args.url} 的内容，然后使用 --file 参数传入。")
        print("或者：")
        print(f"  curl -s '{args.url}' | python ingest.py --title '{args.title}' --file /dev/stdin")
        return

    if not content:
        print("错误：请指定 --file 或 --url")
        return

    result = ingest(
        title=args.title,
        content=content,
        source_url=args.url,
        author=args.author,
        topic=args.topic,
        auto_classify_flag=args.auto_classify,
        with_questions=not args.no_questions,
    )

    print("=" * 50)
    print(f"  知识摄入完成 — {result['title']}")
    print("=" * 50)
    print(f"  分类: {result['category']}")
    print(f"  原始文件: {result['raw_path']}")
    print(f"  知识卡片: {result['card_path']}")
    print(f"  关键要点: {result['key_points_count']} 条")
    print("=" * 50)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"摄入报告已保存到 {args.output}")


if __name__ == "__main__":
    main()
