#!/usr/bin/env python3
"""
拆文系统 (Novel Deconstruction Tool)

自动分析小说文本，提取结构化资产：
- 角色卡（人名频率、对话归属、共现关系）
- 剧情线（章节摘要、转折点检测）
- 世界观（地点/势力/专有名词提取）
- 风格 profile（句式/词汇/对话风格）

支持：
- 单个 .txt / .md 文件（多章合一）
- 含多个章节文件的目录

输出：
  {output_dir}/
  ├── characters.json      # 角色提取结果
  ├── plot_structure.json  # 剧情结构
  ├── world_settings.json  # 世界观要素
  ├── style_profile.json   # 风格 DNA
  ├── analysis_report.md   # 可读分析报告
  └── llm_prompts/         # 深度分析用的 LLM 提示
      ├── character_analysis.md
      ├── plot_analysis.md
      └── style_analysis.md

用法:
    python deconstruct_novel.py --input "正文/" --output "拆文结果/"
    python deconstruct_novel.py --input "全文.txt" --output "拆文结果/" --chapters 20
    python deconstruct_novel.py --input "正文/" --output "拆文结果/" --skip-llm-prompts
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import jieba
    import jieba.posseg as pseg
except ImportError:
    jieba = None
    pseg = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# 文本加载
# ============================================================

def load_text_files(input_path: str) -> list[dict[str, Any]]:
    """加载文本文件，返回 [{path, filename, text, chapter_num}]"""
    p = Path(input_path)
    files: list[Path] = []

    if p.is_file():
        files = [p]
    elif p.is_dir():
        for ext in ["*.txt", "*.md"]:
            files.extend(sorted(p.glob(ext)))
    else:
        print(f"[ERROR] 路径不存在: {input_path}", file=sys.stderr)
        return []

    result: list[dict[str, Any]] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        # 尝试从文件名推断章节号
        ch_match = re.search(r"(?:第|ch|chapter[ _]?)(\d+)", f.name, re.IGNORECASE)
        ch_num = int(ch_match.group(1)) if ch_match else len(result) + 1
        result.append({
            "path": str(f),
            "filename": f.name,
            "text": text,
            "chapter_num": ch_num,
        })

    return result


def split_chapters_from_text(text: str) -> list[dict[str, Any]]:
    """从合一文本中按章节标题拆分"""
    pattern = r"(第[一二三四五六七八九十百千零\d]+[章节卷])"
    parts = re.split(pattern, text)

    chapters: list[dict[str, Any]] = []
    i = 1
    while i < len(parts):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body:
            ch_match = re.search(r"(\d+)", title)
            ch_num = int(ch_match.group(1)) if ch_match else len(chapters) + 1
            chapters.append({
                "path": "",
                "filename": f"chapter_{ch_num:03d}",
                "text": body,
                "chapter_num": ch_num,
                "title": title,
            })
        i += 2

    return chapters


# ============================================================
# 角色提取
# ============================================================

# 常见中文姓氏（用于识别人名）
SURNAMES = set(
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    "戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐"
    "费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄"
    "和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁"
    "杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍"
    "虞万支柯咎管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚"
    "程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓"
    "牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙"
    "叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双"
    "闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农"
    "温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘"
    "匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空"
    "曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公"
)

# 常见名字后缀（双字名的第二个字）
NAME_SUFFIXES = set(
    "宇轩浩博涵睿泽昊然怡欣悦琪瑶蕾婷雅静敏燕玲桂英华平"
    "明杰伟强军磊洋勇刚峰辉超波宁贵福生龙元全国胜学祥才"
    "发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进"
    "林有坚和彪先敬震振壮会思群豪心邦承乐绍功松善厚庆磊"
    "民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌"
    "梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄"
    "琛钧冠策腾楠榕风航弘瑛瑾瑜璋璧"
)


def extract_character_names(text: str, min_count: int = 2) -> list[dict[str, Any]]:
    """提取可能的人名（基于姓氏+名模式和频率）"""
    if pseg is None:
        return _extract_names_simple(text, min_count)

    # 用 jieba 词性标注提取 nr（人名）
    words = pseg.cut(text)
    name_counter: Counter[str] = Counter()
    name_positions: dict[str, list[int]] = defaultdict(list)

    pos = 0
    for word, flag in words:
        if flag == "nr" and len(word) >= 2:
            name_counter[word] += 1
            name_positions[word].append(pos)
        pos += len(word)

    # 补充：姓氏+单字/双字模式
    chars = list(text)
    for i in range(len(chars) - 1):
        if chars[i] in SURNAMES:
            # 单字名
            if i + 2 < len(chars) and re.match(r"[一-鿿]", chars[i + 1]):
                candidate = chars[i] + chars[i + 1]
                if len(candidate) == 2:
                    name_counter[candidate] += 1
            # 双字名
            if i + 3 < len(chars) and re.match(r"[一-鿿]", chars[i + 1]) and re.match(r"[一-鿿]", chars[i + 2]):
                candidate = chars[i] + chars[i + 1] + chars[i + 2]
                if len(candidate) == 3:
                    name_counter[candidate] += 1

    # 过滤：频率 >= min_count，排除纯姓氏和常见词
    names = []
    for name, count in name_counter.most_common():
        if count < min_count:
            continue
        if len(name) == 1:
            continue
        # 排除明显不是人名的
        if name in {"我们", "他们", "她们", "什么", "这里", "那里", "这个", "那个", "怎么", "为什么", "可以", "不是"}:
            continue
        names.append({
            "name": name,
            "count": count,
            "positions": name_positions.get(name, [])[:20],
        })

    return sorted(names, key=lambda x: -x["count"])


def _extract_names_simple(text: str, min_count: int) -> list[dict[str, Any]]:
    """不依赖 jieba 的简单人名提取"""
    name_counter: Counter[str] = Counter()
    chars = list(text)

    for i in range(len(chars) - 1):
        if chars[i] in SURNAMES and i + 2 < len(chars):
            if re.match(r"[一-鿿]", chars[i + 1]):
                candidate = chars[i] + chars[i + 1]
                name_counter[candidate] += 1
            if i + 3 < len(chars) and re.match(r"[一-鿿]", chars[i + 1]) and re.match(r"[一-鿿]", chars[i + 2]):
                candidate = chars[i] + chars[i + 1] + chars[i + 2]
                name_counter[candidate] += 1

    return [
        {"name": name, "count": count, "positions": []}
        for name, count in name_counter.most_common()
        if count >= min_count and len(name) >= 2
    ]


# ============================================================
# 对话归属
# ============================================================

DIALOGUE_PATTERNS = [
    r'"([^"]*)"',
    r'"([^"]*)"',
    r"「([^」]*)」",
    r"'([^']*)'",
]


def extract_dialogues(text: str) -> list[dict[str, Any]]:
    """提取对话及其上下文（用于归属分析）"""
    dialogues: list[dict[str, Any]] = []

    for pattern in DIALOGUE_PATTERNS:
        for m in re.finditer(pattern, text):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            context_before = text[start:m.start()].strip()
            context_after = text[m.end():end].strip()
            dialogue_text = m.group(1).strip()

            if not dialogue_text:
                continue

            # 尝试从上下文推断说话人
            speaker = _guess_speaker(context_before, context_after)

            dialogues.append({
                "text": dialogue_text,
                "speaker": speaker,
                "context_before": context_before[-30:],
                "context_after": context_after[:30],
                "position": m.start(),
            })

    return sorted(dialogues, key=lambda x: x["position"])


def _guess_speaker(before: str, after: str) -> str:
    """从上下文推断说话人"""
    # "xxx说" / "xxx道" / "xxx笑道" 模式
    for pattern in [
        r"([一-鿿]{1,4})(?:说|道|喊|叫|吼|笑|冷|淡淡|轻声|低声|高声|大声|小声|怒|骂|问|答|叹|哼|嗤)",
        r"([一-鿿]{1,4})\s*(?:说|道|喊|叫|吼|笑|问|答|叹)",
    ]:
        m = re.search(pattern, before[-20:])
        if m:
            return m.group(1)

    # 后文 "xxx说" 模式
    for pattern in [
        r"^([一-鿿]{1,4})(?:说|道|喊|叫)",
    ]:
        m = re.match(pattern, after[:15])
        if m:
            return m.group(1)

    return ""


def attribute_dialogues_to_characters(
    dialogues: list[dict[str, Any]],
    characters: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """将对话归属到角色，返回 {角色名: [对话列表]}"""
    char_names = {c["name"] for c in characters}
    attribution: dict[str, list[str]] = defaultdict(list)
    unattributed: list[str] = []

    for d in dialogues:
        speaker = d.get("speaker", "")
        if speaker in char_names:
            attribution[speaker].append(d["text"])
        else:
            unattributed.append(d["text"])

    if unattributed:
        attribution["_unattributed"] = unattributed

    return dict(attribution)


# ============================================================
# 世界观要素提取
# ============================================================

# 地点后缀
LOCATION_SUFFIXES = {"城", "镇", "村", "山", "谷", "洞", "峰", "湖", "河", "海", "岛", "宫", "殿", "阁", "楼", "府", "院", "寺", "庙", "庄", "堡", "关", "门", "街", "巷", "路", "区", "市", "省", "国", "界", "域", "大陆", "星球", "学院", "公司", "集团", "组织", "协会", "门派", "宗", "教", "帮", "派"}

# 势力后缀
FACTION_SUFFIXES = {"门", "派", "宗", "教", "帮", "会", "盟", "族", "家族", "集团", "公司", "组织", "协会", "联盟", "帝国", "王国", "王朝", "势力"}


def extract_locations(text: str, min_count: int = 2) -> list[dict[str, Any]]:
    """提取地点名称"""
    location_counter: Counter[str] = Counter()

    if pseg is not None:
        for word, flag in pseg.cut(text):
            if flag == "ns" and len(word) >= 2:
                location_counter[word] += 1

    # 补充：基于后缀匹配
    for suffix in LOCATION_SUFFIXES:
        pattern = rf"([一-鿿]{{1,6}}{re.escape(suffix)})"
        for m in re.finditer(pattern, text):
            candidate = m.group(1)
            if len(candidate) >= 2:
                location_counter[candidate] += 1

    return [
        {"name": name, "count": count}
        for name, count in location_counter.most_common()
        if count >= min_count
    ]


def extract_factions(text: str, min_count: int = 1) -> list[dict[str, Any]]:
    """提取势力/组织名称"""
    faction_counter: Counter[str] = Counter()

    for suffix in FACTION_SUFFIXES:
        pattern = rf"([一-鿿]{{1,8}}{re.escape(suffix)})"
        for m in re.finditer(pattern, text):
            candidate = m.group(1)
            if len(candidate) >= 3:
                faction_counter[candidate] += 1

    return [
        {"name": name, "count": count}
        for name, count in faction_counter.most_common()
        if count >= min_count
    ]


def extract_proper_nouns(text: str, min_count: int = 3) -> list[dict[str, Any]]:
    """提取专有名词（功法、物品、术语等）"""
    if pseg is None:
        return []

    noun_counter: Counter[str] = Counter()
    # 提取 nz（其他专名）、ng（名词性语素）等
    for word, flag in pseg.cut(text):
        if flag in {"nz", "ng"} and len(word) >= 2 and re.match(r"[一-鿿]+$", word):
            noun_counter[word] += 1

    return [
        {"name": name, "count": count, "type": "proper_noun"}
        for name, count in noun_counter.most_common()
        if count >= min_count
    ]


# ============================================================
# 剧情结构分析
# ============================================================

def analyze_chapter_structure(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """分析每章的基本结构"""
    result: list[dict[str, Any]] = []

    for ch in chapters:
        text = ch["text"]
        sentences = re.split(r"[。！？…]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        # 对话统计
        dialogue_chars = 0
        for pattern in DIALOGUE_PATTERNS:
            for m in re.finditer(pattern, text):
                dialogue_chars += len(m.group(1))

        total_chars = len(re.sub(r"\s", "", text))
        dialogue_ratio = dialogue_chars / total_chars if total_chars > 0 else 0

        # 检测场景切换（空行 + 新段落）
        scene_breaks = len([p for p in paragraphs if len(p) < 10 and re.match(r"[\*\*\-\=\~]{3,}", p)])

        # 情绪关键词检测
        emotion_words = {
            "tension": ["紧张", "恐惧", "害怕", "危险", "威胁", "愤怒", "暴怒", "杀", "死", "血"],
            "joy": ["笑", "开心", "高兴", "欢喜", "兴奋", "幸福", "满足"],
            "sadness": ["哭", "悲伤", "难过", "痛苦", "绝望", "心碎", "泪"],
            "surprise": ["震惊", "惊讶", "吃惊", "不敢相信", "没想到", "突然", "竟然"],
        }

        emotions: dict[str, int] = {}
        for emotion, keywords in emotion_words.items():
            count = sum(text.count(kw) for kw in keywords)
            if count > 0:
                emotions[emotion] = count

        result.append({
            "chapter_num": ch["chapter_num"],
            "filename": ch.get("filename", ""),
            "title": ch.get("title", ""),
            "char_count": total_chars,
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "dialogue_ratio": round(dialogue_ratio, 3),
            "scene_breaks": scene_breaks,
            "emotions": emotions,
            "avg_sentence_length": round(total_chars / len(sentences), 1) if sentences else 0,
        })

    return result


def detect_turning_points(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """检测可能的剧情转折点（基于情绪突变和对话密度变化）"""
    if len(chapters) < 2:
        return []

    turning_points: list[dict[str, Any]] = []
    prev_dialogue = 0.0
    prev_tension = 0

    for i, ch in enumerate(chapters):
        dialogue = ch.get("dialogue_ratio", 0)
        emotions = ch.get("emotions", {})
        tension = emotions.get("tension", 0)
        surprise = emotions.get("surprise", 0)

        reasons: list[str] = []

        # 对话密度突变
        if prev_dialogue > 0 and abs(dialogue - prev_dialogue) / prev_dialogue > 0.5:
            reasons.append(f"对话密度突变: {prev_dialogue:.1%} → {dialogue:.1%}")

        # 紧张度突增
        if prev_tension > 0 and tension > prev_tension * 2:
            reasons.append(f"紧张度突增: {prev_tension} → {tension}")

        # 惊讶情绪高
        if surprise >= 3:
            reasons.append(f"惊讶情绪密集: {surprise}次")

        if reasons:
            turning_points.append({
                "chapter_num": ch["chapter_num"],
                "reasons": reasons,
                "tension": tension,
                "surprise": surprise,
                "dialogue_ratio": dialogue,
            })

        prev_dialogue = dialogue
        prev_tension = tension

    return turning_points


# ============================================================
# 风格分析
# ============================================================

def analyze_style(chapters: list[dict[str, Any]]) -> dict[str, Any]:
    """分析整体写作风格"""
    all_text = "\n".join(ch["text"] for ch in chapters)
    total_chars = len(re.sub(r"\s", "", all_text))

    # 句子长度分布
    sentences = re.split(r"[。！？…]+", all_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sent_lengths = [len(re.sub(r"\s", "", s)) for s in sentences]

    # 词汇丰富度
    if pseg is not None:
        words = [w for w, _ in pseg.cut(all_text) if re.match(r"[一-鿿]+$", w) and len(w) >= 2]
    else:
        words = re.findall(r"[一-鿿]{2,}", all_text)

    word_counter = Counter(words)
    unique_words = len(word_counter)
    total_words = len(words)

    # 高频词
    high_freq = word_counter.most_common(50)

    # 对话总比例
    dialogue_chars = 0
    for pattern in DIALOGUE_PATTERNS:
        for m in re.finditer(pattern, all_text):
            dialogue_chars += len(m.group(1))

    # 描写类型比例（粗略估计）
    env_keywords = ["阳光", "月光", "风", "雨", "雪", "天空", "大地", "山", "水", "花", "树", "云", "雾", "夜", "晨"]
    psych_keywords = ["心想", "心中", "暗想", "想到", "觉得", "感觉", "明白", "意识到", "回忆", "想起"]
    action_keywords = ["走", "跑", "跳", "冲", "挥", "打", "踢", "拿", "抓", "推", "拉", "站", "坐", "躺"]

    env_count = sum(all_text.count(kw) for kw in env_keywords)
    psych_count = sum(all_text.count(kw) for kw in psych_keywords)
    action_count = sum(all_text.count(kw) for kw in action_keywords)
    desc_total = env_count + psych_count + action_count

    # 常见句式模式
    sentence_patterns: list[dict[str, Any]] = []
    pattern_counter: Counter[str] = Counter()
    for s in sentences[:200]:  # 只分析前200句
        # 提取句首模式
        if len(s) >= 4:
            prefix = s[:4]
            pattern_counter[prefix] += 1

    for pattern, count in pattern_counter.most_common(10):
        if count >= 3:
            sentence_patterns.append({"pattern": pattern + "...", "count": count})

    return {
        "total_chars": total_chars,
        "total_sentences": len(sentences),
        "total_words": total_words,
        "unique_words": unique_words,
        "vocabulary_richness": round(unique_words / total_words, 4) if total_words > 0 else 0,
        "avg_sentence_length": round(sum(sent_lengths) / len(sent_lengths), 1) if sent_lengths else 0,
        "sentence_length_std": round(
            (sum((x - sum(sent_lengths) / len(sent_lengths)) ** 2 for x in sent_lengths) / len(sent_lengths)) ** 0.5,
            1,
        ) if sent_lengths else 0,
        "dialogue_ratio": round(dialogue_chars / total_chars, 3) if total_chars > 0 else 0,
        "description_breakdown": {
            "environment": env_count,
            "psychology": psych_count,
            "action": action_count,
            "env_ratio": round(env_count / desc_total, 3) if desc_total > 0 else 0,
            "psych_ratio": round(psych_count / desc_total, 3) if desc_total > 0 else 0,
            "action_ratio": round(action_count / desc_total, 3) if desc_total > 0 else 0,
        },
        "high_freq_words": [{"word": w, "count": c} for w, c in high_freq],
        "sentence_patterns": sentence_patterns,
        "dialogue_markers": _detect_dialogue_markers(all_text),
    }


def _detect_dialogue_markers(text: str) -> dict[str, int]:
    """检测对话标记偏好"""
    markers = {
        "双引号": len(re.findall(r'"[^"]*"', text)),
        "单引号": len(re.findall(r"'[^']*'", text)),
        "中文引号": len(re.findall(r'"[^"]*"', text)),
        "日式括号": len(re.findall(r"「[^」]*」", text)),
    }
    return {k: v for k, v in markers.items() if v > 0}


# ============================================================
# 共现分析
# ============================================================

def analyze_co_occurrence(
    text: str,
    characters: list[dict[str, Any]],
    window: int = 200,
) -> list[dict[str, Any]]:
    """分析角色共现关系（在同一窗口内出现的角色视为有关系）"""
    names = [c["name"] for c in characters[:20]]  # 只分析前20个角色
    co_occurrence: Counter[tuple[str, str]] = Counter()

    # 滑动窗口
    for i in range(0, len(text), window // 2):
        segment = text[i:i + window]
        present = [name for name in names if name in segment]
        for j in range(len(present)):
            for k in range(j + 1, len(present)):
                pair = tuple(sorted([present[j], present[k]]))
                co_occurrence[pair] += 1

    relationships: list[dict[str, Any]] = []
    for (a, b), count in co_occurrence.most_common(50):
        if count >= 2:
            relationships.append({
                "characters": [a, b],
                "co_occurrence_count": count,
                "strength": "strong" if count >= 10 else "medium" if count >= 5 else "weak",
            })

    return relationships


# ============================================================
# LLM 深度分析提示生成
# ============================================================

def generate_llm_prompts(
    characters: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    style: dict[str, Any],
    relationships: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """生成供 Claude 深度分析的提示文件"""
    prompts_dir = output_dir / "llm_prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # 角色深度分析提示
    char_list = "\n".join(f"- {c['name']} (出现{c['count']}次)" for c in characters[:15])
    char_prompt = f"""# 角色深度分析任务

