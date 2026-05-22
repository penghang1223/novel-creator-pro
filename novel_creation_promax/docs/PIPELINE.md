# Pipeline

> 本文是流水线速查。完整裁决规则见 `references/orchestrator.md`。

## 总流程

| 阶段 | 输入 | 动作 | 输出 | Gate |
|---|---|---|---|---|
| 立项门禁 | 用户确认的书名/平台/题材/核心设定 | `project_bootstrap_pipeline.py init` → 补齐资料 → `seal` | `素材/project_bootstrap_gate.json` | `can_write_chapter=true` |
| 创意 | 用户想法 | 题材/平台/卖点评估 | 创意文档 | 五维评分 |
| 设定 | 创意文档 | 人物、地点、势力、事件、关系、常识约束、能力、伏笔 | 设定目录+真相文件 | 设定底座+真相文件+12项完整性 |
| 大纲 | 设定 | 雪花级联、主支线 | 结构/总大纲 | 结构评估 |
| 细纲 | 大纲 | 分卷、章节节点 | 细纲文件 | 节奏/伏笔检查 |
| 正文 | 细纲+记忆包 | Pass 1/2 写作 | 章节正文 | pre/gate/audit |
| 记忆 | 章节摘要 | 回填状态变化 | 记忆 JSON | schema |
| 复盘 | 全书/阶段内容 | 总结问题和规则 | 复盘报告 | 用户确认 |

## 从零开始长篇

从零写长篇时，先跑立项门禁。`init` 只创建结构和占位文件，不允许正文；`seal` 负责最终复核。

```bash
python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "{平台}" --title "{书名}" --genre "{题材}" --premise "{核心设定}"
python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "novel_output/{平台}/{书名}"
```

`seal` 通过后会写入：

```json
{
  "workflow_gate": {
    "bootstrap_status": "pass",
    "bootstrap_report": "素材/project_bootstrap_gate.json",
    "last_checklist_step": 20,
    "can_write_chapter": true
  }
}
```

`write_pipeline.py pre/post/all` 会先读取这个状态；缺失或失败时直接退出。

`seal` 还会强制检查设定底座：`人物档案.md`、`地点档案.md`、`势力档案.md`、`事件档案.md`、`关系网络.md`、`常识约束.md`。这些文件用于锁定人物行为、居住收入、组织边界、事件因果和信息差，避免正文里出现高薪却无解释住老破小、技术强却无原因被裁、角色突然说不符合身份的话。

`seal` 同时检查 `设定/真相文件/` 下 7 个结构化事实源：`characters.json`、`locations.json`、`factions.json`、`events.json`、`relationships.json`、`resources.json`、`foreshadowing.json`。这些文件不是可选资料；它们会被 `write_pipeline.py pre` 编译成每章 `rule_stack`。

## 每章强制流程

1. 校验真相文件，并生成章节记忆包。
2. 编译 `摘要/chapter_NNN_rule_stack.json` 和 `素材/chapter_NNN_truth_brief.md`。
3. 回答 9 问并运行 `novel_creation_promax/scripts/pre_write_check.py`。
4. 按 rule_stack 组装场景写作卡和知识包。
5. 写 Pass 1 剧情稿。
6. 运行 `novel_creation_promax/scripts/writing_gate.py`。
7. 写 Pass 2 去AI稿。
8. `post` 自动提取 `素材/truth_delta_candidates_chNNN.json|md`，先审查候选事实，再补齐 `摘要/chapter_NNN_truth_delta.json`。
9. 运行 `novel_creation_promax/scripts/post_write_audit.py`。
10. 运行字数归一化、truth delta、风格校准和人物一致性检查。
11. 生成章节摘要和 chapter passport，回填 `novel-memory-pro`、真相文件和 `novel_state.json`。

推荐命令：

```bash
python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "{小说目录}" --chapter N --title "{标题}"
python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "{小说目录}" --chapter N --title "{标题}"
```

`post` 如果发现正文低于 2800，会生成 `素材/chapter_NNN_normalizer_task.md`，列出必须补写的观察、试探、交锋、代价、新线索位置。不能用水景物、复述、空泛心理凑字。

`post` 还会先运行 `story_truth_manager.py extract-delta`。如果正文出现人物状态、关系、地点、势力、资源、伏笔等疑似变化，会写入 `truth_delta.auto_extraction`，并把 `review_status` 设为 `needs_review`。必须审查 `素材/truth_delta_candidates_chNNN.md`，把属实项写入 `chapter_observations/proposed_updates`，再把 `auto_extraction.review_status` 改为 `reviewed` 并填写 `review_note`；否则 truth delta 校验不通过。

## 失败处理

| 失败项 | 处理 |
|---|---|
| 9问低于70 | 补全本章目标、冲突、伏笔、截断点后重跑 |
| Gate 不通过 | 修 Pass 1，不进入去AI |
| 字数不达标 | 扩写有效剧情，不水重复信息 |
| AI词/乒乓句超标 | 定点修，不破坏剧情结构 |
| 风格漂移 | 参照 style DNA 修局部语感 |
| OOC 风险 | 回看人物档案，修动机和声纹 |
| 记忆回填失败 | 不推进下一章，先修摘要或 schema |
