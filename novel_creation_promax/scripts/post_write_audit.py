#!/usr/bin/env python3
"""
写后自动审计脚本 (Post-Write Audit Script)

每章生成后必须运行此脚本，检测AI词、对话比例、标题关键词、重复度等指标。
任何检查不通过时，输出详细报告并建议修复。

用法:
    python post_write_audit.py --chapter-file "正文/第1章-xxx.md" --title "第1章 xxx"
    python post_write_audit.py --chapter-file "正文/第1章-xxx.md" --prev-file "正文/第0章-xxx.md" --title "第1章 xxx"
    python post_write_audit.py --scan-all --dir "正文/"  # 扫描目录下所有章节
"""

import argparse
import glob
import json
import re
import sys
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ============================================================
# 配置区 — 可根据项目调整
# ============================================================

# 绝对禁止词 (写后必须为0)
ABSOLUTE_BANNED = {
    "切面": 0,  # 元叙事工艺术语，不得出现在正文中
    "旁白": 0,
    "镜头": 0,
    "转场": 0,
    "他是一个": 0,  # "他是一个XX的人" 模板化角色介绍
    "从而": 0,  # 尾巴句
    "以此": 0,  # 尾巴句
    "进一步凸显": 0,  # 尾巴句
    "这表明": 0,  # 尾巴句
    "这说明": 0,  # 尾巴句
    "这反映了": 0,  # 尾巴句
    "总而言之": 0,  # 尾巴句
    "不言而喻": 0,  # 尾巴句
}

# 严格限制词 (超限只预警，不直接阻断；避免机械清零自然常用词)
STRICT_LIMITED = {
    # 词汇: (单章建议上限, 20章建议上限)
    "突然": (3, 20),
    "微微": (3, 20),
    "沉默": (3, 20),
    "感觉": (3, 30),
    "嘴角": (3, 20),
    "天旋地转": (0, 2),
    "或许": (2, 15),  # 堆叠模糊限定词
    "一定程度上": (0, 5),  # 出现即替换
    "然而": (2, 15),  # 段首连接词
    "总之": (0, 5),  # 出现即替换
}

# 浓度预警
CONCENTRATION_PER_CHAPTER = 5  # 任何AI词单章 >= 5次 → 浓度预警
TOTAL_AI_WORDS_PER_CHAPTER = 30  # 全章AI词总数 >= 30 → AI味预警

# 字数红线（中文字符）
WORD_COUNT_MIN = 2800  # 每章最低中文字数
WORD_COUNT_MAX = 3200  # 每章最高中文字符
WORD_COUNT_TARGET = 3000

# 对话比例红线
DIALOGUE_RATIO_MIN = 0.25  # 网文对话比例 >= 25%

# 重复度红线
REPEAT_RATIO_MAX = 0.25  # 相邻章节开头重复度 <= 25%

# 单句成行红线
# 注：本网文采用碎片化短句风格（每句单独成段），经20章实测数据：85-167次/章。
# 阈值设为200，仅拦截极端异常情况（如换行符污染、格式错乱）。
SINGLE_LINE_PARAGRAPH_MAX = 200  # 每章单句成行段落不得超过N个（实测基准：85-167）

# 标题关键词最小长度
TITLE_KEYWORD_MIN_LEN = 2

# 能力泄露检测 — 默认关键词（可通过 --ability-keywords 覆盖）
DEFAULT_ABILITY_KEYWORDS = [
    "读心", "预知", "透视", "隐身", "瞬移", "治愈", "操控",
    "异能", "超能力", "觉醒", "系统", "空间", "金手指",
]

# ============================================================
# 审计函数
# ============================================================

def count_word(text: str, word: str) -> int:
    """统计词汇在文本中的出现次数。"""
    return text.count(word)


def count_true_similes(text: str) -> int:
    """
    统计真正的"像"比喻数量。
    排除: 像...一样(非比喻), 偶像, 想象, 好像, 不像, 像她自己 等非比喻用法。
    """
    # 先排除常见非比喻用法
    cleaned = text
    for pattern in [
        '偶像', '想象', '想像', '好像', '不像', '像自己', '像她', '像他',
        '像我', '像你', '像我们', '像他们', '像什么', '像这样', '像那样',
        '像......一样', '像……一样',
    ]:
        cleaned = cleaned.replace(pattern, 'XXX')
    # 统计剩余的"像"字（大概率是比喻）
    return cleaned.count('像')


def calc_dialogue_ratio(text: str) -> float:
    """
    计算对话比例。
    简单算法：统计中文引号内的字符数 / 总字符数。
    """
    # 匹配 "xxx" 和 「xxx」 和 "xxx" 中的内容
    dialogue_chars = 0
    # 中文双引号
    for match in re.finditer(r'"([^"]*)"', text):
        dialogue_chars += len(match.group(1))
    # 中文双引号另一种
    for match in re.finditer(r'"([^"]*)"', text):
        dialogue_chars += len(match.group(1))
    # 单引号
    for match in re.finditer(r"'([^']*)'", text):
        dialogue_chars += len(match.group(1))

    total_chars = len(text.replace('\n', '').replace(' ', ''))
    if total_chars == 0:
        return 0.0
    return dialogue_chars / total_chars


def check_title_keywords(text: str, title: str) -> list:
    """
    提取标题中的关键词(>=2字的核心词)，检查是否在正文中出现。
    返回未匹配的关键词列表。
    """
    # 移除"第X章"前缀
    clean_title = re.sub(r'^第[零一二三四五六七八九十\d]+章\s*', '', title.strip())
    # 提取>=2字的连续中文词
    keywords = re.findall(r'[\u4e00-\u9fa5]{%d,}' % TITLE_KEYWORD_MIN_LEN, clean_title)
    # 过滤掉常见的非关键词
    stop_words = {'之', '的', '了', '在', '是', '有', '和', '与', '及'}
    keywords = [kw for kw in keywords if kw not in stop_words]

    missing = []
    for kw in keywords:
        if kw not in text:
            missing.append(kw)
    return missing


