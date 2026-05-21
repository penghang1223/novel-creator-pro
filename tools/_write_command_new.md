# 写章节

写一章新章节，并强制走完写前/写后流水线。

**输入**：`/write 第X章 [章节名]`
**示例**：`/write 第52章 突破金丹期`

---

## 强制执行顺序（不可跳过）

### 1. 识别项目

从最近对话或当前 `MEMORY.md` / `progress.md` 找出**当前活跃小说**的目录，例如：
`novel_output/番茄/002_我发疯后全世界都正常了`

### 2. 写前流水线（pre）

```bash
python novel_creation_promax/scripts/write_pipeline.py pre \
  --novel-dir "<小说目录>" --chapter <N> --title "<章节标题>"
```

这一步会触发的硬门禁（任一不通过即停止）：

- **立项门禁**：`novel_state.json.workflow_gate.can_write_chapter == true`
- **前置审计门禁**：第 N-1 章必须已通过 post_write_audit（详见 write_pipeline.py 的 ensure_prev_chapter_audited）
- **9 问检查**：pre_write_check 分数 ≥ 70
- **记忆包**：chapter-pack 生成成功

**门禁失败时不要强行绕过**。补审计场景才用 `--override-prev-audit`，并在变更记录里登记。

### 3. 读路由表 + 必读 5 项

读取 `knowledge_base/_ROUTING.md`，按表头"每章必读 5 项"读：

1. `novel_creation_promax/references/writing_constitution.md`
2. `novel_creation_promax/references/写作速查卡.md`
3. 本章对应细纲：`<小说目录>/细纲/卷X_xxx.md`
4. 上一章正文
5. `novel_creation_promax/references/chapter_constraint_template.md`

按场景再从 `_ROUTING.md` 的"按需读取"部分挑 1-3 个。

### 4. 项目内必读

- `knowledge_base/80_Projects/<编号_书名>/伏笔追踪/总表.md`
- `knowledge_base/80_Projects/<编号_书名>/角色状态/<出场角色>.md`
- `knowledge_base/80_Projects/<编号_书名>/剧情节点/主线.md`

如果项目目录不存在或文件缺失：先跑 `python tools/init_kb_project.py --title "<书名>" --id <编号>` 生成骨架。

### 5. 写正文（Pass 1 + Pass 2）

按 SKILL.md 阶段 1-2 执行：先剧情稿、再 AI 词清理。

### 6. 写后流水线（post）

```bash
python novel_creation_promax/scripts/write_pipeline.py post \
  --novel-dir "<小说目录>" --chapter <N> --title "<章节标题>"
```

跑完会自动：
- writing_gate 7 项速检
- post_write_audit 完整审计
- style_calibrator + character_consistency_checker（如有 baseline）
- 摘要回填到 `记忆/`
- 在 `novel_state.json.chapters[NNN].audit_status` 写入 `pass`/`fail`

**未通过审计 → 不得开始下一章**。这是 write_pipeline.py pre 的硬门禁。

### 7. 同步 80_Projects

如果本章有新伏笔/角色变化/主线节点：

- 更新 `伏笔追踪/总表.md`
- 更新对应 `角色状态/{角色}.md`（last_appearance + status）
- 更新 `剧情节点/主线.md`
- 偏离细纲 → 在 `变更记录.md` 登记

---

## 默认行为

- 不主动跳过任何步骤
- 不在 CLAUDE.md 或 SKILL.md 里硬编码具体知识文件路径，只走 `_ROUTING.md`
- 任何"我觉得不需要跑 audit"的判断 = 错误，必须跑

## 紧急绕过（仅限补写历史章节）

```bash
python novel_creation_promax/scripts/write_pipeline.py pre \
  --novel-dir "..." --chapter N --title "..." --override-prev-audit
```

加 `--override-prev-audit` 时，必须同时在 `变更记录.md` 里登记原因。
