# 人物档案模板

## 概览

人物档案是确保小说人物一致性的核心工具。本文档提供了标准的人物档案模板和填写指南，用于记录和维护人物的多维度特征。

## 档案结构

### 一、基础信息 (basic_info)

记录人物的基本属性。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 人物姓名 |
| age | integer | 否 | 年龄 |
| gender | string | 否 | 性别 |
| occupation | string | 否 | 职业 |
| appearance | string | 否 | 外貌特征描述 |
| background | string | 否 | 背景经历 |

**示例**：
```json
{
  "basic_info": {
    "name": "李明",
    "age": 28,
    "gender": "男",
    "occupation": "侦探",
    "appearance": "身材高大，面容刚毅，左眉有一道浅浅的疤痕",
    "background": "曾是刑警，因一次失误离开警队，现经营私人侦探事务所"
  }
}
```

### 二、性格特征 (personality)

记录人物的核心性格特征。

#### 核心性格 (core_traits)

数组类型，列出人物的3-5个核心性格特征。

**示例**：
```json
{
  "core_traits": ["理性", "执着", "内向", "正义感强"]
}
```

#### 性格矛盾点 (contradictions)

记录人物性格中的矛盾之处，这些矛盾是人物的立体感和成长空间。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| trait1 | string | 是 | 第一个矛盾特征 |
| trait2 | string | 是 | 第二个矛盾特征 |
| context | string | 否 | 矛盾出现的情境 |
| resolution | string | 否 | 如何处理这个矛盾 |

**示例**：
```json
{
  "contradictions": [
    {
      "trait1": "外表冷漠",
      "trait2": "内心温暖",
      "context": "面对弱者时会不由自主地展现温柔",
      "resolution": "随着故事发展，逐渐外露温暖的一面"
    }
  ]
}
```

#### 成长方向 (growth_direction)

记录人物在故事中的成长弧线方向。

**示例**：
```json
{
  "growth_direction": "从封闭自我到学会信任他人，从追求正义到理解宽恕"
}
```

### 三、说话风格 (speech_style)

#### 口头禅 (catchphrases)

数组类型，列出人物常用的口头禅或习惯用语。

**示例**：
```json
{
  "catchphrases": ["有意思", "让我想想", "事情没那么简单"]
}
```

#### 用词偏好 (word_preference)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| formal_level | string | 否 | 正式程度（formal/casual/mixed） |
| vocabulary_style | string | 否 | 词汇风格（文雅/通俗/专业） |
| preferred_words | array | 否 | 常用的特定词汇 |
| avoided_words | array | 否 | 避免使用的词汇 |

**示例**：
```json
{
  "word_preference": {
    "formal_level": "mixed",
    "vocabulary_style": "专业",
    "preferred_words": ["证据", "推理", "逻辑", "真相"],
    "avoided_words": ["也许", "可能", "大概"]
  }
}
```

#### 句式特点 (sentence_patterns)

数组类型，记录人物说话的典型句式。

**示例**：
```json
{
  "sentence_patterns": [
    "根据我的推断...",
    "这让我想起一个案子...",
    "有三种可能..."
  ]
}
```

#### 情绪表达方式 (emotional_expression)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| expression_style | string | 是 | 表达风格（直接/含蓄/反讽） |
| under_stress | string | 否 | 压力下的表达特点 |
| when_happy | string | 否 | 开心时的表达特点 |
| when_angry | string | 否 | 愤怒时的表达特点 |

**示例**：
```json
{
  "emotional_expression": {
    "expression_style": "含蓄",
    "under_stress": "说话更加简短，语速加快",
    "when_happy": "会不自觉地哼歌",
    "when_angry": "完全沉默，眼神变得锐利"
  }
}
```

### 四、行为模式 (behavior_pattern)