def calc_repeat_ratio(text1: str, text2: str, window: int = 200) -> float:
    """
    计算两段文本开头window字符的相似度。
    使用简单的字符重叠率。
    """
    s1 = text1[:window]
    s2 = text2[:window]
    if not s1 or not s2:
        return 0.0

    # 计算最长公共子序列长度
    def lcs_len(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if a[i] == b[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
        return dp[m][n]

    lcs = lcs_len(s1, s2)
    return lcs / max(len(s1), len(s2))


def check_first_300_chars(text: str) -> bool:
    """
    检查前300字是否有冲突/悬念/动作。
    简单启发式：前300字是否包含动作词、对话、悬念词。
    """
    first_300 = text[:300]
    # 检查是否有对话
    has_dialogue = bool(re.search(r'[""""].*?["""]', first_300))
    # 检查是否有动作/冲突词
    action_words = ['突然', '猛然', '冷不丁', '砰', '轰', '喊', '叫', '冲', '跑',
                    '追', '逃', '打', '杀', '破', '碎', '裂', '撞', '跌', '闪']
    has_action = any(w in first_300 for w in action_words)
    # 检查是否有悬念词
    suspense_words = ['但是', '然而', '却', '可是', '没想到', '竟然', '居然', '?', '？']
    has_suspense = any(w in first_300 for w in suspense_words)

    return has_dialogue or has_action or has_suspense


def count_single_line_paragraphs(text: str) -> int:
    """
    统计单句成行的段落数量。
    单句成行 = 一行只有一句话（不含标点分隔的多句话）就换行。
    用于检测"诗歌体"文风——每句话单独成行，阅读体验差。
    """
    # 跳过标题行（以#开头）和空行
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('#')]
    count = 0
    for line in lines:
        # 统计句子结束标点
        endings = len(re.findall(r'[。！？；]', line))
        # 如果一行只有1个或0个结束标点，且长度较短（<30字），算单句成行
        if endings <= 1 and len(re.findall(r'[\u4e00-\u9fff]', line)) < 30:
            count += 1
    return count


# ============================================================
# AI味扩展检测函数（来自 novel-review 技能包，参考预警级）
# ============================================================

def analyze_sentence_length_distribution(text: str) -> dict:
    """
    指标1：句式单一检测 — 句子长度分布。
    短句<10字、中句10-30字、长句>30字。
    """
    sentences = re.split(r'[。！？]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    short = sum(1 for s in sentences if len(re.findall(r'[\u4e00-\u9fff]', s)) < 10)
    medium = sum(1 for s in sentences if 10 <= len(re.findall(r'[\u4e00-\u9fff]', s)) <= 30)
    long = sum(1 for s in sentences if len(re.findall(r'[\u4e00-\u9fff]', s)) > 30)
    total = len(sentences)

    if total == 0:
        return {"short_ratio": 0, "medium_ratio": 0, "long_ratio": 0, "total_sentences": 0,
                "short_count": 0, "medium_count": 0, "long_count": 0}

    return {
        "short_ratio": short / total,
        "medium_ratio": medium / total,
        "long_ratio": long / total,
        "total_sentences": total,
        "short_count": short,
        "medium_count": medium,
        "long_count": long,
    }


def check_connector_density(text: str) -> dict:
    """
    指标2：连接词过度检测 — 统计每1000字中连接词数量。
    """
    char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_connectors = 0
    connector_detail = {}
    for cw in CONNECTOR_WORDS:
        cnt = text.count(cw)
        total_connectors += cnt
        if cnt > 0:
            connector_detail[cw] = cnt
    per_1000 = (total_connectors / max(char_count, 1)) * 1000
    return {"total": total_connectors, "per_1000": round(per_1000, 1), "detail": connector_detail}


def check_passive_voice_ratio(text: str) -> dict:
    """
    指标3：被动语态检测 — 统计"被"字句占比。
    """
    sentences = re.split(r'[。！？]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total = len(sentences)
    passive_count = sum(1 for s in sentences if any(p in s for p in PASSIVE_PATTERNS))
    ratio = passive_count / max(total, 1)
    return {"total": passive_count, "ratio": round(ratio, 3), "total_sentences": total}


def check_degree_adverb_repetition(text: str) -> dict:
    """
    指标7：程度副词重复检测 — 同一副词出现次数。
    """
    detail = {}
    max_count = 0
    for adv in DEGREE_ADVERBS:
        cnt = text.count(adv)
        detail[adv] = cnt
        max_count = max(max_count, cnt)
    return {"detail": detail, "max_count": max_count}


def check_cliche_density(text: str) -> dict:
    """
    指标8：陈词滥调检测 — 常见套话密度。
    """
    char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total = 0
    detail = {}
    for c in CLICHES:
        cnt = text.count(c)
        total += cnt
        if cnt > 0:
            detail[c] = cnt
    per_1000 = (total / max(char_count, 1)) * 1000
    return {"total": total, "per_1000": round(per_1000, 1), "detail": detail}


def check_sentence_ending_pattern(text: str) -> dict:
    """
    指标9：句尾模式化检测 — 连续句子相同结尾。
    """
    sentences = re.split(r'[。！？]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    max_consecutive = 0
    current_consecutive = 1
    prev_ending = None

    for s in sentences:
        ending = s[-2:] if len(s) >= 2 else s[-1:] if s else ""
        if ending and ending == prev_ending:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1
        prev_ending = ending

    return {"max_consecutive": max_consecutive}


def check_tell_words_density(text: str) -> dict:
    """
    指标11：Show vs Tell 近似检测 — 直接情感/内心描写密度。
    """
    char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    total = 0
    detail = {}
    for tw in TELL_WORDS:
        cnt = text.count(tw)
        total += cnt
        if cnt > 0:
            detail[tw] = cnt
    per_1000 = (total / max(char_count, 1)) * 1000
    return {"total": total, "per_1000": round(per_1000, 1), "detail": detail}



def check_timer_psychology(text: str) -> list:
    """
    指标12：计时器心理检测 — "顿了几秒/沉默了十秒/想了一秒"等。
    这类表达人类作者几乎不用，是典型的AI默认行为。
    """
    patterns = [
        r'[顿停静沉默想等愣]了[一二三四五六七八九十\d]+秒',
        r'过了[一二三四五六七八九十\d]+秒',
    ]
    matches = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            matches.append(m.group())
    return list(set(matches))


def check_foreign_chars(text: str) -> list:
    """
    指标14：非中文字符检测 — 英文单词不应出现在中文网文正文中。
    排除 markdown 标题/代码块等语法元素。
    """
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'`[^`]+`', '', cleaned)
    cleaned = re.sub(r'^#{1,6}\s+.*$', '', cleaned, flags=re.MULTILINE)
    # 匹配连续 2+ 个英文字母
    words = re.findall(r'[A-Za-z]{2,}', cleaned)
    seen = []
    for w in words:
        if w not in seen:
            seen.append(w)
    return seen


def check_ping_pong_dialogue(text: str) -> int:
    """
    指标13：乒乓球短句检测 — 连续纯对话行数。
    检测A→B→A→B骨架：提取所有对话行（以引号开头或主要是引号内容），
    忽略空行和非对话行之间的分隔，计算最长的"对话回合数"。
    规则：
    - 对话行 = 以引号开头，或行内引号内容占比超过50%
    - 对话回合 = 两个连续对话行之间，非对话行的中文字符数 <= 15
    - 返回最长连续对话回合数
    阈值：>= 8 = audit fail（只拦截长段机械问答）
    """
    lines = text.split('\n')
    # 先提取所有"有效行"（跳过空行、标题、分隔符）
    valid_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('```') or stripped.startswith('─'):
            continue
        valid_lines.append(stripped)

    def is_dialogue_line(line: str) -> bool:
        """判断一行是否主要是对话。"""
        if line.startswith('"') or line.startswith('"') or line.startswith('「'):
            return True
        # 检查引号内容占比
        dialogue_chars = 0
        for m in re.finditer(r'[""""""""""""](.*?)[""""""""""""]', line):
            dialogue_chars += len(m.group(1))
        total_cjk = len(re.findall(r'[一-鿿]', line))
        if total_cjk > 0 and dialogue_chars / total_cjk > 0.5:
            return True
        return False

    def count_non_dialogue_chars(line: str) -> int:
        """计算一行中非对话部分的中文字符数。"""
        non_dialogue = line
        for m in re.finditer(r'[""""""""""""](.*?)[""""""""""""]', line):
            non_dialogue = non_dialogue.replace(m.group(0), '', 1)
        return len(re.findall(r'[一-鿿]', non_dialogue))

    max_consecutive = 0
    current_consecutive = 0
    prev_was_dialogue = False
    prev_non_dialogue_chars = 0

    for line in valid_lines:
        if is_dialogue_line(line):
            if prev_was_dialogue:
                # 上一个也是对话，检查中间的非对话字符是否很少
                current_consecutive += 1
            else:
                current_consecutive = 1
            prev_was_dialogue = True
            prev_non_dialogue_chars = 0
        else:
            nd_chars = count_non_dialogue_chars(line)
            if nd_chars <= 15:
                # 这一行是非对话，但字符很少，视为"穿插动作"，不重置计数器
                pass
            else:
                # 非对话内容太多，重置
                if current_consecutive > max_consecutive:
                    max_consecutive = current_consecutive
                current_consecutive = 0
                prev_was_dialogue = False

    if current_consecutive > max_consecutive:
        max_consecutive = current_consecutive

    return max_consecutive


def check_intra_chapter_duplicates(text: str, similarity_threshold: float = 0.70, min_len: int = 15) -> list:
    """
    检测同一章内部的段落重复。
    将文本按段落分割，两两比较相似度，超过阈值的报告。
    相似度 = 最长公共子序列长度 / 较长段落长度。
    最小检测长度 = 15个中文字符（太短的不算）。
    """
    # 按空行分割段落，也按单行分割（网文常用单行分段）
    raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    # 如果段落数太少，再按单行分割
    if len(raw_paragraphs) < 3:
        raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    # 提取每个段落的中文字符，过滤太短的
    paragraphs = []
    for p in raw_paragraphs:
        cjk_count = len(re.findall(r'[一-鿿]', p))
        if cjk_count >= min_len:
            paragraphs.append(p)

    def lcs_len(a, b):
        m, n = len(a), len(b)
        if m > 500 or n > 500:
            # 对长段落只比较前500字符，避免超时
            a, b = a[:500], b[:500]
            m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if a[i] == b[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
        return dp[m][n]

    duplicates = []
    seen_pairs = set()
    for i in range(len(paragraphs)):
        for j in range(i + 1, len(paragraphs)):
            pair_key = (i, j)
            if pair_key in seen_pairs:
                continue
            longer = max(len(paragraphs[i]), len(paragraphs[j]))
            if longer == 0:
                continue
            lcs = lcs_len(paragraphs[i], paragraphs[j])
            ratio = lcs / longer
            if ratio >= similarity_threshold:
                # 截取预览
                preview_i = paragraphs[i][:40].replace('\n', ' ')
                preview_j = paragraphs[j][:40].replace('\n', ' ')
                duplicates.append({
                    "paragraph_1": i + 1,
                    "paragraph_2": j + 1,
                    "similarity": round(ratio, 2),
                    "preview_1": preview_i,
                    "preview_2": preview_j,
                })
                seen_pairs.add(pair_key)

    return duplicates


# ============================================================
# 新增检查函数（warning 级，不阻断）
# ============================================================

def check_ability_exposure(text: str, keywords: list = None) -> list:
    """
    检测角色能力泄露 — 能力关键词是否在不该出现的段落中暴露。
    例如读心术、预知等能力名出现在非主角视角的描写中。

    Args:
        text: 章节正文
        keywords: 能力关键词列表，默认使用 DEFAULT_ABILITY_KEYWORDS

    Returns:
        警告列表
    """
    if keywords is None:
        keywords = DEFAULT_ABILITY_KEYWORDS
    warnings = []
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    for i, para in enumerate(paragraphs):
        for kw in keywords:
            if kw in para:
                # 只提示，不阻断 — 让作者确认是否合理暴露
                warnings.append(f"段落{i+1}出现能力关键词「{kw}」: {para[:50]}…")
                break  # 一段只报一次
    return warnings


def check_three_cuts_compliance(text: str) -> list:
    """
    "每段三刀"合规检查：
    1. 超200字无对话段落 — 可能是流水账
    2. 嵌套"的"字过多（单句>=4个"的"）— 修饰链过长

    Returns:
        警告列表
    """
    warnings = []
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    for i, para in enumerate(paragraphs):
        # 跳过对话段落（引号开头）
        if para.startswith('"') or para.startswith('“'):
            continue

        # 检查1: 超200字无对话
        has_quote = '"' in para or '“' in para
        char_count = len(re.findall(r'[一-鿿]', para))
        if char_count > 200 and not has_quote:
            warnings.append(f"段落{i+1}超过200字({char_count}字)且无对话，可能需精简")

        # 检查2: 嵌套"的"字
        sentences = re.split(r'[。！？；]', para)
        for sent in sentences:
            de_count = sent.count('的')
            if de_count >= 4:
                warnings.append(f"段落{i+1}单句含{de_count}个「的」: {sent[:40]}…")

    return warnings


def check_inner_monologue_format(text: str) -> list:
    """
    心声格式检查 — 心声标记（心里/心想/暗想/嘀咕/默念）后不应使用引号。
    心声应为叙述体，不用引号包裹。

    Returns:
        警告列表
    """
    warnings = []
    # 心声标记 + 后面紧跟引号的模式
    pattern = re.compile(
        r'(心里|心想|暗想|嘀咕|默念|暗道|心说)[^。\n]{0,10}["“]'
    )
    matches = pattern.findall(text)
    for m in matches:
        warnings.append(f"心声格式: 「{m}」后使用了引号，心声应为叙述体")
    return warnings


def check_scene_budget(text: str, min_scenes: int = 2, max_scenes: int = 6) -> list:
    """
    场景字数预算检查：
    - 场景数 < min_scenes 或 > max_scenes 警告
    - 单场景 < 200字 警告（太短）
    - 单场景 > 1200字 警告（太长，需拆分）

    Returns:
        警告列表
    """
    warnings = []
    # 场景分隔符: *** / --- / ### / ***\n 等
    scenes = re.split(r'\n\s*[\*\-#]{3,}\s*\n', text)
    # 过滤空场景
    scenes = [s.strip() for s in scenes if s.strip()]

    scene_count = len(scenes)
    if scene_count < min_scenes:
        warnings.append(f"场景数 {scene_count} 过少(建议≥{min_scenes})，可能节奏单调")
    elif scene_count > max_scenes:
        warnings.append(f"场景数 {scene_count} 过多(建议≤{max_scenes})，可能切换太频繁")

    for i, scene in enumerate(scenes):
        char_count = len(re.findall(r'[一-鿿]', scene))
        if char_count < 200:
            warnings.append(f"场景{i+1}仅{char_count}字，可能太短")
        elif char_count > 1200:
            warnings.append(f"场景{i+1}达{char_count}字，可能太长需拆分")

    return warnings


# ============================================================

def audit_chapter(chapter_text: str, title: str, prev_text: str = None, ability_keywords: list = None) -> dict:
    """
    对单个章节执行完整审计。

    Args:
        chapter_text: 章节正文
        title: 章节标题
        prev_text: 上一章节正文（用于重复检测）
        ability_keywords: 能力泄露关键词列表（覆盖默认值）

    Returns:
        审计结果字典
    """
    results = {
        "title": title,
        "word_count": len(re.findall(r'[\u4e00-\u9fff]', chapter_text)),  # 仅中文字符，与 writing_gate.py 统一
        "ai_words": {},
        "dialogue_ratio": 0.0,
        "title_keywords": [],
        "missing_keywords": [],
        "repeat_ratio": 0.0,
        "first_300_ok": True,
        "single_line_count": 0,
        "timer_matches": [],
        "ping_pong_max": 0,
        "concentration_issues": [],
        "total_ai_words": 0,
        "intra_duplicates": [],
        "pass": True,
        "warnings": [],
        "ai_extended": {},
        "phase_status": {"logic": "unchecked", "ai_words": "unchecked", "dialogue": "unchecked"},
        "advisory": {},  # warning级检查项，不阻断
    }

    # ========== 阶段1：逻辑检查（不通过则直接驳回）==========
    for word, limit in ABSOLUTE_BANNED.items():
        count = count_word(chapter_text, word)
        results["ai_words"][word] = count
        results["total_ai_words"] += count
        if count > limit:
            results["pass"] = False
            results["warnings"].append(f"❌ 绝对禁止词 '{word}' 出现 {count} 次 (要求: {limit})")

    for word, (per_chapter, total_20) in STRICT_LIMITED.items():
        count = count_word(chapter_text, word)
        results["ai_words"][word] = count
        results["total_ai_words"] += count
        if count > per_chapter:
            results["warnings"].append(f"⚠️ '{word}' 单章出现 {count} 次 (建议上限: {per_chapter})")

    # 特殊处理 "像" 比喻
    simile_count = count_true_similes(chapter_text)
    results["ai_words"]["像(比喻)"] = simile_count
    results["total_ai_words"] += simile_count
    if simile_count > 12:
        results["warnings"].append(f"⚠️ '像'比喻出现 {simile_count} 次 (建议上限: 12)")

    # 浓度检测
    for word, count in results["ai_words"].items():
        if count >= CONCENTRATION_PER_CHAPTER:
            results["concentration_issues"].append(f"⚠️ '{word}' 浓度超标: {count}次 (阈值: {CONCENTRATION_PER_CHAPTER})")

    if results["total_ai_words"] >= TOTAL_AI_WORDS_PER_CHAPTER:
        results["warnings"].append(f"⚠️ AI词总数 {results['total_ai_words']} (建议阈值: {TOTAL_AI_WORDS_PER_CHAPTER})，注意是否堆叠")

    # ========== 阶段1：逻辑检查（不通过则直接驳回）==========
    # 2. 字数检查
    wc = results["word_count"]
    if wc < WORD_COUNT_MIN:
        results["pass"] = False
        results["warnings"].append(f"❌ 字数 {wc} (最低: {WORD_COUNT_MIN}，目标: {WORD_COUNT_TARGET})")
    elif wc > WORD_COUNT_MAX:
        results["pass"] = False
        results["warnings"].append(f"❌ 字数 {wc} (最高: {WORD_COUNT_MAX}，目标: {WORD_COUNT_TARGET})")

    # ========== 阶段2：AI词清理（只改词汇，不动叙事结构）==========
    # ========== 阶段3：对话质量（不改变角色说话方式）==========
    # 3. 对话比例
    results["dialogue_ratio"] = calc_dialogue_ratio(chapter_text)
    if results["dialogue_ratio"] < DIALOGUE_RATIO_MIN:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 对话比例 {results['dialogue_ratio']:.1%} (最低: {DIALOGUE_RATIO_MIN:.0%})"
        )

    # 4. 标题关键词匹配
    results["title_keywords"] = re.findall(
        r'[\u4e00-\u9fa5]{%d,}' % TITLE_KEYWORD_MIN_LEN,
        re.sub(r'^第[零一二三四五六七八九十\d]+章\s*', '', title.strip())
    )
    results["missing_keywords"] = check_title_keywords(chapter_text, title)
    if results["missing_keywords"]:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 标题关键词不在正文中: {', '.join(results['missing_keywords'])}"
        )

    # 5. 重复检测
    if prev_text:
        results["repeat_ratio"] = calc_repeat_ratio(chapter_text, prev_text)
        if results["repeat_ratio"] > REPEAT_RATIO_MAX:
            results["pass"] = False
            results["warnings"].append(
                f"❌ 与上一章开头重复度 {results['repeat_ratio']:.1%} (最高: {REPEAT_RATIO_MAX:.0%})"
            )

    # 6. 前300字检查
    results["first_300_ok"] = check_first_300_chars(chapter_text)
    if not results["first_300_ok"]:
        results["warnings"].append("⚠️ 前300字未检测到冲突/悬念/动作，建议增强开头吸引力")

    # 7. 单句成行检查
    results["single_line_count"] = count_single_line_paragraphs(chapter_text)
    if results["single_line_count"] > SINGLE_LINE_PARAGRAPH_MAX:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 单句成行段落 {results['single_line_count']} 次 (最高: {SINGLE_LINE_PARAGRAPH_MAX})，文风过于碎片化"
        )

    # 8. 计时器心理检测（硬门禁）
    results["timer_matches"] = check_timer_psychology(chapter_text)
    if results["timer_matches"]:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 计时器心理: {', '.join(results['timer_matches'])} — 改为动作/环境/叙事节奏"
        )

    # 8b. 非中文字符检测（预警参考，不阻断通过 — 游戏/科幻题材常用英文术语）
    results["foreign_chars"] = check_foreign_chars(chapter_text)
    if results["foreign_chars"]:
        results["warnings"].append(
            f"⚠️ 非中文字符（英文）: {', '.join(results['foreign_chars'])} — 游戏题材常用，仅供参考"
        )

    # 9. 乒乓球短句检测（硬门禁）
    results["ping_pong_max"] = check_ping_pong_dialogue(chapter_text)
    if results["ping_pong_max"] >= 8:
        results["pass"] = False
        results["warnings"].append(
            f"❌ 连续纯对话 {results['ping_pong_max']} 回合（上限: 8），存在乒乓球短句结构 — 需合并为叙事/删除对话回合"
        )

    # 10. 章内段落重复检测（硬门禁）
    results["intra_duplicates"] = check_intra_chapter_duplicates(chapter_text)
    if results["intra_duplicates"]:
        results["pass"] = False
        for dup in results["intra_duplicates"]:
            results["warnings"].append(
                f"❌ 章内重复: 段落{dup['paragraph_1']}与段落{dup['paragraph_2']}相似度{dup['similarity']:.0%} — 「{dup['preview_1']}…」vs 「{dup['preview_2']}…」"
            )

    # 10. AI味扩展检测（参考预警级，不阻断通过）
    results["ai_extended"] = {
        "sentence_distribution": analyze_sentence_length_distribution(chapter_text),
        "connector_density": check_connector_density(chapter_text),
        "passive_voice": check_passive_voice_ratio(chapter_text),
        "degree_adverb": check_degree_adverb_repetition(chapter_text),
        "cliche_density": check_cliche_density(chapter_text),
        "sentence_ending": check_sentence_ending_pattern(chapter_text),
        "tell_words": check_tell_words_density(chapter_text),
    }
    ai_ext = results["ai_extended"]

    # 指标1：句式单一预警
    sd = ai_ext["sentence_distribution"]
    if sd["short_ratio"] > 0.50:
        results["warnings"].append(
            f"⚠️ 短句占比 {sd['short_ratio']:.0%} 过高（>50%），可能存在短句堆叠"
        )
    if sd["long_ratio"] > 0.40:
        results["warnings"].append(
            f"⚠️ 长句占比 {sd['long_ratio']:.0%} 过高（>40%），可能存在长句堆叠"
        )

    # 指标2：连接词过度预警
    cd = ai_ext["connector_density"]
    if cd["per_1000"] > CONNECTOR_MAX_PER_1000:
        detail_str = ", ".join(f"{k}:{v}" for k, v in cd["detail"].items())
        results["warnings"].append(
            f"⚠️ 连接词密度 {cd['per_1000']:.0f}/千字（阈值: {CONNECTOR_MAX_PER_1000}），详情: {detail_str}"
        )

    # 指标3：被动语态预警
    pv = ai_ext["passive_voice"]
    if pv["ratio"] > PASSIVE_MAX_RATIO and pv["total"] > 0:
        results["warnings"].append(
            f"⚠️ 被动句占比 {pv['ratio']:.1%}（阈值: {PASSIVE_MAX_RATIO:.0%}），共{pv['total']}句"
        )

    # 指标7：程度副词重复预警
    da = ai_ext["degree_adverb"]
    if da["max_count"] >= DEGREE_ADVERB_CONSECUTIVE_MAX:
        repeated = [k for k, v in da["detail"].items() if v >= DEGREE_ADVERB_CONSECUTIVE_MAX]
        results["warnings"].append(
            f"⚠️ 程度副词重复: {', '.join(repeated)} 各出现{da['max_count']}次以上"
        )

    # 指标8：陈词滥调预警
    cl = ai_ext["cliche_density"]
    if cl["per_1000"] > CLICHE_MAX_PER_1000:
        detail_str = ", ".join(f"{k}:{v}" for k, v in cl["detail"].items())
        results["warnings"].append(
            f"⚠️ 陈词滥调密度 {cl['per_1000']:.1f}/千字（阈值: {CLICHE_MAX_PER_1000}），详情: {detail_str}"
        )

    # 指标9：句尾模式化预警
    se = ai_ext["sentence_ending"]
    if se["max_consecutive"] >= SENTENCE_ENDING_MAX_REPEAT:
        results["warnings"].append(
            f"⚠️ 连续{se['max_consecutive']}句句尾相同，句式可能单调"
        )

    # 指标11：Show vs Tell 预警
    tw = ai_ext["tell_words"]
    if tw["per_1000"] > TELL_MAX_PER_1000:
        detail_str = ", ".join(f"{k}:{v}" for k, v in tw["detail"].items())
        results["warnings"].append(
            f"⚠️ 直接情感词密度 {tw['per_1000']:.1f}/千字（阈值: {TELL_MAX_PER_1000}），详情: {detail_str}"
        )

    # ========== 建议级检查（不阻断通过）==========
    results["advisory"] = {
        "ability_exposure": check_ability_exposure(chapter_text, ability_keywords),
        "three_cuts": check_three_cuts_compliance(chapter_text),
        "inner_monologue": check_inner_monologue_format(chapter_text),
        "scene_budget": check_scene_budget(chapter_text),
    }

    return results


