#!/usr/bin/env python3
"""
小说记忆文件管理器
用于创建、更新和管理小说创作的记忆文件
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# 记忆文件目录
MEMORY_DIR = Path("memory/novels")


class MemoryManager:
    """小说记忆文件管理器"""
    
    def __init__(self, memory_dir: str = None):
        self.memory_dir = Path(memory_dir) if memory_dir else MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, novel_name: str) -> Path:
        """获取记忆文件路径"""
        return self.memory_dir / f"{novel_name}.md"
    
    def create_novel(
        self,
        name: str,
        novel_type: str = "通用",
        theme: str = "",
        style: str = "",
        platform: str = "",
        target_length: str = "",
    ) -> bool:
        """创建新的小说记忆文件"""
        file_path = self._get_file_path(name)
        
        if file_path.exists():
            print(f"⚠️ 记忆文件已存在: {file_path}")
            return False
        
        template = f"""# 《{name}》记忆文件

> 版本：v1.0.0 | 创建日期：{datetime.now().strftime('%Y-%m-%d')} | 当前章节：第1章

## 基本信息

| 字段 | 内容 |
|------|------|
| 类型 | {novel_type} |
| 风格 | {style} |
| 主题 | {theme} |
| 目标平台 | {platform} |
| 预计篇幅 | {target_length} |
| 当前字数 | 0 |
| 创建日期 | {datetime.now().strftime('%Y-%m-%d')} |

## 世界观

### 背景设定
（待填写）

### 力量体系/特殊规则
（如有）

### 文化特征

## 主要人物

### 主角
（待填写）

## 章节大纲

| 章节 | 标题 | 字数 | 关键内容 | 伏笔 |
|------|------|------|----------|------|
| - | - | - | - | - |

## 伏笔追踪

| 优先级 | 状态 | 伏笔内容 | 埋设章节 | 回收章节 |
|--------|------|----------|----------|----------|
| - | - | - | - | - |

## 时间线

### 主线时间线
1. （待填写）

## 剧情概要

### 当前进度
（第1章）

### 未解决冲突
（待填写）

### 下一步计划
（待填写）

---

