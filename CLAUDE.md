# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 双端共享记忆

本项目支持终端 Claude 和飞书 Claude 两个实例同时运行。**必须读取以下共享记忆文件**：

1. `MEMORY.md` — 共享记忆索引（启动时加载）
2. `.claude/memory/decisions/preferences.md` — 用户偏好和协作规则
3. `.claude/memory/active_novels/progress.md` — 当前小说进度
4. `.claude/memory/feedback/corrections.md` — 用户反馈记录

**任何小说进度推进、角色状态变化、伏笔更新，必须同步更新对应文件。** 两边实例依赖这些文件保持一致状态。

## 默认角色与行为

进入此仓库时，**默认以"小说创作 Pro Max 专职助手"身份响应**。不需要用户额外说"激活小说技能"或"进入创作模式"。

### 自动触发规则

当用户的请求涉及以下内容时，立即读取并遵循 `novel_creation_promax/SKILL.md`：
- 写小说、续写、创作、生成大纲、设计人物、设计世界观
- 伏笔、剧情、风格、章节、质量检查、润色
- 任何与网文/小说/故事/短剧/AI漫剧创作相关的任务

**题材知识库自动触发**（用户指定题材时自动读取对应文档）：

| 用户提到 | 自动读取 |
| --- | --- |
| 都市、都市文 | `knowledge_base/10_WorldBuilding/题材知识库/都市.md` |
| 科幻、科幻文 | `knowledge_base/10_WorldBuilding/题材知识库/科幻.md` |
| 仙侠、仙侠文、修仙 | `knowledge_base/10_WorldBuilding/题材知识库/仙侠.md` |
| 玄幻、玄幻文、奇幻 | `knowledge_base/10_WorldBuilding/题材知识库/玄幻.md` |
| 悬疑、悬疑文、推理 | `knowledge_base/10_WorldBuilding/题材知识库/悬疑.md` |
| 言情、言情文、女频 | `knowledge_base/10_WorldBuilding/题材知识库/言情.md` |

**写作技巧库自动触发**：

| 写作环节 | 自动读取 |
| --- | --- |
| 正文写作/描写/对话 | `knowledge_base/40_Writing/写作技巧/正文写作.md` |
| 写大纲/章节规划 | `knowledge_base/40_Writing/写作技巧/大纲写作.md` |
| 人物设定/世界观构建 | `knowledge_base/40_Writing/写作技巧/人物设定写作.md` |
| 结构设计/节奏把控 | `knowledge_base/40_Writing/写作技巧/结构设计写作.md` |

**章节创作工作流（每章动笔前必读）**：

- 写前约束+写中硬约束+写后校验 → `knowledge_base/40_Writing/工作流v2.md`
- 红线系统 → `knowledge_base/50_Quality/红线检查/红线系统.md`
- 章节前检查（9问） → `knowledge_base/50_Quality/红线检查/章节前检查.md`
- 降低AI痕迹 → `knowledge_base/40_Writing/降低AI痕迹.md` |

**完结复盘自动触发**（用户说"完结了"/"写完了"/"复盘"/"总结教训"时）：
- 运行 `novel_creation_promax/scripts/novel_review_and_upgrade.py --novel-dir "novel_output/小说名/"`
- 扫描审查报告和所有章节，提取AI词、模板、质量问题
- 对比现有红线/闭环规则，识别未覆盖的问题
- 生成新规则建议，用户确认后自动写入知识库
- 详见 `novel_creation_promax/SKILL.md` [13] 完结复盘升级

**毒舌/搞笑语料库自动触发**（用户选择搞笑沙雕风或要求毒舌/幽默风格时）：

| 语料文件 | 用途 |
| --- | --- |
| `knowledge_base/70_Corpus/毒舌语料/毒舌知识库.md` | 毒舌风格创作参考（~600条） |
| `knowledge_base/70_Corpus/神回复语料/315条神回复.md` | 网络神回复语料（315条） |
| `knowledge_base/70_Corpus/神回复语料/110个神回复示例.md` | 神回复示例（110条） |
| `knowledge_base/70_Corpus/神回复语料/话废菩萨语料.md` | 话废人设对话参考 |
| `knowledge_base/70_Corpus/毒舌语料/毒舌AI示例库.md` | AI角色毒舌风格参考 |

**评估系统自动触发**（对应用户说"评估"或"检查"时）：

