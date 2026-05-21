# 小说正文写作

Write or continue a chapter through the Pro Max pipeline.

**输入**：`/novel-write [小说名] 第N章 [标题]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `chapter-write` 模式。
2. 写前先确认 `novel_state.json.workflow_gate.can_write_chapter=true`；否则运行：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "{小说目录}"`
3. 写前运行：
   `python novel_creation_promax/scripts/write_pipeline.py pre --novel-dir "{小说目录}" --chapter N --title "{标题}"`
   并先按番茄默认预算组织正文：首稿目标 2950-3150 中文字符，建议 5-6 场，每场 450-650 字。
4. 正文完成后运行：
   `python novel_creation_promax/scripts/write_pipeline.py post --novel-dir "{小说目录}" --chapter N --title "{标题}"`
   如果 `post` 报字数不足，不允许直接交付，必须先补写有效剧情到 2800-3200 再重跑。

**示例**：`/novel-write 我在末世开便利店 第12章 夜班来客`
