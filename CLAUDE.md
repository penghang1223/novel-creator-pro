# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 双端共享记忆

本项目支持终端 Claude 和飞书 Claude 两个实例同时运行。**必须读取以下共享记忆文件**：

1. `MEMORY.md` — 共享记忆索引（启动时加载，5 条 feedback 记录）
2. `feedback_no_skip_workflow.md` — 接新任务必须走完整10步流程
3. `feedback_no_code_blocks.md` — 正文禁止使用 ```text 代码块
4. `feedback_autonomous_publish.md` — 发布工作流反馈记录
5. `feedback_optimization_workflow.md` — 优化流程反馈
6. `feedback_word_count.md` — 每章2800-3200字硬约束

**任何小说进度推进、角色状态变化、伏笔更新，必须同步更新 `knowledge_base/80_Projects/` 对应文件。** 两边实例依赖这些文件保持一致状态。

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
   | 题材相关（都市/科幻/仙侠/玄幻/悬疑/言情/历史/大女主/惊悚/无限流/游戏/灵异/百合） | `10_WorldBuilding/题材知识库/` |
   | 角色设计/人物塑造/命名 | `20_Characters/` |
   | 剧情结构/伏笔/大纲/节奏 | `30_Plot/` |
   | 写作技法/风格/开头技巧/降低AI痕迹 | `40_Writing/` |
   | 质量评估/红线/检查清单 | `50_Quality/` |
   | 平台规则/番茄/起点/晋江/发布技巧 | `60_Platform/` |
   | 语料/神回复/毒舌/对话示例 | `70_Corpus/` |
   | 具体小说项目的角色状态/伏笔追踪 | `80_Projects/{小说名}/` |

5. **更新索引** — 在 `knowledge_base/00_Index.md` 和对应目录 README 中新增引用
6. **提出 3 个思考问题** — 连接层、挑战层、行动层

**处理原则**：

- 不原文照搬，只提取可执行的写作技法/规则/模板
- 文件命名用中文短标题，如 `knowledge_base/40_Writing/黄金三章写法.md`
- 如果分类不确定，先放 `00_Inbox/` 待用户确认
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

创作前必读知识库（直接从 `knowledge_base/` 读取）：

- 红线系统 → `knowledge_base/50_Quality/红线检查/红线系统.md`
- 章节前检查 → `knowledge_base/50_Quality/红线检查/章节前检查.md`
- 降低AI痕迹 → `knowledge_base/40_Writing/降低AI痕迹.md`
- 爽点设计 → `knowledge_base/40_Writing/爽点设计.md`

### 默认工作流
1. **短篇/自由创作**：直接调用自由创作流程，无需菜单选择
2. **长篇第1章**：先引导立项 → 记忆初始化 → 大纲 → 正文
3. **长篇续写**：自动执行章节前检查（9个问题）→ 记忆唤醒 → 写作 → 记忆回填
4. **风格/人物/设定问题**：自动读取对应的知识库文档后回答

### 行为准则
- 内部思考使用英文
- 所有回复使用中文
- 长篇创作必须配合 `novel-memory-pro` 子技能执行记忆初始化、唤醒、回填
- 每次修改/润色/审稿后自动记录到 `novel_state.json` 的 `revision_history`
- **知识库优先**：创作知识统一从 `knowledge_base/` 读取，`novel_creation_promax/references/` 为原始来源，`knowledge_base/` 为优化后的结构

### 新增功能

正文润色 [10]、审稿评估 [11]、短篇创作 [12]、续写他人作品、多平台输出、人物关系网、内容资产提取、亲密场景写作、动漫分镜生成、知乎盐选审查 — 详见 `novel_creation_promax/SKILL.md` 对应章节。

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
├── 记忆/          # novel-memory-pro 生成的记忆 JSON
├── 素材/          # 封面、插图、审查报告等媒体文件
├── outline.md     # 总大纲（短篇/自由创作时使用）
└── novel_state.json  # 小说状态（章节进度、伏笔追踪等）
```

