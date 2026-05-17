# LLM 生成搜索关键词 → 向量检索

> 借鉴 AI_NovelGenerator：不直接注入"最近N条"记忆，而是先让 LLM 生成"这章需要查什么"的搜索关键词，再按关键词精确检索。
> 结合现有的相关度评分系统，形成"关键词召回 + 相关度过滤"的双层检索。

## 流程

```
Chapter N 写前
    │
    ▼
Step 1: LLM 生成搜索关键词
    │  基于：本章细纲 + 出场人物 + 前一章结尾
    │  输出：5-10 个搜索关键词（实体名/剧情线/设定术语/伏笔编号）
    │
    ▼
Step 2: 按关键词检索
    │  从 entity_graph + chapter_summaries + character_profiles 中
    │  匹配包含关键词的记忆条目
    │
    ▼
Step 3: 相关度过滤
    │  对检索结果执行 relevance_score() 过滤
    │  ≥60 → 完整注入
    │  30-59 → 摘要注入
    │  <30 → 排除
    │
    ▼
Step 4: 输出 chapter pack
```

## 搜索关键词类型

| 类型 | 示例 | 检索范围 |
|------|------|---------|
| 实体名 | "沈知言"、"天衍宗" | entity_graph, character_profiles |
| 剧情线 | "入赘真相"、"灵根觉醒" | chapter_summaries, plot_updates |
| 设定术语 | "九转玄功"、"灵根等级" | world_building, knowledge_base |
| 伏笔编号 | "F003"、"蛇绕古币" | foreshadowing |
| 关系 | "沈知言→林清月" | entity_graph edges |
| 事件 | "入宗考核"、"秘境试炼" | chapter_summaries key_events |

## 与 memory_manager.py 的集成

在 `generate_chapter_pack()` 中：
1. 先加载本章细纲 + 上一章摘要
2. 从细纲提取出场人物、场景类型、核心冲突
3. 生成关键词列表（entity names + plot line names + 伏笔 ID）
4. 用关键词在 entity_graph + chapter_summaries 中做子串匹配
5. 对匹配结果做 relevance_score 过滤
6. 输出最终 chapter pack

## 注意事项

- 关键词生成是"假设性"的——LLM 预测需要什么信息，可能遗漏
- 相关度评分是"补漏性"的——即使关键词没命中，高相关度记忆仍会注入
- 双层互补：关键词确保精确性，相关度确保完整性
