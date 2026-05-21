# 执行链编排器 (Orchestrator)

> **这是整个小说创作系统的唯一调度器。** 它只定义一件事：**谁在什么时候被谁调用。**
> 所有参考文档的执行顺序、审计时机、裁决优先级都在这里声明。

---

## 一、7阶段执行链

```
创意 → 设定 → 大纲 → 细纲 → 正文 → 记忆更新 → 完结复盘
 │      │       │      │      │       │          │
 ▼      ▼       ▼      ▼      ▼       ▼          ▼
Stage1 Stage2  Stage3 Stage4 Stage5  Memory     Review
```

### 1a. 4阶段雪花级联（大纲设计子流程）

大纲阶段内部分为4级级联，每级必须通过检查点才能进入下一级（借鉴 AI_NovelGenerator 的雪花法适配）：

```
Level 1: 世界观一句话（核心矛盾 + 一句话设定）
    │ checkpoint: 世界观完整性
    ▼
Level 2: 100字摘要（主线 + 起因 + 高潮 + 结局）
    │ checkpoint: 因果链完整
    ▼
Level 3: 主线分支（主线 + 每条支线3句话摘要）
    │ checkpoint: 支线与主线关联度
    ▼
Level 4: 章节规划（每章一句话 + 关键事件 + 伏笔节点）
    │ checkpoint: 节奏均匀 + 伏笔分布
    ▼
输出：细纲文档
```

**检查点规则**：
- 每级独立暂停/恢复：可在任意 checkpoint 停下，下次从该点继续
- Level 1 缺失 → 禁止进入 Level 2
- Level 2 因果链断裂 → 回退 Level 1 修补
- Level 3 支线与主线无关联 → 删除或重写该支线
- Level 4 节奏不均匀（连续5章无爽点）→ 回退 Level 3 调整分支

**与现有流程的关系**：这是 Stage 3（大纲）内部的展开，不改变 7 阶段结构。

### 执行链明细

| 阶段 | 触发条件 | 输入 | 使用模块 | 输出 | 进入下一阶段条件 |
|------|----------|------|----------|------|------------------|
| **1. 创意** | 用户给想法 | 自由文本 | `stages/01-idea/` + `../knowledge_base/50_Quality/评估系统/创意评估.md` | 创意文档 | 用户确认 + 评估通过 |
| **2. 设定** | 创意通过 | 创意文档 | `stages/02-setting/` + `../knowledge_base/50_Quality/评估系统/设定评估.md` + **设定底座** + **12项完整性审查** | 设定文档 | 用户确认 + 设定底座通过 + 评估通过 + 12项审查通过 |
| **3. 大纲** | 设定通过 | 设定文档 | `stages/03-structure/` + `../knowledge_base/50_Quality/评估系统/结构评估.md` | 大纲+结构文档 | 用户确认 + 评估通过 |
| **4. 细纲** | 大纲通过 | 大纲文档 | `stages/04-outline/` + `../knowledge_base/50_Quality/评估系统/大纲评估.md` | 细纲JSON | 用户确认 + 主节点规划完成 |
| **5. 正文** | 用户要写第N章 | 细纲+记忆包 | 9问→写前检查→写正文→写后审计 | 章节正文 | 审计全部通过 |
| **6. 记忆** | 章节完成 | 章节摘要 | `novel-memory-pro` sync-chapter | 记忆更新 | 自动完成 |
| **7. 复盘** | 完结/用户触发 | 全部章节 | `novel_creation_promax/scripts/novel_review_and_upgrade.py` | 规则升级建议 | 用户确认后写入知识库 |

**硬规则**：禁止跨阶段、禁止跳过评估、禁止跳过用户确认。详见 `references/workflow.md` 的阶段门禁机制。

### Stage 2 设定完整性审查（新增）

**触发时机**：创意确认后、大纲开始前。**新小说必须执行，已有小说续写时跳过。**

**问题来源**：《废婿觉醒》写完10章才发现没有"入赘原因"设定。用户问"有伏笔么"才补救。被动补全3次。

**规则**：以下12项任何一项缺失，停下来补全，**不写正文**。发现缺失立即补全，不等用户催促。

