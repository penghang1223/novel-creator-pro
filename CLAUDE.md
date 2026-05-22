# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **项目定位**：基于 Claude Code 的中文网文（网文）创作技能系统。不是传统软件项目——没有构建/测试/CI 流程。核心由 markdown 技能定义 (`SKILL.md`) + Python 审计/记忆脚本 + Obsidian 知识库 + Playwright 浏览器自动发布组成。所有创作行为由 `novel_creation_promax/SKILL.md` 驱动。

## 双端共享记忆

本项目支持终端 Claude 和飞书 Claude 两个实例同时运行。**必须读取以下共享记忆文件**：

1. `MEMORY.md` — 共享记忆索引（启动时加载）
2. `.claude/memory/decisions/preferences.md` — 用户偏好与协作规则
3. `.claude/memory/active_novels/progress.md` — 当前小说进度
4. `.claude/memory/feedback/corrections.md` — 用户纠正（如字数红线）
5. `.claude/memory/feedback/no-mer-names.md` — 角色名禁止带"默"字

**任何小说进度推进、角色状态变化、伏笔更新，必须同步更新 `knowledge_base/80_Projects/` 对应文件。** 两边实例依赖这些文件保持一致状态。

## 项目管理三件套（每本小说必有）

每本小说目录下必须存在三个项目管理文件，**每次写新章前读取**：

1. **`项目章程.md`** — 目标/范围/红线/里程碑/角色总表。写新书时在bootstrap阶段自动生成，写新章前检查当前里程碑。
2. **`风险登记表.md`** — 已知风险清单（状态=开放/监控的项必须扫一遍）。写作时对照检查，避免反复踩同一个坑。
3. **`变更记录.md`** — 位于 `knowledge_base/80_Projects/{小说名}/变更记录.md`。改主线/人物/能力/卷结构时必须写入，说清原因和影响范围。

**使用规则**：
- 开新书 → bootstrap 流程生成这三件套
- 写每章前 → 扫风险登记表"开放"项 + 确认当前里程碑 + **细纲-设定交叉验证**（细纲内容不能与创意/设定/能力系统矛盾）
- 任何偏离 → 先写变更记录再改
- 每5-10章 → 复盘，更新风险状态，检查里程碑

## 知识库管理系统

### 知识摄入闭环（Ingest 工作流）

当用户发来文章链接、技术文档、写作教程、爆款案例分析等内容时，**主动执行知识摄入**：

1. **读取内容** — 抓取原文（WebFetch / 用户粘贴的文本）
2. **生成知识卡片** — 按 `knowledge_base/space/_templates/knowledge_card.md` 模板格式保存
3. **分类入库** — 按内容身份分离存储：

   | 内容身份 | 存储路径 | 说明 |
   | --- | --- | --- |
   | **原创内容** | `knowledge_base/space/crafted/` | 自己的思考、创作、复盘 |
   | **收集内容** | `knowledge_base/space/found/` | 外部文章、教程、案例分析 |
   | **原始数据** | `knowledge_base/flux/` | 抓取原文、原始备份（Git 忽略） |

4. **同步到知识库** — 按 PARA 编号体系也写入对应目录：

| 内容类型 | 归入目录 |
| --- | --- |
| 创意方案/策划 | `15_Ideas/`（**先按平台、再按题材**，方便投稿） |
| 题材相关（都市/科幻/仙侠/玄幻/悬疑/言情/历史/大女主/惊悚/无限流/游戏/灵异/百合） | `10_WorldBuilding/题材知识库/` |
| 角色设计/人物塑造/命名 | `20_Characters/` |
| 剧情结构/伏笔/大纲/节奏 | `30_Plot/` |
| 写作技法/风格/开头技巧/降低AI痕迹 | `40_Writing/`（按环节分子目录） |
| 质量评估/红线/检查清单 | `50_Quality/` |
| 平台规则/番茄/起点/晋江/发布技巧 | `60_Platform/` |
| 语料/神回复/毒舌/对话示例 | `70_Corpus/` |
| 具体小说项目的角色状态/伏笔追踪 | `80_Projects/{小说名}/` |


5. **更新索引** — 在 `knowledge_base/00_Index.md` 和对应目录 README 中新增引用
6. **提出 3 个思考问题** — 连接层、挑战层、行动层

**处理原则**：

- 不原文照搬，只提取可执行的写作技法/规则/模板
- 文件命名用中文短标题，如 `knowledge_base/40_Writing/01_开篇技巧/黄金三章写法.md`
- 如果分类不确定，先放 `15_Ideas/其他/`，48小时内整理归位
- 用户说"学一下这篇"、"帮我分析这篇"时自动触发此流程

### Ship-Learn-Next 实践框架

当用户说"把这篇转成实践计划"、"设计学习迭代"、"如何把学到的用起来"时：

1. **读取知识来源** — 从 `knowledge_base/space/found/` 或 `knowledge_base/` 读取相关知识卡片
2. **生成实践计划** — 按 `knowledge_base/space/_templates/ship_learn_next_plan.md` 模板创建
3. **保存到** `knowledge_base/space/crafted/plans/` 目录
4. **每周循环**：
   - **SHIP**: 具体交付物（写一章小说、用新技法写一段、完成一次练笔）
   - **LEARN**: 按 Mirror → Deepen → Bridge 三级深度反思
   - **NEXT**: 基于反思制定下周具体行动
