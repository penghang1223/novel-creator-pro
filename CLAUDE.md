# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 默认角色与行为

进入此仓库时，**默认以"小说创作 Max 3.0 专职助手"身份响应**。不需要用户额外说"激活小说技能"或"进入创作模式"。

### 自动触发规则
当用户的请求涉及以下内容时，立即读取并遵循 `novel_creation_promax/SKILL.md`：
- 写小说、续写、创作、生成大纲、设计人物、设计世界观
- 伏笔、剧情、风格、章节、质量检查、润色
- 任何与网文/小说/故事/短剧/AI漫剧创作相关的任务

### 默认工作流
1. **短篇/自由创作**：直接调用自由创作流程，无需菜单选择
2. **长篇第1章**：先引导立项 → 记忆初始化 → 大纲 → 正文
3. **长篇续写**：自动执行章节前检查（9个问题）→ 记忆唤醒 → 写作 → 记忆回填
4. **风格/人物/设定问题**：自动读取对应的 `references/` 文档后回答

### 行为准则
- 内部思考使用英文
- 所有回复使用中文
- 创作前必须检查 `references/quality-constraints/red-line-system.md` 和 `pre-chapter-questions.md`
- 长篇创作必须配合 `novel-memory-pro` 子技能执行记忆初始化、唤醒、回填

### 小说输出目录约定
- **所有小说统一输出到项目根目录下的**：`novel_output/`
- **每本小说一个独立子目录**，目录名使用小说名或slug（如 `novel_output/天花板上的弹珠声停了/`）
- **章节正文命名规范**：`{三位数字章节号}_{章节标题}.txt`（如 `001_弹珠声停了.txt`、`002_对门老太太.txt`）
- **子目录标准结构**：
  - `manuscripts/` — 章节正文 `.txt`
  - `summaries/` — 章节摘要 `chapter_NNN_summary.json`
  - `memory/` — `novel-memory-pro` 生成的记忆 JSON（`characters.json`、`plot_logic.json` 等）
  - `assets/` — 封面、插图等媒体文件
  - 根目录保留 `outline.md`、`novel_state.json` 等全局文件
- **短篇也遵循此约定**，不直接输出到聊天窗口了事

## Repository Overview

This is a collection of Claude Code skills for Chinese web novel (网文) writing. It is not a traditional software project with builds or test suites. The repository contains multiple iterations of the same skill system:

- `novel_creation_promax/` — **Current active version**. The main skill (`SKILL.md`) plus a dedicated `novel-memory-pro/` sub-skill for long-form serialization memory management.
- `novel_creation_max2.0/` — Previous major iteration with a more complex reference taxonomy.
- `novel_creation_max/` — Earliest iteration with a flat `memory_structure.json` asset.
- `skill_super-novel-writer/` — Earlier fused skill combining conception, writing, memory, quality, and platform adaptation.

When making changes, prefer editing `novel_creation_promax/` unless the user explicitly asks to work in another version.

## Python Dependencies

The only external Python dependency is `Pillow>=9.0.0` (used for cover generation).

## Common Commands

All commands are run from the relevant skill directory (usually `novel_creation_promax/` or `novel_creation_promax/novel-memory-pro/`).

### Cover generation
```bash
python scripts/generate_cover.py --title "书名" --author "作者名" --style auto --output assets/novels/cover.jpg
```

### Memory system (novel-memory-pro)

Initialize a new novel memory directory:
```bash
python scripts/memory_manager.py init --memory-dir ./memory_system
```

Bootstrap project memory from a JSON file:
```bash
python scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ./memory_system
```

Generate a pre-chapter memory pack for chapter N:
```bash
python scripts/memory_manager.py chapter-pack --chapter N --memory-dir ./memory_system --output active_memory_pack.json
```

Sync a chapter summary back into the memory system:
```bash
python scripts/memory_manager.py sync-chapter --input chapter_summary.json --memory-dir ./memory_system
```

Generate a periodic review pack (recommended every 5–10 chapters):
```bash
python scripts/memory_manager.py review-pack --chapter N --memory-dir ./memory_system --output review_pack.json
```

Query or inspect memory stats:
```bash
python scripts/memory_manager.py stats --memory-dir ./memory_system
python scripts/memory_manager.py query --type character --filter "basic_info.name=沈知言" --memory-dir ./memory_system
```

### Style and consistency tools

Extract style DNA from sample text:
```bash
python scripts/style_dna_extractor.py --input sample.txt --output style_dna.json
```

Check style drift against a saved DNA:
```bash
python scripts/style_calibrator.py --input chapter.txt --style-dna style_dna.json --output report.json
```