| # | 检查项 | 必须包含 |
| --- | -------- | ---------- |
| 1 | 主角档案 | 基本信息+外貌+性格(含矛盾性)+背景+核心恐惧+核心渴望+成长弧线+起点原因 |
| 2 | 女主档案 | 同上，含独立行为线和感情线阶段 |
| 3 | 核心配角档案 | 每个配角：基本信息+外貌+性格(含矛盾性)+背景+作用+成长线 |
| 4 | 反派档案 | 基本信息+外貌+性格+动机+压迫感来源+结局 |
| 5 | 能力/金手指详解 | 起源+等级表+体感+冷却+反噬+限制+盲区+升级体感 |
| 6 | 世界观设定 | 时代背景+社会结构+核心场景+术语表 |
| 7 | 家族/组织谱系 | 族谱+权力结构+各方关系+关键历史事件 |
| 8 | 主角起点原因 | 为什么在故事开始时的处境中（赘婿/穷/被欺）— 必须交代 |
| 9 | 父母/家庭背景 | 父母是谁、在不在世、什么关系 |
| 10 | 势力档案 | 每个势力的家主+核心成员+弱点+关系网+与主线关联 |
| 11 | 地理设定 | 城市地图级设定，各方势力据点 |
| 12 | 伏笔表 | 编号+内容+埋设章节+回收章节+状态 |

**审查结果**：通过后写入 `设定/设定完整性审查报告.md`，标记通过/不通过及缺失项。

### Stage 2b 设定底座审查（新增）

**触发时机**：新书立项 `project_bootstrap_pipeline.py seal` 时强制执行。

**问题来源**：人物只有基本信息，缺少现实锚点和关系网络，导致正文中出现收入、居住、职业、台词、组织行为不符合常识。

**必填文件**：

| 文件 | 必须锁定 |
| --- | --- |
| `设定/人物档案.md` | 职业收入、居住原因、能力边界、动机恐惧、行为指纹、声纹、OOC禁止项 |
| `设定/地点档案.md` | 住所、工作地点、通勤距离、消费水平、场景使用规则 |
| `设定/势力档案.md` | 组织结构、资源限制、利益关系、行动边界 |
| `设定/事件档案.md` | 关键事件的前因后果、证据链、影响范围、后续债务 |
| `设定/关系网络.md` | 信任等级、利益冲突、信息差、关系变化规则 |
| `设定/常识约束.md` | 经济、职业、居住、法律流程、技术能力、禁止漂移清单 |

缺任一文件、栏目不全、内容仍含占位词、内容过短 → 禁止进入正文。

---

## 二、正文创作执行链（每章）

这是系统最高频的执行路径，必须严格遵循：

```
用户要求写第N章
    │
    ▼
1. 生成记忆包 ────────── python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir novel_output/{平台}/{小说名}/记忆 --output chapter_N_pack.json
    │
    ▼
1.5 加载知识路由 ──────── 读 `../knowledge_base/40_Writing/写作知识路由表.md`
    │                      确定本章主要场景类型（投资打脸/父女温情/系统升级/职场受辱等）
    │                      按路由表读对应必读文件（2-3个），提取本章约束
    │                      在摘要JSON的 knowledge_references 字段记录引用文件
    │
    ▼
2. 9问必答系统 ──────── python novel_creation_promax/scripts/pre_write_check.py --novel-dir ... --chapter N --answers-file ...
    │                    `../knowledge_base/50_Quality/红线检查/章节前检查.md`（总分≥70分）
    │                    检查 exit code，非0则必须完善答案后重跑
    │
    ▼
3. 生成场景写作卡 ────── `references/scene-writing-card.md` 模板，填入本章信息
    │                      重点：章节截断点（本章在什么事件后结束）
    │
    ▼
══════════════════════════════════════
4. PASS 1：第一遍剧情稿
══════════════════════════════════════
    │ 目标：写出完整剧情，不管AI词
    │ 规则：
    │   - 不检查AI词、不检查对话比例、不检查乒乓球短句
    │   - 先按场景预算把首稿写到位，番茄默认目标 2950-3150 中文字符，不接受 1500 字摘要稿
    │   - 默认拆成 5-6 场，每场约 450-650 字；缺的是过程场景，不是解释句
    │   - 每300-500字自检：有没有无聊？有没有重复？有没有推进？
    │   - 严格在场景写作卡截断点停笔，不蹭到下一章内容
    │
    ▼
══════════════════════════════════════
4.5 GATE 检查（Pass 1→2 断点）
══════════════════════════════════════
    │ 目标：Pass 1→Pass 2 的质量门禁，拦截剧情硬伤
    │
    ▼
python novel_creation_promax/scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
    │
    ├── exit 0 → 进入 Pass 2
    └── exit 1 → 回到 Pass 1 修复
    │
    ▼
══════════════════════════════════════
5. PASS 2：AI词清理稿
══════════════════════════════════════
    │ 目标：在保留剧情逻辑和对话风格的前提下，清理AI词
    │ 规则：
    │   - 以PASS 1输出为基准，只改词汇，不动叙事结构
    │   - 对话修改不改变角色说话方式
    │   - 如果某个词替换会导致语义不通，跳过该替换
    │
    ▼
6. 写后审计 ─────────── python novel_creation_promax/scripts/post_write_audit.py
    │                   执行顺序：①逻辑检查 → ②AI词清理 → ③对话质量
    │                   ①逻辑检查不通过，不进入②③
    │
    ▼
7. 审计通过？ ── 否 ──→ 只修复AI词问题（不动剧情）→ 回到步骤6
    │ 是
    ▼
8. 风格校准 ────────── python novel_creation_promax/scripts/style_calibrator.py
    │                    偏差<0.3通过，0.3-0.5警告，≥0.5重写（exit code 1）
    │
    ▼
9. 人物一致性 ──────── python novel_creation_promax/scripts/character_consistency_checker.py
    │                    无严重OOC警告方可继续
    │
    ▼
10. 输出章节 + 生成摘要 → 记忆回填（novel-memory-pro sync-chapter）
```

