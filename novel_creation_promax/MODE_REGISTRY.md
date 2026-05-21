# Mode Registry

> 本文件是小说创作 Pro Max 的功能编号与触发规则唯一真源。`SKILL.md`、`CLAUDE.md`、`AGENTS.md`、命令文档只引用本表，不另行维护编号副本。

## 使用规则

- 用户明确选择编号时，按 `mode_id` 执行。
- 用户用自然语言描述任务时，按 `trigger_examples` 匹配模式。
- 如果一个请求同时命中多个模式，按更具体的模式优先：发布 > 审稿 > 润色 > 正文写作 > 大纲/立项。
- 正文写作、润色、审稿、复盘会写入或读取小说项目目录；纯咨询类模式只读知识库，除非用户要求落盘。

## 模式总表

| mode_id | mode_key | 名称 | 典型触发 | 必读入口 | 主要产物 | 强制门禁 |
|---:|---|---|---|---|---|---|
| 0 | onboarding | 新手立项 | 从零写、帮我立项、新书 | `references/orchestrator.md` Stage 1-4 + `scripts/project_bootstrap_pipeline.py` | 创意/设定/结构/细纲 | bootstrap gate |
| 1 | free-create | 自由创作 | 写个故事、来一篇短故事 | `references/trigger-rules.md` + 对应题材知识 | 正文、摘要、outline | 基础审计 |
| 2 | genre-analysis | 题材分析 | 这个题材怎么样、分析赛道 | `knowledge_base/10_WorldBuilding/题材知识库/` | 题材分析报告 | 无 |
| 3 | idea-classify | 创意归类 | 这个点子适合哪个平台/题材 | `knowledge_base/60_Platform/平台规则.md` | 创意归类建议 | 创意评分可选 |
| 4 | outline | 大纲生成 | 生成大纲、分卷、细纲 | `references/orchestrator.md` Stage 3-4 | 大纲、分卷、细纲 | 结构评估 |
| 5 | chapter-write | 正文写作 | 写第N章、续写、下一章 | `references/orchestrator.md` Stage 5 | 章节正文、摘要、passport | pre-check、gate、audit |
| 6 | style | 风格定制 | 模仿风格、调语气、毒舌风 | `knowledge_base/40_Writing/风格指南/风格索引.md` | style_dna 或风格约束 | 风格校准 |
| 7 | memory | 记忆管理 | 查看记忆、同步记忆、别吃设定 | `novel-memory-pro/SKILL.md` | memory JSON、review pack | schema 校验 |
| 8 | polish | 正文润色 | 润色、降AI、改对话、调节奏 | `knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md` | 修订稿、revision_history | 审计复跑 |
| 9 | review | 审稿评估 | 审一下、质量怎么样、帮我看看 | `review-skill/SKILL.md` | 审稿报告 | 自动审计先跑 |
| 10 | short-story | 短篇创作 | 短篇、知乎盐选、短故事 | `references/trigger-rules.md` | 短篇正文、摘要 | 字数/结构审计 |
| 11 | platform-output | 多平台输出 | 番茄格式、起点格式、发布同步 | `knowledge_base/60_Platform/平台规则.md` | 平台稿、同步结果 | 平台规则检查 |
| 12 | retrospective | 完结复盘 | 完结复盘、总结教训、升级规则 | `novel_creation_promax/scripts/novel_review_and_upgrade.py` | 复盘报告、规则建议 | 用户确认后入库 |
| 13 | continuation | 续写他人作品 | 续写这篇、接着这个风格写 | `novel_creation_promax/scripts/style_dna_extractor.py` | 风格DNA、续写正文 | 风格校准 |

## 模式执行要点

### 0. 新手立项

从零开始写长篇时，必须先创建并封存项目门禁；未通过门禁不得写第1章。

```bash
python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "{平台}" --title "{书名}" --genre "{题材}" --premise "{核心设定}"
python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "novel_output/{平台}/{书名}"
```

`seal` 会检查共享记忆、4个必读知识库、项目目录、`project_bootstrap.json`、风格DNA、总纲、8卷细纲、`素材/小说信息.md`、`80_Projects/_config.md`、`MEMORY.md`。只有 `novel_state.json.workflow_gate.can_write_chapter=true` 时，正文流水线才允许运行。

### 5. 正文写作

必须按 `references/orchestrator.md` 的 Stage 5 执行。推荐命令：

```bash
python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "{小说目录}" --chapter N --title "{标题}"
python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "{小说目录}" --chapter N --title "{标题}"
```

交付前必须具备：

- 章节正文文件
- 写后审计通过或明确列出未通过项
- `摘要/chapter_NNN_passport.json`
- 若有章节摘要，则同步到 `记忆/`

### 8. 正文润色

润色不允许只改聊天窗口内容。必须读取原章节文件，输出修订稿或覆盖前备份，并更新 `novel_state.json.revision_history`。润色后至少重跑 `novel_creation_promax/scripts/post_write_audit.py`。

### 9. 审稿评估

基础审计自动执行；深度审稿由用户触发或基础审计问题较多时建议进入。深度审稿使用 `review-skill/SKILL.md`，不要把它和硬规则审计混为一谈。

### 12. 完结复盘

自动升级知识库规则前必须先给出建议清单，等待用户确认。确认后才可写入 `knowledge_base/`。