def format_report(results: dict) -> str:
    """格式化审计报告。"""
    lines = []
    lines.append(f"{'='*50}")
    lines.append(f"  写后审计报告 — {results['title']}")
    lines.append(f"  优先级：剧情逻辑 > AI词清理 > 对话质量")
    lines.append(f"{'='*50}")
    wc = results["word_count"]
    wc_status = "✅" if WORD_COUNT_MIN <= wc <= WORD_COUNT_MAX else "❌"
    lines.append(f"【字数】{wc_status} {wc} 中文字符 (范围: {WORD_COUNT_MIN}-{WORD_COUNT_MAX})")
    lines.append(f"")

    # AI词统计
    lines.append(f"【AI词统计】")
    for word, count in results["ai_words"].items():
        status = "✅" if count <= 1 else "⚠️"
        lines.append(f"  {status} {word}: {count}次")
    lines.append(f"  AI词总数: {results['total_ai_words']}")

    if results["concentration_issues"]:
        lines.append(f"  浓度问题:")
        for issue in results["concentration_issues"]:
            lines.append(f"    {issue}")

    lines.append(f"")
    lines.append(f"【对话比例】")
    ratio = results["dialogue_ratio"]
    status = "✅" if ratio >= DIALOGUE_RATIO_MIN else "❌"
    lines.append(f"  {status} {ratio:.1%} (目标: ≥{DIALOGUE_RATIO_MIN:.0%})")

    lines.append(f"")
    lines.append(f"【标题关键词】")
    if results["title_keywords"]:
        for kw in results["title_keywords"]:
            found = kw not in results["missing_keywords"]
            status = "✅" if found else "❌"
            lines.append(f"  {status} '{kw}': {'正文中出现' if found else '未找到'}")
    else:
        lines.append(f"  (无关键词可检测)")

    lines.append(f"")
    lines.append(f"【重复检测】")
    if results["repeat_ratio"] > 0:
        status = "✅" if results["repeat_ratio"] <= REPEAT_RATIO_MAX else "❌"
        lines.append(f"  {status} 与上一章开头重复度: {results['repeat_ratio']:.1%}")
    else:
        lines.append(f"  (无上一章，跳过)")

    intra = results.get("intra_duplicates", [])
    if intra:
        lines.append(f"  ❌ 章内段落重复: {len(intra)}对")
        for dup in intra:
            lines.append(f"    段落{dup['paragraph_1']} ↔ 段落{dup['paragraph_2']} (相似度{dup['similarity']:.0%})")
            lines.append(f"      A: {dup['preview_1']}…")
            lines.append(f"      B: {dup['preview_2']}…")
    else:
        lines.append(f"  ✅ 章内无段落重复")

    lines.append(f"")
    lines.append(f"【开头检查】")
    status = "✅" if results["first_300_ok"] else "⚠️"
    lines.append(f"  {status} 前300字{'有冲突/悬念/动作' if results['first_300_ok'] else '缺少冲突/悬念/动作'}")

    lines.append(f"")
    lines.append(f"【单句成行】")
    slc = results["single_line_count"]
    status = "✅" if slc <= SINGLE_LINE_PARAGRAPH_MAX else "❌"
    lines.append(f"  {status} 单句成行段落: {slc} 次 (最高: {SINGLE_LINE_PARAGRAPH_MAX})")

    lines.append(f"")
    lines.append(f"【计时器心理】")
    timer = results["timer_matches"]
    status = "✅" if not timer else "❌"
    if timer:
        lines.append(f"  {status} 检测到: {', '.join(timer)}")
    else:
        lines.append(f"  {status} 未检测到计时器心理")

    lines.append(f"")
    lines.append(f"【乒乓球短句】")
    pp = results["ping_pong_max"]
    status = "✅" if pp < 8 else "❌"
    lines.append(f"  {status} 最长连续纯对话: {pp} 行 (上限: 8)")

    # AI味扩展检测（参考预警级）
    ai_ext = results.get("ai_extended", {})
    if ai_ext:
        lines.append(f"")
        lines.append(f"【AI味扩展检测】（预警参考，不阻断通过）")

        # 指标1：句式分布
        sd = ai_ext.get("sentence_distribution", {})
        if sd.get("total_sentences", 0) > 0:
            lines.append(f"  句式分布: 短句{sd['short_ratio']:.0%} / 中句{sd['medium_ratio']:.0%} / 长句{sd['long_ratio']:.0%} (共{sd['total_sentences']}句)")

        # 指标2：连接词
        cd = ai_ext.get("connector_density", {})
        if cd.get("total", 0) > 0:
            lines.append(f"  ⚠️ 连接词: {cd['total']}次 ({cd['per_1000']:.0f}/千字) — {', '.join(f'{k}:{v}' for k, v in cd.get('detail', {}).items())}")
        else:
            lines.append(f"  ✅ 连接词: 0次")

        # 指标3：被动语态
        pv = ai_ext.get("passive_voice", {})
        if pv.get("total", 0) > 0:
            lines.append(f"  被动句: {pv['total']}句 ({pv['ratio']:.1%})")

        # 指标8：陈词滥调
        cl = ai_ext.get("cliche_density", {})
        if cl.get("total", 0) > 0:
            lines.append(f"  ⚠️ 陈词滥调: {cl['total']}次 ({cl['per_1000']:.1f}/千字) — {', '.join(f'{k}:{v}' for k, v in cl.get('detail', {}).items())}")
        else:
            lines.append(f"  ✅ 陈词滥调: 0次")

        # 指标11：直接情感词
        tw = ai_ext.get("tell_words", {})
        if tw.get("total", 0) > 0:
            lines.append(f"  ⚠️ 直接情感词: {tw['total']}次 ({tw['per_1000']:.1f}/千字)")
        else:
            lines.append(f"  ✅ 直接情感词: 0次")

    # 建议级检查（不阻断）
    advisory = results.get("advisory", {})
    if advisory:
        has_advisory = any(v for v in advisory.values())
        if has_advisory:
            lines.append(f"")
            lines.append(f"【建议级检查】（不阻断通过）")

            ability = advisory.get("ability_exposure", [])
            if ability:
                lines.append(f"  ⚠️ 能力泄露: {len(ability)}处")
                for w in ability[:3]:
                    lines.append(f"    - {w}")

            three_cuts = advisory.get("three_cuts", [])
            if three_cuts:
                lines.append(f"  ⚠️ 三刀合规: {len(three_cuts)}处")
                for w in three_cuts[:3]:
                    lines.append(f"    - {w}")

            monologue = advisory.get("inner_monologue", [])
            if monologue:
                lines.append(f"  ⚠️ 心声格式: {len(monologue)}处")
                for w in monologue[:3]:
                    lines.append(f"    - {w}")

            scenes = advisory.get("scene_budget", [])
            if scenes:
                lines.append(f"  ⚠️ 场景预算: {len(scenes)}处")
                for w in scenes[:3]:
                    lines.append(f"    - {w}")

    lines.append(f"")
    if results["pass"]:
        lines.append(f"{'='*50}")
        lines.append(f"  ✅ 审计通过！")
        lines.append(f"{'='*50}")
    else:
        lines.append(f"{'='*50}")
        lines.append(f"  ❌ 审计未通过，修复优先级:")
        lines.append(f"{'='*50}")
        lines.append(f"  ① 先修逻辑问题（章节边界、剧情顺序）")
        lines.append(f"  ② 再修AI词（只改词汇，不动叙事）")
        lines.append(f"  ③ 最后检查对话质量")
        lines.append(f"  ---")
        for w in results["warnings"]:
            lines.append(f"  {w}")
    lines.append(f"")

    return "\n".join(lines)


