# 完整工作流指南

## 概览

本文档提供小说创作记忆系统的完整工作流程，包括初始化、章节前记忆唤醒、章节后回填、定期维护和紧急处理五个阶段。
新版流程重点是与“随心写小说 / novel-creation-*”配合，而不是孤立使用。

## 目录

1. [初始化流程](#初始化流程)
2. [项目导入](#项目导入)
3. [创作前检查](#创作前检查)
4. [创作后校准](#创作后校准)
5. [定期回顾](#定期回顾)
6. [紧急校准](#紧急校准)

---

## 初始化流程

### 第一步：创建记忆系统

在开始创作前，首先初始化五层记忆系统。

**操作步骤**：

```bash
# 初始化记忆系统
python scripts/memory_manager.py --init

# 指定自定义目录（可选）
python scripts/memory_manager.py --init --memory-dir ./my_novel_memory
```

**输出结果**：
```
记忆系统已初始化: ./memory_system
```

**验证**：
检查记忆系统目录下是否生成了以下文件：
- `style_dna.json`
- `characters.json`
- `plot_logic.json`
- `context_relations.json`
- `creation_history.json`

### 第二步：提取风格DNA

从作者的代表性作品中提取写作风格特征。

**准备工作**：
- 准备3-5章代表性章节（txt格式）
- 确保样本章节涵盖不同的场景类型（对话、描写、动作等）

**操作步骤**：

```bash
# 从单个文件提取
python scripts/style_dna_extractor.py \
  --input 代表作目录或文件 \
  --output style_dna.json \
  --author "作者名"
```

**或使用Python直接调用**：

```python
from scripts.style_dna_extractor import extract_from_text

# 从文本提取
with open('代表作.txt', 'r', encoding='utf-8') as f:
    text = f.read()

style_dna = extract_from_text(text)

# 保存结果
with open('style_dna.json', 'w', encoding='utf-8') as f:
    f.write(style_dna.to_json())
```

**导入到记忆系统**：

```bash
# 将风格DNA导入记忆系统
python scripts/memory_manager.py create \
  --type style_dna \
  --data '{"style_data": "从style_dna.json读取的内容"}'
```

### 第三步：建立人物档案

为主要人物创建详细的档案。

**操作步骤**：

1. 参考 [人物档案模板](character_profile_template.md) 创建人物档案JSON文件
2. 为每个主要人物创建独立档案
3. 将档案导入记忆系统

**示例命令**：

```bash
# 创建人物档案
python scripts/memory_manager.py create \
  --type character \
  --data '{"basic_info": {"name": "李明", "age": 28}, "personality": {...}}'
```

**建议**：
- 主要人物：填写完整档案
- 重要配角：填写核心特征
- 次要人物：仅填写基础信息

### 第四步：初始化剧情和上下文

**创建剧情主线**：

```bash
python scripts/memory_manager.py create \
  --type plot \
  --data '{
    "plot_name": "主线",
    "description": "故事的主线情节",
    "key_events": [],
    "status": "进行中"
  }'
```

**创建上下文关联**：

```bash
python scripts/memory_manager.py create \
  --type context \
  --data '{
    "chapter": 1,
    "key_elements": [],
    "foreshadowing": [],
    "unresolved": []
  }'
```

## 项目导入

如果已经由写作技能产出了标题、人物卡和大纲，优先把这些内容整理成 `project_bootstrap.json`，再一次性导入：

```bash
python scripts/memory_manager.py bootstrap-project \
  --input project_bootstrap.json \
  --memory-dir ./memory_system
```

这一步能让记忆系统直接进入可用状态，避免手工一条条录入。

---

## 创作前检查

每次创作新章节前，执行以下检查流程。

### 第一步：生成章节记忆包

在开写新章节前，优先生成一份精简的记忆包，而不是把全部记忆直接丢给写作技能：

```bash
python scripts/memory_manager.py chapter-pack \
  --chapter 12 \
  --output active_memory_pack.json \
  --memory-dir ./memory_system
```

这份包会聚合：

- 当前活跃人物
- 当前活跃剧情线
- 最近章节摘要
- 未解决问题
- 风格 guardrails

新版 `chapter-pack` 会优先只带“最近 1-3 章仍活跃的人物”，避免把全量角色常驻塞回写作上下文。

### 第二步：加载相关记忆

**查询人物信息**：

```bash
# 查询特定人物
python scripts/memory_manager.py query \
  --type character \
  --filter "basic_info.name=李明"
```

**查询剧情线索**：

```bash
# 查询主线剧情
python scripts/memory_manager.py query --type plot
```

**查询上下文关联**：

```bash
# 查询未解决的伏笔
python scripts/memory_manager.py query --type context
```

### 第三步：确认风格要点

**回顾风格DNA关键特征**：

智能体会协助分析：
1. 句式特征：短/中/长句比例
2. 用词习惯：高频词汇和词性分布
3. 描写风格：环境/心理/动作描写比例
4. 对话风格：对话占比和标记词偏好

**建议**：
- 打印风格DNA报告作为参考
- 标记需要特别注意的风格特征

### 第四步：回顾人物状态

**检查内容**：
1. 人物当前的情感状态
2. 人物最近的行为和决策
3. 人物之间的关系状态
4. 人物的未完成目标

**操作**：

```bash
# 查看人物的最新状态
python scripts/memory_manager.py query \
  --type history \
  --filter "character=李明"
```

---

## 创作后校准

每完成一章后，执行以下校准流程。

### 第一步：风格校准

**实时校准**（快速检查）：

```bash
python scripts/style_calibrator.py \
  --input 新章节.txt \
  --style-dna style_dna.json \
  --mode realtime
```

**输出示例**：
```
=== 风格校准报告 ===
偏离度: 12.5%
校准模式: realtime

各维度偏离度:
  sentence: 8.3%
  word_usage: 15.2%
  description: 10.1%
  dialogue: 16.4%

校准建议:
  1. 用词习惯偏离：建议检查用词选择和词性分布
     高频用词：的, 了, 是
  2. 对话风格偏离：建议调整对话占比和对话标记词使用
     参考：对话占比35.0%
```

**详细校准**（定期进行）：

```bash
python scripts/style_calibrator.py \
  --input 新章节.txt \
  --style-dna style_dna.json \
  --mode periodic \
  --output calibration_report.json
```

### 第二步：人物一致性检查

**检查新章节中的人物表现**：

```bash
python scripts/character_consistency_checker.py \
  --input 新章节.txt \
  --character-profile 李明_profile.json
```

**输出示例**：
```
=== 人物一致性检查报告 ===
人物: 李明
一致性分数: 85.0%

OOC警告 (3个):
  1. [moderate] 人物行为与果断决策风格不符：他在门口犹豫了很久...
  2. [minor] 未发现人物口头禅：有意思, 让我想想
  3. [minor] 情绪表达过于压抑，与外放性格不符...

修正建议:
  1. 【中等】发现1处中等程度OOC，建议调整
  2. 【轻微】发现2处轻微偏差，可选择优化
  3. 具体建议：
     - 该人物设定为果断型，应避免犹豫行为
     - 考虑在对话中加入口头禅，增强人物特色
```

### 第三步：更新记忆系统

推荐优先使用结构化章节摘要回填，而不是手工分别更新多个层级：

```bash
python scripts/memory_manager.py sync-chapter \
  --input chapter_summary.json \
  --memory-dir ./memory_system
```

这会自动：

- 创建 context 记录
- 创建 history 记录
- 更新或创建 plot 节点
- 更新相关人物的当前状态

**更新剧情进展**：

```bash
python scripts/memory_manager.py update \
  --id "plot_xxx" \
  --data '{
    "latest_chapter": 10,
    "key_events": ["新事件1", "新事件2"]
  }'
```

**记录创作历史**：

```bash
python scripts/memory_manager.py create \
  --type history \
  --data '{
    "chapter": 10,
    "title": "第十章 真相",
    "characters_involved": ["李明", "张三"],
    "key_events": ["发现线索", "遇到对手"],
    "created_at": "2024-01-15"
  }'
```

**更新上下文关联**：

```bash
python scripts/memory_manager.py update \
  --id "context_xxx" \
  --data '{
    "new_foreshadowing": ["新埋下的伏笔"],
    "resolved": ["已解决的伏笔"]
  }'
```

---

## 定期回顾

每创作5-10章后，执行定期回顾流程。

### 第一步：评估记忆质量

**检查记忆系统统计**：

```bash
python scripts/memory_manager.py stats
```

**生成阶段体检包**：

```bash
python scripts/memory_manager.py review-pack \
  --chapter 30 \
  --output review_pack.json \
  --memory-dir ./memory_system
```

**输出示例**：
```
=== 记忆系统统计 ===
总记忆数: 45

style_dna:
  数量: 1
  最近更新: 2024-01-10T10:30:00

character:
  数量: 8
  最近更新: 2024-01-15T14:20:00

plot:
  数量: 12
  最近更新: 2024-01-15T16:00:00
```

### 第二步：按 active / warm / archive 分层

优先依据 `review_pack.json` 判断：

- 什么必须进入下 1-3 章的 active 层
- 什么只保留在 warm 层备用
- 什么已经可以 archive，不再进入章节包

### 第三步：清理过期信息

**识别需要清理的内容**：
- 已解决的伏笔
- 过期的上下文信息
- 重复或冗余的记录

**操作示例**：

```bash
# 删除过期的上下文记录
python scripts/memory_manager.py delete --id "context_xxx"
```

### 第四步：优化记忆结构

**检查内容**：
1. 人物档案是否需要更新（人物成长）
2. 剧情逻辑是否需要修正（剧情调整）
3. 风格DNA是否需要重新提取（风格演变）

**建议**：
- 每20-30章重新提取一次风格DNA
- 每次重大剧情转折后更新人物档案

### 第五步：生成回顾报告

**导出完整记忆**：

```bash
python scripts/memory_manager.py export \
  --output memory_review_20240115.json
```

**智能体分析**：
智能体会协助分析：
1. 整体创作质量趋势
2. 风格稳定性分析
3. 人物一致性评估
4. 剧情逻辑检查
5. 改进建议

---

## 紧急校准

当发现明显问题时，执行紧急校准流程。

### 触发条件

- 风格偏离度超过50%
- 人物出现严重OOC
- 剧情出现逻辑矛盾
- 读者反馈一致性问题

### 第一步：快速诊断

**运行所有检查**：

```bash
# 风格检查
python scripts/style_calibrator.py \
  --input 问题章节.txt \
  --style-dna style_dna.json \
  --mode emergency

# 人物检查（对所有主要人物）
python scripts/character_consistency_checker.py \
  --input 问题章节.txt \
  --character-profile 人物1.json

python scripts/character_consistency_checker.py \
  --input 问题章节.txt \
  --character-profile 人物2.json
```

### 第二步：生成修复方案

**智能体会协助生成**：
1. 具体的问题点定位
2. 修正建议和示例
3. 修正后的预期效果

### 第三步：更新记忆系统

**修正错误的记忆记录**：

```bash
# 更新人物档案
python scripts/memory_manager.py update \
  --id "character_xxx" \
  --data '{"修正后的数据"}'

# 修正剧情记录
python scripts/memory_manager.py update \
  --id "plot_xxx" \
  --data '{"修正后的数据"}'
```

### 第四步：重新校准

**修正后重新检查**：

```bash
python scripts/style_calibrator.py \
  --input 修正后的章节.txt \
  --style-dna style_dna.json \
  --mode realtime
```

---

## 最佳实践

### 日常使用建议

1. **创作前**：快速浏览相关人物和剧情信息（5分钟）
2. **创作后**：运行风格校准和人物检查（10分钟）
3. **每周**：更新记忆系统和创作历史（30分钟）
4. **每月**：执行定期回顾和优化（1小时）

### 常见问题处理

**Q: 风格偏离度一直较高怎么办？**
- 检查风格DNA样本是否具有代表性
- 考虑重新提取风格DNA
- 可能是创作风格在自然演变，可以接受

**Q: 人物一致性分数很低怎么办？**
- 检查人物档案是否完整和准确
- 考虑人物是否有合理的成长和变化
- 修正档案或修正内容

**Q: 记忆系统变得混乱怎么办？**
- 执行定期回顾流程
- 清理过期和冗余信息
- 重新组织记忆结构

### 效率优化技巧

1. **自动化脚本**：编写批处理脚本自动运行检查
2. **模板复用**：建立常用人物档案模板
3. **快速查询**：为常用查询创建快捷命令
4. **定期备份**：定期导出记忆系统备份

---

## 附录：命令速查表

```bash
# 初始化
python scripts/memory_manager.py --init

# 风格DNA提取
python scripts/style_dna_extractor.py --input 文件.txt --output style_dna.json

# 风格校准
python scripts/style_calibrator.py --input 文件.txt --style-dna style_dna.json

# 人物检查
python scripts/character_consistency_checker.py --input 文件.txt --character-profile 人物.json

# 记忆查询
python scripts/memory_manager.py query --type character

# 记忆创建
python scripts/memory_manager.py create --type plot --data '{"..."}'

# 记忆更新
python scripts/memory_manager.py update --id xxx --data '{"..."}'

# 记忆导出
python scripts/memory_manager.py export --output backup.json

# 记忆统计
python scripts/memory_manager.py stats
```
