# Architecture

> 本文描述 `novel_creation_promax` 的系统边界、数据流和唯一真源。日常执行细节见 `references/orchestrator.md`，功能编号见 `MODE_REGISTRY.md`。

## 系统目标

小说创作 Pro Max 是面向中文网文的创作技能系统。它不是单个 prompt，而是由技能入口、知识库、记忆中台、审计脚本和发布辅助组成的闭环。

核心目标：

- 立项时避免创意、设定、大纲缺口。
- 连载时保持人物、伏笔、风格、节奏一致。
- 写后用脚本兜住字数、AI痕迹、重复、OOC 等硬问题。
- 将用户纠正沉淀到共享记忆和知识库，而不是停留在对话里。

## 组件边界

| 组件 | 责任 | 不负责 |
|---|---|---|
| `SKILL.md` | 触发、导航、最小工作流说明 | 大量规则细节 |
| `MODE_REGISTRY.md` | 功能编号和模式唯一真源 | 具体写作技巧 |
| `references/orchestrator.md` | 阶段、门禁、调用顺序 | 知识库内容本身 |
| `references/trigger-rules.md` | 题材/技巧/审稿/连贯性触发 | 模式编号 |
| `references/knowledge-pack-workflow.md` | 每章知识包组装 | 长篇记忆 CRUD |
| `novel-memory-pro/` | 风格、人物、剧情、上下文、历史记忆 | 正文创作 |
| `review-skill/` | LLM 深度审稿 | 硬性自动审计 |
| `scripts/` | 可执行门禁和确定性工具 | 创意判断 |
| `knowledge_base/` | 题材、技巧、质量、平台、项目知识 | 临时草稿缓存 |

## 数据流

```text
用户请求
  ↓
MODE_REGISTRY.md 选择模式
  ↓
SKILL.md 导航到对应 reference / script
  ↓
知识库 + 记忆包 + 项目文件
  ↓
真相文件校验 + rule_stack 编译
  ↓
正文/大纲/审稿/润色产物
  ↓
脚本审计与 passport 记录
  ↓
novel_state.json + novel-memory-pro + knowledge_base/80_Projects
```

## 正文写作闭环

```text
细纲 + 记忆包 + 知识包 + 真相文件
  ↓
story_truth_manager.py validate/compile
  ↓
pre_write_check.py
  ↓
Pass 1 剧情稿
  ↓
writing_gate.py
  ↓
Pass 2 去AI修订
  ↓
post_write_audit.py
  ↓
story_truth_manager.py normalize + validate-delta + apply-delta
  ↓
style_calibrator.py + character_consistency_checker.py
  ↓
chapter passport + chapter summary
  ↓
memory_manager.py sync-chapter
```

## 唯一真源

| 主题 | 唯一真源 |
|---|---|
| 功能编号 | `MODE_REGISTRY.md` |
| 执行阶段 | `references/orchestrator.md` |
| 触发规则 | `references/trigger-rules.md` |
| 知识包 | `references/knowledge-pack-workflow.md` |
| 结构化事实源 | `设定/真相文件/*.json` |
| 输出结构 | `docs/ARTIFACTS.md` |
| 数据访问层级 | `docs/DATA_ACCESS_LEVELS.md` |
| 长篇记忆 | `novel-memory-pro/` |
| 用户偏好/纠正 | `.claude/memory/` |

## 维护原则

- 新功能先登记到 `MODE_REGISTRY.md`，再写入 `SKILL.md`。
- 新脚本必须能从项目根目录执行。
- 新质量规则优先进入脚本或知识库，不直接堆到 `SKILL.md`。
- 任何章节推进、角色状态变化、伏笔变化，必须同步项目级知识库或记忆系统。
