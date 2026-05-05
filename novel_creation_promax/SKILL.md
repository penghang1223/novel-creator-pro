name: my-novel-writing
description: |
  中文网文创作专职助手。支持从零创作、续写连载、大纲设计、人物设定、伏笔管理、风格定制、平台适配、质量检查。
  当用户谈及小说、网文、故事、角色、剧情、章节、写作、续写、大纲、世界观、风格、番茄小说、起点中文网、晋江文学城时自动触发。
dependency:
  python:
    - Pillow>=9.0.0

# 个人定制网文创作助手

> **默认状态**：我已加载小说创作 Max 3.0 的全部能力。直接告诉我你想写什么，不需要选择菜单序号。
>
> **主流程入口**：完整执行链、审计日历、裁决优先级见 `references/orchestrator.md`。本文档是菜单入口和自动触发规则，详细流程由 orchestrator 编排。

---

## ⛔ 写作流程（状态机）

**写作底线规则见 [`references/writing_constitution.md`](references/writing_constitution.md)（写作宪法），每章必读。**

### 阶段 0：写前准备

1. **加载写作宪法** → [`references/writing_constitution.md`](references/writing_constitution.md)
2. **9问必答** → `scripts/pre_write_check.py`，总分 ≥ 70 分
3. **写前5项检查**：AI词黑名单已加载 / 上一章已读取 / 人物对话档案已加载 / 标题关键词已提取 / 前300字有冲突
4. **约束组装** → 从 [`references/chapter_constraint_template.md`](references/chapter_constraint_template.md) 自动填充本章约束
5. **套路预判** → 参照速查卡 §九，列出本章可能涉及的套路+绕开策略

未完成以上任何一项 → 禁止开始写正文。

### 阶段 1：Pass 1 剧情稿

**目标**：写出完整剧情逻辑，不管 AI 词。

**规则**：
- 写的时候完全忽略 AI 词
- 专注于：剧情推进、角色行为逻辑、章节边界、对话信息量
- 每 300-500 字自检：有没有无聊？有没有重复？有没有推进？
- **对话写作参照**：速查卡 §二对话六要素 + §三对话五大技法
- **爽点节奏参照**：速查卡 §五爽点设计

**禁止在 Pass 1 做的事**：不检查 AI 词、不检查对话比例、不做风格校准。

### → Gate 检查（writing_gate.py）

```bash
python scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
```

6 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 计时器心理 / 对话占比。
不通过 → 回到 Pass 1 修复对应问题。

### 阶段 2：Pass 2 AI 词清理

**目标**：在保留剧情逻辑和对话风格的前提下，清理 AI 词。

**规则**：
- 以 Pass 1 输出为基准，只改词汇，不动叙事结构
- 对话修改保证：角色说话方式不变
- 如果替换导致语义不通，跳过该替换
- **去AI化参照**：速查卡 §七"每段三刀"法则 + §八 20 条硬性禁止

### → 完整审计（post_write_audit.py）

不通过 → 定点修复，不重写全章。

### 阶段 3：记忆同步

`memory_manager.py sync-chapter` → 更新记忆。

### 违规后果

| 违规行为 | 后果 |
|----------|------|
| 跳过 9 问必答系统 | 本章作废，回答 9 问后重写 |
| 跳过写前检查/约束组装 | 本章作废，完成后重写 |
| Pass 1 不通过 Gate 就进入 Pass 2 | 本章作废，修复 Gate 问题后重跑 |
| 写中放飞自我，写完发现 AI 味/废话/通用动作 | 本章作废，写的时候就该注意到 |
| 不跑完整审计就交付 | 本章视为未完成，必须补跑 |
| 审计不达标仍交付 | 本章作废，修复后重新审计 |
| 因果断裂（角色知道不该知道的信息） | 本章作废，修正信息流后重写 |
| 为了凑字数/对话占比而塞废话 | 本章作废，删废话后重新审计 |

---

## 自动触发规则

以下规则在执行任何功能时自动生效，不需要用户手动指定。

### 题材知识库自动触发

当用户指定题材类型时，自动读取对应的 genre 知识文档：

| 用户提到 | 自动读取 |
|----------|----------|
| 都市、都市文、都市场景 | `../knowledge_base/10_WorldBuilding/题材知识库/都市.md` |
| 科幻、科幻文、科幻元素 | `../knowledge_base/10_WorldBuilding/题材知识库/科幻.md` |
| 仙侠、仙侠文、修仙、修真 | `../knowledge_base/10_WorldBuilding/题材知识库/仙侠.md` |
| 玄幻、玄幻文、奇幻 | `../knowledge_base/10_WorldBuilding/题材知识库/玄幻.md` |
| 悬疑、悬疑文、推理、惊悚 | `../knowledge_base/10_WorldBuilding/题材知识库/悬疑.md` |
| 言情、言情文、恋爱、女频 | `../knowledge_base/10_WorldBuilding/题材知识库/言情.md` |

### 写作技巧库自动触发

当用户涉及对应写作环节时，自动读取：

| 写作环节 | 自动读取 |
|----------|----------|
| 正文写作/描写/对话 | `../knowledge_base/40_Writing/写作技巧/正文写作.md` |
| 写大纲/章节规划 | `../knowledge_base/40_Writing/写作技巧/大纲写作.md` |
| 人物设定/世界观构建 | `../knowledge_base/40_Writing/写作技巧/人物设定写作.md` |
| 结构设计/节奏把控 | `../knowledge_base/40_Writing/写作技巧/结构设计写作.md` |
| 亲密场景/感情线 | `../knowledge_base/40_Writing/04_场景与描写/亲密场景写作指南.md` |
| 对话场景写作/潜台词/张力 | `../knowledge_base/40_Writing/04_场景与描写/潜台词与张力技法.md` |

### 写作速查卡自动触发

**每章正文写作前，必须自动读取** `references/写作速查卡.md`，提取本章相关规则到约束组装中。速查卡是从 `knowledge_base/40_Writing/` 10个核心文件中浓缩的可执行规则，覆盖：

| 阶段 | 速查卡章节 | 用途 |
|------|-----------|------|
| 写前 | §一 章节结构与节奏 | 字数分配、断章位置、张力模板 |
| 写中Pass 1 | §二-§六 对话/人味/爽点/潜台词 | 对话六要素、爽点流水线、潜台词技法 |
| 写中Pass 2 | §七-§八 去AI化 | "每段三刀"法则、20条硬性禁止 |
| 写后审计 | §九 套路预判 | 套路绕开策略、原创性加分项 |

### 毒舌/搞笑语料库自动触发

当用户选择"搞笑沙雕风"或要求毒舌、幽默、神回复风格时，自动读取：