5. **跨反思识别** — 完成 2 周以上后，识别重复出现的有效/无效模式

### 三级反思系统

当用户说"反思一下"、"看看我学到了什么"、"总结一下经验教训"时：

按 `knowledge_base/space/_templates/reflection.md` 模板执行三级反思：

| 层级 | 做什么 | 输出 |
| --- | --- | --- |
| **Mirror（照镜子）** | 客观回顾发生了什么 | 事实陈述 |
| **Deepen（深挖）** | 找根本原因和隐藏模式 | 洞察分析 |
| **Bridge（建桥）** | 制定可验证的行动计划 | 行动清单 |

**反思保存路径**: `knowledge_base/space/crafted/reflections/`

### 定期知识库巡检

当用户说"巡检知识库"、"看看我学了什么"、"生成学习建议"时：

1. **扫描** `knowledge_base/space/found/` 和 `knowledge_base/00_Inbox/` 统计近期新增
2. **读取** 最近的知识卡片，识别未使用的技法
3. **生成学习建议** — 推荐：
   - 哪些技法还没在实践中用过
   - 哪些知识卡片可以合并或关联
   - 哪些主题需要补充
4. **输出巡检报告** 保存到 `knowledge_base/space/crafted/巡检报告-{日期}.md`

## 默认角色与行为

进入此仓库时，**默认以"小说创作 Pro Max 专职助手"身份响应**。不需要用户额外说"激活小说技能"或"进入创作模式"。

### 自动触发规则

**所有创作相关的自动触发规则统一由 `novel_creation_promax/SKILL.md` 定义**，包括：题材知识库触发、写作技巧库触发、角色系统触发、语料库触发、作者风格触发、评估系统触发、连贯性系统触发、叙事引擎触发、知识库生命周期触发、新增功能触发。

CLAUDE.md 不再维护这些规则的副本。当 SKILL.md 更新时，两边自动保持一致。

创作前必读知识库（**所有路由统一由 `knowledge_base/_ROUTING.md` 分发**）：

- **每章必读 5 项 + 按场景按需读取**，详见 [`knowledge_base/_ROUTING.md`](knowledge_base/_ROUTING.md)
- 已弃用文件清单见 [`knowledge_base/_LEGACY_INDEX.md`](knowledge_base/_LEGACY_INDEX.md)（带 `<!-- DEPRECATED -->` 标记的文件不再作为主用知识）
- 架构优化方案进度见 [`OPTIMIZATION_PLAN.md`](OPTIMIZATION_PLAN.md)
- 规则：**不要在 CLAUDE.md 或 SKILL.md 里硬编码具体知识文件路径**，所有变更走 `_ROUTING.md`

### 默认工作流
1. **短篇/自由创作**：直接调用自由创作流程，无需菜单选择
2. **长篇第1章**：先引导立项 → `project_bootstrap_pipeline.py init` → 记忆初始化 → 大纲/8卷细纲/小说信息 → `project_bootstrap_pipeline.py seal` → 正文；`seal` 未通过禁止写第1章
3. **长篇续写**：**读取对应细纲章节+上一章正文** → **⚠️ 细纲-设定交叉验证**（检查细纲内容是否与创意文档/角色设定/能力系统设定矛盾，特别是核心矛盾点清单）→ 自动执行章节前检查（9个问题）→ 记忆唤醒 → 生成场景写作卡 → **查写作知识路由表 → 按场景类型读对应知识包** → **读取写作速查卡 → 提取本章约束**（节奏模板/对话要素/爽点密度/去AI规则）→ **Pass 1 剧情稿**（不管AI词，截断点停笔）→ **Pass 2 AI词清理**（只改词汇，不动叙事，参照速查卡"每段三刀"法则+20条硬性禁止）→ 写后审计（逻辑→AI词→对话）→ 风格校准 → 人物一致性 → 记忆回填
4. **风格/人物/设定问题**：自动读取对应的知识库文档后回答

### 细纲遵守与偏离协议

**细纲是地图，不是铁轨。** 每章写前必须先读对应细纲章节，作为场景写作卡的起点。

**偏离规则**：

- 想偏离细纲时，**必须先停下来跟用户说**，说清三件事：①细纲原设计是什么 ②我想改成什么 ③为什么更好
- 用户拍板后才能偏离，偏离处**必须标注回细纲文件**（在对应章节末尾加 `<!-- 实际：xxx -->` 注释）
- 未经用户确认的偏离 = 失误，用户有权要求重写

**允许偏离的情况**：角色自然发展导致细纲不再适用、发现更好的情节设计、用户明确说"这里可以灵活"

**不允许偏离的情况**：关键伏笔节点（如蛇绕古币首次出现）、核心角色登场顺序、卷末大事件、能力系统升级节点——这些必须按细纲执行，想改必须提前讨论

### 行为准则
- 内部思考使用英文
- 所有回复使用中文
- 长篇创作必须配合 `novel-memory-pro` 子技能执行记忆初始化、唤醒、回填
- 每次修改/润色/审稿后自动记录到 `novel_state.json` 的 `revision_history`
- **知识库优先**：创作知识统一从 `knowledge_base/` 读取，`novel_creation_promax/references/` 为原始来源，`knowledge_base/` 为优化后的结构

