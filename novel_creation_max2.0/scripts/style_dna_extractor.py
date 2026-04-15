#!/usr/bin/env python3
"""
风格 DNA 提取器

支持：
- 单个文本文件
- 含多个 .txt 文件的目录
- 输出标准化的风格 DNA JSON

不依赖 jieba，使用正则表达式实现中文基础分词。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime
from statistics import fmean, pstdev
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 基础分词（不依赖第三方库）
# ---------------------------------------------------------------------------

def simple_tokenize(text: str) -> List[str]:
    """使用正则表达式进行中文基础分词，按单字切分"""
    return [
        token
        for token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]|[^\s]", text)
        if token.strip() and not re.match(r"[^\w\u4e00-\u9fff]", token)
    ]


def tagged_tokens(text: str) -> List[tuple[str, str]]:
    """基于正则的简易词性标注（eng/num/cn/x）"""
    tokens = simple_tokenize(text)
    tagged: List[tuple[str, str]] = []
    for token in tokens:
        if re.fullmatch(r"[A-Za-z]+", token):
            tagged.append((token, "eng"))
        elif re.fullmatch(r"\d+", token):
            tagged.append((token, "num"))
        elif re.fullmatch(r"[\u4e00-\u9fff]", token):
            tagged.append((token, "cn"))
        else:
            tagged.append((token, "x"))
    return tagged


# ---------------------------------------------------------------------------
# 风格 DNA 数据模型
# ---------------------------------------------------------------------------

class StyleDNA:
    def __init__(self) -> None:
        self.metadata: Dict[str, Any] = {
            "author": "",
            "extract_date": "",
            "sample_chapters": 0,
            "total_words": 0,
            "total_sentences": 0,
        }
        self.sentence_features: Dict[str, Any] = {
            "length_distribution": {},
            "type_ratio": {},
            "complexity_index": 0.0,
        }
        self.word_usage: Dict[str, Any] = {
            "high_freq_words": [],
            "pos_distribution": {},
            "unique_words": [],
            "avg_word_length": 0.0,
        }
        self.description_style: Dict[str, Any] = {
            "environment_ratio": 0.0,
            "psychology_ratio": 0.0,
            "action_ratio": 0.0,
            "typical_patterns": [],
        }
        self.dialogue_style: Dict[str, Any] = {
            "dialogue_ratio": 0.0,
            "marker_preference": [],
            "rhythm_features": {},
            "typical_patterns": [],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "sentence_features": self.sentence_features,
            "word_usage": self.word_usage,
            "description_style": self.description_style,
            "dialogue_style": self.dialogue_style,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def compare(self, other: "StyleDNA") -> Dict[str, float]:
        """比较两个 StyleDNA 的相似度"""
        similarity: Dict[str, float] = {}

        length_sim = self._compare_distribution(
            {
                "short": self.sentence_features["length_distribution"].get("short", 0.0),
                "medium": self.sentence_features["length_distribution"].get("medium", 0.0),
                "long": self.sentence_features["length_distribution"].get("long", 0.0),
            },
            {
                "short": other.sentence_features["length_distribution"].get("short", 0.0),
                "medium": other.sentence_features["length_distribution"].get("medium", 0.0),
                "long": other.sentence_features["length_distribution"].get("long", 0.0),
            },
        )
        type_sim = self._compare_distribution(
            self.sentence_features["type_ratio"],
            other.sentence_features["type_ratio"],
        )
        avg_length_gap = abs(
            float(self.sentence_features["length_distribution"].get("avg_length", 0.0))
            - float(other.sentence_features["length_distribution"].get("avg_length", 0.0))
        )
        avg_length_sim = max(0.0, 1 - avg_length_gap / 40.0)
        similarity["sentence"] = (length_sim + type_sim + avg_length_sim) / 3

        similarity["word_usage"] = self._compare_distribution(
            self.word_usage["pos_distribution"],
            other.word_usage["pos_distribution"],
        )

        desc_self = self.description_style
        desc_other = other.description_style
        desc_gap = (
            abs(desc_self["environment_ratio"] - desc_other["environment_ratio"])
            + abs(desc_self["psychology_ratio"] - desc_other["psychology_ratio"])
            + abs(desc_self["action_ratio"] - desc_other["action_ratio"])
        ) / 3
        similarity["description"] = 1 - desc_gap

        dialogue_gap = abs(
            float(self.dialogue_style["dialogue_ratio"]) - float(other.dialogue_style["dialogue_ratio"])
        )
        dialogue_sim = 1 - dialogue_gap
        rhythm_self = self.dialogue_style.get("rhythm_features", {})
        rhythm_other = other.dialogue_style.get("rhythm_features", {})
        rhythm_sim = self._compare_distribution(
            {
                "short_ratio": rhythm_self.get("short_ratio", 0.0),
                "medium_ratio": rhythm_self.get("medium_ratio", 0.0),
                "long_ratio": rhythm_self.get("long_ratio", 0.0),
            },
            {
                "short_ratio": rhythm_other.get("short_ratio", 0.0),
                "medium_ratio": rhythm_other.get("medium_ratio", 0.0),
                "long_ratio": rhythm_other.get("long_ratio", 0.0),
            },
        )
        similarity["dialogue"] = (dialogue_sim + rhythm_sim) / 2
        similarity["overall"] = sum(similarity.values()) / len(similarity)
        return similarity

    @staticmethod
    def _compare_distribution(left: Dict[str, Any], right: Dict[str, Any]) -> float:
        if not left or not right:
            return 0.0
        keys = set(left.keys()) | set(right.keys())
        total_diff = 0.0
        for key in keys:
            total_diff += abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0)))
        return max(0.0, 1 - total_diff / 2.0)


# ---------------------------------------------------------------------------
# 提取器
# ---------------------------------------------------------------------------

class StyleDNAExtractor:
    def __init__(self) -> None:
        self.dna = StyleDNA()
        self.description_keywords = {
            "environment": ["天", "地", "山", "水", "风", "雨", "光", "影", "街", "楼", "房间", "门"],
            "psychology": ["想", "觉得", "感到", "心里", "内心", "害怕", "怀疑", "后悔", "不安"],
            "action": ["走", "跑", "看", "听", "说", "抓", "推", "拉", "停", "转身", "抬头"],
        }
        self.dialogue_markers = ["说", "道", "问", "答", "喊", "叫", "笑道", "说道", "问道", "答道"]

    # -- 公开接口 ----------------------------------------------------------

    def extract_from_path(self, path: str, author: str = "") -> StyleDNA:
        """从文件或目录提取风格 DNA"""
        self._validate_input(path)
        texts = self._read_texts(path)
        return self.extract_from_texts(texts, author=author)

    def extract_from_texts(self, texts: List[str], author: str = "") -> StyleDNA:
        text = "\n".join(texts)
        dna = self.extract_from_text(text)
        dna.metadata["author"] = author
        dna.metadata["extract_date"] = datetime.now().isoformat(timespec="seconds")
        dna.metadata["sample_chapters"] = len(texts)
        return dna

    def extract_from_text(self, text: str) -> StyleDNA:
        self.dna = StyleDNA()
        sentences = self._extract_sentences(text)
        words = self._extract_words(text)

        self.dna.metadata["total_words"] = len(text)
        self.dna.metadata["total_sentences"] = len(sentences)
        self._extract_sentence_features(sentences)
        self._extract_word_usage(words, text)
        self._extract_description_style(sentences)
        self._extract_dialogue_style(text, sentences)
        return self.dna

    # -- 输入验证 ----------------------------------------------------------

    @staticmethod
    def _validate_input(path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"输入路径不存在: {path}")
        if os.path.isfile(path) and not path.lower().endswith(".txt"):
            raise ValueError(f"输入文件必须是 .txt 格式: {path}")

    # -- 内部方法 ----------------------------------------------------------

    def _read_texts(self, path: str) -> List[str]:
        if os.path.isdir(path):
            file_paths = sorted(
                os.path.join(path, name)
                for name in os.listdir(path)
                if name.lower().endswith(".txt")
            )
            if not file_paths:
                raise FileNotFoundError(f"目录中未找到 txt 文件: {path}")
            texts = []
            for file_path in file_paths:
                with open(file_path, "r", encoding="utf-8-sig", errors="replace") as handle:
                    texts.append(handle.read())
            return texts
        with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
            return [handle.read()]

    def _extract_sentences(self, text: str) -> List[str]:
        return [item.strip() for item in re.findall(r"[^。！？]+[。！？]", text) if item.strip()]

    def _extract_words(self, text: str) -> List[str]:
        return simple_tokenize(text)

    def _extract_sentence_features(self, sentences: List[str]) -> None:
        if not sentences:
            return
        lengths = [len(item) for item in sentences]
        total = len(sentences)
        self.dna.sentence_features["length_distribution"] = {
            "short": sum(1 for item in lengths if item <= 10) / total,
            "medium": sum(1 for item in lengths if 10 < item <= 30) / total,
            "long": sum(1 for item in lengths if item > 30) / total,
            "avg_length": float(fmean(lengths)),
            "std_length": float(pstdev(lengths)) if len(lengths) > 1 else 0.0,
        }
        type_counts = {"declarative": 0, "interrogative": 0, "exclamatory": 0}
        for sentence in sentences:
            if sentence.endswith("？"):
                type_counts["interrogative"] += 1
            elif sentence.endswith("！"):
                type_counts["exclamatory"] += 1
            else:
                type_counts["declarative"] += 1
        self.dna.sentence_features["type_ratio"] = {key: value / total for key, value in type_counts.items()}
        complex_count = sum(1 for item in sentences if len(re.findall(r"[,，、；：]", item)) >= 2)
        self.dna.sentence_features["complexity_index"] = complex_count / total

    def _extract_word_usage(self, words: List[str], text: str) -> None:
        if not words:
            return
        word_freq = Counter(words)
        self.dna.word_usage["high_freq_words"] = [
            {"word": word, "freq": freq, "ratio": freq / len(words)}
            for word, freq in word_freq.most_common(20)
        ]
        pos_counter = Counter()
        for word, pos in tagged_tokens(text):
            if word.strip() and not re.match(r"[^\w]", word):
                pos_counter[pos] += 1
        total_pos = sum(pos_counter.values()) or 1
        self.dna.word_usage["pos_distribution"] = {
            tag: count / total_pos for tag, count in pos_counter.most_common(10)
        }
        self.dna.word_usage["unique_words"] = [word for word, freq in word_freq.items() if freq == 1][:50]
        self.dna.word_usage["avg_word_length"] = float(fmean([len(word) for word in words]))

    def _extract_description_style(self, sentences: List[str]) -> None:
        if not sentences:
            return
        counts = {"environment": 0, "psychology": 0, "action": 0}
        patterns = []
        for sentence in sentences:
            for category, keywords in self.description_keywords.items():
                if any(keyword in sentence for keyword in keywords):
                    counts[category] += 1
                    if len(patterns) < 12 and len(sentence) <= 50:
                        patterns.append({"type": category, "pattern": sentence})
                    break
        total = len(sentences)
        self.dna.description_style["environment_ratio"] = counts["environment"] / total
        self.dna.description_style["psychology_ratio"] = counts["psychology"] / total
        self.dna.description_style["action_ratio"] = counts["action"] / total
        self.dna.description_style["typical_patterns"] = patterns

    def _extract_dialogue_style(self, text: str, sentences: List[str]) -> None:
        dialogues = re.findall(r'["\u201c\u300c]([^"\u201d\u300d]+)["\u201d\u300d]', text)
        dialogue_chars = sum(len(item) for item in dialogues)
        total_chars = len(text) or 1
        self.dna.dialogue_style["dialogue_ratio"] = dialogue_chars / total_chars

        marker_counter = Counter()
        for sentence in sentences:
            for marker in self.dialogue_markers:
                if marker in sentence:
                    marker_counter[marker] += 1
        marker_total = sum(marker_counter.values()) or 1
        self.dna.dialogue_style["marker_preference"] = [
            {"marker": marker, "freq": freq, "ratio": freq / marker_total}
            for marker, freq in marker_counter.most_common(5)
        ]

        if dialogues:
            lengths = [len(item) for item in dialogues]
            total = len(lengths)
            self.dna.dialogue_style["rhythm_features"] = {
                "avg_length": float(fmean(lengths)),
                "short_ratio": sum(1 for item in lengths if item <= 10) / total,
                "medium_ratio": sum(1 for item in lengths if 10 < item <= 30) / total,
                "long_ratio": sum(1 for item in lengths if item > 30) / total,
            }
        self.dna.dialogue_style["typical_patterns"] = [
            sentence for sentence in sentences if any(marker in sentence for marker in self.dialogue_markers)
        ][:10]


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

def extract_from_text(text: str) -> StyleDNA:
    return StyleDNAExtractor().extract_from_text(text)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="风格 DNA 提取器")
    parser.add_argument("--input", required=True, help="输入文件路径或包含多个 txt 的目录")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--author", default="", help="作者名")
    args = parser.parse_args()

    # 输入验证
    if not os.path.exists(args.input):
        print(f"错误: 输入路径不存在: {args.input}", file=__import__("sys").stderr)
        __import__("sys").exit(1)

    extractor = StyleDNAExtractor()
    dna = extractor.extract_from_path(args.input, author=args.author)

    # 确保输出目录存在
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(dna.to_json())
    print(f"风格 DNA 已保存到: {args.output}")
    print(f"样本章节数: {dna.metadata['sample_chapters']}")
    print(f"总字数: {dna.metadata['total_words']}")
    print(f"总句数: {dna.metadata['total_sentences']}")


if __name__ == "__main__":
    main()