#### 决策风格 (decision_style)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| style | string | 是 | 决策风格（果断/谨慎/犹豫） |
| based_on | string | 否 | 决策依据（逻辑/直觉/情感） |
| example | string | 否 | 典型决策示例 |

**示例**：
```json
{
  "decision_style": {
    "style": "谨慎",
    "based_on": "逻辑",
    "example": "在做出判断前，会收集所有可能的证据，排除每一个疑点"
  }
}
```

#### 应对压力 (stress_response)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| typical_response | string | 是 | 典型反应 |
| physical_signs | array | 否 | 肢体语言表现 |
| coping_mechanism | string | 否 | 应对机制 |

**示例**：
```json
{
  "stress_response": {
    "typical_response": "更加专注，进入高度警觉状态",
    "physical_signs": ["眉头紧锁", "手指无意识地敲击桌面", "来回踱步"],
    "coping_mechanism": "通过抽烟或喝咖啡来缓解压力"
  }
}
```

#### 人际交往 (social_interaction)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| approachability | string | 否 | 可接近程度 |
| trust_level | string | 否 | 信任他人的程度 |
| communication_style | string | 否 | 沟通风格 |
| relationship_patterns | array | 否 | 人际关系模式 |

**示例**：
```json
{
  "social_interaction": {
    "approachability": "不易接近",
    "trust_level": "低",
    "communication_style": "直接且目的性强",
    "relationship_patterns": [
      "对陌生人保持距离",
      "一旦信任某人，会极其忠诚"
    ]
  }
}
```

### 五、情感特征 (emotional_traits)

#### 情感表达方式 (expression_style)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| style | string | 是 | 表达风格（内敛/外放/波动） |
| intensity | string | 否 | 情感强度（强烈/温和/平淡） |
| visibility | string | 否 | 可见度（易察觉/不易察觉） |

**示例**：
```json
{
  "expression_style": {
    "style": "内敛",
    "intensity": "强烈",
    "visibility": "不易察觉"
  }
}
```

#### 情感触发点 (emotional_triggers)

数组类型，记录容易触发特定情感的场景或话题。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| trigger | string | 是 | 触发因素 |
| emotion | string | 是 | 触发的情感 |
| response | string | 否 | 典型反应 |

**示例**：
```json
{
  "emotional_triggers": [
    {
      "trigger": "提到过去的错误",
      "emotion": "愧疚",
      "response": "沉默，回避话题"
    },
    {
      "trigger": "看到不公正的事",
      "emotion": "愤怒",
      "response": "虽然表面平静，但会暗中调查"
    }
  ]
}
```

### 六、成长轨迹 (growth_arc)

#### 人物弧线 (arc)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| starting_point | string | 是 | 起点（初始状态） |
| ending_point | string | 是 | 终点（目标状态） |
| arc_type | string | 是 | 弧线类型（成长/堕落/平坦） |

**示例**：
```json
{
  "arc": {
    "starting_point": "封闭自我，独自承担一切",
    "ending_point": "学会信任他人，接受帮助",
    "arc_type": "成长"
  }
}
```

#### 关键转变点 (turning_points)

数组类型，记录人物发生重要转变的时刻。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| chapter | integer | 否 | 所在章节 |
| event | string | 是 | 转变事件 |
| change | string | 是 | 产生的变化 |

**示例**：
```json
{
  "turning_points": [
    {
      "chapter": 15,
      "event": "搭档在危险中救了他",
      "change": "开始重新审视对他人的信任"
    },
    {
      "chapter": 30,
      "event": "真相大白，发现过去的错误并非全因自己",
      "change": "放下了多年的愧疚"
    }
  ]
}
```

## 完整示例