def write_audit_report(report_path: str, results) -> None:
    payload = build_audit_payload(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def build_audit_payload(results) -> dict:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "passed" if _results_passed(results) else "failed",
        "results": results,
    }


def sync_novel_state(novel_state_path: str, report_path: str, payload: dict) -> None:
    state_file = Path(novel_state_path)
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"novel_state.json 不存在: {novel_state_path}")
    except JSONDecodeError as exc:
        raise ValueError(f"novel_state.json 不是有效 JSON: {novel_state_path} ({exc})") from exc

    gate = state.setdefault("workflow_gate", {})
    gate["audit_status"] = payload["status"]
    gate["last_audit_report"] = _relative_report_path(state_file, report_path)
    gate["last_audit_at"] = payload["generated_at"]
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _relative_report_path(state_file: Path, report_path: str) -> str:
    report = Path(report_path)
    if not report.is_absolute():
        report = (Path.cwd() / report).resolve()
    try:
        return report.relative_to(state_file.parent.resolve()).as_posix()
    except ValueError:
        return report.as_posix()


def _results_passed(results) -> bool:
    if isinstance(results, list):
        return all(item.get("pass", False) for item in results)
    return results.get("pass", False)


# ============================================================
# AI味扩展检测指标库（来自 novel-review 技能包）
# 以下指标作为参考预警，不阻断审计通过。
# ============================================================