以下是从文本中自动提取的高频角色：
{char_list}

请基于原文，为每个重要角色生成结构化角色卡：
1. 姓名 / 性别 / 年龄段
2. 性格特征（3-5个关键词）
3. 说话风格（语气词、句式偏好、口癖）
4. 行为模式（日常状态 vs 压力状态）
5. 人物弧光（从开头到结尾的变化）
6. 核心动机
7. 与其他角色的关系

输出格式：JSON
"""
    (prompts_dir / "character_analysis.md").write_text(char_prompt, encoding="utf-8")

    # 剧情结构分析提示
    ch_summaries = "\n".join(
        f"- 第{ch['chapter_num']}章: {ch['char_count']}字, 对话{ch['dialogue_ratio']:.0%}, 情绪{ch.get('emotions', {})}"
        for ch in chapters[:30]
    )
    plot_prompt = f"""# 剧情结构分析任务

章节统计：
{ch_summaries}

请分析：
1. 整体故事线（主线 + 2-3条副线）
2. 核心矛盾/冲突
3. 每卷/每幕的转折点
4. 伏笔设置与回收
5. 节奏评估（哪些章节拖沓/紧凑）
6. 高潮位置

输出格式：JSON
"""
    (prompts_dir / "plot_analysis.md").write_text(plot_prompt, encoding="utf-8")

    # 风格分析提示
    style_prompt = f"""# 风格深度分析任务

