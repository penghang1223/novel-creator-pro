#!/usr/bin/env python3
"""
人物一致性检查器
检测新章节中人物行为、说话风格、决策模式是否符合初始设定
"""

import json
import re
import argparse
import sys
from typing import Dict, List, Any
from dataclasses import dataclass, field

try:
    import jieba
except ImportError:  # pragma: no cover - graceful fallback for portable skill use
    jieba = None


def simple_tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]|[^\s]", text)
        if token.strip() and not re.match(r"[^\w\u4e00-\u9fff]", token)
    ]


@dataclass
class OOCWarning:
    """OOC警告"""
    character_name: str
    warning_type: str  # behavior, speech, decision, emotion
    description: str
    severity: str  # minor, moderate, severe
    suggestion: str


@dataclass
class ConsistencyReport:
    """一致性检查报告"""
    character_name: str
    consistency_score: float = 0.0
    ooc_warnings: List[OOCWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'character_name': self.character_name,
            'consistency_score': self.consistency_score,
            'ooc_warnings': [
                {
                    'character_name': w.character_name,
                    'warning_type': w.warning_type,
                    'description': w.description,
                    'severity': w.severity,
                    'suggestion': w.suggestion
                }
                for w in self.ooc_warnings
            ],
            'suggestions': self.suggestions
        }
    
    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def get_ooc_warnings(self) -> List[OOCWarning]:
        return self.ooc_warnings
    
    def get_suggestions(self) -> List[str]:
        return self.suggestions


