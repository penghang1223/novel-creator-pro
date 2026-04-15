# 长篇小说创作助手 - 用户指南

## 目录
- [快速开始](#快速开始)
- [系统架构](#系统架构)
- [记忆系统](#记忆系统)
- [风格校准](#风格校准)
- [人物一致性检查](#人物一致性检查)
- [剧情连贯性检查](#剧情连贯性检查)
- [综合使用](#综合使用)
- [数据管理](#数据管理)
- [故障排除](#故障排除)

## 快速开始

### 环境要求
- Python 3.8+
- 依赖包：jsonschema, jieba, numpy

### 安装依赖
```bash
pip install jsonschema==4.21.1 jieba==0.42.1 numpy==1.26.3
```

### 首次使用
```bash
# 1. 进入技能目录
cd novel_creation_max

# 2. 初始化系统
python scripts/main.py init

# 3. 创建第一个剧情线索
python scripts/main.py plot --create main "主线剧情"

# 4. 注册第一个角色
python scripts/main.py character --register '{"character_id":"protagonist","name":"主角","personality_traits":["勇敢","正直"]}'
```

## 系统架构

### 五大核心模块

```
长篇小说创作助手
├── 记忆管理系统
│   ├── 风格DNA层
│   ├── 人物一致性层
│   ├── 剧情逻辑层
│   ├── 上下文关联层
│   └── 创作历史层
│
├── 风格校准器
│   ├── 文本特征分析
│   ├── 漂移检测
│   └── 校准建议
│
├── 人物一致性检查器
│   ├── 人物档案管理
│   ├── 行为一致性检查
│   └── OOC风险评估
│
├── 剧情连贯性检查器
│   ├── 线索管理
│   ├── 伏笔追踪
│   └── 连贯性评分
│
└── 统一主入口
    ├── 命令行界面
    ├── 综合分析
    └── 数据持久化
```

## 记忆系统

### 初始化
```bash
python scripts/main.py memory --status
```

### 创建章节记忆
```python
from memory_manager import MemoryManager

manager = MemoryManager()
manager.initialize_memory()

# 创建章节记忆
result = manager.create_chapter_memory(
    chapter_id="ch1",
    content="章节完整内容...",
    metadata={"title": "第一章", "word_count": 5000}
)
```

### 五层记忆结构

1. **风格DNA层**：记录整体风格特征
2. **人物一致性层**：维护人物设定
3. **剧情逻辑层**：追踪剧情发展
4. **上下文关联层**：保存重要上下文
5. **创作历史层**：记录创作历程

## 风格校准

### 分析文本风格
```bash
python scripts/style_calibrator.py --analyze "待分析的文本..."
```

### 设置风格基准
```bash
python scripts/style_calibrator.py --set-baseline "代表你写作风格的参考文本..."
```

### 检测风格漂移
```bash
python scripts/style_calibrator.py --detect-drift "需要检查的章节文本..."
```

### 输出示例
```
总体漂移评分: 15.0%
漂移等级: 轻微

校准建议:
1. 建议调整句子长度分布，保持与基准文本相似的句子长度
```

## 人物一致性检查

### 注册人物
```bash
python scripts/character_consistency_checker.py --register '{
    "character_id": "hero",
    "name": "英雄主角",
    "personality_traits": ["勇敢", "正直", "保护弱者"],
    "speech_patterns": ["坚定", "直接"],
    "behavioral_patterns": ["冲在最前面", "保护队友"]
}'
```

### 检查一致性
```bash
python scripts/character_consistency_checker.py --check "包含人物的文本..." --character-id hero
```

### 输出示例
```
一致性评分: 85.0%
OOC风险: 否

建议:
✓ 人物行为一致性良好
```

### 批量检查
```bash
python scripts/character_consistency_checker.py --batch-check "文本内容..."
```

## 剧情连贯性检查

### 创建剧情线索
```bash
python scripts/plot_continuity_checker.py --create-thread main "英雄成长主线"
```

### 添加伏笔
```bash
python scripts/plot_continuity_checker.py --add-clue main "神秘剑的来历"
```

### 检查连贯性
```bash
# 检查到第10章为止的连贯性
python scripts/plot_continuity_checker.py --check 10
```

### 生成报告
```bash
# 生成文本报告
python scripts/plot_continuity_checker.py --report 10 --format text

# 生成HTML报告
python scripts/plot_continuity_checker.py --report 10 --format html > report.html
```

### 输出示例
```
==================================================
📖 剧情连贯性检查报告
章节: 10
检查时间: 2024-01-15T10:30:00
==================================================

📊 总体评分: 92.0% (优秀)

⏰ 时间线一致性: 95.0%
  ✓ 无问题

🧠 逻辑一致性: 90.0%
  发现 1 个问题:
  - [中等] 事件之间缺乏逻辑连接

🔮 伏笔解决: 88.0%
  已解决: 7/8
  未解决: 1
    - 神秘剑的来历 (预期第5章, 已逾期5章)

📝 承诺兑现: 100.0%
  ✓ 所有承诺已兑现

--------------------------------------------------
💡 改进建议:
  1. 建议在下一章揭示"神秘剑的来历"
  2. 检查第8-9章之间的逻辑连接
--------------------------------------------------
==================================================
```

## 综合使用

### 使用统一主入口
```bash
# 综合检查
python scripts/main.py check \
    --chapter ch10 \
    --content "$(cat ch10.txt)" \
    --chapter-num 10 \
    --chars hero villain mentor
```

### 完整工作流示例
```bash
#!/bin/bash
# novel_workflow.sh

echo "=== 开始创作第 $1 章 ==="

# 加载上次进度
python scripts/main.py load --dir ./backup

# 写入章节内容（这里用变量代替实际写作）
CHAPTER_CONTENT="第${1}章的写作内容..."

# 综合检查
python scripts/main.py check \
    --chapter ch${1} \
    --content "$CHAPTER_CONTENT" \
    --chapter-num $1 \
    --chars hero villain

# 保存进度
python scripts/main.py save --dir ./backup

echo "=== 第 $1 章检查完成 ==="
```

## 数据管理

### 文件结构
```
novel_creation_max/
├── memory_data.json          # 记忆系统数据
├── character_profiles.json    # 人物档案
├── plot_data.json           # 剧情数据
└── reports/                 # 分析报告
```

### 导出数据
```bash
# 从脚本导出
python scripts/memory_manager.py --output memory_backup.json
python scripts/character_consistency_checker.py --export profiles.json
python scripts/plot_continuity_checker.py --save plot_backup.json
```

### 导入数据
```bash
python scripts/character_consistency_checker.py --import profiles.json
python scripts/plot_continuity_checker.py --load plot_backup.json
```

### 自动保存配置
在 `config.json` 中设置：
```json
{
  "memory_system": {
    "enable_auto_save": true,
    "auto_save_interval": 5
  }
}
```

## 故障排除

### 常见问题

**Q: 导入模块失败**
```
ModuleNotFoundError: No module named 'jieba'
```
解决：`pip install jieba==0.42.1`

**Q: 人物检查找不到人物ID**
```
人物ID hero 未注册
```
解决：先使用 `--register` 注册人物

**Q: 风格检测提示"请先设置风格基准"**
```
请先使用 --set-baseline 设置风格基准
```
解决：先用一段代表性的文本设置基准

**Q: 剧情连贯性分数过低**
- 检查时间线是否有回溯
- 确认伏笔是否及时揭示
- 验证事件之间的因果关系

### 性能优化

1. **启用缓存**：在 `config.json` 中设置 `enable_cache: true`
2. **减少检查频率**：不必每章都全面检查
3. **使用增量处理**：大量文本分批处理

### 获取帮助
```bash
# 查看所有命令
python scripts/main.py --help

# 查看子命令帮助
python scripts/main.py memory --help
python scripts/main.py plot --help
```
