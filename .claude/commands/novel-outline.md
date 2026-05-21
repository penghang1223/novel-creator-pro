# 小说大纲

Generate or update outline and chapter plan.

**输入**：`/novel-outline [小说名] [卷/章节范围]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `outline` 模式。
2. 读取 `novel_creation_promax/references/orchestrator.md` Stage 3-4。
3. 输出或更新 `outline.md`、`细纲/卷一.md` 到 `细纲/卷八.md`、伏笔节点。
4. 如果这是从零长篇立项，完成后运行：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "{小说目录}"`
5. `seal` 失败时继续补齐大纲/设定/素材信息，不进入正文。

**示例**：`/novel-outline 我在末世开便利店 第一卷 1-30章`
