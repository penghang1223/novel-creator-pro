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
│   └── 常识约束.md
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
  "pipeline": {
    "pre_write_check": "pass|fail|skipped",
    "writing_gate": "pass|fail|skipped",
    "post_write_audit": "pass|fail|skipped",
    "style_calibration": "pass|warning|fail|skipped",
    "character_consistency": "pass|warning|fail|skipped",
    "memory_sync": "pass|fail|pending"
  },
  "inputs": {
    "outline_version": "",
    "memory_pack": "",
    "knowledge_pack": ""
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
