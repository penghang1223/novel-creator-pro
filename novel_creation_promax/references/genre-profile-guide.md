# 题材结构化配置指南

> 每个题材有一个 `.profile.yaml` 文件，定义机器可读的数值阈值和偏好参数。
> 与 `genre-specific-templates.md`（流程文档）互补：profile 是参数集，templates 是流程指南。

---

## 文件位置

| 文件 | 用途 |
|------|------|
| `assets/templates/genre-profile-schema.yaml` | Schema 定义（所有字段+默认值） |
| `knowledge_base/10_WorldBuilding/题材知识库/{题材}.profile.yaml` | 具体题材配置 |
| `references/genre-specific-templates.md` | 题材写作流程（人可读） |

已创建 profile 的题材：都市、言情、玄幻、仙侠、悬疑。

---

## 与约束模板的联动

写前约束组装时，从 profile 读取以下参数注入 `chapter_constraint_template.md` 的 `== 题材约束 ==` 区块：

| 约束项 | 来源字段 |
|--------|----------|
| 字数范围 | `pacing.target_word_count` |
| 开头钩子字数 | `pacing.opening_hook_within_chars` |
| 高潮位置 | `pacing.climax_at_percent` |
| 爽:压比例 | `cool_point.cool_to_pressure_ratio` |
| 对话占比目标 | `dialogue.target_ratio` |
| 主strand断档上限 | `strand_gap_limits.max_chapters_without_main_strand` |
| 偏好爽点类型 | `cool_point.preferred_types` |
| 偏好钩子类型 | `reading_power.preferred_hook_types` |

---

## 如何新建题材 Profile

1. 复制 `genre-profile-schema.yaml` 为 `{题材}.profile.yaml`
2. 填写 `genre` 字段
3. 按题材特性调整数值：
   - **爽文向**（玄幻/都市）：`cool_to_pressure_ratio` 偏高（8:2），`max_consecutive_no_cool_point_chapters` 设为 1
   - **情感向**（言情）：`dialogue.target_ratio` 偏高（35%），`micro_payoff.preferred_types` 偏好 M3/M5
   - **悬疑向**：`hook_density.small_per_chapter` 设为 2，`cool_to_pressure_ratio` 偏低（5:5）
4. 在 `genre_specific` 区块添加题材特有参数
5. 放入 `knowledge_base/10_WorldBuilding/题材知识库/` 目录
6. 更新 `SKILL.md` 题材知识库触发表的 Profile 列

---

## 数值参考

| 参数 | 爽文向 | 情感向 | 悬疑向 |
|------|--------|--------|--------|
| cool:pressure | 8:2 | 6:4 | 5:5 |
| dialogue target | 20% | 35% | 35% |
| opening_hook | 200字 | 300字 | 200字 |
| climax_at | 75% | 65% | 80% |
| no_cool_point_max | 1章 | 2章 | 3章 |
