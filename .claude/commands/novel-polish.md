# 小说润色

Polish an existing chapter and record revision history.

**输入**：`/novel-polish [小说名] 第N章 [方向]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `polish` 模式。
2. 读取原章节文件，不只在聊天窗口修改。
3. 完成后运行 `write_pipeline.py post` 或 `audit_pipeline.py`。
4. 更新 `novel_state.json.revision_history`。

**示例**：`/novel-polish 我在末世开便利店 第12章 降AI味、增强对话`

