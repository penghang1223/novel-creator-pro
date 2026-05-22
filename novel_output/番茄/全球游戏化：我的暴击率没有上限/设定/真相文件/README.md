# 全球游戏化：我的暴击率没有上限 真相文件

这些 JSON 是正文写作的事实源，不是灵感草稿。

- `characters.json`: 人物现实锚点、动机、声纹、行为边界
- `locations.json`: 地点成本、通勤、权限、场景用途
- `factions.json`: 势力资源、利益、行动边界
- `events.json`: 事件因果、证据链、剧情债
- `relationships.json`: 信任、冲突、信息差、关系变化规则
- `resources.json`: 金钱、技能、权限、道具、系统能力及代价
- `foreshadowing.json`: 伏笔埋设、回收计划、遗忘风险

写第 N 章前运行 `write_pipeline.py pre` 会编译本章 `rule_stack`；写后必须补齐 `chapter_NNN_truth_delta.json`。
