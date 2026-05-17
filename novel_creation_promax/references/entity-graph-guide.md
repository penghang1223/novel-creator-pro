# 实体图谱指南 (Entity Graph Guide)

> 实体图谱 = 角色/地点/物品/势力/功法的结构化追踪 + 关系边 + 别名解析。
> 存储为 JSON，位于每个项目的 `memory/entity_graph.json`。

---

## 实体类型

| 类型 | type 值 | 示例 |
|------|---------|------|
| 角色 | `character` | 主角、配角、NPC |
| 地点 | `location` | 城市、建筑、秘境 |
| 物品 | `item` | 法宝、关键道具 |
| 势力 | `faction` | 宗门、家族、组织 |
| 功法 | `technique` | 修炼功法、技能 |

---

## Canonical ID 命名规则

格式：`{type}_{canonical_name}`

- 角色：`character_沈知言`
- 地点：`location_天玄宗`
- 物品：`item_蛇绕古币`
- 势力：`faction_玄天门`
- 功法：`technique_九转玄功`

**命名原则**：
- 使用最常用的正式名称作为 canonical_name
- 不用昵称/简称作为 canonical_name（这些放 aliases）
- 一旦确定不轻易改（改名 = 新实体 + 旧实体 archived）

---

## 别名解析

每个实体有 `aliases` 数组，包含所有已知称呼：

```json
{
  "entity_id": "character_沈知言",
  "canonical_name": "沈知言",
  "aliases": ["知言", "沈师兄", "沈师弟"]
}
```

查询时先匹配 canonical_name，再匹配 aliases。正文出现别名时自动解析到对应实体。

---

## 关系边

```json
{
  "source": "character_沈知言",
  "target": "character_林若雪",
  "relation_type": "恋人",
  "polarity": "positive",
  "strength": 8,
  "established_chapter": 15,
  "status": "active"
}
```

| 字段 | 说明 | 取值 |
|------|------|------|
| `source` | 来源实体 ID | 任意 entity_id |
| `target` | 目标实体 ID | 任意 entity_id |
| `relation_type` | 关系类型 | 自由文本（师徒/恋人/敌对/同盟/...) |
| `polarity` | 关系极性 | `positive` / `negative` / `neutral` / `complex` |
| `strength` | 关系强度 | 1-10 |
| `established_chapter` | 建立章节 | 章节号 |
| `status` | 当前状态 | `active` / `dissolved` / `evolved` |

---

## 状态时间线

每个实体有 `state_timeline` 数组，记录每个关键章节的状态快照：

```json
{
  "state_timeline": [
    {"chapter": 1, "state": {"境界": "炼气三层", "身份": "外门弟子"}},
    {"chapter": 50, "state": {"境界": "筑基期", "身份": "内门弟子"}}
  ]
}
```

只记录有变化的字段，不重复存储不变信息。

---

## 实体状态生命周期

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `active` | 活跃，每章写前注入 | 最近 5 章内出现或被引用 |
| `warm` | 温态，仅摘要注入 | 5-15 章未出现 |
| `archived` | 归档，不注入 | >15 章未出现 |

状态由 `entity_graph_manager.py` 自动管理，也可手动调整。

---

## 与 chapter-summary 联动

章节摘要新增两个字段：

- `new_entities[]`：本章首次出现的实体，格式 `{"entity_id": "", "type": "", "canonical_name": ""}`
- `relationship_changes[]`：本章变化的关系，格式 `{"source": "", "target": "", "action": "create|update|dissolve", "details": {}}`

`sync_chapter()` 时处理这些事件，更新 entity_graph.json。

---

## 与 chapter-pack 联动

`generate_chapter_pack()` 时：
1. 加载 entity_graph.json
2. 筛选 status=active 的实体
3. 附带它们的关系边（source 和 target 都是 active）
4. 注入到 chapter pack 的 `entity_context` 字段

---

## 查询示例

| 查询 | 方法 | 返回 |
|------|------|------|
| 查角色的所有关系 | `query_connections("character_沈知言")` | 关系边列表 |
| 查活跃实体 | `query_active(chapter=30)` | 活跃实体列表 |
| 别名解析 | `resolve_alias("知言")` | `character_沈知言` |
| 查两个实体的关系路径 | `find_path("A", "B")` | 实体 ID 路径 |

---

## 存储位置

| 文件 | 内容 |
|------|------|
| `memory/entity_graph.json` | 实体图谱数据 |
| `assets/templates/entity-graph.json` | 空模板 |
| `novel-memory-pro/scripts/entity_graph_manager.py` | 管理脚本 |