**优先级原则**：剧情逻辑 > 角色一致 > AI词清理。审计时按此顺序检查，AI词清理不能破坏前两者。

**执行强制机制**：
- PASS 1 必须在场景写作卡截断点停笔，蹭到下一章内容 = 本章作废。
- 步骤4.5（GATE 检查）必须通过 `novel_creation_promax/scripts/writing_gate.py` 实际执行，exit code 1 = 回到 Pass 1 修复，不得跳过。
- 步骤6（写后审计）必须通过 `novel_creation_promax/scripts/post_write_audit.py` 实际执行，不得跳过或仅口头检查。
- 脚本返回 exit code 1 = 审计未通过，必须修复后重新运行，直到 exit code 0。
- 未执行审计或审计未通过就输出章节 → 本章作废。

---

## 三、审计日历

不同审计在不同时机触发，避免"审计成本爆炸"和"反馈冲突"：

| 时机 | 触发方式 | 执行模块 | 检查内容 | 失败处理 |
|------|----------|----------|----------|----------|
| **每章写完** | 自动 | `novel_creation_promax/scripts/post_write_audit.py` | AI词、字数、对话比、单行段、重复度 | 自动修复→重新审计 |
| **每章写完** | 自动 | `novel_creation_promax/scripts/style_calibrator.py` | 风格DNA偏差 | 偏差≥0.3警告，≥0.5必须重写 |
| **每章写完** | 自动 | `novel_creation_promax/scripts/character_consistency_checker.py` | 人物OOC检测 | 严重OOC必须修正 |
| **每5章** | 自动 | `stages/04-outline/review-mechanism.md` | 定期复盘：漂移风险、伏笔堆积 | 输出复盘报告 |
| **每10章** | 自动 | `novel_creation_promax/scripts/plot_continuity_checker.py` | 时间线、逻辑、伏笔回收 | 输出连贯性报告 |
| **用户要求"评估"** | 手动 | `../knowledge_base/50_Quality/评估系统/内容评估.md` | 正文质量评级 | 输出评级报告 |
| **完结** | 自动 | `novel_creation_promax/scripts/novel_review_and_upgrade.py` | 全量扫描+规则升级 | 生成升级建议→用户确认→写入知识库 |

**原则**：每章必跑 post_write_audit + style_calibrator + character_consistency_checker 三项。定期审计和全量审计不在每章运行。

---

## 四、风格裁决链

风格系统有多个模块，**谁说了算**在此声明：

```
项目初始化
    │
    ▼ style_dna_extractor.py 从样本文提取DNA（定量基线）
    │
    ▼ 创作前：通用风格.md（knowledge_base/风格指南/）选定作者风格（定性参考，不强制）
    │          witty-style-guide.md 仅用户明确要求毒舌时启用（独立域）
    │
    ▼ 创作中：遵守DNA约束 + 人味写作指南去AI味
    │
    ▼ 创作后：style_calibrator.py 校准偏差（定量裁决）
               · 偏差 < 0.3：通过
               · 0.3 ≤ 偏差 < 0.5：警告，建议修改
               · 偏差 ≥ 0.5：不通过，必须重写
```

**裁决优先级**：
- **Style DNA = 定量裁决者**（数值超标必须修）
- **通用风格.md（knowledge_base/风格指南/） = 定性参考**（方向指引，不强制）
- **人味写作指南 = 通用后处理**（所有风格都适用）
- **witty-style-guide.md = 独立域**（不是小说风格，仅特殊需求时启用）