> 最后更新：{datetime.now().strftime('%Y-%m-%d')} | 更新内容：创建记忆文件
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"✅ 记忆文件创建成功: {file_path}")
        return True
    
    def update_chapter(
        self,
        novel_name: str,
        chapter: int,
        title: str = "",
        summary: str = "",
        word_count: int = 0,
        foreshadows: List[str] = None,
    ) -> bool:
        """更新章节信息"""
        file_path = self._get_file_path(novel_name)
        
        if not file_path.exists():
            print(f"❌ 记忆文件不存在: {file_path}")
            return False
        
        # 读取现有内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新当前章节
        content = re.sub(
            r'\| 当前章节：.*?\|',
            f'| 当前章节：第{chapter}章 |',
            content
        )
        
        # 更新字数
        current_word = self._extract_current_word(content)
        new_word = current_word + word_count
        content = re.sub(
            r'\| 当前字数 \|.*?\|',
            f'| 当前字数 | {new_word} |',
            content
        )
        
        # 添加章节记录到大纲表
        chapter_row = f"| 第{chapter}章 | {title} | {word_count} | {summary} | {', '.join(foreshadows) if foreshadows else '-'} |"
        
        # 在章节大纲表格末尾添加新行
        pattern = r'(\| 第\d+章 \|.*?\|.*?\|.*?\|)\n\n##'
        match = re.search(pattern, content)
        if match:
            existing_row = match.group(1)
            # 检查是否已存在该章节
            if f"| 第{chapter}章 |" not in existing_row:
                new_content = content.replace(
                    existing_row,
                    existing_row + "\n" + chapter_row
                )
                content = new_content
        
        # 更新最后修改时间
        content = re.sub(
            r'> 最后更新：.*?\|',
            f'> 最后更新：{datetime.now().strftime("%Y-%m-%d")} |',
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 章节 {chapter} 更新成功")
        return True
    
    def add_foreshadow(
        self,
        novel_name: str,
        content: str,
        buried_chapter: int,
        priority: str = "P2",
    ) -> bool:
        """添加伏笔记录"""
        file_path = self._get_file_path(novel_name)
        
        if not file_path.exists():
            print(f"❌ 记忆文件不存在: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 添加新伏笔行
        new_row = f"| {priority} | 待回收 | {content} | 第{buried_chapter}章 | - |"
        
        # 找到伏笔表格位置并添加
        pattern = r'(\| 优先级 \| 状态 \| 伏笔内容 \| 埋设章节 \| 回收章节 \|)\n(\| - \| - \| - \| - \| - \|)'
        
        if re.search(pattern, file_content):
            file_content = re.sub(
                pattern,
                f'\\1\n| {priority} | 待回收 | {content} | 第{buried_chapter}章 | - |',
                file_content
            )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"✅ 伏笔添加成功: {content[:30]}...")
        return True
    
    def resolve_foreshadow(
        self,
        novel_name: str,
        foreshadow_content: str,
        resolve_chapter: int,
    ) -> bool:
        """标记伏笔已回收"""
        file_path = self._get_file_path(novel_name)
        
        if not file_path.exists():
            print(f"❌ 记忆文件不存在: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新伏笔状态
        pattern = rf'(\| P\d+ \| )(待回收|进行中)( \| {re.escape(foreshadow_content)} \| \S+ \| )(- \|)'
        replacement = rf'\1已回收\3第{resolve_chapter}章 |'
        
        content = re.sub(pattern, replacement, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 伏笔已回收: {foreshadow_content[:30]}...")
        return True
    
    def get_status(self, novel_name: str) -> Dict:
        """获取小说状态摘要"""
        file_path = self._get_file_path(novel_name)
        
        if not file_path.exists():
            return {"error": "文件不存在"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取关键信息
        current_chapter = re.search(r'\| 当前章节：.*?第(\d+)章', content)
        current_word = self._extract_current_word(content)
        
        # 统计伏笔
        unresolved = len(re.findall(r'\| P\d+ \| (待回收|进行中) \|', content))
        resolved = len(re.findall(r'\| P\d+ \| 已回收 \|', content))
        
        return {
            "novel_name": novel_name,
            "current_chapter": int(current_chapter.group(1)) if current_chapter else 1,
            "current_word": current_word,
            "unresolved_foreshadows": unresolved,
            "resolved_foreshadows": resolved,
        }
    
    def _extract_current_word(self, content: str) -> int:
        """提取当前字数"""
        match = re.search(r'\| 当前字数 \| (\d+) \|', content)
        return int(match.group(1)) if match else 0
    
    def list_novels(self) -> List[str]:
        """列出所有小说"""
        return [f.stem for f in self.memory_dir.glob("*.md")]


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="小说记忆文件管理器")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建新小说")
    create_parser.add_argument("name", help="小说名称")
    create_parser.add_argument("--type", default="通用", help="小说类型")
    create_parser.add_argument("--theme", default="", help="主题")
    
    # update 命令
    update_parser = subparsers.add_parser("update", help="更新章节")
    update_parser.add_argument("name", help="小说名称")
    update_parser.add_argument("--chapter", type=int, required=True, help="章节号")
    update_parser.add_argument("--title", default="", help="章节标题")
    update_parser.add_argument("--summary", default="", help="章节概要")
    update_parser.add_argument("--words", type=int, default=0, help="字数")
    
    # foreshadow 命令
    foreshadow_parser = subparsers.add_parser("foreshadow", help="添加伏笔")
    foreshadow_parser.add_argument("name", help="小说名称")
    foreshadow_parser.add_argument("--content", required=True, help="伏笔内容")
    foreshadow_parser.add_argument("--chapter", type=int, required=True, help="埋设章节")
    foreshadow_parser.add_argument("--priority", default="P2", help="优先级")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="查看状态")
    status_parser.add_argument("name", help="小说名称")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有小说")
    
    args = parser.parse_args()
    manager = MemoryManager()
    
    if args.command == "create":
        manager.create_novel(args.name, args.type, args.theme)
    elif args.command == "update":
        manager.update_chapter(args.name, args.chapter, args.title, args.summary, args.words)
    elif args.command == "foreshadow":
        manager.add_foreshadow(args.name, args.content, args.chapter, args.priority)
    elif args.command == "status":
        status = manager.get_status(args.name)
        print(json.dumps(status, ensure_ascii=False, indent=2))
    elif args.command == "list":
        novels = manager.list_novels()
        print("📚 已有小说:")
        for n in novels:
            print(f"  - {n}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
