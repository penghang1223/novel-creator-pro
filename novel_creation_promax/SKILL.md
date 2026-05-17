name: my-novel-writing
description: |
  中文网文创作专职助手。支持从零创作、续写连载、大纲设计、人物设定、伏笔管理、风格定制、平台适配、质量检查。
  当用户谈及小说、网文、故事、角色、剧情、章节、写作、续写、大纲、世界观、风格、番茄小说、起点中文网、晋江文学城时自动触发。
dependency:
  python:
    - Pillow>=9.0.0

# 小说创作 Pro Max

> **主流程入口**：完整执行链、审计日历、裁决优先级见 [`references/orchestrator.md`](references/orchestrator.md)。
> **写作宪法**：每章必读 [`references/writing_constitution.md`](references/writing_constitution.md)。

---

## 写作流程（状态机）

### 阶段 0：写前准备

1. **加载写作宪法** → [`references/writing_constitution.md`](references/writing_constitution.md)
2. **9问必答** → `scripts/pre_write_check.py`，总分 ≥ 70 分
3. **写前 5 项检查**：□ AI词黑名单已加载 □ 上一章已读取 □ 人物对话档案已加载 □ 标题关键词已提取 □ 前300字有冲突/悬念/动作
4. **物理状态追踪**：□ 列出位置/时间/关键物品 □ 写中逐句对照 □ 写后追加检查
5. **约束组装** → [`references/chapter_constraint_template.md`](references/chapter_constraint_template.md) 自动填充本章约束：
   - □ 人物矛盾行为 □ 行为指纹 □ 桥段去重 □ 对话风格 □ 潜台词策略 □ 高压力场景标记 □ 节奏类型 □ 常识校验 □ 因果链预检
   - □ Strand 类型已确定（Quest/Fire/Constellation）+ 是否触发断档预警（参照 `knowledge_base/40_Writing/02_节奏与结构/strand节奏追踪.md`）
   - □ 题材profile已加载（从 `knowledge_base/10_WorldBuilding/题材知识库/{题材}.profile.yaml` 读取数值阈值，注入约束模板 `== 题材约束 ==` 区块）
   - □ 追读力三要素已确定（H_+C_+M_，参照 `references/reading-power-taxonomy.md`）+ 当前未回收债务数已检查
   - □ 债务状态已检查（open合同数≤3，需本章处理的合同已列出，参照 `references/override-debt-system.md`）
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
python scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
```

7 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 计时器心理 / 对话占比 / 非中文字符。
不通过 → 回到 Pass 1 修复。

### 阶段 2：Pass 2 AI 词清理

- 以 Pass 1 输出为基准，只改词汇，不动叙事结构
- 对话修改保证角色说话方式不变
- 参照速查卡 §七"每段三刀"法则 + §八 20 条硬性禁止

### → 完整审计

```bash
python scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --prev-file "正文/第N-1章-xxx.md" --title "第N章 xxx"
```

不通过 → 定点修复，不重写全章。

### 阶段 3：风格校准 + 一致性 + 记忆同步

- 风格校准 → `scripts/style_calibrator.py`（偏差 ≥0.3 警告，≥0.5 必须重写）
- 人物一致性 → `scripts/character_consistency_checker.py`（无严重 OOC）
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

**输入**：本章细纲（从 `细纲/卷X_标题.md` 定位本章段落）

**Step A：提取本章元信息**
出场人物 / 场景类型（对话/动作/情绪/悬疑/环境） / 核心冲突 / 情绪基调 / 章末截断点

**Step B：按场景类型读取知识**

| 场景类型 | 读取路径 |
|---------|---------|
| 对话场景 | `knowledge_base/40_Writing/03_人物与对话/` |
| 情绪/心理 | `knowledge_base/40_Writing/04_场景与描写/` |
| 悬疑/紧张 | `knowledge_base/40_Writing/02_节奏与结构/` |
| 去AI（每章必读） | `knowledge_base/40_Writing/05_降AI痕迹/` |
| 毒舌/特殊语体 | `knowledge_base/70_Corpus/毒舌知识库.md` |

不涉及 → 跳过。

**Step C：读取出场人物档案（9 字段）**

| 字段 | 用途 |
|------|------|
| 矛盾特质 | 防止角色扁平化 |
| 行为指纹 | 动作唯一化 |
| 对话声纹 | 遮住名字仍可辨认 |
| 动机优先级 | 每个行动必须服务目标 |
| 决策模型 | 驱动行为选择 |
| 反差开关 | 控制反差揭露节奏 |
| 情绪触发器 | 每场冲突至少触发一个 |
| 渴望/恐惧 | 核心驱动力 |
| 行为红线 | 硬约束，违规即 OOC |

某字段不存在 → 跳过。

**Step C+：读取实体关系（from entity_graph.json）**

从 `memory/entity_graph.json` 读取本章活跃实体的关系边：
- 筛选 status=active 的实体（最近 5 章内出现）
- 附带它们的关系边（source/target 都是 active）
- 特别关注：本章出场角色之间的关系类型、极性、强度变化
- 如果 entity_graph.json 不存在 → 跳过（不影响知识包生成）

**Step D：组装知识包（≤600字）**

```markdown
# 第N章 知识包
## 出场人物
- 角色A：矛盾=xxx | 声纹=xxx | 优先级=xxx | 反差=xxx | 触发器=xxx | 红线=xxx
## 本章场景类型：[类型]
适用技法：[技法要点]
## 本章高危项
- 绝对禁止词已加载（13个）
- 本章重点去AI：[具体项]
## 平台要求
- 字数：[范围] / 截断点：[事件]
```

**Step E：注入写作 prompt**
Pass 1 开始时直接包含在写作指令中。约束：知识包是建议不是命令，每次写前重新生成，找不到文件 → 跳过。

---

## 自动触发规则

以下规则在执行任何功能时自动生效。

### 题材知识库触发

| 用户提到 | 自动读取 | Profile |
|----------|----------|---------|
| 都市 | `knowledge_base/10_WorldBuilding/题材知识库/都市.md` | `.profile.yaml` |
| 科幻 | `knowledge_base/10_WorldBuilding/题材知识库/科幻.md` | — |
| 仙侠/修仙 | `knowledge_base/10_WorldBuilding/题材知识库/仙侠.md` | `.profile.yaml` |
| 玄幻/奇幻 | `knowledge_base/10_WorldBuilding/题材知识库/玄幻.md` | `.profile.yaml` |
| 悬疑/推理/惊悚 | `knowledge_base/10_WorldBuilding/题材知识库/悬疑.md` | `.profile.yaml` |
| 言情/恋爱/女频 | `knowledge_base/10_WorldBuilding/题材知识库/言情.md` | `.profile.yaml` |
| 灵异/恐怖 | `knowledge_base/10_WorldBuilding/题材知识库/灵异.md` | — |
| 无限流/游戏 | `knowledge_base/10_WorldBuilding/题材知识库/无限流.md` | — |
| 历史/架空 | `knowledge_base/10_WorldBuilding/题材知识库/历史.md` | — |
| 大女主 | `knowledge_base/10_WorldBuilding/题材知识库/大女主.md` | — |

### 写作技巧库触发

| 写作环节 | 自动读取 |
|----------|----------|
| 正文写作/描写/对话 | `knowledge_base/40_Writing/写作技巧/正文写作.md` |
| 写大纲/章节规划 | `knowledge_base/40_Writing/写作技巧/大纲写作.md` |
| 人物设定/世界观构建 | `knowledge_base/40_Writing/写作技巧/人物设定写作.md` |
| 结构设计/节奏把控 | `knowledge_base/40_Writing/写作技巧/结构设计写作.md` |
| 亲密场景/感情线 | `knowledge_base/40_Writing/04_场景与描写/亲密场景写作指南.md` |
| 对话场景/潜台词/张力 | `knowledge_base/40_Writing/04_场景与描写/潜台词与张力技法.md` |
| 修仙/修炼体系 | `knowledge_base/10_WorldBuilding/题材知识库/修仙体系构建指南.md` |
| 推理/探案流程 | `knowledge_base/10_WorldBuilding/题材知识库/推理破案流程指南.md` |
| 灵异/恐怖氛围 | `knowledge_base/10_WorldBuilding/题材知识库/恐怖氛围营造指南.md` |
| 职场/创业/商战 | `knowledge_base/10_WorldBuilding/题材知识库/职场商战指南.md` |
| 末世/废土 | `knowledge_base/10_WorldBuilding/题材知识库/末世生存指南.md` |
| 校园/青春 | `knowledge_base/10_WorldBuilding/题材知识库/校园青春指南.md` |
| 权谋/宫斗 | `knowledge_base/10_WorldBuilding/题材知识库/权谋宫斗指南.md` |

### 速查卡触发

每章正文写作前，自动读取 `references/写作速查卡.md`，提取本章相关规则到约束组装中。

| 阶段 | 速查卡章节 | 用途 |
|------|-----------|------|
| 写前 | §一 | 字数分配、断章位置、张力模板 |
| Pass 1 | §二-§六 | 对话六要素、爽点流水线、潜台词技法 |
| Pass 2 | §七-§八 | "每段三刀"法则、20 条硬性禁止 |
| 写后 | §九 | 套路绕开策略 |

### 立项触发

[9.0] 长篇立项启动时，自动执行：
- 平台热门趋势：`knowledge_base/60_Platform/平台热门趋势.md`
- 流派模板：`knowledge_base/10_WorldBuilding/流派模板总览.md`
- 五维评分：`knowledge_base/50_Quality/创意五维评分.md`（≥65分通过，55-64修改重评，<55重新构思）

### 毒舌/搞笑语料触发

选择"搞笑沙雕风"或要求毒舌/幽默风格时自动读取：

| 语料 | 用途 |
|------|------|
| `knowledge_base/70_Corpus/毒舌语料/毒舌知识库.md` | 毒舌风格参考（~600条） |
| `knowledge_base/70_Corpus/神回复语料/315条神回复.md` | 网络神回复（315条） |
| `knowledge_base/70_Corpus/神回复语料/110个神回复示例.md` | 神回复示例（110条） |
| `knowledge_base/70_Corpus/神回复语料/话废菩萨语料.md` | 话废人设对话参考 |
| `knowledge_base/70_Corpus/毒舌语料/毒舌AI示例库.md` | AI角色毒舌风格参考 |

### 审稿系统触发

| 触发场景 | 动作 |
|----------|------|
| 写完一章后 | 主动询问"需要审稿吗？" |
| "审一下"/"帮我看看"/"质量怎么样" | 进入审稿流程 → `review-skill/SKILL.md` |
| 审计发现问题较多 | 建议进入深度审查 |

### 连贯性系统触发

| 场景 | 读取 |
|------|------|
| 偏离大纲 | `knowledge_base/30_Plot/偏离处理.md` |
| 维护主线 | `knowledge_base/30_Plot/主线节点维护.md` |
| 细纲执行 | `knowledge_base/30_Plot/细纲执行机制.md` |
| 定期复盘 | `knowledge_base/30_Plot/定期复盘机制.md` |

---

## 功能菜单

| 编号 | 功能 | 说明 |
|------|------|------|
| [0] | 新手模式 | 系统提问引导，10步完成从零创作 |
| [1] | 自由创作 | 自动提取关键信息生成大纲和正文 |
| [2] | 题材分析 | 热门题材分析：爽点/毒点/难度/热度 |
| [3] | 创意归类 | 归类想法到题材，推荐写作风格 |
| [4] | 生成大纲 | 分卷大纲 + 逐次10章细化大纲 |
| [5] | 正文写作 | 按大纲生成，必须走完硬门禁流程 |
| [6] | 风格定制 | 8种内置风格 + 自定义 + 组合 |
| [7] | 帮助中心 | 续写/长篇/发表/常见问题 |
| [8] | 记忆管理 | 人物/剧情/设定/关系网管理 |
| [9] | 正文润色 | 定向优化：节奏/AI味/对话/描写 |
| [10] | 审稿评估 | 知识库驱动深度质量审查 → `review-skill/SKILL.md` |
| [11] | 短篇创作 | 七步法快速短篇模板 |
| [12] | 多平台输出 | 番茄/起点/晋江/七猫/飞卢格式转换 |
| [13] | 完结复盘 | 从已完结小说提取教训，自动更新知识库规则 |

### [5] 正文写作补充

必须走完「写作流程（状态机）」的完整阶段 0→1→Gate→2→3。跳过任何一步 = 本章作废。

长篇必须配合 `novel-memory-pro`：
- 写前生成记忆包 → `memory_manager.py chapter-pack --chapter N --memory-dir ...`
- 写后同步摘要 → `memory_manager.py sync-chapter --input chapter_N_summary.json --memory-dir ...`
- 每5-10章定期体检 → `memory_manager.py review-pack --chapter N --memory-dir ...`

详见 `novel-memory-pro/references/integration-with-novel-creation.md`。

### [9] 正文润色方向

| 方向 | 参考 |
|------|------|
| 节奏调整 | `knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 降低AI味 | `knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 对话优化 | `knowledge_base/20_Characters/角色命名指南.md` |
| 结构优化 | `knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md` |

记录修改历史到 `novel_state.json` 的 `revision_history`。

### [9.0] 长篇立项

```
创意确认 → 读取平台趋势+流派模板+五维评分
  → 五维自检
    ├─ ≥65分 → 用户确认 → 进入设定/大纲
    ├─ 55-64分 → 修改重评 → 通过后进入
    └─ <55分 → 重新构思