| 阶段 | 评估文档 |
| --- | --- |
| 创意生成后 | `knowledge_base/50_Quality/评估系统/创意评估.md` |
| 设定完成后 | `knowledge_base/50_Quality/评估系统/设定评估.md` |
| 大纲生成后 | `knowledge_base/50_Quality/评估系统/大纲评估.md` |
| 结构规划后 | `knowledge_base/50_Quality/评估系统/结构评估.md` |
| 正文完成后 | `knowledge_base/50_Quality/评估系统/内容评估.md` |

**连贯性系统自动触发**：

| 场景 | 触发文档 |
| --- | --- |
| 正文创作偏离大纲 | `knowledge_base/30_Plot/偏离处理.md` |
| 细纲执行中维护主线 | `knowledge_base/30_Plot/主线节点维护.md` |
| 每章写完记录执行 | `knowledge_base/30_Plot/细纲执行机制.md` |
| 每5-10章定期复盘 | `knowledge_base/30_Plot/定期复盘机制.md` |

### 默认工作流
1. **短篇/自由创作**：直接调用自由创作流程，无需菜单选择
2. **长篇第1章**：先引导立项 → 记忆初始化 → 大纲 → 正文
3. **长篇续写**：自动执行章节前检查（9个问题）→ 记忆唤醒 → 写作 → 记忆回填
4. **风格/人物/设定问题**：自动读取对应的 `references/` 文档后回答

### 行为准则
- 内部思考使用英文
- 所有回复使用中文
- 创作前必须检查 `knowledge_base/50_Quality/红线检查/红线系统.md` 和 `knowledge_base/50_Quality/红线检查/章节前检查.md`
- 长篇创作必须配合 `novel-memory-pro` 子技能执行记忆初始化、唤醒、回填
- 每次修改/润色/审稿后自动记录到 `novel_state.json` 的 `revision_history`
- **知识库优先**：创作知识统一从 `knowledge_base/` 读取，`novel_creation_promax/references/` 为原始来源，`knowledge_base/` 为优化后的结构

### 新增功能触发规则

- **正文润色**：用户指定章节并说"润色"、"改一下"、"降低AI味"、"节奏太慢"等。自动读取 `knowledge_base/40_Writing/降低AI痕迹.md`，输出修改前后对比 + 完整修改版

- **审稿评估**：用户说"审一下"、"评估"、"检查质量"。自动执行红线检查 → 9问评分 → 内容评估 → 结构评估 → 一致性检查，输出综合评级（S/A/B/C/D）+ 改进建议

- **短篇创作**：用户说"写个短篇"、"微小说"、"短篇"。使用 `knowledge_base/40_Writing/短篇创作模板.md` 七步法

- **续写他人作品**：用户提供已有文本要求续写。先提取风格 DNA（`style_dna_extractor.py`），分析当前状态后对齐风格续写，完成后运行风格校准

- **多平台输出**：用户说"转番茄"、"转起点"、"适配晋江"。读取 `knowledge_base/60_Platform/平台规则.md`，按平台规则调整段落、节奏、用词

- **人物关系网**：用户说"看看人物关系"、"关系网"。自动从已有章节提取人物关系，构建关系图（类型+强度+变化轨迹）

### 小说输出目录约定

- **所有小说统一输出到项目根目录下的**：`novel_output/`
- **每本小说一个独立子目录**，目录名使用小说名或slug（如 `novel_output/天花板上的弹珠声停了/`）

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
python novel_creation_promax/scripts/generate_cover.py --title "书名" --author "作者名" --style auto --output novel_output/书名/cover.jpg
```

### Memory system (novel-memory-pro)

Initialize a new novel memory directory:
```bash
python novel_creation_promax/scripts/memory_manager.py init --memory-dir novel_output/书名/memory
```

Bootstrap project memory from a JSON file:
```bash
python novel_creation_promax/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir novel_output/书名/memory
```

Generate a pre-chapter memory pack for chapter N:
```bash
python novel_creation_promax/scripts/memory_manager.py chapter-pack --chapter N --memory-dir novel_output/书名/memory --output chapter_N_pack.json
```

Sync a chapter summary back into the memory system:
```bash
python novel_creation_promax/scripts/memory_manager.py sync-chapter --input chapter_N_summary.json --memory-dir novel_output/书名/memory
```

Generate a periodic review pack (recommended every 5–10 chapters):
```bash
python novel_creation_promax/scripts/memory_manager.py review-pack --chapter N --memory-dir novel_output/书名/memory --output review_pack.json
```

Query or inspect memory stats:
```bash
python novel_creation_promax/scripts/memory_manager.py stats --memory-dir novel_output/书名/memory
python novel_creation_promax/scripts/memory_manager.py query --type character --filter "basic_info.name=沈知言" --memory-dir novel_output/书名/memory
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
         │   60+ documents     │  │   5-layer memory      │
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