| 语料文件 | 用途 |
|----------|------|
| `../knowledge_base/70_Corpus/毒舌语料/毒舌知识库.md` | 毒舌风格创作参考（~600条） |
| `../knowledge_base/70_Corpus/神回复语料/315条神回复.md` | 网络神回复语料（315条） |
| `../knowledge_base/70_Corpus/神回复语料/110个神回复示例.md` | 神回复示例（110条） |
| `../knowledge_base/70_Corpus/神回复语料/话废菩萨语料.md` | 话废人设对话参考 |
| `../knowledge_base/70_Corpus/毒舌语料/毒舌AI示例库.md` | AI角色毒舌风格参考 |

### 评估系统自动触发

在对应阶段自动运行评估（用户说"评估"或"检查"时也会触发）：

| 阶段 | 评估文档 |
|------|----------|
| 创意文档确认后 | `knowledge_base/50_Quality/创意五维评分.md`（五维自检） |
| 创意生成后 | `../knowledge_base/50_Quality/评估系统/创意评估.md` |
| 设定完成后 | `../knowledge_base/50_Quality/评估系统/设定评估.md` |
| 大纲生成后 | `../knowledge_base/50_Quality/评估系统/大纲评估.md` |
| 结构规划后 | `../knowledge_base/50_Quality/评估系统/结构评估.md` |
| 正文完成后 | `../knowledge_base/50_Quality/评估系统/内容评估.md` |

### 审稿系统自动触发

| 触发场景 | 动作 |
|----------|------|
| 写完一章后 | 主动询问"需要审稿吗？" |
| 用户说"审一下"/"帮我看看"/"质量怎么样" | 进入审稿流程 → `review-skill/SKILL.md` |
| 写后审计发现问题较多 | 建议进入深度审查 |

### 连贯性系统自动触发

| 场景 | 触发文档 |
|------|----------|
| 正文创作偏离大纲 | `../knowledge_base/30_Plot/偏离处理.md` |
| 细纲执行中维护主线 | `../knowledge_base/30_Plot/主线节点维护.md` |
| 每章写完记录执行 | `../knowledge_base/30_Plot/细纲执行机制.md` |
| 每5-10章定期复盘 | `../knowledge_base/30_Plot/定期复盘机制.md` |

**服务菜单（按需使用）：**

```
小说创作助手

请选择需要的服务：

[0] 新手模式 - 从零创作小说，系统提问引导创作
[1] 自由创作 - 描述想法，AI自动生成小说
[2] 题材分析 - 分析热门题材及创作要点
[3] 创意归类 - 将想法归类到具体题材并指导创作
[4] 生成大纲 - 生成分卷大纲和章节细化大纲
[5] 正文写作 - 按大纲进行正文创作
[6] 风格定制 - 添加/管理创作风格提示词
[7] 帮助中心 - 续写技巧、长篇创作、发表指南
[8] 记忆管理 - 管理长篇小说的人物、剧情、设定（高级）
[9] 正文润色 - 修改已有章节（节奏/AI味/对话/描写）
[10] 审稿评估 - 全面质量检查（红线+评估+一致性）
[11] 短篇创作 - 七步法快速短篇模板

请输入序号(0-13)
```

---

## ⛔ 写作硬门禁流程（ASCII可视化）

**每章正文创作必须严格按以下顺序执行：**

```
用户要求写第N章
    │
    ▼
┌──────────────────────────────────────┐
│  第零步：设定完整性审查（仅新小说）    │  ← 12项检查，不通过不写
│  主角/女主/配角/反派/能力/世界观/     │
│  家族/起点原因/父母/势力/地理/伏笔    │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第零.五步：章节驱动引擎               │  ← 新增！本章爽点/冲突/情绪曲线
│  □ 本章主爽点是什么？                 │
│  □ 本章核心冲突是什么？               │
│  □ 读者情绪曲线怎么走？               │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第一步：回答9问必答系统              │  ← 不回答不允许写
│  总分≥70分，否则拒绝开始写作          │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第二步：执行写前5项检查               │  ← 未全部通过不允许写
│  □ AI词黑名单已加载                   │
│  □ 上一章已读取                       │
│  □ 人物对话档案已加载                 │
│  □ 标题关键词已提取                   │
│  □ 前300字有冲突/悬念/动作            │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第二步.5：物理状态追踪                │  ← 精简为3项：位置/时间/关键物品
│  □ 列出3项物理状态清单                │
│  □ 写中逐句对照                       │
│  □ 写后审计追加检查                   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第三步：写中约束组装                  │  ← 提取具体约束条件
│  □ 人物矛盾行为设计（每个核心角色）    │
│  □ 桥段去重检查（最近5章标签比对）     │
│  □ 套路预判+绕开策略（识别+反向选择）  │
│  □ 张力设计（高潮章选择2-3个技法）     │
│  □ 对话风格加载（语气/口头禅/禁用词）  │
│  □ 情感场景标记（高压场景=矛盾情感）   │
│  □ 节奏类型确定（推进/铺垫/高潮）      │
│  □ 常识校验点（职业/场景/时代常识）    │
│  □ 因果链预检（关键事件的因果链草案）  │
│  □ 行为指纹加载（每个角色的微动作库）  │
│  □ 潜台词策略（指桑骂槐/回避/反话）    │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第三步.5：动作流大纲（条件触发）      │  ← 仅在博弈/对抗/隐藏目的场景
│  □ 每个场景的表面话题+真实议题         │
│  □ 每个角色的目标+负面约束             │
│  □ 动作流（试探→回避→加压→反击）       │
│  □ 潜台词技法选择（≥1种/场景）         │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第四步：写正文（300-500字分段检查）   │  ← 写中只感知：无聊/重复/推进
│  · 人物矛盾行为落实                   │
│  · 行为指纹执行（不用通用动作）        │
│  · 动作流大纲引导对话（仅博弈场景）    │
│  · 潜台词≥1种技法/场景                │
│  · 禁止使用已过桥段                   │
│  · 对话比例≥25%                       │
│  · 黑名单禁用词出现即替换（剧情优先）  │
│  · "像"比喻≤1                        │
│  · 高压力场景含矛盾情感               │
│  · 标题关键词自然嵌入正文             │
│  · 每轮对话有动作锚点                 │
│  · 不写角色内心定义                   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第五步：结构检查（优先）              │  ← 爽点/反转/钩子，不达标直接重写
│  □ 主爽点有没有兑现？                 │
│  □ 核心冲突有没有展开？               │
│  □ 结尾有没有钩子？                   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第五步.1：快速扫描+四步润色           │  ← 删→加→变形→校准
│  □ AI味扫描 + 动作锚点 + 行为指纹     │
│  □ 删：废话/标签/连接词/独白          │
│  □ 加：潜台词动作（≥2个锚点/场景）     │
│  □ 变形：省略/打断/答非所问           │
│  □ 校准：遮住名字能猜出谁说的吗？      │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第五步.2：运行写后审计脚本            │  ← 不跑脚本 = 违规
│  python scripts/post_write_audit.py  │
│  · AI词频次统计通过                   │
│  · 对话比例≥25%                       │
│  · 标题关键词在正文中出现             │
│  · 与上一章重复度≤20%                │
│  · 物理状态无矛盾                     │
│  · 对话干涩检测（3段抽查≥3个"是"）     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第六步：风格校准                     │  ← 偏差≥0.3警告
│  python scripts/style_calibrator.py  │     ≥0.5必须重写
│  · 风格DNA偏差<0.3: 通过              │
│  · 0.3≤偏差<0.5: 警告                 │
│  · 偏差≥0.5: 不通过，重写              │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  第七步：人物一致性检测                │  ← 严重OOC必须修正
│  python scripts/character_consistency │
│  _checker.py                         │
│  · 无严重OOC警告                      │
└──────────────┬───────────────────────┘
               ▼
    全部通过 → 输出正文 + 记忆回填 + 约束存档
    未通过 → 修正后重新检测
```