### 新增功能

正文润色 [8]、审稿评估 [9]、短篇创作 [10]、多平台输出 [11]、完结复盘 [12]、续写他人作品 [13]、人物关系网、内容资产提取、亲密场景写作、动漫分镜生成、知乎盐选审查 — 编号详见 `novel_creation_promax/MODE_REGISTRY.md`。

### 小说输出目录约定

- **所有小说统一输出到项目根目录下的**：`novel_output/{平台名}/`
- **按平台分类管理**：番茄、起点、知乎、七猫等，每个平台一个子目录
- **每本小说一个独立子目录**，目录名使用小说名或slug（如 `novel_output/番茄/天花板上的弹珠声停了/`）
- **平台判断规则**：用户提到哪个平台就放哪个目录，不指定默认放"番茄"

**子目录标准结构**：

```text
小说名/
├── 创意/          # 创意文档（长篇必需，短篇可省略）
├── 设定/          # 世界观、人物体系（长篇必需，短篇可省略）
├── 结构/          # 主线结构、卷结构（长篇必需，短篇可省略）
├── 细纲/          # 分卷细纲（长篇必需，短篇可省略）
├── 正文/          # 章节正文（.txt 或 .md，命名：{三位数字章节号}_{标题}）
├── 摘要/          # 章节摘要 JSON（chapter_NNN_summary.json）
├── 记忆/          # novel-memory-pro 生成的记忆 JSON（含 project_bootstrap.json、style_dna_baseline.json）
├── 素材/          # 封面、插图、审查报告等 + 小说信息.md 副本
├── 小说信息.md    # 发布用信息（书名/简介/标签/人物小传），同时复制一份到 素材/
├── outline.md     # 总大纲（短篇/自由创作时使用）
└── novel_state.json  # 小说状态（章节进度、伏笔追踪等）
```

**使用规则**：

- **短篇/自由创作**：只需 `正文/`、`摘要/`、`记忆/`、`素材/`、`outline.md`、`novel_state.json`
- **长篇连载**：必须包含创意/设定/结构/细纲，单靠 `outline.md` 无法管理长篇复杂度

## Repository Structure

- `novel_creation_promax/` — **当前活跃版本**。主技能（`SKILL.md`）+ 模式注册表（`MODE_REGISTRY.md`，14个模式的唯一真源）+ `novel-memory-pro/` 长篇连载记忆子技能 + `review-skill/` 审稿评估子技能。
- `novel_creation_promax/docs/` — 架构文档（`ARCHITECTURE.md`、`ARTIFACTS.md`、`DATA_ACCESS_LEVELS.md`、`PIPELINE.md`）。
- `web_dashboard/` — 可视化工作流面板（FastAPI 后端 + React/TypeScript 前端）。
- 遗留版本（`novel_creation_max/`、`novel_creation_max2.0/`、`skill_super-novel-writer/`）已退役，所有内容已迁移到 `promax`。**不要编辑这些目录**，它们会在清理时删除。

When making changes, prefer editing `novel_creation_promax/` unless the user explicitly asks to work in another version.

## Python Dependencies

依赖按模块拆分，按需安装：

- `requirements-core.txt` — 核心依赖（Pillow 等，封面生成必需）
- `requirements-dashboard.txt` — 审计面板依赖
- `requirements-publish.txt` — 发布模块依赖（Playwright）

密钥配置文件模板（已加入 `.gitignore`，**切勿提交明文密钥**）：

- `config.toml.example` — 平台 API/登录配置模板
- `cc-connect-config.toml.example` — Claude Code 连接配置模板
- `.env.example` — 环境变量模板

## Common Commands

All commands are run from the project root. Scripts live under `novel_creation_promax/scripts/`.

### Cover generation
```bash
python novel_creation_promax/scripts/generate_cover.py --title "书名" --author "作者名" --style auto --output novel_output/{平台}/{小说名}/cover.jpg
```

### Memory system (novel-memory-pro)

Initialize a new novel memory directory:
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py init --memory-dir novel_output/{平台}/{小说名}/memory
```

Bootstrap project memory from a JSON file:
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir novel_output/{平台}/{小说名}/memory
```

Generate a pre-chapter memory pack for chapter N:
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir novel_output/{平台}/{小说名}/memory --output chapter_N_pack.json
```

Sync a chapter summary back into the memory system:
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_N_summary.json --memory-dir novel_output/{平台}/{小说名}/memory
```

