---
name: novel-memory-pro
description: 为长篇小说和连载创作提供生产级记忆系统，并与“随心写小说 / novel-creation-*”技能配合使用。用于小说立项后的记忆初始化、风格DNA提取、人物档案维护、剧情逻辑追踪、章节前记忆包生成、章节后回填同步、OOC检查、风格漂移校准、定期回顾和紧急修复。
---

# 小说记忆 Pro

## 概览

把这个技能视为小说创作的“记忆中台”，不是单独的写作器。
它最适合与“随心写小说”类技能配合：

- 写作技能负责：立项、大纲、章纲、正文、改稿
- 本技能负责：记忆初始化、风格锁定、人物与剧情追踪、章节前唤醒、章节后回填、阶段性体检、长期防漂移与压缩建议

目标不是保存一堆资料，而是让长篇创作持续稳定：

- 风格不跑偏
- 人物不 OOC
- 剧情不打架
- 伏笔不丢
- 下一章开写前，能快速拿到最该记住的东西

## 何时使用

以下情况应触发本技能：

- 用户已经开始做长篇小说、连载或同人长线创作
- 用户想建立“记忆系统 / 内存系统 / 设定数据库 / 连贯性系统”
- 用户说“继续写但别吃设定”“把前文记住”“人物别跑偏”
- 用户要做章节前回顾、章节后回填、阶段性回顾或紧急修复
- 用户希望本技能与“随心写小说 / novel-creation-*”配套协作

## 核心定位

本技能围绕五层记忆工作：

- 风格 DNA：写法和语感的稳定基线
- 人物层：角色设定、说话方式、行为模式、成长方向
- 剧情层：主线、支线、因果和时间线
- 上下文层：章节状态、伏笔、未解问题、当前目标
- 历史层：章节摘要、创作决策、修订记录、漂移修复记录

这五层不是平铺保存，而是要服务两个动作：

1. 写之前，生成一份“当前最该记住的包”
2. 写之后，把新章节的有效信息回填进去

## 与“随心写小说”的配合方式

推荐协作顺序：

### 1. 立项后初始化

当“随心写小说”已经给出：

- 书名
- 一句话 premise
- 人物卡
- 大纲 / 分卷 / 章节阶梯

就立即用本技能建立项目记忆。

### 2. 每章开写前

先生成章节记忆包，供写作技能读取：

- 角色当前状态
- 主线与支线的当前进展
- 未回收伏笔
- 本章不能忘的限制
- 需要维持的风格特征

### 3. 每章写完后

把新章节摘要回填到五层记忆里，至少更新：

- 章节摘要
- 新事件
- 新伏笔 / 已回收伏笔
- 人物状态变化
- 新增剧情节点

### 4. 每 5-10 章

做一次阶段回顾，压缩记忆、清理过期信息、暴露潜在漂移。
优先使用：

- `python scripts/memory_manager.py review-pack --chapter 30 --output review_pack.json`

## 默认工作流

### 阶段 A：初始化

先创建记忆目录，再导入项目基础资料。

优先准备：

- 风格样本 3-5 章
- 主要人物档案
- 主线 / 支线大纲
- 初始章节或设定摘要

脚本入口：

- `python scripts/memory_manager.py init`
- `python scripts/style_dna_extractor.py --input <文件或目录> --output style_dna.json`
- `python scripts/memory_manager.py bootstrap-project --input project_bootstrap.json`

### 阶段 B：开写前唤醒

在新章开写前，不要把全部记忆都塞给写作技能，只生成精简包。

脚本入口：

- `python scripts/memory_manager.py chapter-pack --chapter 12 --output active_memory_pack.json`
- `python scripts/memory_manager.py review-pack --chapter 12 --output review_pack.json`

该记忆包应该优先包含：

- 当前活跃人物及状态
- 当前活跃剧情线
- 未解问题与伏笔
- 最近 1-3 章摘要
- 风格 guardrails

### 阶段 C：章节后回填

新章写完后，用结构化摘要回填，而不是直接丢整章文本。

脚本入口：

- `python scripts/memory_manager.py sync-chapter --input chapter_012_summary.json`

摘要至少应包括：

- chapter / title / summary
- characters_involved
- key_events
- character_states
- foreshadowing_planted
- foreshadowing_resolved
- unresolved_questions
- plot_updates
- creative_decisions

### 阶段 D：校准与修复

当怀疑作品跑偏时，优先做两种检查：

- 风格校准：`scripts/style_calibrator.py`
- 人物一致性：`scripts/character_consistency_checker.py`

如果发现问题，再决定是：

- 修正文稿
- 修正角色档案
- 修正剧情记忆
- 重新提取风格 DNA

## 参考文件何时读取

只按需要读取，避免把全部资料一次性压进上下文。

- [references/workflow_guide.md](references/workflow_guide.md)
  需要完整操作流程时读取

- [references/character_profile_template.md](references/character_profile_template.md)
  需要建立或修正人物档案时读取

- [references/style_dna_format.md](references/style_dna_format.md)
  需要理解风格 DNA JSON 结构时读取

- [references/integration-with-novel-creation.md](references/integration-with-novel-creation.md)
  需要和“随心写小说 / novel-creation-*”联动时读取

- [references/chapter_sync_schema.md](references/chapter_sync_schema.md)
  需要生成 `project_bootstrap.json` 或 `chapter_summary.json` 时读取

- [references/memory-optimization-playbook.md](references/memory-optimization-playbook.md)
  需要做记忆压缩、阶段回顾、active/warm/archive 分层、紧急修复时读取

## 脚本清单

- [scripts/memory_manager.py](scripts/memory_manager.py)
  核心入口。负责初始化、CRUD、bootstrap、章节记忆包、章节回填、阶段 review、归档候选识别、导出、统计。

- [scripts/style_dna_extractor.py](scripts/style_dna_extractor.py)
  从单文件或目录中的多章文本提取风格 DNA。

- [scripts/style_calibrator.py](scripts/style_calibrator.py)
  比较新文本与风格 DNA 的偏离。

- [scripts/character_consistency_checker.py](scripts/character_consistency_checker.py)
  检查人物 OOC 风险。

## 关键原则

- 记忆系统服务写作，不服务囤积。
- 优先保存“之后会影响创作决策”的信息。
- 每章前用精简包，不用全量档案。
- 每章后回填摘要，不回填整章原文。
- 阶段性 review 时，把记忆拆成 active / warm / archive，而不是默认全量常驻。
- 已解决的内容要压缩和降权，未解决的内容要前置。
- 人物成长不是 OOC，但成长必须能在记忆里被解释。

## 输出模式

根据用户任务选择输出：

- 初始化任务：给目录、脚本命令、需要准备的输入
- 联动任务：给写作技能能直接读取的记忆包
- 回填任务：给结构化章节摘要和更新结果
- 修复任务：给偏离诊断、原因和修正方案
- 阶段回顾：给长线漂移报告和收敛建议
