#!/usr/bin/env python3
"""
风格校准器
计算新章节与风格DNA的偏离度，生成校准建议

依赖：style_dna_extractor.py（同目录）
"""

import json
import argparse
import os
import sys
from typing import Dict, List, Any
from dataclasses import dataclass, field

# 导入风格DNA提取器
sys.path.insert(0, os.path.dirname(__file__))
from style_dna_extractor import StyleDNA, StyleDNAExtractor


@dataclass
class CalibrationReport:
    """校准报告"""
    deviation_score: float = 0.0
    deviation_details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    mode: str = 'realtime'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'deviation_score': self.deviation_score,
            'deviation_details': self.deviation_details,
            'suggestions': self.suggestions,
            'mode': self.mode
        }

    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class StyleCalibrator:
    """风格校准器"""

    def __init__(self, style_dna: StyleDNA = None):
        self.style_dna = style_dna
        self.extractor = StyleDNAExtractor()

        # 偏离度阈值
        self.thresholds = {
            'realtime': {'warning': 0.3, 'critical': 0.5},
            'periodic': {'warning': 0.25, 'critical': 0.4},
            'emergency': {'warning': 0.2, 'critical': 0.3}
        }

    def load_style_dna(self, dna_path: str):
        """加载风格DNA"""
        if not os.path.exists(dna_path):
            raise FileNotFoundError(f"风格DNA文件不存在: {dna_path}")
        try:
            with open(dna_path, 'r', encoding='utf-8-sig') as f:
                dna_data = json.load(f)

            self.style_dna = StyleDNA()
            self.style_dna.metadata = dna_data.get('metadata', {})
            self.style_dna.sentence_features = dna_data.get('sentence_features', {})
            self.style_dna.word_usage = dna_data.get('word_usage', {})
            self.style_dna.description_style = dna_data.get('description_style', {})
            self.style_dna.dialogue_style = dna_data.get('dialogue_style', {})

        except json.JSONDecodeError as e:
            raise ValueError(f"风格DNA文件JSON格式错误: {e}")
        except Exception as e:
            raise Exception(f"加载风格DNA失败: {str(e)}")

    def calibrate(self, text: str, mode: str = 'realtime') -> CalibrationReport:
        """
        校准新文本与风格DNA的偏离度

        Args:
            text: 待校准的文本
            mode: 校准模式（realtime/periodic/emergency）

        Returns:
            CalibrationReport: 校准报告
        """
        if not self.style_dna:
            raise ValueError("未设置风格DNA，请先加载风格DNA")

        if not text or not text.strip():
            raise ValueError("待校准文本不能为空")

        # 提取新文本的风格特征
        new_dna = self.extractor.extract_from_text(text)

        # 计算相似度
        similarity = self.style_dna.compare(new_dna)

        # 转换为偏离度
        deviation_score = 1 - similarity.get('overall', 1.0)

        # 计算各维度的偏离度
        deviation_details = {
            'sentence': 1 - similarity.get('sentence', 1.0),
            'word_usage': 1 - similarity.get('word_usage', 1.0),
            'description': 1 - similarity.get('description', 1.0),
            'dialogue': 1 - similarity.get('dialogue', 1.0)
        }

        # 生成校准建议
        suggestions = self._generate_suggestions(deviation_score, deviation_details, mode)

        return CalibrationReport(
            deviation_score=deviation_score,
            deviation_details=deviation_details,
            suggestions=suggestions,
            mode=mode
        )

    def _generate_suggestions(self, deviation_score: float,
                              deviation_details: Dict[str, float],
                              mode: str) -> List[str]:
        """生成校准建议"""
        suggestions = []
        threshold = self.thresholds.get(mode, self.thresholds['realtime'])

        # 总体建议
        if deviation_score >= threshold['critical']:
            suggestions.append("【严重警告】风格偏离度过高，建议重新审视并大幅调整")
        elif deviation_score >= threshold['warning']:
            suggestions.append("【警告】风格偏离度较高，建议进行校准")

        # 句式特征建议
        if deviation_details.get('sentence', 0) > 0.3:
            suggestions.append("句式特征偏离：建议检查句子长度分布和句式类型")
            if self.style_dna.sentence_features.get('length_distribution'):
                target = self.style_dna.sentence_features['length_distribution']
                suggestions.append(
                    f"参考：短句占比{target.get('short', 0):.1%}，"
                    f"中句占比{target.get('medium', 0):.1%}，"
                    f"长句占比{target.get('long', 0):.1%}"
                )

        # 用词习惯建议
        if deviation_details.get('word_usage', 0) > 0.3:
            suggestions.append("用词习惯偏离：建议检查用词选择和词性分布")
            if self.style_dna.word_usage.get('high_freq_words'):
                top_words = self.style_dna.word_usage['high_freq_words'][:5]
                suggestions.append(
                    f"高频用词：{', '.join([w['word'] for w in top_words])}"
                )

        # 描写风格建议
        if deviation_details.get('description', 0) > 0.3:
            suggestions.append("描写风格偏离：建议调整环境、心理、动作描写的比例")
            desc_style = self.style_dna.description_style
            suggestions.append(
                f"参考：环境描写{desc_style.get('environment_ratio', 0):.1%}，"
                f"心理描写{desc_style.get('psychology_ratio', 0):.1%}，"
                f"动作描写{desc_style.get('action_ratio', 0):.1%}"
            )

        # 对话风格建议
        if deviation_details.get('dialogue', 0) > 0.3:
            suggestions.append("对话风格偏离：建议调整对话占比和对话标记词使用")
            dialogue_style = self.style_dna.dialogue_style
            suggestions.append(
                f"参考：对话占比{dialogue_style.get('dialogue_ratio', 0):.1%}"
            )
            if dialogue_style.get('marker_preference'):
                markers = dialogue_style['marker_preference'][:3]
                suggestions.append(
                    f"常用对话标记：{', '.join([m['marker'] for m in markers])}"
                )

        if not suggestions:
            suggestions.append("风格保持良好，无明显偏离")

        return suggestions

    def compare_texts(self, text1: str, text2: str) -> Dict[str, float]:
        """比较两段文本的风格差异"""
        dna1 = self.extractor.extract_from_text(text1)
        dna2 = self.extractor.extract_from_text(text2)
        return dna1.compare(dna2)


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

def calibrate(new_text: str, style_dna: StyleDNA, mode: str = 'realtime') -> CalibrationReport:
    calibrator = StyleCalibrator(style_dna)
    return calibrator.calibrate(new_text, mode)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='风格校准器')
    parser.add_argument('--input', required=True, help='待校准的文本文件路径')
    parser.add_argument('--style-dna', required=True, help='风格DNA文件路径')
    parser.add_argument('--mode', choices=['realtime', 'periodic', 'emergency'],
                        default='realtime', help='校准模式')
    parser.add_argument('--output', help='输出报告文件路径（可选）')

    args = parser.parse_args()

    # 输入验证
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.style_dna):
        print(f"错误: 风格DNA文件不存在: {args.style_dna}", file=sys.stderr)
        sys.exit(1)

    try:
        calibrator = StyleCalibrator()
        calibrator.load_style_dna(args.style_dna)

        with open(args.input, 'r', encoding='utf-8-sig', errors='replace') as f:
            text = f.read()

        report = calibrator.calibrate(text, args.mode)

        # 输出结果
        result = report.to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report.to_json())
            print(f"\n报告已保存到: {args.output}", file=sys.stderr)

    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