```

通过后初始化记忆系统 → 设定 → 大纲。

### [11] 短篇创作

七步流程：引子(1-3章) → 发展(4-10) → 转折(11-15) → 高潮(16-20) → 结局(21-25) → 复盘 → 润色

短篇只需：`正文/`、`摘要/`、`记忆/`、`素材/`、`outline.md`、`novel_state.json`

### [13] 完结复盘

```bash
# 预览模式
python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/"

# 自动升级模式
python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/" --upgrade
```

扫描审查报告 → 识别未覆盖问题 → 生成新规则建议 → 用户确认后写入知识库。

### 续写他人作品

1. 提取风格 DNA：`python scripts/style_dna_extractor.py --input 已有文本.txt --output style_dna.json`
2. 分析人物关系/当前状态/未解决伏笔
3. 按风格 DNA 续写，完成后校准：`python scripts/style_calibrator.py --input 章节.txt --style-dna style_dna.json --output report.json`

---

## 输出目录约定

- 输出根目录：`novel_output/{平台名}/`（不指定平台默认放"番茄"）
- 每本小说一个子目录，长篇必须包含：创意/设定/结构/细纲/正文/摘要/记忆/素材/outline.md/novel_state.json
- 短篇只需：正文/摘要/记忆/素材/outline.md/novel_state.json
- 禁止只输出到聊天窗口而不落盘
- 小说信息.md 同时复制一份到素材/

---

## 参考文档

### 核心流程
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