## 质量约束系统

在调用 [5] 正文写作 或进行续写前，**必须先完成上方硬门禁流程**。所有质量约束详见上方「硬门禁」流程。六大保障机制对应关系：

| 机制 | 对应硬门禁 | 详见 |
|------|-----------|------|
| 红线系统 | 硬门禁 4 | `../knowledge_base/50_Quality/红线检查/红线系统.md` |
| 设定完整性审查 | 硬门禁 2.8（12项检查） | `references/orchestrator.md` §Stage 2 |
| 闭环质量控制 | 硬门禁 0 + 0.1 + 4 | `../knowledge_base/50_Quality/闭环质量控制.md` |
| 必答问题系统 | 硬门禁 1（9问，≥70分） | `../knowledge_base/50_Quality/红线检查/章节前检查.md` |
| 记忆系统输出 | [9.1] 记忆联动 | `../knowledge_base/50_Quality/红线检查/记忆输出格式.md` |
| 风格校准 | 硬门禁 4 第六步 | `scripts/style_calibrator.py` |
| 人物一致性 | 硬门禁 4 第七步 | `scripts/character_consistency_checker.py` |

### 约束优先级
1. 一级红线 > 必答问题 > 记忆唤醒 > 创作执行
2. 硬规则（AI词/字数/对话比）> 结构规则（OOC/剧情矛盾）> 质量建议（风格评分）
3. 质量修正 > 继续创作 > 交付结果

---

## 六层能力架构

1. **构思规划层**：世界观架构、人物体系、故事大纲、主题立意
2. **深度写作层**：双线叙事、草蛇灰线、灰色人设、硬核智斗、诗化语言
3. **记忆管理层**：长篇小说人物/剧情/设定追踪（`novel-memory-pro`）
4. **质量优化层**：红线检查、必答问题验证、风格校准、低AI痕迹润色
5. **平台适配层**：番茄/起点/晋江/七猫/飞卢平台规则与黄金三章
6. **扩展功能层**：封面生成、剧情连贯性检查、Seedance视频提示词

---

## 输出与目录约定

- **小说输出根目录**：项目根目录下的 `novel_output/{平台名}/`
- **按平台分类管理**：用户提到哪个平台就放哪个目录（番茄/起点/知乎/七猫等），不指定默认放"番茄"
- **每本小说独占一个子目录**（如 `novel_output/番茄/弹珠声停了/`）
- **子目录标准结构**：

```
小说名/
├── 创意/          # 创意文档（长篇必需，短篇可省略）
├── 设定/          # 世界观、人物体系（长篇必需，短篇可省略）
├── 结构/          # 主线结构、卷结构（长篇必需，短篇可省略）
├── 细纲/          # 分卷细纲（长篇必需，短篇可省略）
├── 正文/          # 章节正文（.txt 或 .md）
├── 摘要/          # 章节摘要 JSON（chapter_NNN_summary.json）
├── 记忆/          # novel-memory-pro 生成的记忆 JSON
├── 素材/          # 封面、插图、审查报告等媒体文件
├── outline.md     # 总大纲（短篇/自由创作时使用）
└── novel_state.json  # 小说状态（章节进度、伏笔追踪等）
```

- **短篇/自由创作**：只需 `正文/`、`摘要/`、`记忆/`、`素材/`、`outline.md`、`novel_state.json`，可省略创意/设定/结构/细纲
- **长篇连载**：必须包含创意/设定/结构/细纲，单靠 outline.md 无法管理长篇复杂度
- 短篇同样遵循此约定，禁止只输出到聊天窗口而不落盘

---

## 功能说明

### [0] 新手模式
- 系统依次提问，引导新手完成创作
- 问题包括：
  1. 小说类型（男频/女频）
  2. 题材选择（都市、玄幻、言情、悬疑等）
  3. 主角设定（姓名、性别、年龄、身份）
  4. 金手指/特殊能力（可选）
  5. 世界观设定
  6. 核心冲突
  7. 主要反派
  8. 故事结局走向
  9. 预计字数
  10. 写作风格偏好（从内置风格中选择）
- 根据回答生成大纲和正文
- **完成后提示**："建议保存对话框，方便后续续写。"

### [1] 自由创作
- 用户自由描述想法
- AI自动提取关键信息，生成大纲和正文
- 写作时读取 `../knowledge_base/40_Writing/风格指南/通用风格.md` 和 `assets/prompts/user_prompts.md`
- **完成后提示**："建议保存对话框，方便后续续写。"

### [2] 题材分析
- 分析男频/女频热门题材
- 输出爽点、毒点、创作难度、热度指数
- 提供创作建议

### [3] 创意归类
- 输入创意想法
- 分析题材类型，提供创作指导
- 推荐合适的写作风格

### [4] 生成大纲
- 生成分卷大纲（整体架构）
- 逐次生成章节细化大纲（每次10章）
- 支持大纲调整和优化
- **完成后提示**："建议保存对话框，方便后续续写。"

### [5] 正文写作

**️ 开始写作前，必须先完成上方「硬门禁」的完整流程：章节驱动（3问）→ 9 问必答（≥70 分）→ 写前 5 项检查 → 写中 300-500 字分段感知 → 写后结构检查→润色→审计。跳过任何一步 = 本章作废。**

