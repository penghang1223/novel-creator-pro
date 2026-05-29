---
name: novel-creation-promax
description: |
  中文网文创作专职助手。支持从零创作、续写连载、大纲设计、人物设定、伏笔管理、风格定制、平台适配、质量检查。
  当用户谈及小说、网文、故事、角色、剧情、章节、写作、续写、大纲、世界观、风格、番茄小说、起点中文网、晋江文学城时自动触发。
dependency:
  python:
    - Pillow>=9.0.0
---

# 小说创作 Pro Max

> **主流程入口**：完整执行链、审计日历、裁决优先级见 [`references/orchestrator.md`](references/orchestrator.md)。
> **写作宪法**：每章必读 [`references/writing_constitution.md`](references/writing_constitution.md)。
> **功能编号唯一真源**：见 [`MODE_REGISTRY.md`](MODE_REGISTRY.md)。
> **架构与产物规范**：见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)、[`docs/ARTIFACTS.md`](docs/ARTIFACTS.md)、[`docs/DATA_ACCESS_LEVELS.md`](docs/DATA_ACCESS_LEVELS.md)。

---

## 写作流程（状态机）

### 阶段 -1：长篇立项门禁

从零开始写长篇时，必须先跑项目门禁；未通过时不得进入第1章正文。

```bash
python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "{平台}" --title "{书名}" --genre "{题材}" --premise "{核心设定}"
python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "novel_output/{平台}/{书名}"
```

`seal` 会生成 `素材/project_bootstrap_gate.json`，并把 `novel_state.json.workflow_gate.can_write_chapter` 设为 `true`。如果该字段缺失或为 `false`，`write_pipeline.py` 会阻断正文写作。

长篇新书还必须补齐设定底座：`设定/人物档案.md`、`设定/地点档案.md`、`设定/势力档案.md`、`设定/事件档案.md`、`设定/关系网络.md`、`设定/常识约束.md`。这些文件用于锁住人物动机、职业收入、居住逻辑、组织边界、关键事件因果和信息差；缺失或仍含占位词时，`seal` 不放行正文。

长篇新书还必须补齐 `设定/真相文件/` 的 7 个 JSON：`characters.json`、`locations.json`、`factions.json`、`events.json`、`relationships.json`、`resources.json`、`foreshadowing.json`。这些文件是正文事实源；`seal` 不通过则禁止第1章，`write_pipeline.py pre` 会把它们编译成 `摘要/chapter_NNN_rule_stack.json` 和 `素材/chapter_NNN_truth_brief.md`。

### 阶段 0：写前准备

1. **加载写作宪法** → [`references/writing_constitution.md`](references/writing_constitution.md)
2. **9问必答** → `novel_creation_promax/scripts/pre_write_check.py`，总分 ≥ 70 分
3. **写前 5 项检查**：□ AI词黑名单已加载 □ 上一章已读取 □ 人物对话档案已加载 □ 标题关键词已提取 □ 前300字有冲突/悬念/动作
4. **物理状态追踪**：□ 列出位置/时间/关键物品 □ 写中逐句对照 □ 写后追加检查
5. **约束组装** → [`references/chapter_constraint_template.md`](references/chapter_constraint_template.md) 自动填充本章约束：
   - □ 人物矛盾行为 □ 行为指纹 □ 桥段去重 □ 对话风格 □ 潜台词策略 □ 高压力场景标记 □ 节奏类型 □ 常识校验 □ 因果链预检
   - □ 人物/地点/势力/事件/关系/常识底座已读取，角色行为和台词不得脱离设定底座
   - □ `chapter_NNN_rule_stack.json` 与 `chapter_NNN_truth_brief.md` 已读取，正文不得违背真相文件
   - □ Strand 类型已确定（Quest/Fire/Constellation）+ 是否触发断档预警（参照 `knowledge_base/40_Writing/02_节奏与结构/strand节奏追踪.md`）
   - □ 题材profile已加载（若存在则读取 `knowledge_base/10_WorldBuilding/题材知识库/{题材}.profile.yaml`，提取数值阈值注入约束模板 `== 题材约束 ==` 区块）
   - □ 追读力三要素已确定（H_+C_+M_，参照 `references/reading-power-taxonomy.md`）+ 当前未回收债务数已检查
   - □ 债务状态已检查（open合同数≤3，需本章处理的合同已列出，参照 `references/override-debt-system.md`）
   - □ 时间距离已检查（近2章SKIP/3-5章需改写/6-10章可简略，参照 `references/memory-relevance-filtering.md` 内容时间距离规则）
   - □ 隐喻环境主题已确定（环境描写必须服务叙事，注入约束模板 `== 隐喻环境约束 ==` 区块）
