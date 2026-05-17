# 记忆相关度过滤 + 生命周期

> 当前 `generate_chapter_pack()` 使用"最近 3 条"的粗暴启发式，导致不相关的记忆抢占上下文。
> 本文件定义相关度评分公式和状态生命周期，让记忆注入更精准。

---

## 相关度评分公式

每条记忆在生成 chapter pack 时计算相关度分数（0-100）：

```
score = recency(0-40) + importance(0-30) + connection(0-30)
```

### recency（时效性，0-40 分）

| 距上次引用章数 | 分数 |
|--------------|------|
| 1-2 章 | 40 |
| 3-5 章 | 30 |
| 6-10 章 | 20 |
| 11-15 章 | 10 |
| >15 章 | 0 |

### importance（重要性，0-30 分）

| 类型 | 分数 | 说明 |
|------|------|------|
| 主角人物档案 | 30 | 核心角色，永不过期 |
| 主线剧情 | 25 | 主线 plot，优先级最高 |
| 世界观设定 | 20 | 基础设定，偶尔需要引用 |
| 支线剧情 | 15 | 可以摘要形式注入 |
| 配角档案 | 15 | 活跃配角加权 |
| 历史章节摘要 | 10 | 越老越不重要 |
| 风格DNA | 25 | 每章都需要 |

### connection（关联性，0-30 分）

| 条件 | 分数 |
|------|------|
| 本章出场角色 | +15 |
| 本章推进的剧情线 | +15 |
| 实体图谱中与本章活跃实体有关系边 | +10 |
| 最近 3 章内被引用过 | +10 |
| 无直接关联 | 0 |

---

## 注入阈值

| 分数区间 | 注入方式 |
|---------|---------|
| ≥60 | 完整注入（全部字段） |
| 30-59 | 仅摘要注入（name + status + 关键事件） |
| <30 | 排除（不注入） |

**兜底规则**：
- 主角档案永远完整注入（不受分数限制）
- 主线剧情永远至少摘要注入
- 风格DNA永远完整注入

---

## 状态生命周期

| 状态 | 含义 | 触发条件 | 注入行为 |
|------|------|---------|---------|
| `active` | 活跃 | 被本章引用 / 最近 3 章内引用 | 完整注入 |
| `warm` | 温态 | 5 章未被引用 | 仅摘要注入 |
| `archived` | 归档 | 15 章未被引用 / review pack 推荐 | 不注入，仅在 review pack 中出现 |
| `compressed` | 压缩 | archived 后 10 章仍无引用 | 合并为阶段摘要，释放存储 |

### 自动状态转换

在 `build_review_pack()` 中自动执行：

```python
# warm → archived: 5 章无引用
if memory.status == "warm" and last_ref <= chapter - 5:
    memory.status = "archived"

# archived → compressed: 10 章无引用
if memory.status == "archived" and last_ref <= chapter - 10:
    memory.status = "compressed"  # 合并为阶段摘要
```

### 手动升级

用户可以手动将任何记忆从 archived 恢复为 active（当旧角色重新出场时）。

---

## 与 generate_chapter_pack 的联动

替换原来的 `[-3:]` 启发式：

```python
# 旧：粗暴截断
recent_contexts = [m for m in context_items if ...][-3:]

# 新：相关度过滤
scored = [(m, relevance_score(m, chapter, active_names)) for m in context_items]
recent_contexts = [m for m, s in scored if s >= 30]  # 至少摘要注入
full_contexts = [m for m, s in scored if s >= 60]    # 完整注入
```

---

## 与 build_review_pack 的联动

`build_review_pack()` 扩展职责：
1. 扫描所有 warm 状态记忆，5 章无引用 → archived
2. 扫描所有 archived 状态记忆，10 章无引用 → compressed（合并为阶段摘要）
3. 在 archive_candidates 中列出即将归档的记忆

---

## 存储

相关度分数是运行时计算的，不持久化。状态字段存储在每条 Memory 的 `metadata.status` 中。
