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

### 执行链明细

| 阶段 | 触发条件 | 输入 | 使用模块 | 输出 | 进入下一阶段条件 |
|------|----------|------|----------|------|------------------|
| **1. 创意** | 用户给想法 | 自由文本 | `stages/01-idea/` + `quality/evaluation/idea-evaluation.md` | 创意文档 | 用户确认 + 评估通过 |
| **2. 设定** | 创意通过 | 创意文档 | `stages/02-setting/` + `quality/evaluation/setting-evaluation.md` | 设定文档 | 用户确认 + 评估通过 |
| **3. 大纲** | 设定通过 | 设定文档 | `stages/03-structure/` + `quality/evaluation/structure-evaluation.md` | 大纲+结构文档 | 用户确认 + 评估通过 |
| **4. 细纲** | 大纲通过 | 大纲文档 | `stages/04-outline/` + `quality/evaluation/outline-evaluation.md` | 细纲JSON | 用户确认 + 主节点规划完成 |
| **5. 正文** | 用户要写第N章 | 细纲+记忆包 | 9问→写前检查→写正文→写后审计 | 章节正文 | 审计全部通过 |
| **6. 记忆** | 章节完成 | 章节摘要 | `novel-memory-pro` sync-chapter | 记忆更新 | 自动完成 |
| **7. 复盘** | 完结/用户触发 | 全部章节 | `scripts/novel_review_and_upgrade.py` | 规则升级建议 | 用户确认后写入知识库 |

**硬规则**：禁止跨阶段、禁止跳过评估、禁止跳过用户确认。详见 `references/workflow.md` 的阶段门禁机制。

---

## 二、正文创作执行链（每章）

这是系统最高频的执行路径，必须严格遵循：

```
用户要求写第N章
    │
    ▼
1. 生成记忆包 ────────── python novel-memory-pro/scripts/memory_manager.py chapter-pack
    │
    ▼
2. 9问必答系统 ──────── quality/pre-chapter-questions.md（总分≥70分）
    │
    ▼
3. 写前5项检查 ──────── AI词黑名单、上一章读取、人物档案、标题关键词、前300字冲突
    │
    ▼
4. 写正文 ───────────── 遵守写中约束（对话≥25%、AI词≤限制、"像"≤1、单行段≤8）
    │
    ▼
5. 写后审计 ─────────── python scripts/post_write_audit.py
    │
    ▼
6. 审计通过？ ── 否 ──→ 自动修复 → 回到步骤5
    │ 是
    ▼
7. 输出章节 + 生成摘要 → 记忆回填（novel-memory-pro sync-chapter）
```

**违规后果**：跳过任一步骤 = 本章作废，必须从头开始。详见 `SKILL.md` 的硬门禁章节。

---

## 三、审计日历

不同审计在不同时机触发，避免"审计成本爆炸"和"反馈冲突"：

| 时机 | 触发方式 | 执行模块 | 检查内容 | 失败处理 |
|------|----------|----------|----------|----------|
| **每章写完** | 自动 | `scripts/post_write_audit.py` | AI词、字数、对话比、单行段、重复度 | 自动修复→重新审计 |
| **每章写完** | 自动 | `novel-memory-pro/scripts/style_calibrator.py` | 风格DNA偏差 | 偏差≥0.3警告，≥0.5必须重写 |
| **每5章** | 自动 | `stages/04-outline/review-mechanism.md` | 定期复盘：漂移风险、伏笔堆积 | 输出复盘报告 |
| **每10章** | 自动 | `scripts/plot_continuity_checker.py` | 时间线、逻辑、伏笔回收 | 输出连贯性报告 |
| **用户要求"评估"** | 手动 | `quality/evaluation/content-evaluation.md` | 正文质量评级 | 输出评级报告 |
| **完结** | 自动 | `scripts/novel_review_and_upgrade.py` | 全量扫描+规则升级 | 生成升级建议→用户确认→写入知识库 |

**原则**：每章只跑 post_write_audit + style_calibrator。定期审计和全量审计不在每章运行。

---

## 四、风格裁决链

风格系统有多个模块，**谁说了算**在此声明：

```
项目初始化
    │
    ▼ style_dna_extractor.py 从样本文提取DNA（定量基线）
    │
    ▼ 创作前：style-guide.md 选定作者风格（定性参考，不强制）
    │          witty-style-guide.md 仅用户明确要求毒舌时启用（独立域）
    │
    ▼ 创作中：遵守DNA约束 + low-ai-trace-polish.md 去AI味
    │
    ▼ 创作后：style_calibrator.py 校准偏差（定量裁决）
               · 偏差 < 0.3：通过
               · 0.3 ≤ 偏差 < 0.5：警告，建议修改
               · 偏差 ≥ 0.5：不通过，必须重写
```