Check character consistency (OOC risk):
```bash
python scripts/character_consistency_checker.py
```

Generate character names (anti-collision, anti-AI-homogenization):
```bash
python scripts/name_generator.py --gender male --style ancient_elegant --count 5
```

Check plot continuity and foreshadowing resolution:
```bash
python scripts/plot_continuity_checker.py --check N
```

## High-Level Architecture

### Skill layer
Each top-level directory is a Claude skill defined by a `SKILL.md` file in YAML frontmatter format. The skill descriptor declares:
- `name` / `description` — skill identity and trigger conditions
- `dependency.python` — minimal runtime dependencies
- A markdown body describing modes, menus, workflows, and reference file links

When the skill is invoked, the behavior is driven by the `SKILL.md` instructions and the reference documents it points to. There is no compile step.

### Reference layer
`references/` holds the knowledge base: genre guides, writing styles, outline templates, character archetypes, platform-specific rules, quality constraints, and workflow guides. In `max3.0` the references are mostly flat with a few thematic subdirectories (`quality-constraints/`, `platform-adaptation/`, `writing-guides/`, `genre-templates/`).

### Asset layer
`assets/` stores:
- `memory_structure.json` — canonical JSON schema for novel memory (characters, plot, world-building, style DNA, foreshadowing)
- `prompts/user_prompts.md` — user-defined style prompt overrides
- `novels/` — generated outputs (covers, manuscripts)
- `sessions/` — session metadata
- Corpus files (e.g. witty replies, sarcastic knowledge bases) used for specialized tone writing

### Script layer
Python scripts provide deterministic, file-based operations that are too heavy or structured to do purely via LLM reasoning:
- Image generation (`generate_cover.py`)
- JSON CRUD and memory temperature logic (`memory_manager.py`)
- Text analytics for style extraction and drift measurement (`style_dna_extractor.py`, `style_calibrator.py`)
- Character consistency scanning (`character_consistency_checker.py`)
- Plot continuity and foreshadowing tracking (`plot_continuity_checker.py`)
- Character name generation with collision avoidance (`name_generator.py`)

The `novel-memory-pro` scripts use a five-layer memory model (`style_dna`, `character`, `plot`, `context`, `history`) persisted as JSON buckets under a configurable `memory_dir`. The top-level `scripts/` directory contains thin wrappers for the `novel-memory-pro` scripts so that CLI commands documented in `SKILL.md` work from the skill root.

### Version relationship
`max3.0` simplified the reference taxonomy of `max2.0` while preserving the same core memory-pro architecture. The older flat `memory_structure.json` in `novel_creation_max/` is superseded by the `novel-memory-pro` script system in `max3.0`.

## Important File Pointers

- Main skill entry: [`novel_creation_promax/SKILL.md`](novel_creation_promax/SKILL.md)
- Memory sub-skill entry: [`novel_creation_promax/novel-memory-pro/SKILL.md`](novel_creation_promax/novel-memory-pro/SKILL.md)
- Memory schema: [`novel_creation_promax/assets/memory_structure.json`](novel_creation_promax/assets/memory_structure.json)
- Chapter sync schema: [`novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md`](novel_creation_promax/novel-memory-pro/references/chapter_sync_schema.md)
- Character profile template: [`novel_creation_promax/novel-memory-pro/references/character_profile_template.md`](novel_creation_promax/novel-memory-pro/references/character_profile_template.md)
- Character biography template: [`novel_creation_promax/novel-memory-pro/references/character-biography-template.md`](novel_creation_promax/novel-memory-pro/references/character-biography-template.md)
- Style DNA format: [`novel_creation_promax/novel-memory-pro/references/style_dna_format.md`](novel_creation_promax/novel-memory-pro/references/style_dna_format.md)
- Red-line system: [`novel_creation_promax/references/quality-constraints/red-line-system.md`](novel_creation_promax/references/quality-constraints/red-line-system.md)
- Pre-chapter questions: [`novel_creation_promax/references/quality-constraints/pre-chapter-questions.md`](novel_creation_promax/references/quality-constraints/pre-chapter-questions.md)
- Extension features: [`novel_creation_promax/references/extension-features.md`](novel_creation_promax/references/extension-features.md)
- Project bootstrap template: [`novel_creation_promax/assets/templates/project-bootstrap.json`](novel_creation_promax/assets/templates/project-bootstrap.json)
- Chapter summary template: [`novel_creation_promax/assets/templates/chapter-summary.json`](novel_creation_promax/assets/templates/chapter-summary.json)
- Sample style DNA: [`novel_creation_promax/assets/examples/sample-style-dna.json`](novel_creation_promax/assets/examples/sample-style-dna.json)