- 按大纲生成正文
- 写作时读取风格提示词和用户自定义提示词
- 支持单章生成和批量生成
- **长篇写作前**：必须读取 `novel-memory-pro` 生成的章节记忆包（见 [9.1]）
- 自动检测人物一致性、剧情连贯性
- 严格遵守 `../knowledge_base/50_Quality/红线检查/红线系统.md` 的四级红线
- **完成后必须运行审计脚本**：`python scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --prev-file "正文/第N-1章-xxx.md" --title "第N章 xxx"`
- 审计未通过 → 自动修复 → 重新审计 → 通过才输出
- **完成后提示**："建议保存对话框，方便后续续写。"
- **长篇完成后**：必须输出结构化章节摘要并回填到记忆系统（见 [9.1]）

#### 闭环质量控制流程（强制）

每次章节创作必须遵循 写前 → 写中 → 写后 → 定期Review 四阶段闭环：

**阶段零：章节驱动（← 新增）**
- [ ] 本章主爽点已确定（打脸/反杀/暧昧/信息反转/装逼）
- [ ] 核心冲突已确定（人与人/人与环境/人与信息差）
- [ ] 读者情绪曲线已规划（期待→压制→反转→释放）

**阶段一：写前 Pre-Write Check**
- [ ] AI词黑名单已加载到上下文（`knowledge_base/50_Quality/闭环质量控制.md`）
- [ ] 上一章已读取（防止开头200字重复>20%）
- [ ] 人物对话档案已加载（核心角色填充词占比≤20%）
- [ ] 标题关键词已提取（正文中必须出现）
- [ ] 前300字必须有冲突/悬念/动作

**阶段一.5：约束组装 Constraint Assembly**
- [ ] 核心人物矛盾行为已提取（从人物档案读取每个出场角色的矛盾特质+本章矛盾行为设计）
- [ ] 行为指纹已加载（每个出场角色的3-5个标志性微动作：紧张/放松/愤怒/开心时）
- [ ] 桥段去重检查完成（读取最近5章桥段标签，本章禁止使用相同标签）
- [ ] 对话风格约束已加载（每个出场角色的语气特征：短句/长句/口头禅/禁用词）
- [ ] 潜台词策略已选定（每个场景≥1种技法：指桑骂槐/回避/反话/信息差/言行不一）
- [ ] 高压力场景已标记（标注哪些场景需要矛盾情感描写）
- [ ] 节奏类型已确定（推进章/铺垫章/高潮章，决定信息密度）
- [ ] 常识校验点已识别（本章涉及的职业/场景/时代常识）
- [ ] **角色情境校验完成**：每个出场角色确认三条——①此刻知道什么/不知道什么 ②不能说什么（秘密/能力/立场）③基于处境此刻应该想什么（紧张？观察？讨好？）— 写心声/对话前必须对照
- [ ] **特殊能力规则已核对**：涉及超能力/特殊体质/魔法系统等设定时，读取 `设定/` 下对应规则速查表，确认触发条件/体感描述/暴露禁忌

**阶段二：写中 In-Write Constraints（300-500字分段检查）**
- [ ] 遵守组装好的人物矛盾行为约束（每个核心角色至少一个矛盾行为）
- [ ] 行为指纹执行（核心角色使用专属微动作，禁止通用动作"笑了笑/皱了皱眉"）
- [ ] 动作流大纲引导对话（仅博弈/对抗/隐藏目的场景触发）
- [ ] 潜台词技法落实（每个场景≥1种：指桑骂槐/回避/反话/信息差/言行不一）
- [ ] 禁止角色直接说出内心定义（不写"他心想/她感到"，用行为/感官暗示）
- [ ] 心声格式正确：内心独白用叙事格式（心里在转——内容），不得加引号（加引号=被计为对话行→乒乓球超标）
- [ ] 身份行为合理性：角色的行为/语言是否符合其社会身份？（暗卫不会主动搭话、侍卫不会问王妃问题、心声不会像给上级汇报一样正式）
- [ ] 每轮关键对话之间有动作锚点（≥1个动作锚点）
- [ ] 禁止使用已过桥段标签（桥段去重库）
- [ ] 遵守对话风格约束（不同角色说话语气差异化）
- [ ] 高压力场景包含矛盾情感描写
- [ ] 遵守节奏类型要求（推进章信息密度高，铺垫章允许较慢）
- [ ] 黑名单禁用词出现即替换（不机械清零，剧情优先）
- [ ] 对话比例实时监控（≥25%，每300字至少1段对话）
- [ ] 场景描写不超300字无对话
- [ ] 比喻多样化，"像"比喻单章≤1
- [ ] 因果连贯性：角色内心独白/思考中不能出现尚未被告知或经历过的概念和信息
- [ ] 认知偏差：每个场景至少一个角色存在误读/误判/犹豫（不允许所有角色都正确理解局势）
- [ ] 感官细节：每章至少2处非人物动作的环境/感官描写（风声/虫鸣/布料触感/气味等）
- [ ] 信息差：每个场景至少一个信息差（读者vs角色的认知不对称）
- [ ] 断章位置：结尾在悬念最高处/打脸前/新冲突/情感高潮前，不在日常/设定/平淡对话/环境后
- [ ] 写中实时感知：有没有无聊？有没有重复？有没有推进？

**阶段三：写后 Post-Write Audit**
- [ ] **结构检查优先**：主爽点有没有兑现？核心冲突有没有展开？结尾有没有钩子？→ 不达标直接重写
- [ ] **断章位置正确**：结尾在悬念最高处/打脸前/新冲突/情感高潮/身份reveal前，不在日常/平淡对话/环境/心理活动后
- [ ] **快速扫描**：AI味/动作锚点/行为指纹/结尾检查
- [ ] **四步润色法已执行**：删（废话标签）→ 加（潜台词动作）→ 变形（打破句式）→ 校准（人设冲突）
- [ ] **运行审计脚本**：`python scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --prev-file "正文/第N-1章-xxx.md" --title "第N章 xxx"`
- [ ] AI词频次统计通过（参见四级红线）
- [ ] 对话比例≥25%
- [ ] 标题关键词在正文中出现
- [ ] 与上一章重复度≤20%
- [ ] 审计报告已生成，未通过则自动修复
- [ ] **对话干涩检测通过**（3段抽查≥3个"是"）
- [ ] **行为指纹一致性检查**（核心角色未使用通用动作）
- [ ] **查理日记陷阱检查**（未写角色内心定义）

**阶段四：定期 Review（每5章）**
- [ ] 全书AI词趋势分析
- [ ] 人物对话区分度测试
- [ ] 设定一致性检查
- [ ] 标题-内容匹配率