**使用规则**：

- **短篇/自由创作**：只需 `正文/`、`摘要/`、`记忆/`、`素材/`、`outline.md`、`novel_state.json`
- **长篇连载**：必须包含创意/设定/结构/细纲，单靠 `outline.md` 无法管理长篇复杂度

## Repository Overview

This is a Claude Code skill system for Chinese web novel (网文) writing. It is not a traditional software project with builds or test suites. The skill is defined by markdown documents (`SKILL.md`) and supported by Python scripts for deterministic operations.

- `novel_creation_promax/` — **Current active version**. The main skill (`SKILL.md`) plus a dedicated `novel-memory-pro/` sub-skill for long-form serialization memory management.
- Legacy versions (`novel_creation_max/`, `novel_creation_max2.0/`, `skill_super-novel-writer/`) are retired and being removed from the repository. All content has been migrated to `promax`.

When making changes, prefer editing `novel_creation_promax/` unless the user explicitly asks to work in another version.

## Python Dependencies

The only external Python dependency is `Pillow>=9.0.0` (used for cover generation). A `.venv/` directory exists at the project root for isolation.

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
python novel_creation_promax/scripts/character_consistency_checker.py
```

Generate character names (anti-collision, anti-AI-homogenization):
```bash
python novel_creation_promax/scripts/name_generator.py --gender male --style ancient_elegant --count 5
```

Check plot continuity and foreshadowing resolution:
```bash
python novel_creation_promax/scripts/plot_continuity_checker.py --check N
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
              │         Python Scripts (7 tools)          │
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
- `writing-guides/` — Naming guide
- Standalone: `orchestrator.md`, `workflow.md`, `state-management.md`, `style-guide.md`, `technical-details.md`, `opening-hooks.md`, `short-story-template.md`, `witty-style-guide.md`, `humanized-writing.md`, `interaction.md`

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

Python scripts provide deterministic, file-based operations:

- `memory_manager.py` (35KB) — Core CRUD for 5-layer memory model (style_dna, character, plot, context, history)
- `style_dna_extractor.py` (14KB) — Extract sentence features, word usage, description/dialogue style from text samples
- `style_calibrator.py` (9KB) — Compare new text against saved style DNA for drift detection
- `character_consistency_checker.py` (22KB) — Scan for OOC (out-of-character) risks. Usage: `--input chapter --characters characters.json`
- `plot_continuity_checker.py` (26KB) — Plot logic and foreshadowing tracker. Usage: `--check N` for quick check, `--report N --format text` for full report
- `name_generator.py` — Anti-AI-homogenization naming with famous character collision checks
- `generate_cover.py` — Novel cover generation using Pillow (600x800, male/female style auto-detect)

Top-level `scripts/` provides direct access to novel-memory-pro scripts and standalone tools.

### Quality constraint system

Three-tier red-line system enforced before and during writing:

1. **一级红线** (Absolute prohibition): Originality, POV consistency, gender/name correctness
2. **二级红线** (Quality constraints): Style drift, character OOC, plot contradictions, foreshadowing loss
3. **三级红线** (Quality optimization): Chapter progression, word count, structure, suspense

9 mandatory pre-chapter questions must score >= 70 points before writing begins.

## Important File Pointers

- Main skill entry: [`novel_creation_promax/SKILL.md`](novel_creation_promax/SKILL.md)
- **Execution orchestrator**: [`novel_creation_promax/references/orchestrator.md`](novel_creation_promax/references/orchestrator.md)
- Memory sub-skill: [`novel_creation_promax/novel-memory-pro/SKILL.md`](novel_creation_promax/novel-memory-pro/SKILL.md)
- Memory manager (core): [`novel_creation_promax/novel-memory-pro/scripts/memory_manager.py`](novel_creation_promax/novel-memory-pro/scripts/memory_manager.py)
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
- Low AI trace polish (humanized writing): [`novel_creation_promax/references/humanized-writing.md`](novel_creation_promax/references/humanized-writing.md)
- Short story template: [`novel_creation_promax/references/short-story-template.md`](novel_creation_promax/references/short-story-template.md)
- Opening hooks library: [`novel_creation_promax/references/opening-hooks.md`](novel_creation_promax/references/opening-hooks.md)
- Witty style guide: [`novel_creation_promax/references/witty-style-guide.md`](novel_creation_promax/references/witty-style-guide.md)
- Memory integration workflow: [`novel_creation_promax/novel-memory-pro/references/integration-with-novel-creation.md`](novel_creation_promax/novel-memory-pro/references/integration-with-novel-creation.md)
- Memory optimization playbook: [`novel_creation_promax/novel-memory-pro/references/memory-optimization-playbook.md`](novel_creation_promax/novel-memory-pro/references/memory-optimization-playbook.md)

