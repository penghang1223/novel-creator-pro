# 自动触发规则

以下规则在执行任何功能时自动生效。

## 题材知识库触发

| 用户提到 | 自动读取 | Profile |
|----------|----------|---------|
| 都市 | `knowledge_base/10_WorldBuilding/题材知识库/都市.md` | `.profile.yaml` |
| 科幻 | `knowledge_base/10_WorldBuilding/题材知识库/科幻.md` | — |
| 仙侠/修仙 | `knowledge_base/10_WorldBuilding/题材知识库/仙侠.md` | `.profile.yaml` |
| 玄幻/奇幻 | `knowledge_base/10_WorldBuilding/题材知识库/玄幻.md` | `.profile.yaml` |
| 悬疑/推理/惊悚 | `knowledge_base/10_WorldBuilding/题材知识库/悬疑.md` | `.profile.yaml` |
| 言情/恋爱/女频 | `knowledge_base/10_WorldBuilding/题材知识库/言情.md` | `.profile.yaml` |
| 灵异/恐怖 | `knowledge_base/10_WorldBuilding/题材知识库/灵异.md` | — |
| 无限流/游戏 | `knowledge_base/10_WorldBuilding/题材知识库/无限流.md` | — |
| 历史/架空 | `knowledge_base/10_WorldBuilding/题材知识库/历史.md` | — |
| 大女主 | `knowledge_base/10_WorldBuilding/题材知识库/大女主.md` | — |

## 写作技巧库触发

| 写作环节 | 自动读取 |
|----------|----------|
| 正文写作/描写/对话 | `knowledge_base/40_Writing/写作技巧/正文写作.md` |
| 写大纲/章节规划 | `knowledge_base/40_Writing/写作技巧/大纲写作.md` |
| 人物设定/世界观构建 | `knowledge_base/40_Writing/写作技巧/人物设定写作.md` |
| 结构设计/节奏把控 | `knowledge_base/40_Writing/写作技巧/结构设计写作.md` |
| 亲密场景/感情线 | `knowledge_base/40_Writing/04_场景与描写/亲密场景写作指南.md` |
| 对话场景/潜台词/张力 | `knowledge_base/40_Writing/04_场景与描写/潜台词与张力技法.md` |
| 修仙/修炼体系 | `knowledge_base/10_WorldBuilding/题材知识库/修仙体系构建指南.md` |
| 推理/探案流程 | `knowledge_base/10_WorldBuilding/题材知识库/推理破案流程指南.md` |
| 灵异/恐怖氛围 | `knowledge_base/10_WorldBuilding/题材知识库/恐怖氛围营造指南.md` |
| 职场/创业/商战 | `knowledge_base/10_WorldBuilding/题材知识库/职场商战指南.md` |
| 末世/废土 | `knowledge_base/10_WorldBuilding/题材知识库/末世生存指南.md` |
| 校园/青春 | `knowledge_base/10_WorldBuilding/题材知识库/校园青春指南.md` |
| 权谋/宫斗 | `knowledge_base/10_WorldBuilding/题材知识库/权谋宫斗指南.md` |

## 速查卡触发

每章正文写作前，自动读取 `references/写作速查卡.md`，提取本章相关规则到约束组装中。

| 阶段 | 速查卡章节 | 用途 |
|------|-----------|------|
| 写前 | §一 | 字数分配、断章位置、张力模板 |
| Pass 1 | §二-§六 | 对话六要素、爽点流水线、潜台词技法 |
| Pass 2 | §七-§八 | "每段三刀"法则、20 条硬性禁止 |
| 写后 | §九 | 套路绕开策略 |

## 立项触发

[9.0] 长篇立项启动时，自动执行：
- 平台热门趋势：`knowledge_base/60_Platform/平台热门趋势.md`
- 流派模板：`knowledge_base/10_WorldBuilding/流派模板总览.md`
- 五维评分：`knowledge_base/50_Quality/创意五维评分.md`（≥65分通过，55-64修改重评，<55重新构思）

## 毒舌/搞笑语料触发

选择"搞笑沙雕风"或要求毒舌/幽默风格时自动读取：

| 语料 | 用途 |
|------|------|
| `knowledge_base/70_Corpus/毒舌语料/毒舌知识库.md` | 毒舌风格参考（~600条） |
| `knowledge_base/70_Corpus/神回复语料/315条神回复.md` | 网络神回复（315条） |
| `knowledge_base/70_Corpus/神回复语料/110个神回复示例.md` | 神回复示例（110条） |
| `knowledge_base/70_Corpus/神回复语料/话废菩萨语料.md` | 话废人设对话参考 |
| `knowledge_base/70_Corpus/毒舌语料/毒舌AI示例库.md` | AI角色毒舌风格参考 |

## 审稿系统触发

| 触发场景 | 动作 |
|----------|------|
| 写完一章后 | **自动执行基础审计**（post_write_audit），不通过必须修复后方可交付 |
| "审一下"/"帮我看看"/"质量怎么样" | 进入**深度审稿**流程 → `review-skill/SKILL.md` |
| 基础审计发现问题较多 | 自动建议进入深度审查 |

## 连贯性系统触发

| 场景 | 读取 |
|------|------|
| 偏离大纲 | `knowledge_base/30_Plot/偏离处理.md` |
| 维护主线 | `knowledge_base/30_Plot/主线节点维护.md` |
| 细纲执行 | `knowledge_base/30_Plot/细纲执行机制.md` |
| 定期复盘 | `knowledge_base/30_Plot/定期复盘机制.md` |