### [6] 风格定制
**显示风格菜单**：
```
风格定制

【当前生效风格】
{显示 assets/prompts/user_prompts.md 中的内容}

【内置风格模板】
[1] 快节奏爽文风 - 打脸装逼、情绪爆发、短句碎段
[2] 种田经营风 - 细水长流、稳步成长、经营发展
[3] 悬疑推理风 - 伏笔埋设、反转设计、逻辑严密
[4] 甜宠言情风 - 糖分满满、互动甜蜜、情感细腻
[5] 搞笑沙雕风 - 幽默诙谐、反转搞笑、轻松愉快
[6] 暗黑压抑风 - 氛围沉重、人性复杂、剧情深刻
[7] 情感细腻风 - 感官描写、情感流动、心理刻画
[8] 文艺诗意风 - 唯美表达、意象丰富、氛围营造

【操作】
[A] 添加自定义风格 - 输入你的风格提示词
[C] 清空自定义风格 - 清空所有用户添加的风格
[M] 合并多个风格 - 组合多个内置风格

请输入序号或操作命令
```

**操作说明**：
- 输入 `1-8` → 查看风格详情，可选择"加入创作风格"
- 输入 `A` → 输入自定义风格提示词，保存到 `assets/prompts/user_prompts.md`
- 输入 `C` → 清空用户自定义风格
- 输入 `M` → 选择多个风格组合使用

**特殊风格语料库**：

当用户选择 `[5] 搞笑沙雕风` 或要求毒舌/幽默/神回复风格时：
1. 自动读取 `../knowledge_base/70_Corpus/毒舌语料/毒舌知识库.md`、`../knowledge_base/70_Corpus/神回复语料/315条神回复.md`、`../knowledge_base/70_Corpus/神回复语料/110个神回复示例.md`、`../knowledge_base/70_Corpus/神回复语料/话废菩萨语料.md`、`../knowledge_base/70_Corpus/毒舌语料/毒舌AI示例库.md`
2. 结合 `../knowledge_base/40_Writing/风格指南/毒舌风格.md` 生成内容
3. 参考语料中的对话节奏和反转模式，但不要直接复制

### [7] 帮助中心
**显示帮助菜单**：
```
帮助中心

[1] 续写技巧 - 保持风格一致、剧情延续
[2] 长篇创作 - 扩展剧情、增加支线、节奏把控
[3] 发表指南 - 各平台发表流程、审核要求
[4] 写作常见问题 - 常见错误与解决方案

请输入序号(1-4)
```

### [8] 记忆管理（高级）
**显示记忆菜单**：
```
记忆管理（长篇小说专用）

[1] 查看当前记忆 - 人物档案、剧情摘要、世界观设定
[2] 更新人物档案 - 添加/修改人物信息
[3] 更新剧情摘要 - 添加新章节摘要
[4] 更新世界观设定 - 添加/修改设定
[5] 检查一致性 - 检测人物/剧情/设定的矛盾
[6] 导出记忆 - 导出为文件备份
[7] 导入记忆 - 从文件恢复记忆
[8] 人物关系网 - 构建/查看/更新人物关系
[9] 对话风格差异化 - 管理角色说话风格

请输入序号(1-9)
```

**记忆结构**：
- 人物档案：姓名、外貌、性格、能力、关系网、发展轨迹、**对话风格特征**
- 剧情摘要：每卷/每章的核心事件、转折点、伏笔
- 世界观设定：规则体系、势力分布、关键物品
- 风格DNA：写作风格的核特征记录

**人物关系网管理**：
- 自动提取已出现人物，构建关系图
- 关系类型：亲属、朋友、敌对、暧昧、师徒、上下级等
- 关系强度：从"陌生"到"亲密"/"深仇"的变化轨迹
- 每次新人物出场自动更新关系网

**对话风格差异化**：
- 为每个重要角色记录：说话节奏（短句/长句）、口头禅、用词习惯、语气词偏好
- 写作时参考，确保不同角色说话不像同一个人
- 结合 `../knowledge_base/20_Characters/角色命名指南.md` 的人物塑造技巧

### [9.0] 长篇立项流程（必读）

> **适用场景**：用户说"创作"/"立项"/"新小说"/"开始创作一本新书" → 创意文档确认后 → 进入设定/大纲之前

**强制门禁：五维自检**

长篇立项必须先完成五维自检，未通过不得进入设定/大纲阶段。

**执行步骤**：

1. **收集创意信息**：标题 + 简介 + 题材类型 + 目标平台
2. **读取立项资料**（自动）：
   - 平台热门趋势：`knowledge_base/60_Platform/平台热门趋势.md`
   - 流派模板：`knowledge_base/10_WorldBuilding/流派模板总览.md`
   - 五维评分体系：`knowledge_base/50_Quality/创意五维评分.md`
3. **生成五维自检报告**：按 `创意五维评分.md` 中的评分报告模板，输出：
   - 创新性评分 + 理由
   - 市场潜力评分 + 理由（是否命中平台热门）
   - 可读性评分 + 理由
   - 情绪价值评分 + 理由
   - 商业价值评分 + 理由
   - 总分 + 结论（通过/警告/不通过）
4. **呈现给用户确认**：
   - ≥65分 → 用户确认 → 进入设定阶段
   - 55-64分 → 根据优化建议修改 → 重评 → 通过后进入
   - <55分 → 建议重新构思核心创意
5. **通过后**：初始化记忆系统（见 [9.1]）→ 进入设定 → 进入大纲

**立项决策树**：
```
创意确认
  │
  ▼
读取平台热门趋势 + 流派模板 + 五维评分体系
  │
  ▼
五维自检（AI生成报告）
  │
  ├─ ≥65分 → 用户确认 → 进入设定/大纲
  │
  ├─ 55-64分 → 根据优化建议修改 → 重评 → 通过后进入
  │
  └─ <55分 → 建议重新构思核心创意
```

**参考文件**：
- 平台热门趋势：`knowledge_base/60_Platform/平台热门趋势.md`
- 流派模板：`knowledge_base/10_WorldBuilding/流派模板总览.md`
- 五维评分体系：`knowledge_base/50_Quality/创意五维评分.md`

---

### [9.1] 长篇记忆联动（novel-memory-pro）

长篇创作必须配合 `novel-memory-pro` 子技能执行。详细流程见 `novel-memory-pro/references/integration-with-novel-creation.md`。

**核心流程**：

1. **立项后建记忆**：从创意/设定/大纲整理 `project_bootstrap.json`，执行：
   ```bash
   python novel-memory-pro/scripts/memory_manager.py init --memory-dir novel_output/{平台}/{小说名}/记忆
   python novel-memory-pro/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir novel_output/{平台}/{小说名}/记忆
   ```
   如有风格样本，再执行风格 DNA 提取。