**裁决优先级**：
- **Style DNA = 定量裁决者**（数值超标必须修）
- **style-guide.md = 定性参考**（方向指引，不强制）
- **low-ai-trace-polish.md = 通用后处理**（所有风格都适用）
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
- 脚本：`novel-memory-pro/scripts/memory_manager.py`
- 模板：`novel-memory-pro/references/`
- Schema：`novel-memory-pro/assets/memory_structure.json`

顶层 `scripts/memory_manager.py` 已废弃（薄封装），请直接使用 `novel-memory-pro/` 下的实现。

**分工原则**：
- 写作技能消费 `active_memory_pack`，不直接维护记忆
- 记忆技能提供约束和回填，不替代写作技能写正文
- 冲突时以用户确认过的大纲/正文为准，再修记忆

详细集成流程见 `novel-memory-pro/references/integration-with-novel-creation.md`。

---

## 七、模块索引

### 按执行阶段归类

| 阶段 | 交互模板 | 评估文档 | 连贯性 |
|------|----------|----------|--------|
| 1. 创意 | `stages/01-idea/idea-interaction.md` | `quality/evaluation/idea-evaluation.md` | — |
| 2. 设定 | `stages/02-setting/setting-interaction.md` | `quality/evaluation/setting-evaluation.md` | — |
| 3. 大纲 | `stages/03-structure/structure-interaction.md` | `quality/evaluation/structure-evaluation.md` | — |
| 4. 细纲 | `stages/04-outline/outline-interaction.md` | `quality/evaluation/outline-evaluation.md` | `stages/04-outline/main-node.md` |
| 5. 正文 | `stages/05-writing/content-interaction.md` | `quality/evaluation/content-evaluation.md` | `stages/04-outline/deviation-handling.md`<br>`stages/04-outline/outline-execution.md`<br>`stages/04-outline/review-mechanism.md` |

### 质量约束

| 文档 | 用途 |
|------|------|
| `quality/red-line-system.md` | 四级红线系统（绝对禁止→质量优化） |
| `quality/pre-chapter-questions.md` | 9问必答系统（写前拦截） |
| `quality/memory-output-format.md` | 记忆系统输出格式规范 |

### 工具脚本

| 脚本 | 用途 | 调用时机 |
|------|------|----------|
| `scripts/post_write_audit.py` | 每章审计 | 每章写完 |
| `scripts/style_dna_extractor.py` | 风格DNA提取 | 项目初始化 |
| `scripts/style_calibrator.py` | 风格校准 | 每章写完 |
| `scripts/plot_continuity_checker.py` | 剧情连贯性 | 每10章 |
| `scripts/novel_review_and_upgrade.py` | 完结复盘 | 完结时 |
| `scripts/generate_cover.py` | 封面生成 | 用户要求 |
| `scripts/name_generator.py` | 角色命名 | 设定阶段 |

### 风格系统

| 文档 | 用途 | 阶段 |
|------|------|------|
| `references/style-guide.md` | 5种作者风格参考 | 创作前选择 |
| `references/low-ai-trace-polish.md` | 去除AI痕迹 | 写后润色 |
| `references/witty-style-guide.md` | 毒舌/神回复（非小说） | 特殊风格需求 |

### 独立参考文档（不归类于任何阶段）

| 文档 | 用途 |
|------|------|
| `references/workflow.md` | 5阶段状态机 + 8步子流程（orchestrator的展开） |
| `references/genre-guide.md` | 题材通用指南 |
| `references/fiction-writing-guide.md` | 小说写作指南 |
| `references/writing-style.md` | 写作风格参考 |
| `references/opening-hooks.md` | 开头钩子库 |
| `references/technical-details.md` | 技术细节 |
| `references/state-management.md` | 状态管理 |
| `references/platform-adaptation/` | 平台适配规则 |
| `references/knowledge/` | 题材知识库 + 写作技能 |
| `references/writing-guides/` | 写作指南（命名等） |

---

## 快速开始

如果你是第一次使用这个系统：

1. **短篇创作**：直接跳到"正文创作执行链"，不需要走完7个阶段
2. **长篇从零开始**：从阶段1（创意）开始，严格按顺序执行
3. **长篇续写**：直接跳到阶段5（正文），但必须先跑记忆包（阶段6的前置步骤）
4. **已有章节润色**：使用 [10] 正文润色功能，不触发完整执行链