6. **知识包组装** → 按本章细纲从知识库提取知识点（详见下方流程）
7. **套路预判** → 参照速查卡 §九，列出本章可能涉及的套路+绕开策略

未完成以上任何一项 → 禁止开始写正文。

### 阶段 1：Pass 1 剧情稿

**目标**：写完整剧情逻辑，不管 AI 词。

- 写时完全忽略 AI 词，专注剧情推进、角色行为逻辑、章节边界、对话信息量
- 每 300-500 字自检：有没有无聊？有没有重复？有没有推进？
- 对话参照速查卡 §二对话六要素 + §三对话五大技法
- 爽点节奏参照速查卡 §五

**写中检查项**（每 300-500 字）：
- □ 人物矛盾行为已落实（每个核心角色至少一个）
- □ 行为指纹执行（核心角色用专属微动作，禁通用动作"笑了笑/皱了皱眉"）
- □ 潜台词技法落实（每场景 ≥1 种）
- □ 心声格式正确（叙事格式，不加引号）
- □ 关键对话之间有动作锚点（≥1 个/轮）
- □ 对话风格差异化（不同角色说话语气不同）
- □ 对话比例实时监控（≥25%）
- □ 比喻多样化（"像"比喻单章 ≤1）
- □ 结尾在悬念/打脸前/新冲突/情感高潮处
- □ 主 strand 已推进（本章不是纯 filler）

### → Gate 检查

```bash
python novel_creation_promax/scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
```

7 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 计时器心理 / 对话占比 / 非中文字符。
不通过 → 回到 Pass 1 修复。

### 阶段 2：Pass 2 AI 词清理

- 以 Pass 1 输出为基准，只改词汇，不动叙事结构
- 对话修改保证角色说话方式不变
- 参照速查卡 §七"每段三刀"法则 + §八 20 条硬性禁止

### → 完整审计

```bash
python novel_creation_promax/scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --prev-file "正文/第N-1章-xxx.md" --title "第N章 xxx"
```

不通过 → 定点修复，不重写全章。

### 阶段 3：风格校准 + 一致性 + 记忆同步

- 风格校准 → `novel_creation_promax/scripts/style_calibrator.py`（偏差 ≥0.3 警告，≥0.5 必须重写）
- 人物一致性 → `novel_creation_promax/scripts/character_consistency_checker.py`（无严重 OOC）
- 记忆同步 → `memory_manager.py sync-chapter`
- Strand 记录 → 在章节摘要 `strand` 字段记录 primary/secondary/tension/pace_type，同步到 `novel_state.json` 的 `strand_tracking.chapters[]`，检查是否触发断档预警
- 债务更新 → 检查本章是否偿还了之前的覆盖合同（status→repaid），更新债务利息（未偿合同 debt+1），记录本章新创建的合同到章节摘要 `overrides[]` + `debt_events[]`

全部通过 → 输出正文 + 记忆回填 + 约束存档。

### 违规后果

| 违规行为 | 后果 |
|----------|------|
| 跳过 9 问必答系统 | 本章作废，回答 9 问后重写 |
| 跳过写前检查/约束组装 | 本章作废，完成后重写 |
| Pass 1 不通过 Gate 就进入 Pass 2 | 本章作废，修复 Gate 问题后重跑 |
| 不跑完整审计就交付 | 本章视为未完成，必须补跑 |
| 审计不达标仍交付 | 本章作废，修复后重新审计 |
| 因果断裂（角色知道不该知道的信息） | 本章作废，修正信息流后重写 |

---

## 知识包组装流程

详见 [`references/knowledge-pack-workflow.md`](references/knowledge-pack-workflow.md)。

---

## 自动触发规则

详见 [`references/trigger-rules.md`](references/trigger-rules.md)。

---

## 功能菜单

> 本表摘要来自 [`MODE_REGISTRY.md`](MODE_REGISTRY.md)。新增、删除或重排功能时，先改注册表，再同步本摘要。

