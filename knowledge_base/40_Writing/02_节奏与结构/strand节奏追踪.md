---
tags: [节奏, 追踪, strand, 预警]
---

# Strand Weave 节奏追踪系统

借鉴 webnovel-writer 的 Strand Weave 概念，将每章的叙事内容归类到三条叙事线（strand），追踪比例和断档，防止读者疲劳。

## 三条叙事线

| Strand | 含义 | 典型内容 |
|--------|------|----------|
| **Quest** | 主线剧情 | 推动核心冲突、打怪升级、阴谋推进、任务执行 |
| **Fire** | 感情线 | 男女主互动、暧昧升温、感情冲突、关系变化 |
| **Constellation** | 世界观扩展 | 势力介绍、背景揭示、新能力/新地图、设定展开 |

每章有一个 `primary`（主 strand）和一个可选的 `secondary`（次 strand）。大部分章节以一条线为主，偶尔双线并行。

## 预警红线

| 规则 | 红线 | 级别 | 说明 |
|------|------|------|------|
| Quest 连续 | ≤5 章 | 红 | 主线推太久读者疲劳，必须切感情线或世界观缓一缓 |
| Fire 断档 | ≤10 章 | 红 | 感情线消失太久读者遗忘 CP 线 |
| Constellation 断档 | ≤15 章 | 黄 | 世界观太久不扩展，设定停滞 |
| 张力连续高位 | ≥8 连续 3 章 | 黄 | 高压太久读者喘不过气 |
| 张力连续低位 | ≤3 连续 3 章 | 红 | 太平淡读者弃书 |
| 同 pace_type 连续 | 同类型 3 章 | 黄 | 节奏单一，需要变化 |

## 数据结构

### novel_state.json 中的 strand_tracking

```json
{
  "strand_tracking": {
    "chapters": [
      {"chapter": 1, "primary": "quest", "secondary": null, "tension": 6, "pace_type": "推进"},
      {"chapter": 2, "primary": "quest", "secondary": "fire", "tension": 4, "pace_type": "铺垫"},
      {"chapter": 3, "primary": "quest", "secondary": "fire", "tension": 5, "pace_type": "铺垫"},
      {"chapter": 4, "primary": "quest", "secondary": null, "tension": 8, "pace_type": "高潮"},
      {"chapter": 5, "primary": "fire", "secondary": "constellation", "tension": 2, "pace_type": "过渡"}
    ],
    "warnings": [
      {"chapter": 4, "rule": "quest连续4章", "severity": "yellow", "action": "下章建议切换到fire"}
    ]
  }
}
```

### chapter-summary.json 中的 strand

```json
{
  "strand": {
    "primary": "quest",
    "secondary": "fire",
    "tension": 7,
    "pace_type": "推进"
  }
}
```

## 使用方式

**写前**：确定本章 strand 类型，检查是否触发预警红线。如果触发，调整本章 strand 或与用户讨论。

**写后**：在章节摘要中记录 strand 信息，同步到 novel_state.json 的 strand_tracking。

**审稿时**：检查跨章节的 strand 分布是否均衡，预警是否得到响应。

## 与五章张力模板的关系

速查卡 §1.6 的五章模板（张力 6/4/5/8-9/2-3）对应 pace_type：

| 章序 | 张力 | pace_type | strand 建议 |
|------|------|-----------|------------|
| 第1章 | 6 | 推进 | Quest 为主 |
| 第2章 | 4 | 铺垫 | 可引入 Fire/Constellation |
| 第3章 | 5 | 铺垫 | 继续铺垫，双线并行 |
| 第4章 | 8-9 | 高潮 | Quest 高燃 |
| 第5章 | 2-3 | 过渡 | Fire 或 Constellation 缓冲 |

这是理想模板，实际写作中不必严格遵守，但连续偏离模板时应有意识地做出选择。