---

## 📤 自动发布模块 (Fanqie Auto Publish)

**工具路径：** `fanqie_auto_publish/` (软链接)

### 小说连载发布

**流程（当用户要求发布小说章节时执行）：**

1. **检查状态**：
   ```bash
   cd fanqie_auto_publish
   ls chapters/  # 查看待发章节
   ```

2. **执行发布**：
   ```bash
   cd fanqie_auto_publish
   .venv/bin/python3 publish.py --book "书名" --draft    # 存草稿
   .venv/bin/python3 publish.py --book "书名" --count 3  # 发布3章
   ```

3. **报告结果**：发布成功后告知用户章节号和状态，失败则读取错误截图报告。

### 短故事发布

**短故事 vs 小说的区别**：

- 小说：每章独立发布，逐章创建
- 短故事：所有章节合并为一个文档，用 `<h1>` 标题分隔，发布到短故事编辑器

**流程（当用户要求发布短故事时执行）：**

1. **检查短故事章节**：
   ```bash
   cd fanqie_auto_publish
   ls short_chapters/  # 查看待发短故事
   ```

2. **执行发布**：
   ```bash
   cd fanqie_auto_publish
   .venv/bin/python3 publish.py --short --book "短故事名" --draft    # 存草稿
   .venv/bin/python3 publish.py --short --book "短故事名"            # 直接发布
   ```

3. **短故事工作流**：
   - 自动合并所有章节为一个完整文档
   - 使用 `<h1>第N章 标题</h1>` 分隔各章
   - 导航到短故事管理页 (`/main/writer/short-manage`)
   - 检查是否已有该短故事（有则编辑，无则新建）
   - 自动关闭新手教学弹窗
   - 填写故事标题 + 注入合并后的 HTML 内容到 ProseMirror 编辑器
   - 存草稿或直接发布

**目录结构**：
- `chapters/` — 小说章节（每本子目录一个）
- `short_chapters/` — 短故事章节（每本子目录一个）
- `uploaded/` — 小说已发布归档
- `short_uploaded/` — 短故事已发布归档

### 通用说明

**登录命令（首次或登录过期时）：**

```bash
cd fanqie_auto_publish
.venv/bin/python3 login.py
```

**常用参数**：

| 参数 | 说明 |
|------|------|
| `--short` | 短故事模式 |
| `--book "书名"` | 指定书名（自动选择，跳过交互） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |
| `--no-close` | 不关闭浏览器（便于调试） |

**注意事项**：
- 所有章节脚本使用 `force=True` 点击，确保不被 CSS 动画或事件拦截阻挡
- 短故事编辑器使用 ProseMirror，小说编辑器使用 ql-editor/ProseMirror 双兼容
- 发布失败时会自动保存截图（`error.png` 或 `short_error.png`）

---

## 📚 知识库管理 (Knowledge Base)

**路径**：`knowledge_base/`

**设计原则**：

- Obsidian 兼容，支持双向链接与标签检索
- PARA 编号体系（10-80），数字越小越通用
- 所有创作知识集中于此，`novel_creation_promax/references/` 为原始来源

**目录结构**：

- `10_WorldBuilding/`：世界观、题材知识库（都市/科幻/仙侠/玄幻/悬疑/言情）
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