| 编号 | 功能 | 说明 |
|------|------|------|
| [0] | 新手模式 | 系统提问引导，10步完成从零创作 |
| [1] | 自由创作 | 自动提取关键信息生成大纲和正文 |
| [2] | 题材分析 | 热门题材分析：爽点/毒点/难度/热度 |
| [3] | 创意归类 | 归类想法到题材，推荐写作风格 |
| [4] | 生成大纲 | 分卷大纲 + 逐次10章细化大纲 |
| [5] | 正文写作 | 按大纲生成，必须走完硬门禁流程 |
| [6] | 风格定制 | 8种内置风格 + 自定义 + 组合 |
| [7] | 记忆管理 | 人物/剧情/设定/关系网管理 |
| [8] | 正文润色 | 定向优化：节奏/AI味/对话/描写 |
| [9] | 审稿评估 | 知识库驱动深度质量审查 → `review-skill/SKILL.md` |
| [10] | 短篇创作 | 七步法快速短篇模板 |
| [11] | 多平台输出 | 番茄/起点/晋江/七猫/飞卢格式转换 |
| [12] | 完结复盘 | 从已完结小说提取教训，自动更新知识库规则 |
| [13] | 续写他人作品 | 提取风格DNA并接续已有作品 |

### [5] 正文写作补充

必须走完「写作流程（状态机）」的完整阶段 0→1→Gate→2→3。跳过任何一步 = 本章作废。

推荐使用流水线脚本执行门禁：

```bash
python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "{小说目录}" --chapter N --title "{标题}"
python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "{小说目录}" --chapter N --title "{标题}"
```

长篇必须配合 `novel-memory-pro`：
- 写前生成记忆包 → `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir ...`
- 写后同步摘要 → `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_N_summary.json --memory-dir ...`

每章写后 `post` 会自动生成 `素材/truth_delta_candidates_chNNN.md`。必须先审查候选事实，把属实的人物状态、地点事实、势力行动、事件影响、关系变化、资源变化、伏笔变化写入 `摘要/chapter_NNN_truth_delta.json`，把误报写入 `auto_extraction.review_note`，并将 `auto_extraction.review_status` 改为 `reviewed`、`status` 改为 `approved` 或 `no_changes`。缺失、占位、候选未审查或未 approved 时禁止交付。

番茄字数不足时，`post` 会生成 `素材/chapter_NNN_normalizer_task.md`。补写必须补有效剧情：观察、试探、交锋、代价、新线索；不得靠景物、复述、空泛心理凑字。
- 每5-10章定期体检 → `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py review-pack --chapter N --memory-dir ...`

详见 `novel-memory-pro/references/integration-with-novel-creation.md`。

### [8] 正文润色方向

| 方向 | 参考 |
|------|------|
| 节奏调整 | `knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 降低AI味 | `knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 对话优化 | `knowledge_base/40_Writing/03_人物与对话/对话质感完整框架.md` |
| 结构优化 | `knowledge_base/40_Writing/02_节奏与结构/每章节奏公式与卡章技巧.md` |

记录修改历史到 `novel_state.json` 的 `revision_history`。

### [0] 长篇立项

```
创意确认 → 读取平台趋势+流派模板+五维评分
  → 五维自检
    ├─ ≥65分 → 用户确认 → 进入设定/大纲
    ├─ 55-64分 → 修改重评 → 通过后进入
    └─ <55分 → 重新构思
```

通过后运行 `project_bootstrap_pipeline.py init` → 补齐设定/大纲/8卷细纲/小说信息/80_Projects → 运行 `project_bootstrap_pipeline.py seal`。`seal` 未通过时禁止正文。

### [10] 短篇创作

七步流程：引子(1-3章) → 发展(4-10) → 转折(11-15) → 高潮(16-20) → 结局(21-25) → 复盘 → 润色

短篇只需：`正文/`、`摘要/`、`记忆/`、`素材/`、`outline.md`、`novel_state.json`

### [12] 完结复盘

```bash
# 预览模式
python novel_creation_promax/scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/"

# 自动升级模式
python novel_creation_promax/scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/" --upgrade
```

扫描审查报告 → 识别未覆盖问题 → 生成新规则建议 → 用户确认后写入知识库。

### 续写他人作品

1. 提取风格 DNA：`python novel_creation_promax/scripts/style_dna_extractor.py --input 已有文本.txt --output style_dna.json`
2. 分析人物关系/当前状态/未解决伏笔
3. 按风格 DNA 续写，完成后校准：`python novel_creation_promax/scripts/style_calibrator.py --input 章节.txt --style-dna style_dna.json --output report.json`

---

## 输出目录约定

