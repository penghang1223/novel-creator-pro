# 小说创作 Pro Max

> Claude Code 中文网文创作技能集。整合了 `novel_creation_max`、`max2.0`、`super-novel-writer` 三个旧版本的全部核心优势，以 `novel_creation_promax/` 为唯一活跃版本。

---

## 这是什么

这不是一个传统软件项目，而是一套为 Claude Code 设计的**中文网络小说创作技能系统**。当你在这个仓库下与 Claude 对话时，Claude 会默认以"小说创作专职助手"的身份响应，直接帮你：

- 从零构思并创作小说
- 续写长篇连载并保持前后一致
- 设计人物、世界观、伏笔、剧情结构
- 针对番茄/起点/晋江等平台优化开篇
- 管理长篇小说的人物档案、剧情记忆、风格 DNA

---

## 核心特性

### 1. 旗舰级质量约束系统
- **三级红线**：原创性、人称、OOC、剧情矛盾、伏笔丢失等 12 条硬性规则
- **9 个必答问题**：每章创作前强制自检，防止"水章节"
- **记忆唤醒/回填格式**：确保 AI 真的"读过"前文，而不是假装读过

### 2. 生产级记忆中台（`novel-memory-pro`）
- 五层记忆模型：风格 DNA / 人物 / 剧情 / 上下文 / 历史
- 章节前生成精简记忆包，章节后结构化回填
- 支持阶段性 review（每 5-10 章体检一次），长期防漂移

### 3. 全链路脚本工具
- `name_generator.py`：反 AI 同质化命名 + 知名角色撞名检查
- `memory_manager.py`：记忆初始化、章节包生成、摘要同步
- `style_dna_extractor.py` / `style_calibrator.py`：风格提取与漂移检测
- `character_consistency_checker.py`：OOC 风险扫描
- `plot_continuity_checker.py`：剧情逻辑漏洞与伏笔追踪
- `generate_cover.py`：小说封面生成

### 4. 平台适配与深度技法
- 番茄 / 起点 / 晋江 / 七猫 / 飞卢 五大平台规则与黄金三章写法
- 双线镜像叙事、草蛇灰线伏笔、灰色人设、硬核智斗、诗化语言
- 低 AI 痕迹润色方法论

---

## 目录结构

```
NOVEL_CREAT/
├── CLAUDE.md                           # 项目级行为指南（必读）
├── README.md                           # 本文件
├── novel_creation_promax/              # 唯一活跃技能版本
│   ├── SKILL.md                        # 主技能入口（定义菜单、工作流、规则）
│   ├── scripts/                        # 顶层脚本（含 novel-memory-pro 的 thin wrapper）
│   │   ├── generate_cover.py
│   │   ├── name_generator.py
│   │   ├── plot_continuity_checker.py
│   │   ├── memory_manager.py           # wrapper -> novel-memory-pro/
│   │   ├── style_dna_extractor.py      # wrapper -> novel-memory-pro/
│   │   ├── style_calibrator.py         # wrapper -> novel-memory-pro/
│   │   └── character_consistency_checker.py  # wrapper -> novel-memory-pro/
│   ├── assets/                         # 资源与模板
│   │   ├── memory_structure.json
│   │   ├── corpus/
│   │   ├── templates/
│   │   │   ├── project-bootstrap.json
│   │   │   └── chapter-summary.json
│   │   └── examples/
│   │       └── sample-style-dna.json
│   ├── references/                     # 执行参考（原版，已迁移至 knowledge_base/）
│   │   ├── docs/                       # 纯参考文档
│   │   ├── genre-templates/            # 题材模板
│   │   ├── stages/                     # 阶段流程（01-idea 到 05-writing）
│   │   ├── orchestrator.md             # 编排器
│   │   ├── workflow.md                 # 工作流
│   │   └── interaction.md              # 交互模板
│   └── novel-memory-pro/               # 长篇小说记忆中台（子技能）
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── memory_manager.py
│       │   ├── style_dna_extractor.py
│       │   ├── style_calibrator.py
│       │   └── character_consistency_checker.py
│       └── references/
├── knowledge_base/                      # ✅ 知识库主目录（已迁移整合）
│   ├── 10_WorldBuilding/               # 世界观与题材知识库
│   ├── 40_Writing/                    # 写作技巧（175+ 文档）
│   ├── 50_Quality/                    # 质量约束与评估
│   └── 60_Platform/                   # 平台规则与商业情报
└── .claude/ / .vscode/                 # Claude Code / VS Code 本地配置
```

---

## 快速开始

### 场景一：短篇 / 自由创作
直接告诉 Claude：
> "帮我写一个都市重生题材的短篇小说，主角叫李默，前世被兄弟背叛，重生回 2010 年。"

Claude 会自动读取 `SKILL.md` 和自由创作流程，无需菜单选择。

### 场景二：长篇连载 — 从 0 开始
```bash
# 1. 初始化记忆目录
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py init --memory-dir ./my_novel

# 2. 导入项目基础信息（可选，需先准备 project_bootstrap.json）
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ./my_novel

# 3. 让 Claude 根据 SKILL.md 的新手模式流程，引导你完成立项、大纲、正文
```

