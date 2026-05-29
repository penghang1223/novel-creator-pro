# 项目架构优化方案

> 制定日期: 2026-05-21
> 核心策略: **保留全部 + 重组 + 单一来源映射**
> 总目标: 消除"三代体系叠加"造成的认知噪音；让 80% 写作行为都路由到同一组文件；脚本从摆设升级为硬门禁。

---

## 现状诊断（再确认）

| 维度 | 问题 |
|---|---|
| 知识库 | `knowledge_base/40_Writing/` 80+ 个文件，三代工作流（小说写作指南 / 小说创作工作流 / 工作流v2）并存 |
| 评估体系 | `50_Quality/` 22 个文件，至少 4 套打分（评分体系/创意五维/六编辑/虚拟读者）功能重叠 |
| 子技能死库 | `40_Writing/风格指南/写作风格技能合集/` 13 个完整作家 skill，无人调度 |
| 项目管理 | `80_Projects/` 9 个项目，只有 003/004/005 完整管理，其余只有 `_config.md` |
| 编号漂移 | `novel_output/番茄/002_发疯` ⇄ `80_Projects/003_发疯`，同书不同编号 |
| 脚本利用率 | `002_发疯` 43章只有 ch22-32 跑了 audit，pre_write_check 只跑过 1 次 |
| 引用环 | SKILL.md 阶段0列12项必读，实际单章必读文件 ≈ 20 个，模型必然只能假装读 |

---

## 三阶段路线图

### P0: 单一来源映射 + 弃用标记（今日执行，0 风险）

不动任何源文件，通过**新增 4 份索引/标记文件**让模型路由收敛。

#### P0-1: 写一份 `knowledge_base/_ROUTING.md` ✅

强制单一入口。所有"每章必读"只指向这一个文件，由它分发。

#### P0-2: 在重复/过时文件顶部插入 `<!-- DEPRECATED -->` 标记 ✅

不删除，让 Glob/Grep 仍能找到但语义上明确"非主用"。涉及：

- `40_Writing/02_节奏与结构/小说写作指南.md` → 指向 `工作流v2.md`
- `40_Writing/02_节奏与结构/小说创作工作流.md` → 指向 `工作流v2.md`
- `40_Writing/04_场景与描写/亲密场景写作.md` → 指向 `亲密场景写作指南.md`
- `40_Writing/写作技巧/{人物设定写作,大纲写作,正文写作,结构设计写作}.md` → 指向 `01_~07_` 阶段目录
- `50_Quality/{质量门,质量保证指南,闭环质量控制}.md` → 指向 `红线检查/红线系统.md` + `评估系统/评分体系.md`
- `knowledge_base/00_Inbox/临时001.md` → 待归位
- `knowledge_base/00_Inbox/humanizer-1.0.0/` → 整个标记为外部 skill 候选

#### P0-3: 写一份 `_LEGACY_INDEX.md`，列出所有 deprecated 文件原因 ✅

#### P0-4: 缩 CLAUDE.md 头部"每章必读"清单到 5 个 ✅

不动文件本身，只改 CLAUDE.md 引用路径，让它指向 `_ROUTING.md`。

---

### P1: 80_Projects 对齐 + 脚本硬门禁（本周）

#### P1-1: 编号对齐脚本

写 `tools/align_project_id.py`，扫描 `novel_output/{平台}/{编号_书名}/` 和 `80_Projects/{编号_书名}/`，找出编号或书名不一致的项，输出对齐建议（不自动改）。

#### P1-2: 补齐空壳项目

对每本只有 `_config.md` 的项目（006/010/她眼里有我的未来/被裁员…），用 `project_bootstrap_pipeline.py` 补齐五件套（伏笔/角色/剧情节点/项目索引/_config）。

#### P1-3: 脚本变硬门禁

在 `write_pipeline.py post` 完成时写入 `novel_state.json.last_audit_chapter = N`；
`write_pipeline.py pre` 启动时检查 `last_audit_chapter >= chapter_to_write - 1`，否则拒绝。

在 `.claude/commands/write.md` 里把这一检查写进 slash command。

#### P1-4: 给 002 补审计

对《002_我发疯后…》第 1-21 章 + 33-43 章批量跑 `audit_pipeline.py`，补齐 `素材/audit_chN.json` 历史档。

---

### P2: knowledge_base 收敛（下两周）

#### P2-1: `40_Writing/` 合并

