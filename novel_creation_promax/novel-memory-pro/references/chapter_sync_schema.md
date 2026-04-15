# 章节回填与项目初始化 Schema

本参考定义两个高频输入文件：

- `project_bootstrap.json`
- `chapter_summary.json`

## project_bootstrap.json

用于在立项后一次性导入基础记忆。

```json
{
  "project": {
    "title": "小说标题",
    "premise": "一句话梗概",
    "genre": "都市悬疑",
    "tone": "现实、克制、悬疑",
    "target_length": "长篇连载"
  },
  "style_dna": {
    "author": "作者名",
    "notes": "如果已有 style_dna.json，可放入其内容"
  },
  "characters": [
    {
      "basic_info": {
        "name": "沈知言",
        "occupation": "调查记者"
      },
      "personality": {
        "core_traits": ["冷静", "敏锐", "执拗"]
      }
    }
  ],
  "plots": [
    {
      "plot_type": "main",
      "plot_name": "无声来电失踪案",
      "description": "主线案件",
      "start_chapter": 1,
      "current_chapter": 1,
      "status": "进行中"
    }
  ],
  "contexts": [
    {
      "chapter": 0,
      "title": "立项摘要",
      "summary": "故事初始设定",
      "unresolved_questions": ["幕后人是谁"]
    }
  ]
}
```

## chapter_summary.json

用于每章写完后的结构化回填。

```json
{
  "chapter": 12,
  "title": "静音来电",
  "summary": "本章发生了什么",
  "characters_involved": ["沈知言", "周既明"],
  "key_events": [
    "沈知言拿到录音",
    "周既明确认旧案有关联"
  ],
  "character_states": [
    {
      "name": "沈知言",
      "emotional_state": "警惕但兴奋",
      "location": "报社楼下",
      "goals": ["确认录音来源"]
    }
  ],
  "foreshadowing_planted": [
    "录音里出现新的地名"
  ],
  "foreshadowing_resolved": [
    "前文的陌生号码来源"
  ],
  "unresolved_questions": [
    "录音是谁转交的"
  ],
  "plot_updates": [
    {
      "plot_name": "无声来电失踪案",
      "event": "主角确认旧案与主线并轨",
      "status": "进行中"
    }
  ],
  "creative_decisions": [
    {
      "decision": "本章先给线索，不揭真凶",
      "reason": "保持中段张力"
    }
  ]
}
```

## 最小必填字段

如果时间紧，最少保留：

- `chapter`
- `title`
- `summary`
- `key_events`
- `character_states`
- `unresolved_questions`

## 使用建议

- 摘要写“发生了什么变化”，不要复述整章
- `character_states` 只保留当前对下章重要的信息
- `creative_decisions` 用于记录为什么这样写，便于后续改稿时回溯