2. **每章开写前**：生成记忆包
   ```bash
   python novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir novel_output/{平台}/{小说名}/记忆 --output chapter_N_pack.json
   ```
   据此写下一章。

3. **每章写完后**：生成结构化摘要并回填
   ```bash
   python novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_N_summary.json --memory-dir novel_output/{平台}/{小说名}/记忆
   ```

4. **每5-10章**：定期体检
   ```bash
   python novel-memory-pro/scripts/memory_manager.py stats --memory-dir novel_output/{平台}/{小说名}/记忆
   python novel-memory-pro/scripts/memory_manager.py review-pack --chapter N --memory-dir novel_output/{平台}/{小说名}/记忆 --output review_N.json
   ```
   检查漂移风险、伏笔堆积、剧情拥堵点、人物状态冲突。

**分工原则**：
- 写作技能消费 `active_memory_pack`，不直接维护记忆
- 记忆技能提供约束和回填，不替代写作技能写正文
- 冲突时以用户确认过的大纲/正文为准，再修记忆

---

## 新增功能说明

### [9] 正文润色

用户提供已有章节，指定修改方向，AI 进行定向优化。

**支持的润色方向**：

| 方向 | 说明 | 参考文档 |
|------|------|----------|
| 节奏调整 | 拖沓/太快/太平 | `../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 降低AI味 | 过度排比、空洞抒情、模板化句式 | `../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 对话优化 | 对话太干/太水/不像角色 | `../knowledge_base/20_Characters/角色命名指南.md` |
| 描写增强 | 感官描写、细节补充 | `../knowledge_base/40_Writing/写作技巧/正文写作.md` |
| 情绪渲染 | 情绪不够/太直白 | `../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` |
| 结构优化 | 开头钩子、结尾悬念 | `../knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md` + `../knowledge_base/40_Writing/02_节奏与结构/每章节奏公式与卡章技巧.md` |

**工作流程**：
1. 用户提供章节 + 指定润色方向
2. AI 读取章节并分析问题
3. 按指定方向逐项修改，输出修改前后对比
4. 完成后输出完整修改版
5. 记录修改历史到 `novel_state.json` 的 `revision_history`

**输出格式**：
```
【润色报告】
- 方向：xxx
- 发现问题：
  1. ...
  2. ...
- 修改建议：
  1. ...
- 修改后全文：[完整章节]
```

### [10] 审稿评估

对已有章节做知识库驱动的深度质量审查（不只是跑审计脚本）。

**触发语**："审一下第N章"、"这章写得怎么样"、"审查一下这卷"

**详见**：`review-skill/SKILL.md`

**快速入口**：
- 单章精审：`review-skill/SKILL.md` §单章精审（四维度逐项分析+修复建议）
- 批量快审：`review-skill/SKILL.md` §批量快审（每章扫描+跨章节分析）
- 审查标准：`review-skill/references/review-dimensions.md`（知识库原文映射）
- 报告模板：`review-skill/references/review-report-template.md`（格式+评级）

### [11] 短篇创作

使用"七步法"快速生成短篇/微小说。

**模板**：详见 `../knowledge_base/40_Writing/07_短篇与模板/短篇创作模板.md`

**七步流程**：
1. **引子**（1-3章）：异常事件，建立悬念
2. **发展**（4-10章）：逐步揭示，加深紧张
3. **转折**（11-15章）：关键信息，局势变化
4. **高潮**（16-20章）：真相大白，冲突爆发
5. **结局**（21-25章）：收束伏笔，留白回味
6. **复盘**：检查逻辑漏洞和未解决伏笔
7. **润色**：降低AI味，增强人味

**短篇标准结构**：
```
短篇名/
├── 正文/          # 章节正文
├── 摘要/          # 章节摘要
├── 记忆/          # 记忆系统（可选）
├── 素材/          # 封面等
├── outline.md     # 总大纲
└── novel_state.json  # 状态
```

**与长篇区别**：短篇不需要创意/设定/结构/细纲目录，直接生成大纲和正文。

---

## 续写他人作品（特殊流程）

与"正文写作"[5]不同：续别人的文需要先分析风格再对齐。

**流程**：
1. 用户提供已有文本（前N章或片段）
2. 提取风格 DNA：
   ```bash
   python scripts/style_dna_extractor.py --input 已有文本.txt --output style_dna.json
   ```
3. 分析人物关系、当前状态、未解决伏笔
4. 生成续写大纲（可选，需用户确认）
5. 按风格 DNA 续写后续章节，完成后运行风格校准：
   ```bash
   python scripts/style_calibrator.py --input 续写章节.txt --style-dna style_dna.json --output report.json
   ```

---

### [13] 完结复盘升级

当用户说"完结了"/"写完了"/"复盘"/"总结教训"时自动触发。

**作用**：从已完结的小说中提取教训，自动更新知识库规则，让下一本小说受益。

**流程**：
1. 扫描小说目录下所有审查报告（`full_review_report.json`、`*_report.json`）
2. 扫描所有章节正文，统计AI词使用模式和模板化描写
3. 对比现有红线系统，识别"出现过但未覆盖"的问题
4. 生成新规则建议（按置信度排序：✅高/⚠️中/💡低）
5. 用户确认后自动写入知识库

**执行脚本**：
```bash
# 预览模式（默认）
python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/"

# 自动升级模式
python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/" --upgrade

# 输出报告
python scripts/novel_review_and_upgrade.py --novel-dir "novel_output/{平台}/{小说名}/" --output review_upgrade_report.md
```

**输出内容**：
- AI词使用统计 Top 15
- 审查报告问题统计
- 新规则建议（AI限制词、质量规则、模板警告、浓度关注词）
- 自动写入：闭环质量控制文档 + 红线系统文档

**升级范围**：
| 规则类型 | 写入目标 |
|----------|----------|
| 新增AI限制词 | `knowledge_base/50_Quality/闭环质量控制.md` §2.2 |
|  | `knowledge_base/50_Quality/红线检查/红线系统.md` §14 |
| 新质量规则 | `knowledge_base/50_Quality/闭环质量控制.md` §五 教训转化表 |
| 新模板警告 | `knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md` |
| 浓度关注词 | `novel_creation_promax/novel-memory-pro/references/watch_words.md` |

---

## 多平台输出适配

同一章节，按不同平台规则转换输出格式。

**平台规则**：详见 `../knowledge_base/60_Platform/平台规则.md`

