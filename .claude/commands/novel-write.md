# 小说正文写作

Write or continue a chapter through the Pro Max pipeline.

**输入**：`/novel-write [小说名] 第N章 [标题]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `chapter-write` 模式。
2. 写前先确认 `novel_state.json.workflow_gate.can_write_chapter=true`；否则运行：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "{小说目录}"`
3. 写前运行：
   `python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "{小说目录}" --chapter N --title "{标题}"`
   然后读取 `摘要/chapter_NNN_rule_stack.json` 和 `素材/chapter_NNN_truth_brief.md`。这两个文件是本章硬约束，不能跳过。
   并先按番茄默认预算组织正文：首稿目标 2950-3150 中文字符，建议 5-6 场，每场 450-650 字。
4. 正文完成后运行：
   `python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "{小说目录}" --chapter N --title "{标题}"`
   `post` 会先生成 `素材/truth_delta_candidates_chNNN.md`。必须审查候选事实，再补齐 `摘要/chapter_NNN_truth_delta.json`：属实事实写入 observations/updates，误报写进 `auto_extraction.review_note`，`auto_extraction.review_status=reviewed`，`status=approved` 或 `no_changes`。
   如果 `post` 报字数不足，不允许直接交付，必须先补写有效剧情到 2800-3200 再重跑。

**示例**：`/novel-write 我在末世开便利店 第12章 夜班来客`
