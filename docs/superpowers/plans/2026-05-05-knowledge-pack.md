# 知识包自动组装实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SKILL.md 的 Phase 0 写前准备中新增"知识包组装"步骤，让 AI 写前自动从知识库提取本章相关的精简知识点（~200-400 字），注入写作 prompt。

**Architecture:** 只改一个文件（SKILL.md），在 Phase 0 的"约束组装"和"套路预判"之间插入新步骤。AI 按场景类型读取对应知识目录，组装精简知识包。无新脚本、无新组件。

**Tech Stack:** Markdown（SKILL.md 内容指令）

---

## 文件清单

| 文件 | 动作 | 说明 |
|------|------|------|
| `novel_creation_promax/SKILL.md` lines 26-29 | 修改 | Phase 0 新增 Step 5 知识包组装，原 Step 5 套路预判变为 Step 6 |
| `novel_creation_promax/SKILL.md` line 50 | 修改 | Gate 检查从 6 项更新为 7 项（用户已加非中文字符检查） |

---

## Task 1: 在 Phase 0 新增知识包组装步骤

**Files:**
- Modify: `novel_creation_promax/SKILL.md` lines 26-29

- [ ] **Step 1: 读取当前 Phase 0 内容确认插入点**

当前 Phase 0（lines 21-29）：
```
阶段 0：写前准备
1. 加载写作宪法
2. 9问必答
3. 写前5项检查
4. 约束组装（line 26）
5. 套路预判（line 27）
```

插入点：line 26（约束组装）和 line 27（套路预判）之间。

- [ ] **Step 2: 插入知识包组装步骤**

将 SKILL.md 的 line 27 从：

```markdown
5. **套路预判** → 参照速查卡 §九，列出本章可能涉及的套路+绕开策略
```

替换为：

```markdown
5. **知识包组装** → 根据本章细纲，从知识库提取本章相关知识点（详见下方知识包组装流程）
6. **套路预判** → 参照速查卡 §九，列出本章可能涉及的套路+绕开策略
```

- [ ] **Step 3: 在阶段 0 小节末尾（`未完成以上任何一项` 之前）添加知识包组装详细流程**

在 line 29（`未完成以上任何一项...`）之前插入：

```markdown

#### 知识包组装流程

**输入**：本章细纲（从 `细纲/卷X_标题.md` 定位本章段落）

**Step A：提取本章元信息**
从细纲中提取：出场人物 / 场景类型（对话/动作/情绪/悬疑/环境） / 核心冲突 / 情绪基调 / 章末截断点

**Step B：按场景类型读取知识**

| 场景类型 | 读取路径 |
|---------|---------|
| 对话场景 | `knowledge_base/40_Writing/03_人物与对话/` 下相关文件 |
| 情绪/心理 | `knowledge_base/40_Writing/04_场景与描写/` 下相关文件 |
| 悬疑/紧张 | `knowledge_base/40_Writing/02_节奏与结构/` 下相关文件 |
| 去AI（每章必读） | `knowledge_base/40_Writing/05_降AI痕迹/` 下相关文件 |
| 毒舌/特殊语体 | `knowledge_base/70_Corpus/毒舌知识库.md` |

某类场景不涉及 → 跳过对应读取（不浪费 token）。

**Step C：读取出场人物档案**
从 `设定/人物设定.md`（或 `设定/人物档案/`）提取本章出场角色的：矛盾特质 / 行为指纹 / 负面约束

**Step D：组装知识包（≤400字）**

```markdown
# 第N章 知识包

## 出场人物
- 角色A：矛盾特质=xxx，行为指纹=xxx，本章注意=xxx
- 角色B：矛盾特质=xxx，行为指纹=xxx，本章注意=xxx

## 本章场景类型：[类型]
适用技法：
- [技法要点1]
- [技法要点2]

## 本章高危项
- 绝对禁止词已加载（13个）
- 高危限制词 ≤3 次
- 本章重点去AI：[具体项]

## 平台要求
- 字数：[范围]
- 截断点：[事件]
```

**Step E：注入写作 prompt**
知识包在 Pass 1 开始时直接包含在写作指令中，作为"本章写作指引"。

**约束**：
- 知识包是建议不是命令，不替代写作宪法的硬约束
- 每次写前重新生成，不缓存
- 知识库中找不到对应文件 → 跳过该项，不报错
```

- [ ] **Step 4: 验证 SKILL.md 结构完整性**

```bash
# 确认阶段 0 现在有 6 个步骤
grep -n "^\*\*加载写作宪法\*\*\|^\*\*9问必答\*\*\|^\*\*写前5项\*\*\|^\*\*约束组装\*\*\|^\*\*知识包组装\*\*\|^\*\*套路预判\*\*" novel_creation_promax/SKILL.md

# 确认知识包组装流程已插入
grep -n "知识包组装流程" novel_creation_promax/SKILL.md

# 确认其他阶段未受影响
grep -n "阶段 1\|阶段 2\|阶段 3" novel_creation_promax/SKILL.md
```

预期：阶段 0 有 6 个步骤标记，知识包组装流程存在，阶段 1/2/3 位置不变。

- [ ] **Step 5: 提交**

```bash
git add novel_creation_promax/SKILL.md
git commit -m "feat: add knowledge pack assembly step to Phase 0 pre-write workflow
- AI auto-extracts relevant knowledge from knowledge_base by scene type
- Output: ~200-400 char chapter-specific knowledge pack
- Injected into Pass 1 writing prompt as guidance"
```

---

## Task 2: 更新 Gate 检查项数

**Files:**
- Modify: `novel_creation_promax/SKILL.md` line 50

- [ ] **Step 1: 更新 Gate 检查描述**

当前 line 50：
```markdown
6 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 计时器心理 / 对话占比。
```

替换为：
```markdown
7 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 计时器心理 / 对话占比 / 非中文字符。
```

- [ ] **Step 2: 提交**

```bash
git add novel_creation_promax/SKILL.md
git commit -m "chore: update gate check count from 6 to 7 (added foreign char check)"
```

---

## 验证

- [ ] 用现有小说测试知识包组装：选第 12 章，人工模拟 AI 执行 Step A-E，检查输出格式
- [ ] 确认 SKILL.md 总行数变化合理（增加约 50 行）
- [ ] 确认阶段 1/2/3 和菜单功能未受影响

## 回滚

```bash
git revert HEAD~2..HEAD
```