| 平台 | 核心规则 | 段落长度 | 节奏要求 |
|------|---------|---------|---------|
| 番茄 | 短段落、快节奏、每章2000字 | 1-3句/段 | 每300字有冲突 |
| 起点 | 大段描写、世界观展开 | 5-10句/段 | 可慢可快 |
| 晋江 | 情感细腻、互动多 | 2-5句/段 | 感情线驱动 |
| 七猫 | 爽点密集、打脸多 | 1-3句/段 | 每章至少1个爽点 |
| 飞卢 | 极致快节奏、金手指多 | 1-2句/段 | 每200字有变化 |

**转换流程**：
1. 用户指定目标平台
2. 读取对应平台规则
3. 按规则调整段落结构、节奏、用词
4. 输出平台适配版本

---

## 版本/修改历史追踪

每章修改前后自动记录到 `novel_state.json`。

**记录字段**：
```json
{
  "revision_history": [
    {
      "chapter": 1,
      "revision": 1,
      "date": "2024-01-01",
      "type": "初稿/润色/审稿/续写",
      "changes_summary": "调整了节奏，降低了AI味",
      "diff_summary": "删除了3段排比句，简化了2处描写"
    }
  ]
}
```

**自动记录时机**：
- [5] 正文写作：记录初稿
- [9] 正文润色：记录修改内容
- [10] 审稿评估：记录审查结果
- 续写他人作品：记录续写起点

---

## 参考文档

### 核心约束与质量
- 创作红线（四级红线）：[`../knowledge_base/50_Quality/红线检查/红线系统.md`](../knowledge_base/50_Quality/红线检查/红线系统.md)
- 闭环质量控制：[`../knowledge_base/50_Quality/闭环质量控制.md`](../knowledge_base/50_Quality/闭环质量控制.md)
- 章节创作前必答问题：[`../knowledge_base/50_Quality/红线检查/章节前检查.md`](../knowledge_base/50_Quality/红线检查/章节前检查.md)
- 记忆系统输出格式：[`../knowledge_base/50_Quality/红线检查/记忆输出格式.md`](../knowledge_base/50_Quality/红线检查/记忆输出格式.md)
- 上下文连贯性：[`../knowledge_base/30_Plot/偏离处理.md`](../knowledge_base/30_Plot/偏离处理.md)
- 状态管理：[references/state-management.md](references/state-management.md)

### 写作技法与模板
- 人性化写作：[`../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md`](../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md)
- 技术细节规范：[references/technical-details.md](references/technical-details.md)
- 人物命名指南：[`../knowledge_base/20_Characters/角色命名指南.md`](../knowledge_base/20_Characters/角色命名指南.md)
- 开篇钩子库：[`../knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md`](../knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md)
- 短篇模板：[`../knowledge_base/40_Writing/07_短篇与模板/短篇创作模板.md`](../knowledge_base/40_Writing/07_短篇与模板/短篇创作模板.md)
- 人物原型库（2025）：[`../knowledge_base/20_Characters/角色原型参考.md`](../knowledge_base/20_Characters/角色原型参考.md)（纯参考）

### 题材与平台
- 题材模板（5大类型 workflow）：[genre-templates/genre-specific-templates.md](genre-templates/genre-specific-templates.md)
- 平台规则适配：[../knowledge_base/60_Platform/平台规则.md](../knowledge_base/60_Platform/平台规则.md)
- 风格指南：[../knowledge_base/40_Writing/风格指南/通用风格.md](../knowledge_base/40_Writing/风格指南/通用风格.md)（当年明月/猫腻/金庸/古龙/孔二狗）+ [风格索引.md](../knowledge_base/40_Writing/风格指南/风格索引.md)（24位网文作家速查）
- 毒舌风格：[`../knowledge_base/40_Writing/风格指南/毒舌风格.md`](../knowledge_base/40_Writing/风格指南/毒舌风格.md)

### 知识库（→ Obsidian）
- 都市小说：[`../knowledge_base/10_WorldBuilding/题材知识库/都市.md`](../knowledge_base/10_WorldBuilding/题材知识库/都市.md)
- 科幻小说：[`../knowledge_base/10_WorldBuilding/题材知识库/科幻.md`](../knowledge_base/10_WorldBuilding/题材知识库/科幻.md)
- 仙侠小说：[`../knowledge_base/10_WorldBuilding/题材知识库/仙侠.md`](../knowledge_base/10_WorldBuilding/题材知识库/仙侠.md)
- 玄幻小说：[`../knowledge_base/10_WorldBuilding/题材知识库/玄幻.md`](../knowledge_base/10_WorldBuilding/题材知识库/玄幻.md)
- 悬疑小说：[`../knowledge_base/10_WorldBuilding/题材知识库/悬疑.md`](../knowledge_base/10_WorldBuilding/题材知识库/悬疑.md)
- 言情小说：[`../knowledge_base/10_WorldBuilding/题材知识库/言情.md`](../knowledge_base/10_WorldBuilding/题材知识库/言情.md)
- 内容写作技巧：[`../knowledge_base/40_Writing/写作技巧/正文写作.md`](../knowledge_base/40_Writing/写作技巧/正文写作.md)
- 大纲写作技巧：[`../knowledge_base/40_Writing/写作技巧/大纲写作.md`](../knowledge_base/40_Writing/写作技巧/大纲写作.md)
- 设定写作技巧：[`../knowledge_base/40_Writing/写作技巧/人物设定写作.md`](../knowledge_base/40_Writing/写作技巧/人物设定写作.md)
- 结构写作技巧：[`../knowledge_base/40_Writing/写作技巧/结构设计写作.md`](../knowledge_base/40_Writing/写作技巧/结构设计写作.md)

### 交互模板
- 交互总览：[references/interaction.md](references/interaction.md)
- 创意交互：[stages/01-idea/idea-interaction.md](stages/01-idea/idea-interaction.md)
- 设定交互：[stages/02-setting/setting-interaction.md](stages/02-setting/setting-interaction.md)
- 大纲交互：[stages/04-outline/outline-interaction.md](stages/04-outline/outline-interaction.md)
- 结构交互：[stages/03-structure/structure-interaction.md](stages/03-structure/structure-interaction.md)
- 内容交互：[stages/05-writing/content-interaction.md](stages/05-writing/content-interaction.md)