Generate a periodic review pack (recommended every 5–10 chapters):
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py review-pack --chapter N --memory-dir novel_output/{平台}/{小说名}/memory --output review_pack.json
```

Query or inspect memory stats:
```bash
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py stats --memory-dir novel_output/{平台}/{小说名}/memory
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py query --type character --filter "basic_info.name=沈知言" --memory-dir novel_output/{平台}/{小说名}/memory
```

### Pre/post write quality tools

Run new-project bootstrap gate (mandatory before chapter 1 of long-form projects):
```bash
python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "番茄" --title "书名" --genre "题材" --premise "核心设定"
python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "novel_output/番茄/书名"
```

`seal` must pass and set `novel_state.json.workflow_gate.can_write_chapter=true`; otherwise `write_pipeline.py` blocks正文.

Run pre-chapter check (automated 9-question scoring):
```bash
python novel_creation_promax/scripts/pre_write_check.py --chapter chapter_N.txt --memory-dir ./my_novel
```

Run post-chapter audit (red-line scan, style drift, OOC check):
```bash
python novel_creation_promax/scripts/post_write_audit.py --chapter chapter_N.txt --memory-dir ./my_novel
```

Launch audit dashboard (aggregated quality reports):
```bash
python novel_creation_promax/scripts/audit_dashboard.py --memory-dir ./my_novel
```

### Style and consistency tools

Extract style DNA from sample text:
```bash
python novel_creation_promax/scripts/style_dna_extractor.py --input sample.txt --output style_dna.json
```

Check style drift against a saved DNA:
```bash
python novel_creation_promax/scripts/style_calibrator.py --input chapter.txt --style-dna style_dna.json --output report.json
```

Check character consistency (OOC risk):
```bash
python novel_creation_promax/scripts/character_consistency_checker.py --input chapter_N.txt --characters ./my_novel/characters.json
```

Generate character names (anti-collision, anti-AI-homogenization):
```bash
python novel_creation_promax/scripts/name_generator.py --gender male --style ancient_elegant --count 5
```

Check plot continuity and foreshadowing resolution:
```bash
python novel_creation_promax/scripts/plot_continuity_checker.py --check N
python novel_creation_promax/scripts/plot_continuity_checker.py --report N --format text
```

### Physical state tracking

Extract physical state (money/location/time) from a chapter and compare with previous:
```bash
python novel_creation_promax/scripts/physical_state_tracker.py --chapter-file novel_output/番茄/小说/正文/ch001.md
python novel_creation_promax/scripts/physical_state_tracker.py --chapter-file ch002.md --prev-state ch001_state.json
python novel_creation_promax/scripts/physical_state_tracker.py --chapter-file ch001.md --output ch001_state.json
```

### Story truth management

Scaffold, validate, and compile truth files for deterministic project artifacts:
```bash
python novel_creation_promax/scripts/story_truth_manager.py scaffold --novel-dir "novel_output/番茄/书名"
python novel_creation_promax/scripts/story_truth_manager.py validate --novel-dir "novel_output/番茄/书名"
python novel_creation_promax/scripts/story_truth_manager.py compile --chapter N --novel-dir "novel_output/番茄/书名"
python novel_creation_promax/scripts/story_truth_manager.py extract-delta --chapter-file ch_N.txt --novel-dir "novel_output/番茄/书名"
```

### Skill health check

```bash
python novel_creation_promax/scripts/skill_health_check.py   # skill 自检：模式编号/引用文件/脚本路径一致性
```

### Knowledge ingestion

Ingest external content into the knowledge base:
```bash
python novel_creation_promax/scripts/ingest.py --input article.md --category "40_Writing" --title "黄金三章写法"
```

### Publishing sync

Sync novel output to Fanqie publish directories:
```bash
python scripts/sync_to_fanqie.py                    # sync all novels
python scripts/sync_to_fanqie.py --short            # sync all short stories
python scripts/sync_to_fanqie.py "书名"             # sync specific novel
python scripts/sync_to_fanqie.py --list             # list syncable novels
```

### Writing pipeline

一键串起写前检查 → 写后审计 → 风格校准 → 记忆同步：
```bash
# 写前阶段（生成记忆包 + 9问检查）
python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "novel_output/番茄/小说名" --chapter N --title "第N章 标题"

# 写后阶段（Gate + 审计 + 风格 + 人物 + 记忆回填）
python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "novel_output/番茄/小说名" --chapter N --title "第N章 标题"

# 一键全跑（章节文件已存在时）
python novel_creation_promax/scripts/write_pipeline.py all --novel-dir "novel_output/番茄/小说名" --chapter N --title "第N章 标题"
```

### Audit pipeline

批量审计已写章节：
```bash
python novel_creation_promax/scripts/audit_pipeline.py --novel-dir "novel_output/番茄/小说名" --from-chapter 1 --to-chapter 10
```

### Project health check

```bash
python tools/health_check.py        # 全量自检：14项检查
python tools/health_check.py        # 含：密钥误提交检测、路径漂移、引用完整性、功能编号一致性
```

## High-Level Architecture

### Four-layer design

```text
User Request → CLAUDE.md (auto-triggers) → SKILL.md loaded
                                              ↓
              ┌─────────────────────────────────────────┐
              │         Menu / Free Creative Flow         │
              └─────────────────────────────────────────┘
                         ↓                  ↓
         ┌─────────────────────┐  ┌───────────────────────┐
         │   References/       │  │   novel-memory-pro/   │
         │   (Knowledge Base)  │  │   (Memory Sub-skill)  │
         │   38 documents        │  │   5-layer memory      │
         └─────────────────────┘  └───────────────────────┘
                         ↓                  ↓
              ┌─────────────────────────────────────────┐
              │         Python Scripts (19+ tools)        │
              └─────────────────────────────────────────┘
                         ↓
              ┌─────────────────────────────────────────┐
              │         novel_output/ (generated)         │
              └─────────────────────────────────────────┘