### 场景三：长篇连载 — 续写第 N 章
```bash
# 1. 生成章节前记忆包
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter 15 --memory-dir ./my_novel --output chapter_15_pack.json

# 2. 告诉 Claude "续写第15章"
#    Claude 会自动执行：9问检查 → 阅读记忆包 → 写作 → 输出章节摘要

# 3. 将摘要回填到记忆系统
python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_15_summary.json --memory-dir ./my_novel
```

---

## 常用脚本速查

| 脚本 | 用途 | 示例命令 |
|---|---|---|
| `generate_cover.py` | 生成小说封面 | `python scripts/generate_cover.py --title "书名" --author "作者" --output cover.jpg` |
| `name_generator.py` | 人物命名 | `python scripts/name_generator.py --gender male --style xianxia --count 5` |
| `memory_manager.py` | 记忆系统核心 | `python novel-memory-pro/scripts/memory_manager.py init --memory-dir ./my_novel` |
| `style_dna_extractor.py` | 提取风格 DNA | `python scripts/style_dna_extractor.py --input sample.txt --output dna.json` |
| `style_calibrator.py` | 检查风格漂移 | `python scripts/style_calibrator.py --input chapter.txt --style-dna dna.json` |
| `character_consistency_checker.py` | OOC 扫描 | `python scripts/character_consistency_checker.py` |
| `plot_continuity_checker.py` | 剧情逻辑检查 | `python scripts/plot_continuity_checker.py --check 15` |

---

## 质量约束系统简介

在 `knowledge_base/50_Quality/` 下有三份核心文档：

1. **`红线检查/红线系统.md`**（创作红线）
   - 一级红线（绝对禁止）：原创性、人称、姓名性别
   - 二级红线（质量约束）：风格漂移、人物 OOC、剧情矛盾、伏笔丢失
   - 三级红线（质量优化）：章节推进、字数、结构、悬念

2. **`红线检查/章节前检查.md`**（章节创作前必答问题）
   - 共 9 个问题，涵盖章节位置、悬念承接、伏笔处理、核心推进事件
   - **总分 ≥ 70 分方可进入正文创作**

3. **`红线检查/记忆输出格式.md`**（记忆系统输出格式）
   - 规定章节前记忆唤醒、章节后记忆回填、风格校准报告的标准输出格式

> **约束优先级**：一级红线 > 9 个必答问题 > 记忆唤醒 > 创作执行

---

## 参考文档索引

### 创作前必读
- 红线系统：`knowledge_base/50_Quality/红线检查/红线系统.md`
- 平台规则：`knowledge_base/60_Platform/平台规则.md`
- 题材模板：`novel_creation_promax/references/genre-templates/genre-specific-templates.md`
- 题材知识库：`knowledge_base/10_WorldBuilding/题材知识库/`（都市/科幻/仙侠/玄幻/悬疑/言情/历史/大女主/惊悚/无限流/游戏/灵异/百合，共13个）
- 写作技巧：`knowledge_base/40_Writing/`

### 技法进阶
- 人性化写作：`novel_creation_promax/references/humanized-writing.md`
- 人物命名：`novel_creation_promax/references/writing-guides/naming-guide.md`
- 开篇钩子：`novel_creation_promax/references/opening-hooks.md`
- 风格指南：`knowledge_base/40_Writing/风格指南/通用风格.md`（当年明月/猫腻/金庸/古龙/孔二狗）+ `knowledge_base/40_Writing/风格指南/写作风格技能合集/`（24位网文作家）

### 执行流程
- 编排器：`novel_creation_promax/references/orchestrator.md`
- 工作流：`novel_creation_promax/references/workflow.md`
- 阶段交互：`novel_creation_promax/references/stages/`
- 状态管理：`novel_creation_promax/references/state-management.md`

### 记忆系统
- 人物档案模板：`novel-memory-pro/references/character_profile_template.md`
- 人物小传模板：`novel-memory-pro/references/character-biography-template.md`
- 角色弧线模板：`knowledge_base/20_Characters/角色弧线模板.md`
- 反派设计模板：`knowledge_base/20_Characters/反派设计模板.md`
- 群像角色关系模板：`knowledge_base/20_Characters/群像角色关系模板.md`
- 风格 DNA 格式：`novel-memory-pro/references/style_dna_format.md`
- 章节同步 Schema：`novel-memory-pro/references/chapter_sync_schema.md`

---

## 最佳实践

1. **短篇可轻装上阵**：直接描述想法，不需要初始化记忆系统
2. **长篇必须配记忆系统**：写到 30 章以后没有 `novel-memory-pro` 几乎必然吃设定
3. **每章创作前自检**：回答 9 个问题只需要 30 秒，但能杜绝 90% 的"水章节"
4. **定期体检**：每 5-10 章运行一次 `review-pack`，清理过期记忆、检查漂移
5. **针对平台调开篇**：如果目标是番茄/起点/晋江，先读 `platform-rules.md` 再写前三章

---

## 版本说明

- **`novel_creation_promax/`**：当前唯一活跃版本，整合了全部历史版本的深度内容
- `novel_creation_max/`、`novel_creation_max2.0/`、`skill_super-novel-writer/`：已退役，核心内容已全部迁移至 `promax`

---

**准备好开始创作了吗？直接告诉 Claude 你想写什么。**