# 指标2：连接词过度 — 机械连接词密度
CONNECTOR_WORDS = ['然后', '接着', '因此', '但是', '可是', '于是', '接下来', '随后', '紧接着']
CONNECTOR_MAX_PER_1000 = 15  # 超过此密度预警

# 指标3：被动语态 — "被"字句比例
PASSIVE_PATTERNS = ['被', '遭', '受', '令', '令其']
PASSIVE_MAX_RATIO = 0.08  # 被动句占比超过8%预警（网文一般较低）

# 指标7：程度副词重复 — 同一程度副词连续出现
DEGREE_ADVERBS = ['十分', '非常', '极其', '格外', '格外地', '异常', '颇为', '相当', '异常']
DEGREE_ADVERB_CONSECUTIVE_MAX = 3  # 同一副词出现3次以上预警

# 指标8：陈词滥调 — AI常用套话
CLICHES = [
    '不约而同', '难以置信', '恍然大悟', '心照不宣', '不由自主',
    '意味深长', '若有所思', '欲言又止', '哭笑不得', '无可奈何',
    '异口同声', '不约而同地', '不由自主地', '不假思索', '脱口而出',
]
CLICHE_MAX_PER_1000 = 3  # 每1000字超过3个预警

# 指标9：句尾模式化 — 连续句子相同结尾
SENTENCE_ENDING_MAX_REPEAT = 5  # 连续5句相同句尾预警