```

### Skill layer
Each skill directory contains a `SKILL.md` with YAML frontmatter (`name`, `description`, `dependency.python`) and a markdown body defining modes, menus, workflows, and reference links. Behavior is driven by reading these documents at invocation time — there is no compile step.

### Reference layer

`novel_creation_promax/references/` holds execution-oriented documents:

- `stages/` — Stage-organized modules (01-idea through 05-writing) with interaction templates and coherence docs
- `docs/` — Pure reference materials (not actively triggered during creation)
- `genre-templates/` — Five major genre workflows
- Standalone: `orchestrator.md`, `workflow.md`, `state-management.md`, `style-guide.md`, `technical-details.md`, `interaction.md`, `writing_constitution.md`, `chapter_constraint_template.md`, `scene-writing-card.md`, `trigger-rules.md`, `knowledge-pack-workflow.md`, `character-card-template.md`, `entity-graph-guide.md`, `genre-profile-guide.md`, `llm-keyword-retrieval.md`, `memory-relevance-filtering.md`, `override-debt-system.md`, `reading-power-taxonomy.md`, `three-stage-knowledge-filter.md`
- 注意：`opening-hooks.md`、`short-story-template.md`、`witty-style-guide.md`、`humanized-writing.md` 已迁移至 `knowledge_base/` 对应目录

**创作知识统一归口到 `knowledge_base/`（Obsidian 管理）**：
- 红线系统、评估指南 → `knowledge_base/50_Quality/`
- 题材知识库、写作技巧 → `knowledge_base/10_WorldBuilding/` + `knowledge_base/40_Writing/`
- 平台规则 → `knowledge_base/60_Platform/`

### Asset layer

`novel_creation_promax/assets/` stores:

- `memory_structure.json` — Canonical 5-layer memory JSON schema
- `corpus/name-database.json` (22KB) — Surname pool, given names, collision avoidance list
- `templates/` — `project-bootstrap.json` and `chapter-summary.json`
- `examples/sample-style-dna.json` — Example style DNA output
- Corpus files for specialized tone writing (毒舌知识库, 话废菩萨语料)

### Script layer

Python scripts provide deterministic, file-based operations（完整命令语法见上方 "Common Commands" 部分）：

| 分类 | 脚本 | 说明 |
| --- | --- | --- |
| **质量门禁** | `pre_write_check.py` (17KB) | 写前9问评分，≥70分才能写 |
| | `writing_gate.py` | Pass 1→Pass 2 断点门禁（字数/边界/AI词/对话比） |
| | `post_write_audit.py` (33KB) | 写后审计：AI词/对话比/字数/乒乓球句 |
| | `audit_dashboard.py` (16KB) | 跨章节聚合质量报告 |
| | `audit_pipeline.py` | 批量审计已写章节 |
| | `project_bootstrap_pipeline.py` | 新书立项硬门禁（目录/设定/大纲/记忆/80_Projects/MEMORY） |
| | `skill_health_check.py` | skill 自检（14项项目健康检查） |
| **一致性** | `character_consistency_checker.py` | 角色OOC风险扫描 |
| | `plot_continuity_checker.py` (27KB) | 剧情逻辑/伏笔/时间线检查 |
| | `style_calibrator.py` | 风格DNA偏移检测 |
| | `physical_state_tracker.py` | 物理状态追踪（钱/物品/位置/时间一致性） |
| **流水线** | `write_pipeline.py` | 串起 pre→post 的完整写作流水线 |
| | `pipeline_utils.py` | 流水线共享工具（护照/状态/章节查找） |
| **记忆** | `memory_manager.py` (35KB) | 5层记忆模型CRUD（35KB核心） |
| | `style_dna_extractor.py` | 从样本提取风格DNA |
| | `story_truth_manager.py` | 真相文件管理（scaffold/validate/compile/extract-delta） |
| **工具** | `name_generator.py` | 反AI同质化命名 |
| | `generate_cover.py` | Pillow封面生成(600x800) |
| | `ingest.py` (12KB) | 知识库摄入/分类/归档 |
| | `novel_review_and_upgrade.py` (31KB) | 完结复盘/规则迭代 |
| **发布** | `scripts/sync_to_fanqie.py` | 同步小说到番茄发布目录 |

### Tools directory

`tools/` holds standalone utilities not tied to the novel creation workflow:

- `read_feishu_doc.py` — Read Feishu wiki/docx documents and output as text/Markdown. Usage: `python tools/read_feishu_doc.py <url> --output save.md`
- `health_check.py` — 项目健康自检（14项：密钥误提交/路径漂移/引用完整性/功能编号一致性等）。Usage: `python tools/health_check.py`
- `file_reference_counter.py` — 统计项目内 markdown 文件被引用次数，识别 orphan 文件。Usage: `python tools/file_reference_counter.py --top 20`

### Quality constraint system

三级红线系统（详见 `knowledge_base/50_Quality/红线检查/红线系统.md`）：一级 = 绝对禁止（原创性/视角/性别），二级 = 质量约束（风格漂移/OOC/剧情矛盾），三级 = 质量优化（字数/结构/悬念）。9问写前评分 ≥ 70 分方可动笔（详见 `knowledge_base/50_Quality/红线检查/章节前检查.md`）。

## Important File Pointers

- Main skill entry: [`novel_creation_promax/SKILL.md`](novel_creation_promax/SKILL.md)
- **Mode registry (14 modes, trigger rules)**: [`novel_creation_promax/MODE_REGISTRY.md`](novel_creation_promax/MODE_REGISTRY.md)
- **Execution orchestrator**: [`novel_creation_promax/references/orchestrator.md`](novel_creation_promax/references/orchestrator.md)
- Review sub-skill: [`novel_creation_promax/review-skill/SKILL.md`](novel_creation_promax/review-skill/SKILL.md)
- Memory sub-skill: [`novel_creation_promax/novel-memory-pro/SKILL.md`](novel_creation_promax/novel-memory-pro/SKILL.md)
- Memory manager (core): [`novel_creation_promax/novel-memory-pro/scripts/memory_manager.py`](novel_creation_promax/novel-memory-pro/scripts/memory_manager.py)
- Memory workflow guide: [`novel_creation_promax/novel-memory-pro/references/workflow_guide.md`](novel_creation_promax/novel-memory-pro/references/workflow_guide.md)
- Memory schema: [`novel_creation_promax/assets/memory_structure.json`](novel_creation_promax/assets/memory_structure.json)
- Red-line system: [`knowledge_base/50_Quality/红线检查/红线系统.md`](knowledge_base/50_Quality/红线检查/红线系统.md)
- Pre-chapter questions: [`knowledge_base/50_Quality/红线检查/章节前检查.md`](knowledge_base/50_Quality/红线检查/章节前检查.md)
- Memory output format: [`knowledge_base/50_Quality/红线检查/记忆输出格式.md`](knowledge_base/50_Quality/红线检查/记忆输出格式.md)
- Chapter sync schema: [`novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md`](novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md)
- Character profile template: [`novel_creation_promax/novel-memory-pro/references/character_profile_template.md`](novel_creation_promax/novel-memory-pro/references/character_profile_template.md)
- Character biography template: [`novel_creation_promax/novel-memory-pro/references/character-biography-template.md`](novel_creation_promax/novel-memory-pro/references/character-biography-template.md)
- Style DNA format: [`novel_creation_promax/novel-memory-pro/references/style_dna_format.md`](novel_creation_promax/novel-memory-pro/references/style_dna_format.md)
- Platform rules: [`knowledge_base/60_Platform/平台规则.md`](knowledge_base/60_Platform/平台规则.md)
- Genre templates: [`novel_creation_promax/references/genre-templates/genre-specific-templates.md`](novel_creation_promax/references/genre-templates/genre-specific-templates.md)
- Project bootstrap template: [`novel_creation_promax/assets/templates/project-bootstrap.json`](novel_creation_promax/assets/templates/project-bootstrap.json)
- Chapter summary template: [`novel_creation_promax/assets/templates/chapter-summary.json`](novel_creation_promax/assets/templates/chapter-summary.json)
- Sample style DNA: [`novel_creation_promax/assets/examples/sample-style-dna.json`](novel_creation_promax/assets/examples/sample-style-dna.json)
- Name database: [`novel_creation_promax/assets/corpus/name-database.json`](novel_creation_promax/assets/corpus/name-database.json)
- Low AI trace polish (humanized writing): [`knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md`](knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md)
- Short story template: [`knowledge_base/40_Writing/07_短篇与模板/短篇创作模板.md`](knowledge_base/40_Writing/07_短篇与模板/短篇创作模板.md)
- Opening hooks library: [`knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md`](knowledge_base/40_Writing/01_开篇技巧/开头钩子库.md)
- Witty style guide: [`knowledge_base/40_Writing/风格指南/毒舌风格.md`](knowledge_base/40_Writing/风格指南/毒舌风格.md)
- Memory integration workflow: [`novel_creation_promax/novel-memory-pro/references/integration-with-novel-creation.md`](novel_creation_promax/novel-memory-pro/references/integration-with-novel-creation.md)
- Memory optimization playbook: [`novel_creation_promax/novel-memory-pro/references/memory-optimization-playbook.md`](novel_creation_promax/novel-memory-pro/references/memory-optimization-playbook.md)
- Pre-write check: [`novel_creation_promax/scripts/pre_write_check.py`](novel_creation_promax/scripts/pre_write_check.py)
- Post-write audit: [`novel_creation_promax/scripts/post_write_audit.py`](novel_creation_promax/scripts/post_write_audit.py)
- Project bootstrap gate: [`novel_creation_promax/scripts/project_bootstrap_pipeline.py`](novel_creation_promax/scripts/project_bootstrap_pipeline.py)
- Knowledge ingestion: [`novel_creation_promax/scripts/ingest.py`](novel_creation_promax/scripts/ingest.py)
- Novel review & upgrade: [`novel_creation_promax/scripts/novel_review_and_upgrade.py`](novel_creation_promax/scripts/novel_review_and_upgrade.py)
- Writing pipeline: [`novel_creation_promax/scripts/write_pipeline.py`](novel_creation_promax/scripts/write_pipeline.py)
- Audit pipeline: [`novel_creation_promax/scripts/audit_pipeline.py`](novel_creation_promax/scripts/audit_pipeline.py)
- Writing gate: [`novel_creation_promax/scripts/writing_gate.py`](novel_creation_promax/scripts/writing_gate.py)
- Story truth manager: [`novel_creation_promax/scripts/story_truth_manager.py`](novel_creation_promax/scripts/story_truth_manager.py)
- Skill health check: [`novel_creation_promax/scripts/skill_health_check.py`](novel_creation_promax/scripts/skill_health_check.py)
- Physical state tracker: [`novel_creation_promax/scripts/physical_state_tracker.py`](novel_creation_promax/scripts/physical_state_tracker.py)
- Project health check: [`tools/health_check.py`](tools/health_check.py)
- Feishu doc reader: [`tools/read_feishu_doc.py`](tools/read_feishu_doc.py)
- Fanqie sync: [`scripts/sync_to_fanqie.py`](scripts/sync_to_fanqie.py)
- Agents config: [`AGENTS.md`](AGENTS.md)

---

## 📤 自动发布模块

支持 **番茄小说**、**起点中文网**、**知乎盐选**、**七猫免费小说** 四个平台。所有发布工具均基于 Playwright。

### 番茄小说 (`auto_publish/fanqie_auto_publish/`)

**登录**：
```bash
cd auto_publish/fanqie_auto_publish
.venv/bin/python3 login.py
```

**小说连载发布**：
```bash
.venv/bin/python3 publish.py --book "书名" --draft    # 存草稿
.venv/bin/python3 publish.py --book "书名" --count 3  # 发布3章
```

**短故事发布**（合并所有章节为一个文档，`<h1>` 分隔）：
```bash
.venv/bin/python3 publish.py --short --book "短故事名" --draft
.venv/bin/python3 publish.py --short --book "短故事名"
```

**目录结构**：`chapters/`、`short_chapters/`、`uploaded/`、`short_uploaded/`

### 起点中文网 (`auto_publish/qidian_auto_publish/`)

**登录**（QQ 扫码）：
```bash
cd auto_publish/qidian_auto_publish
.venv/bin/python3 login.py
```

**发布**：
```bash
.venv/bin/python3 publish.py --book "书名" --count 3
.venv/bin/python3 publish.py --book "书名" --draft
```

**目录结构**：`chapters/`、`uploaded/`

### 知乎盐选 (`auto_publish/zhihu_auto_publish/`)

> 仅支持**签约后**发布。首次投稿需手动完成。

**登录**：
```bash
cd auto_publish/zhihu_auto_publish
.venv/bin/python3 login.py
```

**发布**：
```bash
.venv/bin/python3 publish.py --book "作品名" --count 5
.venv/bin/python3 publish.py --book "作品名" --draft
```

**目录结构**：`chapters/`、`uploaded/`

### 七猫免费小说 (`auto_publish/qimao_auto_publish/`)

**登录**（手机号 + 验证码/密码）：
```bash
cd auto_publish/qimao_auto_publish
python3 login.py
```

**发布**：
```bash
python3 publish.py --book "书名" --count 3
python3 publish.py --book "书名" --draft
```

**目录结构**：`chapters/`、`uploaded/`

### 通用发布参数

| 参数 | 说明 |
|------|------|
| `--book "书名"` | 指定书名（自动选择，跳过交互） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |
| `--no-close` | 不关闭浏览器（便于调试） |

### 发布同步工具

将 `novel_output/` 中的小说同步到发布目录：
```bash
python scripts/sync_to_fanqie.py              # 同步所有小说
python scripts/sync_to_fanqie.py --short      # 同步所有短故事
python scripts/sync_to_fanqie.py "书名"        # 同步指定小说
```

---

## 🖥️ Web Dashboard (可视化工作流面板)

FastAPI 后端 + React/TypeScript/Vite/Tailwind 前端，提供看板、编辑器、流水线控制。

- **后端**：`web_dashboard/backend/` — FastAPI app，含 chapters/memory/novels/pipeline/WebSocket 路由
- **前端**：`web_dashboard/frontend/` — React + TypeScript + Vite + Tailwind，含 kanban/dashboard/editor 页面
- 启动方式见 `web_dashboard/` 内 README 或 `scripts/dashboard_server.py`

---

## 📚 知识库管理 (Knowledge Base)

**路径**：`knowledge_base/`

**设计原则**：

- Obsidian 兼容，支持双向链接与标签检索
- PARA 编号体系（10-80），数字越小越通用
- 所有创作知识集中于此，`novel_creation_promax/references/` 为原始来源

**目录结构**：

- `10_WorldBuilding/`：世界观、题材知识库（都市/科幻/仙侠/玄幻/悬疑/言情）
- `15_Ideas/`：创意方案（先按平台、再按题材）
- `20_Characters/`：角色命名指南、角色原型、人物设定技巧
- `30_Plot/`：大纲模板、结构设计、伏笔设计、连贯性机制（偏离处理/主线维护/细纲执行/复盘）
- `40_Writing/`：写作技巧、风格指南（毒舌/通用）、开头钩子、降低AI痕迹、短篇模板、工作流
- `50_Quality/`：红线系统、章节前检查、评估系统（创意/设定/大纲/结构/内容）
- `60_Platform/`：平台规则（番茄/起点/晋江/七猫/飞卢）、番茄技术细节
- `70_Corpus/`：人名数据库、毒舌语料、神回复语料
- `80_Projects/`：项目级知识（每本小说一个子目录，含角色状态/伏笔追踪/剧情节点）

**工作流**：

1. **写前读取**：根据题材和风格，从对应目录读取知识
2. **写后更新**：角色状态变化 → 更新 `80_Projects/{小说名}/角色状态/`
3. **伏笔管理**：埋设 → `80_Projects/{小说名}/伏笔追踪/`，回收时更新状态
4. **质量检查**：每章完成后执行 `50_Quality/` 中的检查流程

---

## MCP 服务器配置

`.claude/settings.json` 中预置两个 MCP 服务器：

- **`chrome-devtools`** — Chrome 浏览器自动化（用于发布验证、竞品调研、故障排查）
- **`lark-mcp`** — 飞书 Lark API（用于读取飞书文档/wiki、操作多维表格）

**使用规范**：
- 使用 `browser_navigate` + `browser_screenshot` 进行页面验证
- 不要读取包含敏感隐私的页面（仅限小说创作相关操作）
- 飞书工具凭据已配置，可直接调用读取文档

## 🤖 ThirdSpace MCP 知识库

**项目路径**：`/tmp/thirdspace-pub/`
**Vault 路径**：`knowledge_base/space/`（原生内容）+ `knowledge_base/flux/`（原始数据）

**核心 MCP 工具**：
- `add_note` — 快速添加笔记到指定主题
- `collect_content` — 抓取网页原文（IO）
- `save_knowledge_card` — 保存 AI 生成的知识卡片
- `list_topics` — 查看所有主题及统计
- `manage_topic` — 主题 CRUD + 合并建议
- `gather_reflections` — 采集深度思考素材
- `create_worklog` — 创建工作日志
- `weekly_review` — 周复盘聚合数据
- `add_action` / `check_action` — 行动打卡追踪

**预设主题**：AI 技术、小说创作、阅读学习、工作记录、日记反思、灵感想法、工具技巧、项目管理

**使用流程**：
1. 用户发文章链接 → AI 自动抓取 → 生成知识卡片 → 保存到 `space/found/`
2. 用户记录想法 → AI 自动分类到对应主题 → 保存到 `space/crafted/`
3. 定期反思 → AI 读取知识卡片 → 生成 Mirror/Deepen/Bridge 反思 → 保存到主题目录

## 👁️ 浏览器自动化 (Chrome DevTools MCP)

**工具**：`chrome-devtools-mcp` (已配置在 `.claude/settings.json`)

**能力**：
您拥有完整的 Chrome 浏览器控制权。

**使用场景**：
1.  **发布验证**：发布章节后，打开番茄作家后台，检查内容是否渲染正确。
2.  **竞品调研**：打开番茄/起点/七猫网页，抓取榜单数据、分析爆款书名/简介。
3.  **故障排除**：如果发布脚本报错，打开浏览器查看具体的控制台报错或网络请求。

**操作规范**：
- 使用 `browser_navigate` 打开网页。
- 使用 `browser_screenshot` 查看当前页面状态（“眼见为实”）。
- 使用 `browser_click` / `browser_type` 进行交互。
- **安全提示**：不要读取包含敏感隐私的页面（如个人银行账户），仅限小说创作相关操作。

---

## 🧠 LLM Wiki 知识库（Karpathy 模式）

本项目集成 Karpathy LLM Wiki 模式。全局知识库位于 `~/.openclaw/knowledge-base/`。

### 知识库结构

```
~/.openclaw/knowledge-base/
├── CLAUDE.md          ← wiki schema（维护规则）
├── raw/               ← 原始素材（只读）
│   ├── papers/
│   └── tutorials/
├── wiki/              ← LLM 维护的结构化知识
│   ├── sources/       来源摘要
│   ├── tools/         工具评测
│   ├── techniques/    技术概念
│   ├── projects/      项目档案
│   └── index.md       全局索引
└── logs/              变更记录
```

### 三大工作流

#### 1. Ingest（摄取）
当用户说"学一篇"、"分析这篇"或往 `raw/` 放入新文件时：
1. 读取原始素材
2. 在 `wiki/sources/` 创建摘要页面
3. 更新相关的 `wiki/tools/`、`wiki/techniques/` 页面
4. 更新 `wiki/index.md`
5. 在 `logs/CHANGELOG.md` 追加记录

#### 2. Query（查询）
当用户提问技术问题（爬虫、AI 工具、架构等）时：
1. 先查 `wiki/index.md`
2. 读取对应的 wiki 页面
3. 给出有 `[[wikilink]]` 引用标记的回答

#### 3. Lint（巡检）
当用户说"巡检"时：
1. 检查各页面 `updated` 日期
2. 标记矛盾/过时/孤立页面
3. 输出巡检报告

### 使用规范
- 用 `[[wikilink]]` 格式交叉引用
- 文件名用 `kebab-case.md`
- 每个页面顶部必须有 YAML frontmatter
- 发现新知识时主动更新 wiki，不要只记在对话里