- 删除 `写作技巧/` 4 文件（已在 P0 标 deprecated），内容已被 `01_~07_` 覆盖
- 合并 `小说写作指南.md` + `小说创作工作流.md` + `工作流v2.md` → 单一 `00_工作流.md`
- 合并 `亲密场景写作.md` + `亲密场景写作指南.md` → 单一文件

#### P2-2: `50_Quality/` 评分体系合并

`评估系统/` 6 文件 + `六编辑审稿系统.md` + `虚拟读者系统.md` + `创意五维评分.md` → 合并为 1 个 `evaluation.md`，列清"什么阶段用哪套"。

`质量门.md` + `质量保证指南.md` + `闭环质量控制.md` 三总纲删（已在 P0 deprecated）。

#### P2-3: 作家风格 skill 矩阵

`40_Writing/风格指南/写作风格技能合集/` → 独立成 `style-skills/` 顶级目录，与小说创作主流程脱钩；在主 SKILL.md 加调度入口（"用户说'用 XX 作家风格写'时才加载"）。

#### P2-4: SKILL.md 阶段 0 重写

12 项必读 → 5 项必读 + N 项 on-demand：

```
必读（每章）:
  1. references/writing_constitution.md
  2. references/写作速查卡.md
  3. 对应细纲/卷X_xxx.md
  4. 上一章正文
  5. references/chapter_constraint_template.md（自动填充本章约束）

按需（由 write_pipeline.py pre 决定）:
  - 高压场景 → 潜台词与张力技法.md
  - 对话密集 → 对话质感完整框架.md + AI对话丰满化技法.md
  - 节奏/卡章 → strand节奏追踪.md + 每章节奏公式.md
  - 题材特殊 → 题材知识库/{题材}.md
  - 风格漂移 → 降低AI痕迹.md
```

---

## 验收指标

| 指标 | 现状 | P0 后 | P1 后 | P2 后 |
|---|---|---|---|---|
| 每章必读文件数 | ~20 | 5（路由表分发）| 5 | 5 |
| 50_Quality/ 文件数 | 22 | 22（标 deprecated）| 22 | 12 |
| 40_Writing/ 文件数 | 80+ | 80+（标 deprecated）| 80+ | ~45 |
| 002 审计覆盖率 | 11/43 | 11/43 | 43/43 | 43/43 |
| 80_Projects 完整率 | 3/9 | 3/9 | 9/9 | 9/9 |
| CLAUDE.md 行数 | 600+ | 400 | 300 | 250 |
| 三套工作流并存 | yes | yes（标）| yes | no（合一）|

---

## 本次提交（P0 执行清单）

- [x] 创建 `OPTIMIZATION_PLAN.md`（本文档）
- [x] 创建 `knowledge_base/_ROUTING.md`
- [x] 创建 `knowledge_base/_LEGACY_INDEX.md`
- [x] 给 9 个 deprecated 文件顶部加注释标记
- [x] 修改 `CLAUDE.md`：将"每章必读"清单改为指向 `_ROUTING.md`
- [x] 修改 `novel_creation_promax/SKILL.md` 阶段 0：把 12 项必读精简注释（不删功能，只改默认路径）

## 本轮架构治理补充（2026-05-29）

- [x] 新增 `.gitignore`，覆盖本地密钥、运行缓存、构建产物、`novel_output/` 与 `knowledge_base/flux/`
- [x] 将 `config.toml`、`cc-connect-config.toml` 保留在本地但取消 git 跟踪
- [x] 按 `MODE_REGISTRY.md` 统一 `SKILL.md` 功能菜单编号
- [x] 新增 `tools/align_project_id.py`，只读扫描 `novel_output/` 与 `knowledge_base/80_Projects/` 的编号/命名漂移
- [x] 新增 `novel_creation_promax/core/`，统一路径、JSON、passport、知识路由、项目注册表逻辑
- [x] 新增 `knowledge_base/_ROUTES.json`，将知识路由从纯 Markdown 约定升级为机器可读契约
- [x] `write_pipeline.py pre` 生成 `摘要/chapter_NNN_knowledge_pack.json`
- [x] 下一章审计门禁改为读取上一章 passport / novel_state 的明确 pass 状态，不再仅凭 audit 文件存在放行
- [x] Web Dashboard 复用 core 章节查找与 passport 状态，兼容 `001_标题.md` / `chapter_001.md` 等命名
- [x] 新增 `tools/build_project_registry.py`、`tools/knowledge_routes_check.py`、`tools/knowledge_lint.py`
- [x] `tools/health_check.py` 扩展到 core 包、知识路由和项目注册表生成检查

后续 P1/P2 等你确认 P0 效果后再启动。