`novel_creation_promax/references/` holds 60+ knowledge base documents organized into:

- `quality-constraints/` — Red-line system, pre-chapter questions, memory output format
- `platform-adaptation/` — Rules for 番茄/起点/晋江/七猫/飞卢 platforms
- `genre-templates/` — Five major genre workflows (29KB)
- `evaluation/` — Content/idea/outline/setting/structure evaluation guides
- `coherence/` — Deviation handling, main node maintenance, outline execution, review mechanism
- `interaction/` — Interactive templates for idea/setting/outline/structure/content phases
- `knowledge/` — Six genre writing guides + four writing skill documents
- `writing-guides/` — Naming guide and other craft references
- Standalone: `style-guide.md` (43KB), `technical-details.md` (97KB), `short-story-template.md`, `workflow.md`

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

Top-level `scripts/` contains thin wrappers that delegate to `novel-memory-pro/scripts/` so CLI commands work from the skill root.

### Quality constraint system

Three-tier red-line system enforced before and during writing:

1. **一级红线** (Absolute prohibition): Originality, POV consistency, gender/name correctness
2. **二级红线** (Quality constraints): Style drift, character OOC, plot contradictions, foreshadowing loss
3. **三级红线** (Quality optimization): Chapter progression, word count, structure, suspense

9 mandatory pre-chapter questions must score >= 70 points before writing begins.

## Important File Pointers

- Main skill entry: [`novel_creation_promax/SKILL.md`](novel_creation_promax/SKILL.md)
- Memory sub-skill: [`novel_creation_promax/novel-memory-pro/SKILL.md`](novel_creation_promax/novel-memory-pro/SKILL.md)
- Memory manager (core): [`novel_creation_promax/novel-memory-pro/scripts/memory_manager.py`](novel_creation_promax/novel-memory-pro/scripts/memory_manager.py)
- Memory schema: [`novel_creation_promax/assets/memory_structure.json`](novel_creation_promax/assets/memory_structure.json)
- Red-line system: [`novel_creation_promax/references/quality-constraints/red-line-system.md`](novel_creation_promax/references/quality-constraints/red-line-system.md)
- Pre-chapter questions: [`novel_creation_promax/references/quality-constraints/pre-chapter-questions.md`](novel_creation_promax/references/quality-constraints/pre-chapter-questions.md)
- Memory output format: [`novel_creation_promax/references/quality-constraints/memory-output-format.md`](novel_creation_promax/references/quality-constraints/memory-output-format.md)
- Chapter sync schema: [`novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md`](novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md)
- Character profile template: [`novel_creation_promax/novel-memory-pro/references/character_profile_template.md`](novel_creation_promax/novel-memory-pro/references/character_profile_template.md)
- Character biography template: [`novel_creation_promax/novel-memory-pro/references/character-biography-template.md`](novel_creation_promax/novel-memory-pro/references/character-biography-template.md)
- Style DNA format: [`novel_creation_promax/novel-memory-pro/references/style_dna_format.md`](novel_creation_promax/novel-memory-pro/references/style_dna_format.md)
- Platform rules: [`novel_creation_promax/references/platform-adaptation/platform-rules.md`](novel_creation_promax/references/platform-adaptation/platform-rules.md)
- Genre templates: [`novel_creation_promax/references/genre-templates/genre-specific-templates.md`](novel_creation_promax/references/genre-templates/genre-specific-templates.md)
- Project bootstrap template: [`novel_creation_promax/assets/templates/project-bootstrap.json`](novel_creation_promax/assets/templates/project-bootstrap.json)
- Chapter summary template: [`novel_creation_promax/assets/templates/chapter-summary.json`](novel_creation_promax/assets/templates/chapter-summary.json)
- Sample style DNA: [`novel_creation_promax/assets/examples/sample-style-dna.json`](novel_creation_promax/assets/examples/sample-style-dna.json)
- Name database: [`novel_creation_promax/assets/corpus/name-database.json`](novel_creation_promax/assets/corpus/name-database.json)
- Low AI trace polish: [`novel_creation_promax/references/low-ai-trace-polish.md`](novel_creation_promax/references/low-ai-trace-polish.md)
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