# 指标11：Show vs Tell 近似检测 — 直接情感词密度
TELL_WORDS = ['感到', '觉得很', '觉得很', '觉得十分', '觉得非常', '觉得特别', '心里想着',
              '心中暗想', '心中暗道', '心想', '暗自', '暗自想着']
TELL_MAX_PER_1000 = 8  # 每1000字超过8个预警

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="写后自动审计脚本")
    parser.add_argument("--chapter-file", help="章节文件路径")
    parser.add_argument("--prev-file", help="上一章节文件路径（用于重复检测）")
    parser.add_argument("--title", help="章节标题")
    parser.add_argument("--scan-all", action="store_true", help="扫描目录下所有章节")
    parser.add_argument("--dir", default="正文/", help="章节目录（配合 --scan-all 使用）")
    parser.add_argument("--output", help="输出审计报告到JSON文件")
    parser.add_argument("--novel-state", help="同步审计状态到 novel_state.json")
    parser.add_argument("--ability-keywords", default="",
                        help="能力泄露关键词(JSON格式列表)，覆盖默认值")
    args = parser.parse_args()

    # 解析能力关键词
    ability_kw = None
    if args.ability_keywords:
        try:
            ability_kw = json.loads(args.ability_keywords)
        except (JSONDecodeError, TypeError):
            print(f"警告: --ability-keywords 解析失败，使用默认值", file=sys.stderr)

    if args.scan_all:
        if args.scan_all and args.novel_state:
            print("--scan-all 不支持 --novel-state；请按单章审计同步章节状态", file=sys.stderr)
            sys.exit(2)

        # 扫描目录下所有 .md 文件
        files = sorted(glob.glob(f"{args.dir}/*.md"))
        if not files:
            print(f"未在 {args.dir} 下找到 .md 文件")
            sys.exit(1)

        all_results = []
        prev_text = None
        for fpath in files:
            with open(fpath, 'r', encoding='utf-8') as f:
                text = f.read()
            # 提取标题（第一行）
            title_line = text.split('\n')[0].lstrip('# ').strip()
            results = audit_chapter(text, title_line, prev_text, ability_keywords=ability_kw)
            all_results.append(results)
            print(format_report(results))
            prev_text = text

        payload = build_audit_payload(all_results)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"审计报告已保存到 {args.output}")
        if args.novel_state:
            if not args.output:
                print("--novel-state 需要同时提供 --output 作为审计凭证路径", file=sys.stderr)
                sys.exit(2)
            try:
                sync_novel_state(args.novel_state, args.output, payload)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                sys.exit(3)
            print(f"审计状态已同步到 {args.novel_state}")

        sys.exit(0 if _results_passed(all_results) else 1)

    elif args.chapter_file:
        with open(args.chapter_file, 'r', encoding='utf-8') as f:
            text = f.read()

        prev_text = None
        if args.prev_file:
            with open(args.prev_file, 'r', encoding='utf-8') as f:
                prev_text = f.read()

        title = args.title
        if not title:
            # 从文件第一行提取标题（如 "# 第041章 世界之锚的重量"）
            title_line = text.split('\n')[0].lstrip('# ').strip()
            title = title_line if title_line else "未知章节"
        results = audit_chapter(text, title, prev_text, ability_keywords=ability_kw)
        print(format_report(results))

        payload = build_audit_payload(results)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"审计报告已保存到 {args.output}")
        if args.novel_state:
            if not args.output:
                print("--novel-state 需要同时提供 --output 作为审计凭证路径", file=sys.stderr)
                sys.exit(2)
            try:
                sync_novel_state(args.novel_state, args.output, payload)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                sys.exit(3)
            print(f"审计状态已同步到 {args.novel_state}")

        sys.exit(0 if results["pass"] else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
