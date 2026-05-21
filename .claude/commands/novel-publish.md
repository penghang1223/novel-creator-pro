# 小说发布同步

Sync chapters to publishing directories and update publish state.

**输入**：`/novel-publish [平台] [小说名] [--short]`

**番茄同步**：
```bash
python scripts/sync_to_fanqie.py "书名"
python scripts/sync_to_fanqie.py --short "书名"
```

**执行后**：
- 更新 chapter passport 的 `publish.status`
- 更新 `novel_state.json.publish_state`

**示例**：`/novel-publish 番茄 我在末世开便利店`

