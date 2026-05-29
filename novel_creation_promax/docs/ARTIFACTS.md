# Artifacts

> 本文规定小说项目产物结构和每章 passport。用于健康检查、流水线和后续发布同步。

## 小说目录结构

长篇项目：

```text
novel_output/{平台}/{小说名}/
├── 创意/
├── 设定/
│   ├── 世界观与人物.md
│   ├── 人物档案.md
│   ├── 地点档案.md
│   ├── 势力档案.md
│   ├── 事件档案.md
│   ├── 关系网络.md
│   ├── 常识约束.md
│   └── 真相文件/
│       ├── characters.json
│       ├── locations.json
│       ├── factions.json
│       ├── events.json
│       ├── relationships.json
│       ├── resources.json
│       └── foreshadowing.json
├── 结构/
├── 细纲/
├── 正文/
├── 摘要/
├── 记忆/
├── 素材/
├── outline.md
└── novel_state.json
```

长篇立项门禁要求：

```text
记忆/project_bootstrap.json
记忆/style_dna_baseline.json
设定/人物档案.md
设定/地点档案.md
设定/势力档案.md
设定/事件档案.md
设定/关系网络.md
设定/常识约束.md
设定/真相文件/*.json
细纲/卷一.md ... 细纲/卷八.md
素材/小说信息.md
素材/project_bootstrap_gate.json
knowledge_base/80_Projects/{小说名}/_config.md
```

## 设定底座

长篇开写前必须完成设定底座，否则 `project_bootstrap_pipeline.py seal` 不放行正文。

| 文件 | 解决的问题 |
|---|---|
| `设定/人物档案.md` | 人物只有姓名年龄、行为和台词容易 OOC |
| `设定/地点档案.md` | 收入、住所、通勤、消费水平不匹配 |
| `设定/势力档案.md` | 公司、家族、组织、反派资源无边界 |
| `设定/事件档案.md` | 被裁、破产、旧案、事故等事件缺因果链 |
| `设定/关系网络.md` | 谁信谁、谁骗谁、谁知道什么不清楚 |
| `设定/常识约束.md` | 工资、房租、技术能力、法律流程等现实常识漂移 |

## 真相文件

`设定/真相文件/` 是写作时的结构化事实源。Markdown 设定底座负责给人读，JSON 真相文件负责给流水线检查和编译章节约束。

| 文件 | 用途 |
|---|---|
| `characters.json` | 人物现实锚点、职业收入、居住逻辑、动机、声纹、行为边界 |
| `locations.json` | 地点成本、通勤、权限、消费水平、场景用途 |
| `factions.json` | 势力资源、限制、利益关系、行动边界 |
| `events.json` | 事件因果、证据链、影响范围、剧情债 |
| `relationships.json` | 信任等级、冲突、信息差、关系变化规则 |
| `resources.json` | 金钱、技能、权限、道具、系统能力及使用代价 |
| `foreshadowing.json` | 伏笔埋设、回收计划、遗忘风险 |

`project_bootstrap_pipeline.py init` 会创建模板；`seal` 会校验 7 个 JSON 全部补齐且无占位词。每章 `write_pipeline.py pre` 会生成：

```text
摘要/chapter_NNN_knowledge_pack.json
摘要/chapter_NNN_rule_stack.json
素材/chapter_NNN_truth_brief.md
摘要/chapter_NNN_truth_delta.json
```

每章 `post` 会强制校验 `chapter_NNN_truth_delta.json`。正文新增的人物状态、地点事实、势力行动、事件影响、关系变化、资源变化、伏笔变化，都必须写入 delta；否则 post 不通过。

`post` 会自动生成：

```text
素材/truth_delta_candidates_chNNN.json
素材/truth_delta_candidates_chNNN.md
```

候选报告会回写到 `chapter_NNN_truth_delta.json` 的 `auto_extraction`。只要 `review_status=needs_review`，delta 校验就不通过；必须审查候选事实，把属实项写入 observations/updates，把误报写进 review_note，最后改为 `reviewed`。

短篇/自由创作：

```text
novel_output/{平台}/{小说名}/
├── 正文/
├── 摘要/
├── 记忆/
├── 素材/
├── outline.md
└── novel_state.json
```

## Chapter Passport

每章完成后生成：

```text
摘要/chapter_NNN_passport.json
```

推荐字段：

```json
{
  "chapter": 12,
  "title": "章节标题",
  "chapter_file": "正文/第012章_章节标题.md",
  "word_count": 0,
  "pipeline_result": "pending|pass|fail",
  "pipeline": {
    "knowledge_pack": "pass|warning|fail|skipped",
    "truth_compile": "pass|fail|skipped",
    "truth_delta_template": "pass|fail|skipped",
    "pre_write_check": "pass|fail|skipped",
    "writing_gate": "pass|fail|skipped",
    "post_write_audit": "pass|fail|skipped",
    "normalizer": "pass|fail|skipped",
    "truth_delta_extract": "pass|fail|pending",
    "truth_delta": "pass|fail|pending",
    "truth_sync": "pass|fail|pending",
    "style_calibration": "pass|warning|fail|skipped",
    "character_consistency": "pass|warning|fail|skipped",
    "memory_sync": "pass|fail|pending"
  },
  "inputs": {
    "knowledge_pack": "",
    "memory_pack": "",
    "rule_stack": "",
    "truth_brief": "",
    "truth_delta": "",
    "truth_delta_candidates": "",
    "truth_delta_candidates_review": "",
    "truth_delta_report": "",
    "normalizer_report": "",
    "normalizer_task": ""
  },
  "changes": {
    "character_state_changes": [],
    "new_foreshadowing": [],
    "resolved_foreshadowing": [],
    "world_state_changes": []
  },
  "publish": {
    "platform": "",
    "status": "not_synced|draft|published",
    "synced_at": ""
  },
  "updated_at": ""
}
```

## novel_state.json 必备区块

```json
{
  "title": "",
  "platform": "",
  "current_chapter": 0,
  "word_count": 0,
  "revision_history": [],
  "audit_history": [],
  "strand_tracking": {
    "chapters": []
  },
  "publish_state": {}
}
```

立项通过后还必须包含：

```json
{
  "workflow_gate": {
    "bootstrap_status": "pass",
    "bootstrap_report": "素材/project_bootstrap_gate.json",
    "last_checklist_step": 20,
    "can_write_chapter": true
  }
}
```

## 写入规则

- 正文变更后必须更新 passport。
- 润色、审稿、重写必须写入 `revision_history`。
- 发布同步必须写入 `publish.status`。
- 角色状态、伏笔状态变化必须同步到 `knowledge_base/80_Projects/{小说名}/` 或 `记忆/`。
