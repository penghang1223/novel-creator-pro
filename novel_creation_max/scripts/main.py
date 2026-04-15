#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长篇小说创作助手 - 统一主入口

功能：
- 协调记忆系统、风格校准、人物一致性、剧情连贯性检查
- 提供统一的命令行界面
- 生成综合分析报告

作者：AI Assistant
版本：2.0.0
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入各个模块
try:
    from memory_manager import MemoryManager
    from style_calibrator import StyleCalibrator
    from character_consistency_checker import CharacterConsistencyChecker
    from plot_continuity_checker import PlotContinuityChecker
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖已安装")
    sys.exit(1)


class NovelCreationAssistant:
    """小说创作助手主类"""
    
    # ANSI 颜色代码
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'underline': '\033[4m'
    }
    
    # Emoji映射
    EMOJIS = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'memory': '🧠',
        'style': '🎨',
        'character': '👤',
        'plot': '📖',
        'report': '📊',
        'check': '🔍',
        'save': '💾',
        'load': '📂'
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化创作助手
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.use_colors = self.config.get('output', {}).get('enable_colors', True)
        self.use_emoji = self.config.get('output', {}).get('enable_emoji', True)
        
        # 初始化各个子系统
        self.memory = MemoryManager()
        self.style = StyleCalibrator()
        self.character = CharacterConsistencyChecker()
        self.plot = PlotContinuityChecker(self.config.get('plot_continuity', {}))
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "output": {
                "enable_colors": True,
                "enable_emoji": True
            }
        }
        
        if not config_path:
            # 尝试从默认位置加载
            default_paths = [
                SCRIPT_DIR.parent / 'config.json',
                SCRIPT_DIR / 'config.json',
                'config.json'
            ]
            for path in default_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _color(self, text: str, color: str) -> str:
        """添加颜色"""
        if not self.use_colors:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _emoji(self, key: str) -> str:
        """获取emoji"""
        if not self.use_emoji:
            return ''
        return self.EMOJIS.get(key, '')
    
    def _header(self, text: str, emoji_key: str = 'info') -> str:
        """生成标题"""
        emoji = self._emoji(emoji_key)
        return self._color(f"\n{emoji} {text}\n{'=' * 50}", 'bold')
    
    def _success(self, text: str) -> str:
        return self._color(f"{self._emoji('success')} {text}", 'green')
    
    def _error(self, text: str) -> str:
        return self._color(f"{self._emoji('error')} {text}", 'red')
    
    def _warning(self, text: str) -> str:
        return self._color(f"{self._emoji('warning')} {text}", 'yellow')
    
    def _info(self, text: str) -> str:
        return self._color(f"{self._emoji('info')} {text}", 'cyan')
    
    def init_memory(self) -> Dict[str, Any]:
        """初始化记忆系统"""
        print(self._header("初始化记忆系统", 'memory'))
        result = self.memory.initialize_memory()
        
        if result['success']:
            print(self._success(result['message']))
            print(f"记忆层次: {', '.join(result['memory_structure']['layers'].keys())}")
        else:
            print(self._error(f"初始化失败: {result.get('message', '未知错误')}"))
        
        return result
    
    def create_chapter_memory(self, chapter_id: str, content: str,
                            metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """创建章节记忆"""
        print(self._header(f"创建章节记忆 - {chapter_id}", 'memory'))
        result = self.memory.create_chapter_memory(chapter_id, content, metadata)
        
        if result['success']:
            print(self._success(result['message']))
            memory = result['chapter_memory']
            print(f"摘要: {memory['content_summary'][:100]}...")
        else:
            print(self._error(f"创建失败: {result.get('message', '未知错误')}"))
        
        return result
    
    def analyze_style(self, text: str) -> Dict[str, Any]:
        """分析文本风格"""
        print(self._header("风格分析", 'style'))
        features = self.style.analyze_style(text)
        
        print(self._info("分析结果:"))
        print(f"  句子长度: 平均 {features['sentence_length']['avg_length']:.1f} 字")
        print(f"  词汇复杂度: {features['vocabulary_complexity']['complexity']}")
        print(f"  情感基调: {features['emotional_tone']['tone']}")
        print(f"  叙事节奏: {features['narrative_rhythm']['rhythm']}")
        
        return features
    
    def calibrate_style(self, reference_text: str, target_text: str) -> Dict[str, Any]:
        """风格校准"""
        print(self._header("风格校准", 'style'))
        
        baseline = self.style.set_baseline(reference_text)
        if not baseline['success']:
            print(self._error(f"设置基准失败: {baseline['message']}"))
            return baseline
        
        print(self._success("基准已设置"))
        drift = self.style.detect_drift(target_text)
        
        if drift['success']:
            print(f"\n总体漂移评分: {drift['overall_drift_score']:.1%}")
            print(f"漂移等级: {drift['drift_level']}")
            
            suggestions = self.style.generate_calibration_suggestions(drift)
            print(self._info("\n校准建议:"))
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        
        return drift
    
    def register_character(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """注册人物"""
        print(self._header(f"注册人物 - {character_data.get('name', 'unknown')}", 'character'))
        result = self.character.register_character(character_data)
        
        if result['success']:
            print(self._success(result['message']))
        else:
            print(self._error(f"注册失败: {result['message']}"))
        
        return result
    
    def check_character(self, text: str, character_id: str) -> Dict[str, Any]:
        """检查人物一致性"""
        print(self._header(f"人物一致性检查 - {character_id}", 'character'))
        result = self.character.check_consistency(text, character_id)
        
        if result['success']:
            score = result['overall_consistency_score']
            score_color = 'green' if score > 0.7 else 'yellow' if score > 0.4 else 'red'
            
            print(f"一致性评分: {self._color(f'{score:.1%}', score_color)}")
            print(f"OOC风险: {'是' if result['is_ooc'] else '否'}")
            
            if result.get('suggestions'):
                print(self._info("\n建议:"))
                for suggestion in result['suggestions']:
                    print(f"  • {suggestion}")
        else:
            print(self._error(f"检查失败: {result['message']}"))
        
        return result
    
    def check_plot_continuity(self, current_chapter: int) -> Dict[str, Any]:
        """检查剧情连贯性"""
        print(self._header(f"剧情连贯性检查 - 第{current_chapter}章", 'plot'))
        result = self.plot.check_continuity(current_chapter)
        
        if result['success']:
            score = result['overall_score']
            score_color = 'green' if score > 0.7 else 'yellow' if score > 0.5 else 'red'
            
            print(f"\n总体评分: {self._color(f'{score:.1%}', score_color)}")
            print(f"连贯性等级: {result['continuity_level']}")
            
            print(self._info("\n各维度检查:"))
            for check_name, check_data in result['checks'].items():
                icon = self._success("✓") if check_data['score'] > 0.7 else self._warning("!")
                print(f"  {icon} {check_name}: {check_data['score']:.1%} "
                      f"({check_data['issue_count']} 个问题)")
        
        return result
    
    def comprehensive_check(self, chapter_id: str, content: str,
                          current_chapter: int,
                          character_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """综合检查"""
        print(self._header("综合检查报告", 'check'))
        print(f"章节: {chapter_id} | 当前章号: {current_chapter}")
        print("-" * 50)
        
        results = {
            'chapter_id': chapter_id,
            'current_chapter': current_chapter,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'checks': {}
        }
        
        # 1. 章节记忆
        print(self._info("\n1. 创建章节记忆..."))
        memory_result = self.create_chapter_memory(chapter_id, content)
        results['checks']['memory'] = memory_result
        
        # 2. 风格分析
        print(self._info("\n2. 风格分析..."))
        if self.style.baseline_features:
            style_result = self.style.detect_drift(content)
            suggestions = self.style.generate_calibration_suggestions(style_result)
            style_result['suggestions'] = suggestions
        else:
            style_result = self.style.analyze_style(content)
        results['checks']['style'] = style_result
        
        # 3. 人物检查
        if character_ids:
            print(self._info("\n3. 人物一致性检查..."))
            character_results = []
            for char_id in character_ids:
                result = self.character.check_consistency(content, char_id)
                character_results.append(result)
            results['checks']['characters'] = character_results
        
        # 4. 剧情检查
        print(self._info("\n4. 剧情连贯性检查..."))
        plot_result = self.check_plot_continuity(current_chapter)
        results['checks']['plot'] = plot_result
        
        # 总结
        print("\n" + "=" * 50)
        print(self._info("总结:"))
        print(f"  记忆创建: {'成功' if memory_result['success'] else '失败'}")
        print(f"  风格评分: {style_result.get('overall_drift_score', 'N/A')}")
        if character_ids:
            ooc_count = sum(1 for r in character_results if r.get('is_ooc', False))
            print(f"  人物OOC: {ooc_count}/{len(character_ids)}")
        print(f"  剧情评分: {plot_result.get('overall_score', 'N/A')}")
        
        return results
    
    def save_all_state(self, output_dir: str = ".") -> Dict[str, Any]:
        """保存所有状态"""
        print(self._header("保存所有状态", 'save'))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        memory_file = output_path / 'memory_data.json'
        results['memory'] = self.memory.save_memory(str(memory_file))
        print(f"  记忆数据: {results['memory']['message']}")
        
        char_file = output_path / 'character_profiles.json'
        results['characters'] = self.character.export_profiles(str(char_file))
        print(f"  人物档案: {results['characters']['message']}")
        
        plot_file = output_path / 'plot_data.json'
        results['plot'] = self.plot.save_state(str(plot_file))
        print(f"  剧情数据: {results['plot']['message']}")
        
        return results


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="长篇小说创作助手 - 统一命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--no-colors', action='store_true', help='禁用颜色输出')
    parser.add_argument('--no-emoji', action='store_true', help='禁用emoji')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # init 命令
    subparsers.add_parser('init', help='初始化记忆系统')
    
    # memory 命令
    memory_parser = subparsers.add_parser('memory', help='记忆系统操作')
    memory_group = memory_parser.add_mutually_exclusive_group(required=True)
    memory_group.add_argument('--chapter', type=str, help='章节ID')
    memory_group.add_argument('--status', action='store_true', help='查看状态')
    memory_parser.add_argument('--content', type=str, help='章节内容')
    
    # style 命令
    style_parser = subparsers.add_parser('style', help='风格校准')
    style_group = style_parser.add_mutually_exclusive_group(required=True)
    style_group.add_argument('--text', type=str, help='待分析文本')
    style_group.add_argument('--baseline', type=str, help='基准文本')
    style_parser.add_argument('--target', type=str, help='目标文本')
    
    # character 命令
    char_parser = subparsers.add_parser('character', help='人物一致性管理')
    char_group = char_parser.add_mutually_exclusive_group(required=True)
    char_group.add_argument('--register', type=str, help='注册人物（JSON）')
    char_group.add_argument('--check', type=str, help='检查文本')
    char_parser.add_argument('--id', type=str, help='人物ID')
    
    # plot 命令
    plot_parser = subparsers.add_parser('plot', help='剧情连贯性管理')
    plot_group = plot_parser.add_mutually_exclusive_group(required=True)
    plot_group.add_argument('--create', nargs=2, metavar=('ID', 'TITLE'), help='创建剧情线索')
    plot_group.add_argument('--check', type=int, help='检查连贯性')
    plot_parser.add_argument('--format', choices=['text', 'html', 'json'], default='text', help='报告格式')
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='综合检查')
    check_parser.add_argument('--chapter', type=str, required=True, help='章节ID')
    check_parser.add_argument('--content', type=str, required=True, help='章节内容')
    check_parser.add_argument('--chapter-num', type=int, required=True, help='当前章号')
    check_parser.add_argument('--chars', nargs='*', help='涉及的人物ID')
    
    # save 命令
    save_parser = subparsers.add_parser('save')
    save_parser.add_argument('--dir', type=str, default='.', help='输出目录')
    
    args = parser.parse_args()
    
    config_path = args.config
    assistant = NovelCreationAssistant(config_path)
    
    if args.no_colors:
        assistant.use_colors = False
    if args.no_emoji:
        assistant.use_emoji = False
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            assistant.init_memory()
        elif args.command == 'memory':
            if args.status:
                assistant.memory.get_memory_status()
            elif args.chapter:
                assistant.create_chapter_memory(args.chapter, args.content or "")
        elif args.command == 'style':
            if args.text:
                assistant.analyze_style(args.text)
            elif args.baseline:
                assistant.calibrate_style(args.baseline, args.target or "")
        elif args.command == 'character':
            if args.register:
                char_data = json.loads(args.register)
                assistant.register_character(char_data)
            elif args.check:
                if not args.id:
                    print(assistant._error("请指定 --id 参数"))
                    return
                assistant.check_character(args.check, args.id)
        elif args.command == 'plot':
            if args.create:
                thread_id, title = args.create
                assistant.plot.create_thread(thread_id, title)
            elif args.check:
                assistant.check_plot_continuity(args.check)
        elif args.command == 'check':
            assistant.comprehensive_check(args.chapter, args.content, args.chapter_num, args.chars)
        elif args.command == 'save':
            assistant.save_all_state(args.dir)
            
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(assistant._error(f"执行出错: {e}"))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
