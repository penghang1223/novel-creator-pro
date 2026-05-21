# 已弃用文件索引

> 这些文件**不删除**（防止破坏旧引用），但**不应再被作为主用知识读取**。
> 模型读取知识时若 Grep/Glob 命中以下文件，应跳过或仅作历史参考。
> 文件顶部均已加 `<!-- DEPRECATED -->` 标记。

---

## 工作流类（被 `工作流v2.md` 取代）

| 文件 | 原因 | 替代 |
|---|---|---|
| `knowledge_base/40_Writing/02_节奏与结构/小说写作指南.md` | 第一代工作流 | `工作流v2.md` |
| `knowledge_base/40_Writing/02_节奏与结构/小说创作工作流.md` | 第二代工作流 | `工作流v2.md` |

## 评估系统总纲类（与 `评估系统/评分体系.md` + `红线检查/红线系统.md` 重复）

| 文件 | 原因 | 替代 |
|---|---|---|
| `knowledge_base/50_Quality/质量门.md` | 写前/写中/写后总纲 | `红线检查/章节前检查.md` + `post_write_audit.py` |
| `knowledge_base/50_Quality/质量保证指南.md` | 总纲性质 | `红线检查/红线系统.md` |
| `knowledge_base/50_Quality/闭环质量控制.md` | 闭环总图 | `_ROUTING.md` 评估系统章节 |

## 写作技巧旧分类（被 `01_~07_` 按阶段目录取代）

| 文件 | 原因 | 替代 |
|---|---|---|
| `knowledge_base/40_Writing/写作技巧/人物设定写作.md` | 旧分类 | `01_开篇技巧/`+`03_人物与对话/` |
| `knowledge_base/40_Writing/写作技巧/大纲写作.md` | 旧分类 | `02_节奏与结构/工作流v2.md` |
| `knowledge_base/40_Writing/写作技巧/正文写作.md` | 旧分类 | `01_~05_` 全分类 |
| `knowledge_base/40_Writing/写作技巧/结构设计写作.md` | 旧分类 | `02_节奏与结构/` |

## 场景写作重复

| 文件 | 原因 | 替代 |
|---|---|---|
| `knowledge_base/40_Writing/04_场景与描写/亲密场景写作.md` | 旧版 | `亲密场景写作指南.md` |

## 收件箱待处理

| 文件 | 原因 | 处理 |
|---|---|---|
| `knowledge_base/00_Inbox/临时001.md` | 待归位 | P1 期间归类 |
| `knowledge_base/00_Inbox/humanizer-1.0.0/` | 外部 skill 包 | 评估后或独立或删除 |
| `knowledge_base/00_Inbox/tools-reference.md` | 待归位 | P1 期间归类 |

## 历史归档（占空间但 0 价值）

| 目录 | 内容 | 处理 |
|---|---|---|
| `knowledge_base/15_Ideas/惊鸿归档/` | 旧《修仙界送外卖》v1.0-v3.1 章节稿 + P0 报告 + memory-agents-old | P1 期间整体移到 git LFS 或外部备份 |

---

## 维护规则

- 文件加入 deprecated → 同步在本表加一行 + 文件头部加 `<!-- DEPRECATED: see _LEGACY_INDEX.md -->`
- 替代文件本身被 deprecated → 链式更新
- 半年后未被任何工具引用 → P3 阶段批量物理删除