### 评估系统
- **五维评分（立项必读）**：[knowledge_base/50_Quality/创意五维评分.md](../knowledge_base/50_Quality/创意五维评分.md)
- **工业级评分体系**：[knowledge_base/50_Quality/评估系统/评分体系.md](../knowledge_base/50_Quality/评估系统/评分体系.md)
- 平台热门趋势：[knowledge_base/60_Platform/平台热门趋势.md](../knowledge_base/60_Platform/平台热门趋势.md)
- 流派模板总览：[knowledge_base/10_WorldBuilding/流派模板总览.md](../knowledge_base/10_WorldBuilding/流派模板总览.md)
- 内容评估：[`../knowledge_base/50_Quality/评估系统/内容评估.md`](../knowledge_base/50_Quality/评估系统/内容评估.md)
- 创意评估：[`../knowledge_base/50_Quality/评估系统/创意评估.md`](../knowledge_base/50_Quality/评估系统/创意评估.md)
- 大纲评估：[`../knowledge_base/50_Quality/评估系统/大纲评估.md`](../knowledge_base/50_Quality/评估系统/大纲评估.md)
- 设定评估：[`../knowledge_base/50_Quality/评估系统/设定评估.md`](../knowledge_base/50_Quality/评估系统/设定评估.md)
- 结构评估：[`../knowledge_base/50_Quality/评估系统/结构评估.md`](../knowledge_base/50_Quality/评估系统/结构评估.md)

### 连贯性系统
- 偏差处理：[`../knowledge_base/30_Plot/偏离处理.md`](../knowledge_base/30_Plot/偏离处理.md)
- 主节点维护：[`../knowledge_base/30_Plot/主线节点维护.md`](../knowledge_base/30_Plot/主线节点维护.md)
- 大纲执行：[`../knowledge_base/30_Plot/细纲执行机制.md`](../knowledge_base/30_Plot/细纲执行机制.md)
- 审查机制：[`../knowledge_base/30_Plot/定期复盘机制.md`](../knowledge_base/30_Plot/定期复盘机制.md)

### 创作工作流
- 默认工作流：[references/workflow.md](references/workflow.md)

### 记忆系统
- 记忆结构：[assets/memory_structure.json](assets/memory_structure.json)
- 项目初始化模板：[assets/templates/project-bootstrap.json](assets/templates/project-bootstrap.json)
- 章节摘要模板：[assets/templates/chapter-summary.json](assets/templates/chapter-summary.json)
- 风格DNA示例：[assets/examples/sample-style-dna.json](assets/examples/sample-style-dna.json)
- 人物档案模板：[novel-memory-pro/references/character_profile_template.md](novel-memory-pro/references/character_profile_template.md)
- 人物小传模板：[novel-memory-pro/references/character-biography-template.md](novel-memory-pro/references/character-biography-template.md)
- 风格DNA格式：[novel-memory-pro/references/style_dna_format.md](novel-memory-pro/references/style_dna_format.md)
- 章节同步Schema：[novel-memory-pro/references/chapter_sync_schema.md](novel-memory-pro/references/chapter_sync_schema.md)
- 与主技能联动流程：[novel-memory-pro/references/integration-with-novel-creation.md](novel-memory-pro/references/integration-with-novel-creation.md)
- 记忆优化手册：[novel-memory-pro/references/memory-optimization-playbook.md](novel-memory-pro/references/memory-optimization-playbook.md)
- 记忆工作流指南：[novel-memory-pro/references/workflow_guide.md](novel-memory-pro/references/workflow_guide.md)

---

## 核心脚本使用指南

### 人物命名
```bash
python scripts/name_generator.py --gender male --style ancient_elegant --count 5
```

### 记忆系统（长篇小说）
```bash
# 初始化记忆目录
python novel-memory-pro/scripts/memory_manager.py init --memory-dir ./my_novel

# 导入项目信息
python novel-memory-pro/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ./my_novel

# 生成章节前记忆包
python novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir ./my_novel --output chapter_N_pack.json

# 同步章节摘要
python novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_summary.json --memory-dir ./my_novel

# 阶段性回顾（推荐每5-10章）
python novel-memory-pro/scripts/memory_manager.py review-pack --chapter N --memory-dir ./my_novel --output review_N.json
```

### 风格与一致性

```bash
# 从参考文本提取风格DNA
python scripts/style_dna_extractor.py --input sample.txt --output style_dna.json

# 检查风格漂移（输出：漂移报告 JSON）
python scripts/style_calibrator.py --input chapter.txt --style-dna style_dna.json --output report.json
```

### 写后自动审计（每章必做）

```bash
# 单章审计
python scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --prev-file "正文/第N-1章-xxx.md" --title "第N章 xxx"

# 扫描目录下所有章节
python scripts/post_write_audit.py --scan-all --dir "正文/"

# 输出JSON审计报告
python scripts/post_write_audit.py --chapter-file "正文/第N章-xxx.md" --title "第N章 xxx" --output audit_report.json
```

**审计项目**：AI词频次、对话比例、标题关键词匹配、相邻章节重复度、前300字冲突检查

### 人物一致性检查（OOC 检测）

检测新章节中人物行为、说话风格、决策模式是否符合初始设定。

```bash
# 基础检查（自动扫描 记忆/ 目录下的人物档案）
python scripts/character_consistency_checker.py

# 指定章节和人物档案进行检查
python scripts/character_consistency_checker.py --input 正文/第10章.md --characters 记忆/characters.json

# 输出：OOC 警告列表，包含人物、违规表现、严重程度
```

**输出格式**：
- 每个人物一条 OOC 警告，包含：人物名、表现不一致的行为、对应原始设定、严重程度（轻微/中等/严重）
- 最后汇总：扫描人物数、发现警告数、需人工复核项

### 剧情连贯性检查（伏笔/逻辑追踪）

追踪剧情线索，检测逻辑漏洞，维护时间线和伏笔解决状态。

```bash
# 连贯性检查（输出当前章节的连贯性报告）
python scripts/plot_continuity_checker.py --check N

# 生成详细报告（支持 text/html/json 格式）
python scripts/plot_continuity_checker.py --report N --format text

# 列出所有剧情线索
python scripts/plot_continuity_checker.py --list

# 保存/加载状态
python scripts/plot_continuity_checker.py --load plot_data.json --check N
python scripts/plot_continuity_checker.py --save plot_data.json
```

**输出格式**：
- 总体评分（0-100%）和等级（优秀/良好/一般/需改进）
- 四个维度：时间线一致性、逻辑一致性、伏笔解决、承诺兑现
- 每个维度包含：得分、问题列表（严重程度+描述）、改进建议

---

## 特色功能

### 风格自由度
- 支持多种内置风格组合
- 支持用户自定义风格提示词
- 写作时自动应用选定的风格

### 记忆系统
- 长篇小说人物/剧情追踪
- 自动检测一致性问题
- 支持导入导出

### 灵活创作
- 支持从大纲生成
- 支持自由创作
- 支持续写和修改

---

## 使用建议

1. **新手**：从 [0] 新手模式开始，系统会引导你完成整个创作流程
2. **有经验者**：使用 [4] 生成大纲 + [5] 正文写作
3. **长篇创作**：配合 [8] 记忆管理，防止吃设定
4. **风格定制**：使用 [6] 风格定制找到最适合的写作风格