---

## 五、审计裁决优先级

当多个审计模块给出冲突结果时，按以下优先级处理：

```
硬性规则（post_write_audit AI词黑名单、字数、对话比）
    ↓ 不通过则直接驳回，不进入后续检查
结构规则（coherence 主线偏离、剧情矛盾、伏笔丢失）
    ↓ 不通过则标记为二级红线，必须修复
质量建议（evaluation 评分、风格评分）
    ↓ 仅作参考，不强制驳回
```

**一句话**：硬规则不过，不进入下一阶段。结构规则不过，标记红线必须修。质量建议不过，记录但不阻断。

---

## 六、记忆系统声明

**记忆系统唯一实现**：`novel-memory-pro/`

所有记忆操作通过以下路径：
- 脚本：`novel_creation_promax/novel-memory-pro/scripts/memory_manager.py`
- 模板：`novel-memory-pro/references/`
- Schema：`novel-memory-pro/assets/memory_structure.json`

旧版 memory_manager 薄封装已废弃，请直接使用 `novel_creation_promax/novel-memory-pro/` 下的实现。

**分工原则**：
- 写作技能消费 `active_memory_pack`，不直接维护记忆
- 记忆技能提供约束和回填，不替代写作技能写正文
- 冲突时以用户确认过的大纲/正文为准，再修记忆

详细集成流程见 `novel-memory-pro/references/integration-with-novel-creation.md`。

---

## 七、闭环验证机制（写→审计→修复→验证）

> **核心原则**：写作不是一次性管道（write→output），而是带反馈环路的闭环系统。

### 7.1 审计闭环流程

```
写正文完成
    │
    ▼
运行 post_write_audit.py
    │
    ├─── exit code 0 (全部通过) ──→ 输出章节 → 记忆回填 → 下一章
    │
    └─── exit code 1 (有未通过项)
         │
         ▼
     分类问题类型：
     ├─ 硬性问题（禁止词、字数、对话比、标题关键词）→ 自动修复
     ├─ 结构性问题（重复度、主线偏离） → 手动重写
     └─ 建议性问题（前300字、风格评分） → 记录不阻断
         │
         ▼
     修复后重新运行 post_write_audit.py
         │
         └─── 最多重试3次，仍不通过 → 标记"本章需人工审核"，暂停下一章
```

### 7.2 自动修复策略

| 问题类型 | 修复方式 |
|----------|----------|
| 绝对禁止词（如"像是"） | 全文替换为近义词（仿佛/似乎/犹如/如...一般） |
| 严格限制词超量 | 优先替换为动作描写或心理描写 |
| "像"比喻超量 | 改为直接陈述或其他比喻词 |
| 标题关键词缺失 | 在章节末尾自然融入标题短语 |
| 对话比例不足 | 在关键场景添加角色对话 |
| 字数不足 | 优先补写观察/试探/交锋/代价/新线索等有效过程，不得用重复解释凑字数 |
| 字数超量 | 精简冗余描写或合并对话 |

### 7.3 审计执行命令

```bash
# 单章审计
python novel_creation_promax/scripts/post_write_audit.py \
  --chapter-file "novel_output/{平台}/{小说名}/正文/第N章-标题.md" \
  --prev-file "novel_output/{平台}/{小说名}/正文/第N-1章-标题.md" \
  --title "第N章 标题"

# 全量扫描（检查已写所有章节）
python novel_creation_promax/scripts/post_write_audit.py \
  --scan-all --dir "novel_output/{平台}/{小说名}/正文/" \
  --output "novel_output/{平台}/{小说名}/素材/audit_report.json"
```

### 7.4 审计记录持久化

每次审计结果必须保存到：`novel_output/{平台}/{小说名}/素材/audit_ch{N}.json`

包含字段：章节号、审计时间、各项指标值、通过/未通过状态、修复记录。

---

## 八、模块索引

### 按执行阶段归类

| 阶段 | 交互模板 | 评估文档 | 连贯性 |
|------|----------|----------|--------|
| 1. 创意 | `stages/01-idea/idea-interaction.md` | `../knowledge_base/50_Quality/评估系统/创意评估.md` | — |
| 2. 设定 | `stages/02-setting/setting-interaction.md` | `../knowledge_base/50_Quality/评估系统/设定评估.md` | — |
| 3. 大纲 | `stages/03-structure/structure-interaction.md` | `../knowledge_base/50_Quality/评估系统/结构评估.md` | — |
| 4. 细纲 | `stages/04-outline/outline-interaction.md` | `../knowledge_base/50_Quality/评估系统/大纲评估.md` | `stages/04-outline/main-node.md` |
| 5. 正文 | `stages/05-writing/content-interaction.md` | `../knowledge_base/50_Quality/评估系统/内容评估.md` | `stages/04-outline/deviation-handling.md`<br>`stages/04-outline/outline-execution.md`<br>`stages/04-outline/review-mechanism.md` |