统计数据：
- 总字数: {style['total_chars']}
- 句子平均长度: {style['avg_sentence_length']}字
- 词汇丰富度: {style['vocabulary_richness']}
- 对话比例: {style['dialogue_ratio']:.1%}
- 描写分布: 环境{style['description_breakdown']['env_ratio']:.0%} / 心理{style['description_breakdown']['psych_ratio']:.0%} / 动作{style['description_breakdown']['action_ratio']:.0%}

高频词前20: {', '.join(w['word'] for w in style['high_freq_words'][:20])}

请分析：
1. 叙事视角（第一/第三人称，限制/全知）
2. 语言风格（文艺/口语/简洁/华丽）
3. 节奏特征（快节奏/慢热/张弛有度）
4. 对话风格（推动剧情/展示性格/信息传递）
5. 环境描写特点
6. 与目标平台（番茄/起点/知乎）的匹配度评估

输出格式：JSON
"""
    (prompts_dir / "style_analysis.md").write_text(style_prompt, encoding="utf-8")

    print(f"[OK] LLM 深度分析提示已生成: {prompts_dir}")


# ============================================================
# 报告生成
# ============================================================

def generate_report(
    characters: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    turning_points: list[dict[str, Any]],
    style: dict[str, Any],
    relationships: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    factions: list[dict[str, Any]],
    dialogues: dict[str, list[str]],
    output_dir: Path,
) -> None:
    """生成可读的 Markdown 分析报告"""
    lines = ["# 拆文分析报告", f"\n> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

    # 角色
    lines.append("## 角色")
    lines.append("")
    lines.append("| 排名 | 角色 | 出现次数 | 对话数 |")
    lines.append("|------|------|----------|--------|")
    for i, c in enumerate(characters[:15], 1):
        d_count = len(dialogues.get(c["name"], []))
        lines.append(f"| {i} | {c['name']} | {c['count']} | {d_count} |")

    # 关系
    if relationships:
        lines.append("\n## 角色关系")
        lines.append("")
        for r in relationships[:10]:
            lines.append(f"- **{r['characters'][0]}** ↔ **{r['characters'][1]}**: {r['strength']} ({r['co_occurrence_count']}次共现)")

    # 世界观
    if locations:
        lines.append("\n## 地点")
        lines.append("")
        for loc in locations[:10]:
            lines.append(f"- {loc['name']} ({loc['count']}次)")

    if factions:
        lines.append("\n## 势力")
        lines.append("")
        for f in factions[:10]:
            lines.append(f"- {f['name']} ({f['count']}次)")

    # 剧情
    lines.append("\n## 章节统计")
    lines.append("")
    lines.append("| 章节 | 字数 | 句数 | 对话比 | 场景切换 | 主要情绪 |")
    lines.append("|------|------|------|--------|----------|----------|")
    for ch in chapters:
        emotions = ch.get("emotions", {})
        emo_str = ", ".join(f"{k}:{v}" for k, v in sorted(emotions.items(), key=lambda x: -x[1])[:2])
        lines.append(
            f"| 第{ch['chapter_num']}章 | {ch['char_count']} | {ch['sentence_count']} | "
            f"{ch['dialogue_ratio']:.0%} | {ch['scene_breaks']} | {emo_str} |"
        )

    # 转折点
    if turning_points:
        lines.append("\n## 可能的转折点")
        lines.append("")
        for tp in turning_points:
            reasons = "; ".join(tp["reasons"])
            lines.append(f"- **第{tp['chapter_num']}章**: {reasons}")

    # 风格
    lines.append("\n## 风格概况")
    lines.append("")
    lines.append(f"- 总字数: {style['total_chars']:,}")
    lines.append(f"- 句均长度: {style['avg_sentence_length']}字")
    lines.append(f"- 词汇丰富度: {style['vocabulary_richness']}")
    lines.append(f"- 对话比例: {style['dialogue_ratio']:.1%}")
    lines.append(f"- 描写分布: 环境 {style['description_breakdown']['env_ratio']:.0%} / 心理 {style['description_breakdown']['psych_ratio']:.0%} / 动作 {style['description_breakdown']['action_ratio']:.0%}")

    if style.get("sentence_patterns"):
        lines.append("\n### 常见句式")
        for p in style["sentence_patterns"][:5]:
            lines.append(f"- `{p['pattern']}` ({p['count']}次)")

    if style.get("dialogue_markers"):
        lines.append("\n### 对话标记偏好")
        for marker, count in style["dialogue_markers"].items():
            lines.append(f"- {marker}: {count}")

    report_path = output_dir / "analysis_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 分析报告已生成: {report_path}")


# ============================================================
# 主流程
# ============================================================

def deconstruct(
    input_path: str,
    output_dir: str,
    min_char_count: int = 2,
    min_location_count: int = 2,
    skip_llm_prompts: bool = False,
) -> dict[str, Any]:
    """执行完整拆文分析"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 加载文本
    chapters = load_text_files(input_path)
    if not chapters:
        # 尝试按章节拆分
        p = Path(input_path)
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            chapters = split_chapters_from_text(text)

    if not chapters:
        print("[ERROR] 未找到可分析的文本", file=sys.stderr)
        return {}

    total_chars = sum(len(re.sub(r"\s", "", ch["text"])) for ch in chapters)
    print(f"[INFO] 已加载 {len(chapters)} 个章节，共 {total_chars:,} 字")

    # 合并全文
    all_text = "\n".join(ch["text"] for ch in chapters)

    # 1. 角色提取
    print("[INFO] 提取角色...")
    characters = extract_character_names(all_text, min_count=min_char_count)
    print(f"[INFO] 发现 {len(characters)} 个角色")

    # 2. 对话提取与归属
    print("[INFO] 提取对话...")
    dialogues_raw = extract_dialogues(all_text)
    dialogues = attribute_dialogues_to_characters(dialogues_raw, characters)
    print(f"[INFO] 提取 {len(dialogues_raw)} 条对话，归属到 {len([k for k in dialogues if k != '_unattributed'])} 个角色")

    # 3. 世界观要素
    print("[INFO] 提取世界观要素...")
    locations = extract_locations(all_text, min_count=min_location_count)
    factions = extract_factions(all_text)
    proper_nouns = extract_proper_nouns(all_text)
    print(f"[INFO] 地点 {len(locations)} 个, 势力 {len(factions)} 个, 专有名词 {len(proper_nouns)} 个")

    # 4. 剧情结构
    print("[INFO] 分析剧情结构...")
    chapter_stats = analyze_chapter_structure(chapters)
    turning_points = detect_turning_points(chapter_stats)
    print(f"[INFO] 检测到 {len(turning_points)} 个可能转折点")

    # 5. 角色关系
    print("[INFO] 分析角色共现...")
    relationships = analyze_co_occurrence(all_text, characters)
    print(f"[INFO] 发现 {len(relationships)} 组关系")

    # 6. 风格分析
    print("[INFO] 分析写作风格...")
    style = analyze_style(chapters)

    # 保存结果
    def save_json_data(data: Any, filename: str) -> None:
        path = out / filename
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] 已保存: {path}")

    save_json_data({
        "characters": characters,
        "dialogue_attribution": {k: v[:5] for k, v in dialogues.items()},  # 每人最多5条示例对话
        "relationships": relationships,
    }, "characters.json")

    save_json_data({
        "chapters": chapter_stats,
        "turning_points": turning_points,
    }, "plot_structure.json")

    save_json_data({
        "locations": locations,
        "factions": factions,
        "proper_nouns": proper_nouns,
    }, "world_settings.json")

    save_json_data(style, "style_profile.json")

    # 生成报告
    generate_report(characters, chapter_stats, turning_points, style, relationships, locations, factions, dialogues, out)

    # 生成 LLM 提示
    if not skip_llm_prompts:
        generate_llm_prompts(characters, chapter_stats, style, relationships, out)

    return {
        "characters": len(characters),
        "chapters": len(chapters),
        "locations": len(locations),
        "factions": len(factions),
        "relationships": len(relationships),
        "turning_points": len(turning_points),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="拆文系统 - 自动分析小说文本提取结构化资产")
    parser.add_argument("--input", required=True, help="小说文本文件或章节目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--min-char-count", type=int, default=2, help="角色最低出现次数（默认2）")
    parser.add_argument("--min-location-count", type=int, default=2, help="地点最低出现次数（默认2）")
    parser.add_argument("--skip-llm-prompts", action="store_true", help="跳过生成 LLM 深度分析提示")
    args = parser.parse_args()

    result = deconstruct(
        args.input,
        args.output,
        min_char_count=args.min_char_count,
        min_location_count=args.min_location_count,
        skip_llm_prompts=args.skip_llm_prompts,
    )

    if not result:
        return 1

    print(f"\n{'=' * 50}")
    print(f"拆文完成:")
    print(f"  角色: {result['characters']}")
    print(f"  章节: {result['chapters']}")
    print(f"  地点: {result['locations']}")
    print(f"  势力: {result['factions']}")
    print(f"  关系: {result['relationships']}")
    print(f"  转折点: {result['turning_points']}")
    print(f"{'=' * 50}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
