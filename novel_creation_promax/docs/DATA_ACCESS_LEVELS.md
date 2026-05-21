# Data Access Levels

> 本文规定不同任务允许读取的数据范围，避免上下文膨胀和记忆污染。

## 层级定义

| level | 读取内容 | 使用场景 | 风险 |
|---|---|---|---|
| `verified_state` | 用户确认过的设定、人物、伏笔、项目配置 | 所有任务默认读取 | 最低 |
| `memory_pack` | 当前章节相关记忆包 | 长篇续写、润色、审稿 | 低 |
| `chapter_context` | 上一章、当前章、下一章细纲 | 正文写作、衔接修复 | 中 |
| `full_text` | 多章或全书正文 | 全书审稿、复盘、重写 | 高，易占上下文 |
| `draft_state` | 临时想法、未确认设定、聊天草稿 | 立项探索 | 中，不可覆盖正式设定 |
| `publish_state` | 发布目录、草稿/上传状态 | 多平台输出、发布同步 | 中 |

## 默认策略

- 正文写作：`verified_state + memory_pack + chapter_context`。
- 润色：`verified_state + 当前章节 full_text + 必要 memory_pack`。
- 深度审稿：`verified_state + 当前章节 full_text + 相邻章节 chapter_context`。
- 全书复盘：允许 `full_text`，但先生成分章摘要再汇总。
- 发布同步：读取 `publish_state + 正文`，不改剧情内容。

## 写入优先级

冲突时按以下顺序裁决：

```text
用户明确确认 > 已发布正文 > novel_state.json > novel-memory-pro > draft_state > 模型推断
```

## 禁止事项

- 不得用临时脑洞覆盖正式人物设定。
- 不得只凭模型推断修改伏笔状态。
- 不得在写正文时无差别读取全书正文。
- 不得把审稿建议直接写入知识库，除非用户确认。