详细规范见 [`docs/ARTIFACTS.md`](docs/ARTIFACTS.md)。

- 输出根目录：`novel_output/{平台名}/`（不指定平台默认放"番茄"）
- 每本小说一个子目录，长篇必须包含：创意/设定/结构/细纲/正文/摘要/记忆/素材/outline.md/novel_state.json
- 短篇只需：正文/摘要/记忆/素材/outline.md/novel_state.json
- 禁止只输出到聊天窗口而不落盘
- 小说信息.md 同时复制一份到素材/

---

## 参考文档

### 核心流程
- 架构总览：[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- 功能注册：[`MODE_REGISTRY.md`](MODE_REGISTRY.md)
- 流水线速查：[`docs/PIPELINE.md`](docs/PIPELINE.md)
- 产物规范：[`docs/ARTIFACTS.md`](docs/ARTIFACTS.md)
- 数据访问层级：[`docs/DATA_ACCESS_LEVELS.md`](docs/DATA_ACCESS_LEVELS.md)
- 执行编排器：[`references/orchestrator.md`](references/orchestrator.md)
- 写作宪法：[`references/writing_constitution.md`](references/writing_constitution.md)
- 约束模板：[`references/chapter_constraint_template.md`](references/chapter_constraint_template.md)
- 速查卡：[`references/写作速查卡.md`](references/写作速查卡.md)
- 场景写作卡：[`references/scene-writing-card.md`](references/scene-writing-card.md)
- 角色卡模板：[`references/character-card-template.md`](references/character-card-template.md)

### 质量与红线
- 四级红线：`knowledge_base/50_Quality/红线检查/红线系统.md`
- 闭环质量控制：`knowledge_base/50_Quality/闭环质量控制.md`
- 9问必答：`knowledge_base/50_Quality/红线检查/章节前检查.md`
- 记忆输出格式：`knowledge_base/50_Quality/红线检查/记忆输出格式.md`
- 覆盖合同+债务系统：[`references/override-debt-system.md`](references/override-debt-system.md)
- 三阶段知识过滤：[`references/three-stage-knowledge-filter.md`](references/three-stage-knowledge-filter.md)
- LLM关键词检索：[`references/llm-keyword-retrieval.md`](references/llm-keyword-retrieval.md)

### 题材与平台
- 题材模板：[`references/genre-templates/genre-specific-templates.md`](references/genre-templates/genre-specific-templates.md)
- 题材Profile Schema：[`assets/templates/genre-profile-schema.yaml`](assets/templates/genre-profile-schema.yaml)
- 题材Profile指南：[`references/genre-profile-guide.md`](references/genre-profile-guide.md)
- 追读力分类法：[`references/reading-power-taxonomy.md`](references/reading-power-taxonomy.md)（H1-H6 钩子 + C1-C8 爽点 + M1-M7 微兑现）
- 平台规则：`knowledge_base/60_Platform/平台规则.md`
- 平台热门趋势：`knowledge_base/60_Platform/平台热门趋势.md`
- 风格指南索引：`knowledge_base/40_Writing/风格指南/风格索引.md`（24位网文作家速查）

### 记忆系统
- 记忆结构：[`assets/memory_structure.json`](assets/memory_structure.json)
- 项目初始化模板：[`assets/templates/project-bootstrap.json`](assets/templates/project-bootstrap.json)
- 章节摘要模板：[`assets/templates/chapter-summary.json`](assets/templates/chapter-summary.json)
- 实体图谱 Schema：[`assets/templates/entity-graph.json`](assets/templates/entity-graph.json)
- 实体图谱指南：[`references/entity-graph-guide.md`](references/entity-graph-guide.md)
- 记忆相关度过滤：[`references/memory-relevance-filtering.md`](references/memory-relevance-filtering.md)
- 联动流程：[`novel-memory-pro/references/integration-with-novel-creation.md`](novel-memory-pro/references/integration-with-novel-creation.md)
- 人物档案模板：[`novel-memory-pro/references/character_profile_template.md`](novel-memory-pro/references/character_profile_template.md)
- 风格DNA格式：[`novel-memory-pro/references/style_dna_format.md`](novel-memory-pro/references/style_dna_format.md)
- 章节同步Schema：[`novel-memory-pro/references/chapter_sync_schema.md`](novel-memory-pro/references/chapter_sync_schema.md)
- 记忆优化手册：[`novel-memory-pro/references/memory-optimization-playbook.md`](novel-memory-pro/references/memory-optimization-playbook.md)