### 质量约束

| 文档 | 用途 |
|------|------|
| `../knowledge_base/50_Quality/红线检查/红线系统.md` | 四级红线系统（绝对禁止→质量优化） |
| `../knowledge_base/50_Quality/红线检查/章节前检查.md` | 9问必答系统（写前拦截） |
| `../knowledge_base/50_Quality/红线检查/记忆输出格式.md` | 记忆系统输出格式规范 |
| `../knowledge_base/50_Quality/红线检查/物理状态追踪.md` | 物理状态追踪（钱/物品/位置/时间一致性） |

### 工具脚本

| 脚本 | 用途 | 调用时机 |
|------|------|----------|
| `novel_creation_promax/scripts/post_write_audit.py` | 每章审计 | 每章写完 |
| `novel_creation_promax/scripts/writing_gate.py` | Pass 1→2 断点门禁 | 每章 PASS 1 完成后 |
| `novel_creation_promax/scripts/style_dna_extractor.py` | 风格DNA提取 | 项目初始化 |
| `novel_creation_promax/scripts/style_calibrator.py` | 风格校准 | 每章写完 |
| `novel_creation_promax/scripts/character_consistency_checker.py` | 人物OOC检测 | 每章写完 |
| `novel_creation_promax/scripts/plot_continuity_checker.py` | 剧情连贯性 | 每10章 |
| `novel_creation_promax/scripts/novel_review_and_upgrade.py` | 完结复盘 | 完结时 |
| `novel_creation_promax/scripts/generate_cover.py` | 封面生成 | 用户要求 |
| `novel_creation_promax/scripts/name_generator.py` | 角色命名 | 设定阶段 |

### 风格系统

| 文档 | 用途 | 阶段 |
| ------ | ------ | ------ |
| `knowledge_base/40_Writing/风格指南/风格索引.md` | **24位网文作家风格总索引（速查表+题材匹配）** | 创作前选择 |
| `knowledge_base/40_Writing/风格指南/写作风格技能合集/` | **24位作家风格技能目录（每个含SKILL.md+references）** | 按需调用 |
| `knowledge_base/40_Writing/风格指南/通用风格.md` | 5种作者风格参考（当年明月/猫腻/金庸/古龙/孔二狗） | 创作前选择 |
| `../knowledge_base/40_Writing/03_人物与对话/人味写作指南.md` | 去除AI痕迹/人性化写作 | 写后润色 |

**注意**：新增的24位网文作家风格技能统一存放在 `knowledge_base/40_Writing/风格指南/写作风格技能合集/`，每位作家独立一个目录，包含 SKILL.md（核心技法）和 references/（详细技法+text-generator.md）。创作时先查风格索引确定作家，再读取对应 SKILL.md 执行。

### 独立参考文档（不归类于任何阶段）

| 文档 | 用途 |
|------|------|
| `references/workflow.md` | 5阶段状态机 + 8步子流程（orchestrator的展开） |
| `references/genre-templates/genre-specific-templates.md` | 题材通用指南 |
| `references/docs/fiction-writing-guide.md` | 小说写作指南（纯参考） |
| `references/docs/writing-style.md` | 写作风格参考（纯参考） |
| `references/opening-hooks.md` | 开头钩子库 |
| `references/technical-details.md` | 技术细节 |
| `references/state-management.md` | 状态管理 |
| `../knowledge_base/60_Platform/` | 平台适配规则 |
| `../knowledge_base/` | 题材知识库 + 写作技能 |
| `references/writing-guides/` | 写作指南（命名等） |

---

## 快速开始

如果你是第一次使用这个系统：

1. **短篇创作**：可跳过阶段1-3（创意/设定/大纲），直接从阶段4（细纲）或阶段5（正文）开始，但仍需通过阶段内的9问和审计流程
2. **长篇从零开始**：从阶段1（创意）开始，严格按顺序执行
3. **长篇续写**：直接跳到阶段5（正文），但必须先跑记忆包（阶段6的前置步骤）
4. **已有章节润色**：使用 [9] 正文润色功能，不触发完整执行链