```json
{
  "basic_info": {
    "name": "李明",
    "age": 28,
    "gender": "男",
    "occupation": "侦探",
    "appearance": "身材高大，面容刚毅，左眉有一道浅浅的疤痕",
    "background": "曾是刑警，因一次失误离开警队，现经营私人侦探事务所"
  },
  "personality": {
    "core_traits": ["理性", "执着", "内向", "正义感强"],
    "contradictions": [
      {
        "trait1": "外表冷漠",
        "trait2": "内心温暖",
        "context": "面对弱者时会不由自主地展现温柔",
        "resolution": "随着故事发展，逐渐外露温暖的一面"
      }
    ],
    "growth_direction": "从封闭自我到学会信任他人，从追求正义到理解宽恕"
  },
  "speech_style": {
    "catchphrases": ["有意思", "让我想想", "事情没那么简单"],
    "word_preference": {
      "formal_level": "mixed",
      "vocabulary_style": "专业",
      "preferred_words": ["证据", "推理", "逻辑", "真相"],
      "avoided_words": ["也许", "可能", "大概"]
    },
    "sentence_patterns": [
      "根据我的推断...",
      "这让我想起一个案子...",
      "有三种可能..."
    ],
    "emotional_expression": {
      "expression_style": "含蓄",
      "under_stress": "说话更加简短，语速加快",
      "when_happy": "会不自觉地哼歌",
      "when_angry": "完全沉默，眼神变得锐利"
    }
  },
  "behavior_pattern": {
    "decision_style": {
      "style": "谨慎",
      "based_on": "逻辑",
      "example": "在做出判断前，会收集所有可能的证据，排除每一个疑点"
    },
    "stress_response": {
      "typical_response": "更加专注，进入高度警觉状态",
      "physical_signs": ["眉头紧锁", "手指无意识地敲击桌面", "来回踱步"],
      "coping_mechanism": "通过抽烟或喝咖啡来缓解压力"
    },
    "social_interaction": {
      "approachability": "不易接近",
      "trust_level": "低",
      "communication_style": "直接且目的性强",
      "relationship_patterns": [
        "对陌生人保持距离",
        "一旦信任某人，会极其忠诚"
      ]
    }
  },
  "emotional_traits": {
    "expression_style": {
      "style": "内敛",
      "intensity": "强烈",
      "visibility": "不易察觉"
    },
    "emotional_triggers": [
      {
        "trigger": "提到过去的错误",
        "emotion": "愧疚",
        "response": "沉默，回避话题"
      },
      {
        "trigger": "看到不公正的事",
        "emotion": "愤怒",
        "response": "虽然表面平静，但会暗中调查"
      }
    ]
  },
  "growth_arc": {
    "arc": {
      "starting_point": "封闭自我，独自承担一切",
      "ending_point": "学会信任他人，接受帮助",
      "arc_type": "成长"
    },
    "turning_points": [
      {
        "chapter": 15,
        "event": "搭档在危险中救了他",
        "change": "开始重新审视对他人的信任"
      },
      {
        "chapter": 30,
        "event": "真相大白，发现过去的错误并非全因自己",
        "change": "放下了多年的愧疚"
      }
    ]
  }
}
```

## 使用建议

1. **动态更新**：人物档案应随着故事发展持续更新，记录人物的成长和变化
2. **重点关注**：主要人物应填写所有字段，次要人物可简化
3. **矛盾利用**：性格矛盾点是戏剧冲突的来源，应善加利用
4. **成长追踪**：定期检查人物的成长轨迹是否符合预期
5. **团队协作**：如有多人参与创作，人物档案是保持一致性的关键工具

## OOC检测说明

人物一致性检查器会检测以下类型的OOC：

1. **说话风格OOC**：使用了人物不应使用的词汇或句式
2. **行为模式OOC**：行为与设定的决策风格或应对方式冲突
3. **情感反应OOC**：情感表达与设定的表达方式不符
4. **决策模式OOC**：决策与核心性格特征冲突

检查结果会分为三个严重程度：
- **轻微**：小幅度偏离，不影响人物形象
- **中等**：明显偏离，可能影响人物一致性
- **严重**：严重偏离，破坏人物形象的完整性
