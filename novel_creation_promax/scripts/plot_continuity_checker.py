#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧情连贯性检查器 - 追踪剧情线索，维护逻辑连贯性

功能：
- 管理多条剧情线索
- 检测剧情逻辑漏洞
- 追踪伏笔和悬念
- 验证时间线一致性
- 生成剧情连贯性报告

作者：AI Assistant
版本：2.0.0
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False


@dataclass
class PlotThread:
    """剧情线索"""
    thread_id: str
    title: str
    status: str = "进行中"  # 进行中、已完结、暂停、废弃
    key_events: List[Dict[str, Any]] = field(default_factory=list)
    timeline_position: str = ""
    dependencies: List[str] = field(default_factory=list)
    clues: List[str] = field(default_factory=list)  # 埋下的伏笔
    promises: List[str] = field(default_factory=list)  # 对读者的承诺
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlotHole:
    """剧情漏洞"""
    hole_id: str
    type: str  # timeline、logic、character、promise
    description: str
    severity: str = "中等"  # 轻微、中等、严重
    related_threads: List[str] = field(default_factory=list)
    suggested_fix: str = ""


class PlotContinuityChecker:
    """剧情连贯性检查器主类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化剧情连贯性检查器
        
        Args:
            config: 配置字典
        """
        self.config = config or self._default_config()
        self.threads: Dict[str, PlotThread] = {}
        self.plot_holes: List[PlotHole] = []
        self.timeline: List[Dict[str, Any]] = []
        self.foreshadowing: List[Dict[str, Any]] = []
        self._load_custom_dict()
    
    def _default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "timeline_consistency_weight": 0.3,
            "logic_consistency_weight": 0.4,
            "promise_resolution_weight": 0.3,
            "foreshadowing_threshold": 0.6,
            "max_unresolved_promises": 5,
            "enable_auto_detection": True
        }
    
    def _load_custom_dict(self) -> None:
        """加载自定义词典"""
        if not HAS_JIEBA:
            return
        # 添加小说常用词汇
        custom_words = [
            '伏笔', '悬念', '线索', '铺垫', '高潮', '转折', '冲突',
            '伏笔', '照应', '悬念', '铺垫', '悬念迭起', '出人意料',
            '情理之中', '意料之外', '命运', '因果', '逻辑'
        ]
        for word in custom_words:
            jieba.add_word(word, freq=100, tag='n')
    
    # ==================== 剧情线索管理 ====================
    
    def create_thread(self, thread_id: str, title: str, 
                     timeline_position: str = "",
                     dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        创建新的剧情线索
        
        Args:
            thread_id: 线索ID
            title: 线索标题
            timeline_position: 时间线位置
            dependencies: 依赖的其他线索
            
        Returns:
            创建结果
        """
        if thread_id in self.threads:
            return {
                "success": False,
                "message": f"线索 {thread_id} 已存在"
            }
        
        thread = PlotThread(
            thread_id=thread_id,
            title=title,
            timeline_position=timeline_position,
            dependencies=dependencies or []
        )
        self.threads[thread_id] = thread
        
        # 检查依赖关系
        if dependencies:
            self._validate_dependencies(thread_id, dependencies)
        
        return {
            "success": True,
            "message": f"剧情线索 '{title}' 创建成功",
            "thread_id": thread_id
        }
    
    def add_event(self, thread_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        为剧情线索添加事件
        
        Args:
            thread_id: 线索ID
            event: 事件信息，包含：
                - chapter: 章节
                - summary: 事件摘要
                - importance: 重要性（高/中/低）
                - characters: 涉及人物
                - consequences: 后续影响
                
        Returns:
            添加结果
        """
        if thread_id not in self.threads:
            return {
                "success": False,
                "message": f"线索 {thread_id} 不存在"
            }
        
        thread = self.threads[thread_id]
        
        # 验证事件格式
        required_fields = ["chapter", "summary"]
        for field in required_fields:
            if field not in event:
                return {
                    "success": False,
                    "message": f"事件缺少必需字段: {field}"
                }
        
        event_entry = {
            "event_id": f"evt_{thread_id}_{len(thread.key_events) + 1}",
            "timestamp": datetime.now().isoformat(),
            "chapter": event["chapter"],
            "summary": event["summary"],
            "importance": event.get("importance", "中"),
            "characters": event.get("characters", []),
            "consequences": event.get("consequences", []),
            "resolved_clues": event.get("resolved_clues", [])
        }
        
        thread.key_events.append(event_entry)
        
        # 更新到时间线
        self.timeline.append({
            "chapter": event["chapter"],
            "thread_id": thread_id,
            "event_summary": event["summary"],
            "timestamp": event_entry["timestamp"]
        })
        self.timeline.sort(key=lambda x: (x["chapter"], x["timestamp"]))
        
        return {
            "success": True,
            "message": f"事件已添加到线索 '{thread.title}'",
            "event_id": event_entry["event_id"]
        }
    
    def add_foreshadowing(self, thread_id: str, clue: str, 
                         resolution_chapter: Optional[str] = None) -> Dict[str, Any]:
        """
        添加伏笔/悬念
        
        Args:
            thread_id: 线索ID
            clue: 伏笔内容
            resolution_chapter: 预期解决章节
            
        Returns:
            添加结果
        """
        if thread_id not in self.threads:
            return {
                "success": False,
                "message": f"线索 {thread_id} 不存在"
            }
        
        thread = self.threads[thread_id]
        thread.clues.append(clue)
        
        self.foreshadowing.append({
            "clue_id": f"clue_{thread_id}_{len(thread.clues)}",
            "thread_id": thread_id,
            "content": clue,
            "resolution_chapter": resolution_chapter,
            "status": "待解决",
            "added_at": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": f"伏笔已添加",
            "clue_id": f"clue_{thread_id}_{len(thread.clues)}"
        }
    
    def add_promise(self, thread_id: str, promise: str,
                   expected_resolution: str) -> Dict[str, Any]:
        """
        添加对读者的承诺（需要解决的悬念）
        
        Args:
            thread_id: 线索ID
            promise: 承诺内容
            expected_resolution: 预期解决方式
            
        Returns:
            添加结果
        """
        if thread_id not in self.threads:
            return {
                "success": False,
                "message": f"线索 {thread_id} 不存在"
            }
        
        thread = self.threads[thread_id]
        thread.promises.append(promise)
        
        return {
            "success": True,
            "message": f"承诺已添加: {promise}",
            "promise_id": f"promise_{thread_id}_{len(thread.promises)}"
        }
    
    # ==================== 连贯性检查 ====================
    
    def check_continuity(self, current_chapter: int) -> Dict[str, Any]:
        """
        执行完整的连贯性检查
        
        Args:
            current_chapter: 当前章节
            
        Returns:
            连贯性检查报告
        """
        results = {
            "success": True,
            "chapter": current_chapter,
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # 1. 时间线一致性检查
        results["checks"]["timeline"] = self._check_timeline_consistency()
        
        # 2. 逻辑一致性检查
        results["checks"]["logic"] = self._check_logic_consistency()
        
        # 3. 伏笔解决检查
        results["checks"]["foreshadowing"] = self._check_foreshadowing_resolution(current_chapter)
        
        # 4. 承诺兑现检查
        results["checks"]["promises"] = self._check_promise_resolution()
        
        # 计算总体评分
        scores = [check["score"] for check in results["checks"].values()]
        results["overall_score"] = round(sum(scores) / len(scores), 3)
        results["continuity_level"] = self._get_continuity_level(results["overall_score"])
        
        return results
    
    def _check_timeline_consistency(self) -> Dict[str, Any]:
        """检查时间线一致性"""
        issues = []
        score = 1.0
        
        # 检查时间顺序
        for i in range(len(self.timeline) - 1):
            current = self.timeline[i]
            next_event = self.timeline[i + 1]
            
            if next_event["chapter"] < current["chapter"]:
                issues.append({
                    "type": "timeline_regression",
                    "description": f"时间线回溯：从第{current['chapter']}章回到第{next_event['chapter']}章",
                    "severity": "严重",
                    "events": [current["event_summary"], next_event["event_summary"]]
                })
                score -= 0.2
        
        # 检查因果关系
        for thread_id, thread in self.threads.items():
            if thread.dependencies:
                for dep_id in thread.dependencies:
                    if dep_id not in self.threads:
                        issues.append({
                            "type": "missing_dependency",
                            "description": f"依赖的线索 '{dep_id}' 不存在",
                            "severity": "中等",
                            "thread": thread_id
                        })
                        score -= 0.1
        
        score = max(0.0, score)
        
        return {
            "score": round(score, 3),
            "issues": issues,
            "issue_count": len(issues)
        }
    
    def _check_logic_consistency(self) -> Dict[str, Any]:
        """检查逻辑一致性"""
        issues = []
        score = 1.0
        
        for thread_id, thread in self.threads.items():
            # 检查事件之间的逻辑关系
            events = thread.key_events
            for i in range(len(events) - 1):
                current_event = events[i]
                next_event = events[i + 1]
                
                # 简单的因果检查
                if not self._has_logical_connection(current_event, next_event):
                    issues.append({
                        "type": "logical_disconnect",
                        "description": f"事件之间缺乏逻辑连接",
                        "severity": "中等",
                        "thread": thread_id,
                        "chapter_range": f"{current_event['chapter']}-{next_event['chapter']}"
                    })
                    score -= 0.05
        
        score = max(0.0, score)
        
        return {
            "score": round(score, 3),
            "issues": issues,
            "issue_count": len(issues)
        }
    
    def _has_logical_connection(self, event1: Dict, event2: Dict) -> bool:
        """检查两个事件是否有逻辑连接"""
        # 简化版：检查关键词
        keywords = ['因此', '于是', '结果', '于是乎', '紧接着', '之后', '后来']
        
        summary1 = event1.get("summary", "")
        summary2 = event2.get("summary", "")
        
        # 检查是否有因果连接词
        for keyword in keywords:
            if keyword in summary1 or keyword in summary2:
                return True
        
        # 检查是否有人物重叠
        chars1 = set(event1.get("characters", []))
        chars2 = set(event2.get("characters", []))
        if chars1 & chars2:  # 有交集
            return True
        
        return True  # 默认返回True，避免误报
    
    def _check_foreshadowing_resolution(self, current_chapter: int) -> Dict[str, Any]:
        """检查伏笔解决情况"""
        unresolved = []
        resolved_count = 0
        
        for clue in self.foreshadowing:
            if clue["status"] == "已解决":
                resolved_count += 1
            else:
                # 检查是否超时未解决
                expected = clue.get("resolution_chapter")
                if expected and int(expected) < current_chapter:
                    unresolved.append({
                        "clue_id": clue["clue_id"],
                        "content": clue["content"],
                        "expected_chapter": expected,
                        "overdue_chapters": current_chapter - int(expected)
                    })
        
        total = len(self.foreshadowing)
        score = resolved_count / total if total > 0 else 1.0
        
        # 对未解决的伏笔扣分
        if unresolved:
            score -= len(unresolved) * 0.1
        
        score = max(0.0, min(1.0, score))
        
        return {
            "score": round(score, 3),
            "resolved_count": resolved_count,
            "total_count": total,
            "unresolved": unresolved,
            "issue_count": len(unresolved)
        }
    
    def _check_promise_resolution(self) -> Dict[str, Any]:
        """检查承诺兑现情况"""
        broken_promises = []
        
        for thread_id, thread in self.threads.items():
            if thread.status == "已完结" and thread.promises:
                # 检查是否所有承诺都已解决
                for promise in thread.promises:
                    # 简化：检查事件中是否有解决标记
                    resolved = any(
                        promise in evt.get("resolved_clues", [])
                        for evt in thread.key_events
                    )
                    if not resolved:
                        broken_promises.append({
                            "thread_id": thread_id,
                            "promise": promise
                        })
        
        total_promises = sum(len(t.promises) for t in self.threads.values())
        resolved = total_promises - len(broken_promises)
        score = resolved / total_promises if total_promises > 0 else 1.0
        
        return {
            "score": round(score, 3),
            "resolved_count": resolved,
            "total_count": total_promises,
            "broken_promises": broken_promises,
            "issue_count": len(broken_promises)
        }
    
    def _get_continuity_level(self, score: float) -> str:
        """获取连贯性等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.7:
            return "良好"
        elif score >= 0.5:
            return "一般"
        else:
            return "需改进"
    
    # ==================== 报告生成 ====================
    
    def generate_report(self, current_chapter: int,
                       format: str = "text") -> str:
        """
        生成连贯性报告
        
        Args:
            current_chapter: 当前章节
            format: 报告格式（text/html/json）
            
        Returns:
            格式化报告
        """
        results = self.check_continuity(current_chapter)
        
        if format == "json":
            return json.dumps(results, ensure_ascii=False, indent=2)
        
        elif format == "html":
            return self._generate_html_report(results)
        
        else:
            return self._generate_text_report(results)
    
    def _generate_text_report(self, results: Dict[str, Any]) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"📖 剧情连贯性检查报告")
        lines.append(f"章节: {results['chapter']}")
        lines.append(f"检查时间: {results['timestamp']}")
        lines.append("=" * 60)
        lines.append("")
        
        # 总体评分
        lines.append(f"📊 总体评分: {results['overall_score']:.1%} ({results['continuity_level']})")
        lines.append("")
        
        # 各维度检查
        for check_name, check_data in results["checks"].items():
            check_title = {
                "timeline": "⏰ 时间线一致性",
                "logic": "🧠 逻辑一致性",
                "foreshadowing": "🔮 伏笔解决",
                "promises": "📝 承诺兑现"
            }.get(check_name, check_name)
            
            lines.append(f"{check_title}: {check_data['score']:.1%}")
            
            if check_data.get("issues"):
                lines.append(f"  发现 {len(check_data['issues'])} 个问题:")
                for issue in check_data["issues"]:
                    lines.append(f"  - [{issue['severity']}] {issue['description']}")
            
            lines.append("")
        
        # 总结建议
        lines.append("-" * 60)
        lines.append("💡 改进建议:")
        
        if results["overall_score"] < 0.7:
            lines.append("  1. 建议检查时间线顺序，避免章节回溯")
            lines.append("  2. 确保事件之间有清晰的因果关系")
            lines.append("  3. 及时解决已埋下的伏笔")
        else:
            lines.append("  继续保持当前的创作节奏！")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>剧情连贯性检查报告 - 第{results['chapter']}章</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; border-radius: 5px; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .check-section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #2196F3; }}
        .issue {{ color: #f44336; }}
        .good {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📖 剧情连贯性检查报告</h1>
        <p>章节: {results['chapter']} | 时间: {results['timestamp']}</p>
        <p class="score">{results['overall_score']:.1%}</p>
        <p>{results['continuity_level']}</p>
    </div>
    <div class="content">
        <h2>检查结果</h2>
        {self._html_check_results(results['checks'])}
    </div>
</body>
</html>
        """
        return html
    
    def _html_check_results(self, checks: Dict[str, Any]) -> str:
        """生成HTML格式的检查结果"""
        sections = []
        for name, data in checks.items():
            title = {"timeline": "⏰ 时间线", "logic": "🧠 逻辑", 
                    "foreshadowing": "🔮 伏笔", "promises": "📝 承诺"}.get(name, name)
            
            section = f'<div class="check-section"><h3>{title}: {data["score"]:.1%}</h3>'
            
            if data.get("issues"):
                section += '<ul class="issue">'
                for issue in data["issues"][:5]:  # 最多显示5个
                    section += f'<li>[{issue["severity"]}] {issue["description"]}</li>'
                section += '</ul>'
            else:
                section += '<p class="good">✓ 无问题</p>'
            
            section += '</div>'
            sections.append(section)
        
        return "\n".join(sections)
    
    # ==================== 数据持久化 ====================
    
    def save_state(self, output_file: str = "plot_data.json") -> Dict[str, Any]:
        """保存状态到文件"""
        try:
            data = {
                "threads": {tid: t.to_dict() for tid, t in self.threads.items()},
                "plot_holes": [asdict(h) for h in self.plot_holes],
                "timeline": self.timeline,
                "foreshadowing": self.foreshadowing,
                "config": self.config
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": f"状态已保存到 {output_file}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"保存失败: {str(e)}"
            }
    
    def load_state(self, input_file: str) -> Dict[str, Any]:
        """从文件加载状态"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建对象
            self.threads = {
                tid: PlotThread(**tdata) 
                for tid, tdata in data.get("threads", {}).items()
            }
            self.plot_holes = [
                PlotHole(**hdata) 
                for hdata in data.get("plot_holes", [])
            ]
            self.timeline = data.get("timeline", [])
            self.foreshadowing = data.get("foreshadowing", [])
            self.config = data.get("config", self._default_config())
            
            return {
                "success": True,
                "message": f"已加载 {len(self.threads)} 个剧情线索"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}"
            }
    
    def get_thread_summary(self) -> List[Dict[str, Any]]:
        """获取所有线索摘要"""
        return [
            {
                "thread_id": tid,
                "title": t.title,
                "status": t.status,
                "event_count": len(t.key_events),
                "clue_count": len(t.clues),
                "promise_count": len(t.promises),
                "created_at": t.created_at
            }
            for tid, t in self.threads.items()
        ]


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="剧情连贯性检查器")
    parser.add_argument("--create-thread", nargs=3, 
                       help="创建剧情线索: ID 标题 时间线位置")
    parser.add_argument("--add-event", nargs=2,
                       help="添加事件: 线索ID 章节")
    parser.add_argument("--add-clue", nargs=2,
                       help="添加伏笔: 线索ID 伏笔内容")
    parser.add_argument("--check", type=int, help="检查连贯性，指定当前章节")
    parser.add_argument("--report", type=int, help="生成报告，指定当前章节")
    parser.add_argument("--format", choices=["text", "html", "json"], 
                       default="text", help="报告格式")
    parser.add_argument("--save", type=str, help="保存状态到文件")
    parser.add_argument("--load", type=str, help="从文件加载状态")
    parser.add_argument("--list", action="store_true", help="列出所有线索")
    
    args = parser.parse_args()
    
    checker = PlotContinuityChecker()
    
    # 加载状态
    if args.load:
        result = checker.load_state(args.load)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if args.create_thread:
        thread_id, title, timeline = args.create_thread
        result = checker.create_thread(thread_id, title, timeline)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.add_event:
        thread_id, chapter = args.add_event
        # 交互式输入事件
        print(f"为线索 {thread_id} 添加事件 (第{chapter}章)")
        summary = input("事件摘要: ")
        importance = input("重要性 [高/中/低]: ") or "中"
        
        result = checker.add_event(thread_id, {
            "chapter": int(chapter),
            "summary": summary,
            "importance": importance
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.add_clue:
        thread_id, clue = args.add_clue
        resolution = input("预期解决章节 (可选): ")
        result = checker.add_foreshadowing(
            thread_id, clue, 
            resolution if resolution else None
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.check:
        result = checker.check_continuity(args.check)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.report:
        report = checker.generate_report(args.report, args.format)
        print(report)
    
    elif args.list:
        summary = checker.get_thread_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    elif args.save:
        result = checker.save_state(args.save)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