class CharacterProfile:
    """人物档案"""
    
    def __init__(self, profile_data: Dict[str, Any] = None):
        self.basic_info = {}
        self.personality = {}
        self.speech_style = {}
        self.behavior_pattern = {}
        self.emotional_traits = {}
        self.growth_arc = {}
        
        if profile_data:
            self.load_from_dict(profile_data)
    
    def load_from_dict(self, data: Dict[str, Any]):
        """从字典加载人物档案"""
        self.basic_info = data.get('basic_info', {})
        self.personality = data.get('personality', {})
        self.speech_style = data.get('speech_style', {})
        self.behavior_pattern = data.get('behavior_pattern', {})
        self.emotional_traits = data.get('emotional_traits', {})
        self.growth_arc = data.get('growth_arc', {})
    
    def load_from_file(self, file_path: str):
        """从文件加载人物档案"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            self.load_from_dict(data)
        except Exception as e:
            raise Exception(f"加载人物档案失败: {str(e)}")


class CharacterConsistencyChecker:
    """人物一致性检查器"""
    
    def __init__(self, character_profile: CharacterProfile = None):
        self.character_profile = character_profile
        
        # 情绪词汇库（简化版）
        self.emotion_keywords = {
            'positive': ['高兴', '开心', '快乐', '兴奋', '激动', '满足', '幸福'],
            'negative': ['悲伤', '难过', '沮丧', '愤怒', '生气', '焦虑', '恐惧'],
            'neutral': ['平静', '冷静', '淡然', '沉着', '理性']
        }
        
        # 行为强度关键词
        self.intensity_keywords = {
            'strong': ['坚决', '果断', '猛烈', '激烈', '狂怒', '歇斯底里'],
            'moderate': ['认真地', '郑重地', '严肃地', '平静地', '温和地'],
            'weak': ['犹豫', '迟疑', '怯怯地', '小心翼翼', '轻声']
        }
    
    def check_consistency(self, text: str, character_name: str = None) -> ConsistencyReport:
        """
        检查人物一致性
        
        Args:
            text: 待检查的文本
            character_name: 人物名称（如果未设置档案）
        
        Returns:
            ConsistencyReport: 一致性检查报告
        """
        if not self.character_profile and not character_name:
            raise ValueError("需要人物档案或人物名称")
        
        name = character_name or self.character_profile.basic_info.get('name', '未知人物')
        
        # 创建报告
        report = ConsistencyReport(character_name=name)
        
        # 检查各维度一致性
        warnings = []
        
        # 1. 检查说话风格一致性
        speech_warnings = self._check_speech_style(text, name)
        warnings.extend(speech_warnings)
        
        # 2. 检查行为模式一致性
        behavior_warnings = self._check_behavior_pattern(text, name)
        warnings.extend(behavior_warnings)
        
        # 3. 检查情绪反应一致性
        emotion_warnings = self._check_emotional_reaction(text, name)
        warnings.extend(emotion_warnings)
        
        # 4. 检查决策模式一致性
        decision_warnings = self._check_decision_pattern(text, name)
        warnings.extend(decision_warnings)
        
        report.ooc_warnings = warnings
        
        # 计算一致性分数
        if warnings:
            # 基于警告数量和严重程度计算分数
            severity_scores = {'minor': 0.1, 'moderate': 0.3, 'severe': 0.5}
            total_deduction = sum(severity_scores.get(w.severity, 0.1) for w in warnings)
            report.consistency_score = max(0.0, 1.0 - total_deduction)
        else:
            report.consistency_score = 1.0
        
        # 生成建议
        report.suggestions = self._generate_suggestions(warnings)
        
        return report
    
    def _check_speech_style(self, text: str, name: str) -> List[OOCWarning]:
        """检查说话风格一致性"""
        warnings = []
        
        if not self.character_profile or not self.character_profile.speech_style:
            return warnings
        
        speech_style = self.character_profile.speech_style
        
        # 提取该人物的对话
        dialogues = self._extract_character_dialogues(text, name)
        
        if not dialogues:
            return warnings
        
        # 检查口头禅
        catchphrases = speech_style.get('catchphrases', [])
        if catchphrases:
            found_catchphrases = sum(1 for cp in catchphrases 
                                    if any(cp in d for d in dialogues))
            if found_catchphrases == 0 and len(dialogues) >= 3:
                warnings.append(OOCWarning(
                    character_name=name,
                    warning_type='speech',
                    description=f"未发现人物口头禅：{', '.join(catchphrases)}",
                    severity='minor',
                    suggestion=f"考虑在对话中加入口头禅，增强人物特色"
                ))
        
        # 检查用词偏好
        word_preference = speech_style.get('word_preference', [])
        if word_preference:
            for dialogue in dialogues:
                words = list(jieba.cut(dialogue)) if jieba is not None else simple_tokenize(dialogue)
                # 简化检查：如果使用了与偏好相反的词汇
                # 这里可以扩展更复杂的逻辑
        
        # 检查句式特点
        sentence_patterns = speech_style.get('sentence_patterns', [])
        if sentence_patterns:
            for pattern in sentence_patterns:
                if not any(pattern in d for d in dialogues):
                    warnings.append(OOCWarning(
                        character_name=name,
                        warning_type='speech',
                        description=f"未发现典型句式：{pattern}",
                        severity='minor',
                        suggestion=f"考虑使用该人物典型的说话句式"
                    ))
        
        return warnings
    
    def _check_behavior_pattern(self, text: str, name: str) -> List[OOCWarning]:
        """检查行为模式一致性"""
        warnings = []
        
        if not self.character_profile or not self.character_profile.behavior_pattern:
            return warnings
        
        behavior_pattern = self.character_profile.behavior_pattern
        
        # 提取该人物的行为描述
        behaviors = self._extract_character_behaviors(text, name)
        
        if not behaviors:
            return warnings
        
        # 检查决策风格
        decision_style = behavior_pattern.get('decision_style', {})
        decision_style_name = decision_style.get('style', '') if isinstance(decision_style, dict) else str(decision_style)
        if decision_style:
            # 检查是否与设定的决策风格冲突
            if decision_style_name == '果断':
                hesitation_keywords = ['犹豫', '迟疑', '徘徊', '犹豫不决']
                for behavior in behaviors:
                    if any(kw in behavior for kw in hesitation_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='behavior',
                            description=f"人物行为与果断决策风格不符：{behavior[:50]}...",
                            severity='moderate',
                            suggestion="该人物设定为果断型，应避免犹豫行为"
                        ))
            elif decision_style_name == '谨慎':
                impulsive_keywords = ['冲动', '鲁莽', '草率', '贸然']
                for behavior in behaviors:
                    if any(kw in behavior for kw in impulsive_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='behavior',
                            description=f"人物行为与谨慎决策风格不符：{behavior[:50]}...",
                            severity='moderate',
                            suggestion="该人物设定为谨慎型，应避免冲动行为"
                        ))
        
        # 检查压力应对方式
        stress_response = behavior_pattern.get('stress_response', '')
        if stress_response:
            # 简化检查：查找压力情境下的反应
            stress_keywords = ['压力', '困境', '危机', '危险', '威胁']
            for behavior in behaviors:
                if any(kw in behavior for kw in stress_keywords):
                    # 简化逻辑：记录压力场景，实际可以添加更复杂的检查
                    pass
        
        return warnings
    
    def _check_emotional_reaction(self, text: str, name: str) -> List[OOCWarning]:
        """检查情绪反应一致性"""
        warnings = []
        
        if not self.character_profile or not self.character_profile.emotional_traits:
            return warnings
        
        emotional_traits = self.character_profile.emotional_traits
        
        # 提取该人物的情绪表达
        emotions = self._extract_character_emotions(text, name)
        
        if not emotions:
            return warnings
        
        # 检查情感表达方式
        expression_style = emotional_traits.get('expression_style', {})
        expression_style_name = expression_style.get('style', '') if isinstance(expression_style, dict) else str(expression_style)
        if expression_style:
            if expression_style_name == '内敛':
                # 检查是否有过于外放的情绪表达
                intense_keywords = ['大声', '喊叫', '哭泣', '崩溃', '失控']
                for emotion in emotions:
                    if any(kw in emotion for kw in intense_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='emotion',
                            description=f"情绪表达过于外放，与内敛性格不符：{emotion[:50]}...",
                            severity='moderate',
                            suggestion="该人物情感表达内敛，应减少激烈的情绪外露"
                        ))
            elif expression_style_name == '外放':
                # 检查是否有过于压抑的情绪表达
                suppress_keywords = ['压抑', '克制', '掩饰', '隐藏']
                for emotion in emotions:
                    if any(kw in emotion for kw in suppress_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='emotion',
                            description=f"情绪表达过于压抑，与外放性格不符：{emotion[:50]}...",
                            severity='minor',
                            suggestion="该人物情感表达外放，可以更直接地表现情绪"
                        ))
        
        # 检查情感触发点
        triggers = emotional_traits.get('emotional_triggers', [])
        if triggers:
            # 查找触发点相关场景
            for trigger in triggers:
                # 简化逻辑：实际可以添加更复杂的触发点检查
                pass
        
        return warnings
    
    def _check_decision_pattern(self, text: str, name: str) -> List[OOCWarning]:
        """检查决策模式一致性"""
        warnings = []
        
        if not self.character_profile or not self.character_profile.personality:
            return warnings
        
        personality = self.character_profile.personality
        
        # 提取该人物的决策场景
        decisions = self._extract_character_decisions(text, name)
        
        if not decisions:
            return warnings
        
        # 检查核心性格与决策的一致性
        core_traits = personality.get('core_traits', [])
        if core_traits:
            # 检查决策是否与核心性格冲突
            for decision in decisions:
                # 简化检查：基于关键词匹配
                if '理性' in core_traits:
                    emotional_keywords = ['一时冲动', '情绪化', '失去理智']
                    if any(kw in decision for kw in emotional_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='decision',
                            description=f"决策与理性性格不符：{decision[:50]}...",
                            severity='severe',
                            suggestion="该人物核心性格为理性，决策应更注重逻辑分析"
                        ))
                
                if '感性' in core_traits:
                    cold_keywords = ['冷酷', '无情', '漠视', '冷血']
                    if any(kw in decision for kw in cold_keywords):
                        warnings.append(OOCWarning(
                            character_name=name,
                            warning_type='decision',
                            description=f"决策与感性性格不符：{decision[:50]}...",
                            severity='severe',
                            suggestion="该人物核心性格为感性，决策应更注重情感因素"
                        ))
        
        return warnings
    
    def _extract_character_dialogues(self, text: str, name: str) -> List[str]:
        """提取人物的对话"""
        dialogues = []
        
        # 匹配对话模式："..."或「...」
        dialogue_pattern = r'["「『]([^"」』]+)["」』]'
        
        # 查找包含人物名的句子
        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            if name in sentence:
                # 提取对话内容
                matches = re.findall(dialogue_pattern, sentence)
                dialogues.extend(matches)
        
        return dialogues
    
    def _extract_character_behaviors(self, text: str, name: str) -> List[str]:
        """提取人物的行为描述"""
        behaviors = []
        
        # 简化逻辑：提取包含人物名的句子
        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            if name in sentence and len(sentence) > 10:
                # 排除纯对话句子
                if not re.match(r'^["「『]', sentence.strip()):
                    behaviors.append(sentence)
        
        return behaviors
    
    def _extract_character_emotions(self, text: str, name: str) -> List[str]:
        """提取人物的情绪表达"""
        emotions = []
        
        # 查找情绪关键词
        all_emotion_keywords = []
        for keywords in self.emotion_keywords.values():
            all_emotion_keywords.extend(keywords)
        
        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            if name in sentence:
                if any(kw in sentence for kw in all_emotion_keywords):
                    emotions.append(sentence)
        
        return emotions
    
    def _extract_character_decisions(self, text: str, name: str) -> List[str]:
        """提取人物的决策场景"""
        decisions = []
        
        # 决策相关关键词
        decision_keywords = ['决定', '选择', '打算', '准备', '要', '想', '必须', '应该']
        
        sentences = re.split(r'[。！？\n]', text)
        for sentence in sentences:
            if name in sentence:
                if any(kw in sentence for kw in decision_keywords):
                    decisions.append(sentence)
        
        return decisions
    
    def _generate_suggestions(self, warnings: List[OOCWarning]) -> List[str]:
        """生成修正建议"""
        suggestions = []
        
        if not warnings:
            suggestions.append("人物表现一致，符合设定")
            return suggestions
        
        # 按严重程度分类
        severe_warnings = [w for w in warnings if w.severity == 'severe']
        moderate_warnings = [w for w in warnings if w.severity == 'moderate']
        minor_warnings = [w for w in warnings if w.severity == 'minor']
        
        if severe_warnings:
            suggestions.append(f"【严重】发现{len(severe_warnings)}处严重OOC，建议立即修正")
            for w in severe_warnings[:3]:  # 只显示前3条
                suggestions.append(f"  - {w.description}")
        
        if moderate_warnings:
            suggestions.append(f"【中等】发现{len(moderate_warnings)}处中等程度OOC，建议调整")
        
        if minor_warnings:
            suggestions.append(f"【轻微】发现{len(minor_warnings)}处轻微偏差，可选择优化")
        
        # 汇总建议
        all_suggestions = [w.suggestion for w in warnings if w.suggestion]
        unique_suggestions = list(dict.fromkeys(all_suggestions))  # 去重保持顺序
        if unique_suggestions:
            suggestions.append("具体建议：")
            for s in unique_suggestions[:5]:
                suggestions.append(f"  - {s}")
        
        return suggestions


def check_consistency(new_text: str, character_profile: CharacterProfile) -> ConsistencyReport:
    """便捷函数：检查人物一致性"""
    checker = CharacterConsistencyChecker(character_profile)
    return checker.check_consistency(new_text)


def main():
    parser = argparse.ArgumentParser(description='人物一致性检查器')
    parser.add_argument('--input', required=True, help='待检查的文本文件路径')
    parser.add_argument('--character-profile', required=True, help='人物档案文件路径')
    parser.add_argument('--output', help='输出报告文件路径（可选）')
    
    args = parser.parse_args()
    
    try:
        # 加载人物档案
        profile = CharacterProfile()
        profile.load_from_file(args.character_profile)
        
        # 创建检查器
        checker = CharacterConsistencyChecker(profile)
        
        # 读取待检查文本
        with open(args.input, 'r', encoding='utf-8-sig') as f:
            text = f.read()
        
        # 执行检查
        report = checker.check_consistency(text)
        
        # 输出结果
        print("=== 人物一致性检查报告 ===")
        print(f"人物: {report.character_name}")
        print(f"一致性分数: {report.consistency_score:.2%}")
        
        if report.ooc_warnings:
            print(f"\nOOC警告 ({len(report.ooc_warnings)}个):")
            for i, warning in enumerate(report.ooc_warnings, 1):
                print(f"  {i}. [{warning.severity}] {warning.description}")
        
        print("\n修正建议:")
        for i, suggestion in enumerate(report.suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report.to_json())
            print(f"\n报告已保存到: {args.output}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
