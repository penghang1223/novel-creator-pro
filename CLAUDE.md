# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of Claude Code skills for Chinese web novel (网文) writing. It is not a traditional software project with builds or test suites. The repository contains multiple iterations of the same skill system:

- `novel_creation_max3.0/` — **Current active version**. The main skill (`SKILL.md`) plus a dedicated `novel-memory-pro/` sub-skill for long-form serialization memory management.
- `novel_creation_max2.0/` — Previous major iteration with a more complex reference taxonomy.
- `novel_creation_max/` — Earliest iteration with a flat `memory_structure.json` asset.
- `skill_super-novel-writer/` — Earlier fused skill combining conception, writing, memory, quality, and platform adaptation.

When making changes, prefer editing `novel_creation_max3.0/` unless the user explicitly asks to work in another version.

## Python Dependencies

The only external Python dependency is `Pillow>=9.0.0` (used for cover generation).

## Common Commands

All commands are run from the relevant skill directory (usually `novel_creation_max3.0/` or `novel_creation_max3.0/novel-memory-pro/`).

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

## High-Level Architecture

### Skill layer
Each top-level directory is a Claude skill defined by a `SKILL.md` file in YAML frontmatter format. The skill descriptor declares:
- `name` / `description` — skill identity and trigger conditions
- `dependency.python` — minimal runtime dependencies
- A markdown body describing modes, menus, workflows, and reference file links

When the skill is invoked, the behavior is driven by the `SKILL.md` instructions and the reference documents it points to. There is no compile step.

### Reference layer
`references/` holds the knowledge base: genre guides, writing styles, outline templates, character archetypes, platform-specific rules, quality constraints, and workflow guides. In `max3.0` the references are flat; in `max2.0` they are grouped into thematic subdirectories.

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

The `novel-memory-pro` scripts use a five-layer memory model (`style_dna`, `character`, `plot`, `context`, `history`) persisted as JSON buckets under a configurable `memory_dir`.

### Version relationship
`max3.0` simplified the reference taxonomy of `max2.0` while preserving the same core memory-pro architecture. The older flat `memory_structure.json` in `novel_creation_max/` is superseded by the `novel-memory-pro` script system in `max3.0`.

## Important File Pointers

- Main skill entry: [`novel_creation_max3.0/SKILL.md`](novel_creation_max3.0/SKILL.md)
- Memory sub-skill entry: [`novel_creation_max3.0/novel-memory-pro/SKILL.md`](novel_creation_max3.0/novel-memory-pro/SKILL.md)
- Memory schema: [`novel_creation_max3.0/assets/memory_structure.json`](novel_creation_max3.0/assets/memory_structure.json)
- Chapter sync schema: [`novel_creation_max3.0/novel-memory-pro/references/chapter_sync_schema.md`](novel_creation_max3.0/novel-memory-pro/references/chapter_sync_schema.md)
- Character profile template: [`novel_creation_max3.0/novel-memory-pro/references/character_profile_template.md`](novel_creation_max3.0/novel-memory-pro/references/character_profile_template.md)
- Style DNA format: [`novel_creation_max3.0/novel-memory-pro/references/style_dna_format.md`](novel_creation_max3.0/novel-memory-pro/references/style_dna_format.md)
