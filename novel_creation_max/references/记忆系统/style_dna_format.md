# 风格DNA档案格式规范

## 概览

风格DNA档案是作者独特写作风格的数字化表示，用于校准新创作内容与作者原有风格的一致性。本文档定义了风格DNA档案的标准格式、字段含义和验证规则。

## 数据结构

### 顶层结构

```json
{
  "metadata": { ... },
  "sentence_features": { ... },
  "word_usage": { ... },
  "description_style": { ... },
  "dialogue_style": { ... }
}
```

### 元数据 (metadata)

存储档案的基本信息。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| author | string | 否 | 作者名称 |
| extract_date | string | 是 | 提取日期（ISO 8601格式） |
| sample_chapters | integer | 是 | 样本章节总数 |
| total_words | integer | 是 | 样本总字数 |
| total_sentences | integer | 是 | 样本总句数 |

**示例**：
```json
{
  "metadata": {
    "author": "张三",
    "extract_date": "2024-01-15T10:30:00",
    "sample_chapters": 5,
    "total_words": 25000,
    "total_sentences": 1850
  }
}
```

### 句式特征 (sentence_features)

量化描述作者的句式使用习惯。

#### 句子长度分布 (length_distribution)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| short | number | 是 | 短句占比（≤10字），范围0-1 |
| medium | number | 是 | 中句占比（11-30字），范围0-1 |
| long | number | 是 | 长句占比（>30字），范围0-1 |
| avg_length | number | 是 | 平均句长（字数） |
| std_length | number | 是 | 句长标准差 |

**验证规则**：
- short + medium + long ≈ 1.0（允许±0.01误差）
- avg_length ≥ 0
- std_length ≥ 0

**示例**：
```json
{
  "length_distribution": {
    "short": 0.15,
    "medium": 0.60,
    "long": 0.25,
    "avg_length": 18.5,
    "std_length": 12.3
  }
}
```

#### 句式类型比例 (type_ratio)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| declarative | number | 是 | 陈述句占比，范围0-1 |
| interrogative | number | 是 | 疑问句占比，范围0-1 |
| exclamatory | number | 是 | 感叹句占比，范围0-1 |

**验证规则**：
- 三者之和 ≈ 1.0

#### 复杂度指标 (complexity_index)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| complexity_index | number | 是 | 复杂句占比，范围0-1 |

**说明**：复杂句指包含多个标点符号（逗号、顿号、分号等）的句子。

### 用词习惯 (word_usage)

#### 高频词表 (high_freq_words)

数组类型，每个元素包含：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| word | string | 是 | 词语 |
| freq | integer | 是 | 出现次数 |
| ratio | number | 是 | 占总词数的比例 |

**示例**：
```json
{
  "high_freq_words": [
    {"word": "的", "freq": 850, "ratio": 0.034},
    {"word": "了", "freq": 620, "ratio": 0.025},
    {"word": "是", "freq": 480, "ratio": 0.019}
  ]
}
```

#### 词性分布 (pos_distribution)

键值对，键为词性标签，值为占比。

**常见词性标签**：
- n: 名词
- v: 动词
- a: 形容词
- r: 代词
- d: 副词
- p: 介词

**示例**：
```json
{
  "pos_distribution": {
    "n": 0.35,
    "v": 0.25,
    "a": 0.15,
    "r": 0.10,
    "d": 0.08,
    "p": 0.07
  }
}
```

#### 独特用词 (unique_words)

数组类型，存储仅出现一次的独特词汇（最多50个）。

#### 平均词长 (avg_word_length)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| avg_word_length | number | 是 | 平均词长（字数） |

### 描写风格 (description_style)

#### 描写比例

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| environment_ratio | number | 是 | 环境描写占比，范围0-1 |
| psychology_ratio | number | 是 | 心理描写占比，范围0-1 |
| action_ratio | number | 是 | 动作描写占比，范围0-1 |

**说明**：
- 环境描写：包含天、地、山、水、风、雨、光、影等自然或场景描写
- 心理描写：包含想、觉得、感到、心里等内心活动描写
- 动作描写：包含走、跑、看、听、说等动作行为描写

#### 典型句式 (typical_patterns)

数组类型，每个元素包含：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| type | string | 是 | 描写类型（environment/psychology/action） |
| pattern | string | 是 | 典型句式片段 |

**示例**：
```json
{
  "typical_patterns": [
    {
      "type": "environment",
      "pattern": "夕阳西下，金色的余晖洒在..."
    },
    {
      "type": "psychology",
      "pattern": "他心里明白，这一切都是..."
    }
  ]
}
```

### 对话风格 (dialogue_style)

#### 对话占比 (dialogue_ratio)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| dialogue_ratio | number | 是 | 对话内容占总文本的比例 |

#### 对话标记词偏好 (marker_preference)

数组类型，每个元素包含：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| marker | string | 是 | 对话标记词 |
| freq | integer | 是 | 使用次数 |
| ratio | number | 是 | 占总标记词的比例 |

**常见对话标记词**：说、道、问、答、喊、叫、笑道、说道、问道、答道

#### 节奏特征 (rhythm_features)

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| avg_length | number | 是 | 对话平均长度（字数） |
| short_ratio | number | 是 | 短对话占比（≤10字） |
| medium_ratio | number | 是 | 中对话占比（11-30字） |
| long_ratio | number | 是 | 长对话占比（>30字） |

#### 典型句式 (typical_patterns)

数组类型，存储典型的对话句式示例。

## 完整示例

```json
{
  "metadata": {
    "author": "张三",
    "extract_date": "2024-01-15T10:30:00",
    "sample_chapters": 5,
    "total_words": 25000,
    "total_sentences": 1850
  },
  "sentence_features": {
    "length_distribution": {
      "short": 0.15,
      "medium": 0.60,
      "long": 0.25,
      "avg_length": 18.5,
      "std_length": 12.3
    },
    "type_ratio": {
      "declarative": 0.85,
      "interrogative": 0.08,
      "exclamatory": 0.07
    },
    "complexity_index": 0.32
  },
  "word_usage": {
    "high_freq_words": [
      {"word": "的", "freq": 850, "ratio": 0.034},
      {"word": "了", "freq": 620, "ratio": 0.025},
      {"word": "是", "freq": 480, "ratio": 0.019}
    ],
    "pos_distribution": {
      "n": 0.35,
      "v": 0.25,
      "a": 0.15,
      "r": 0.10,
      "d": 0.08,
      "p": 0.07
    },
    "unique_words": ["幽蓝", "琥珀", "斑驳", "涟漪"],
    "avg_word_length": 1.8
  },
  "description_style": {
    "environment_ratio": 0.25,
    "psychology_ratio": 0.30,
    "action_ratio": 0.45,
    "typical_patterns": [
      {
        "type": "environment",
        "pattern": "夜色如墨，星光稀疏地洒在..."
      },
      {
        "type": "psychology",
        "pattern": "他感到一阵莫名的惆怅，..."
      }
    ]
  },
  "dialogue_style": {
    "dialogue_ratio": 0.35,
    "marker_preference": [
      {"marker": "说", "freq": 150, "ratio": 0.45},
      {"marker": "道", "freq": 80, "ratio": 0.24},
      {"marker": "笑道", "freq": 60, "ratio": 0.18}
    ],
    "rhythm_features": {
      "avg_length": 15.5,
      "short_ratio": 0.25,
      "medium_ratio": 0.55,
      "long_ratio": 0.20
    },
    "typical_patterns": [
      "\"我知道了，\"他轻声说。",
      "\"这不可能！\"她惊讶地喊道。"
    ]
  }
}
```

## 验证规则汇总

1. **数值范围**：所有比例值必须在0-1之间
2. **比例和**：type_ratio和length_distribution的比例和应≈1.0
3. **必需字段**：所有标注为"必需"的字段必须存在
4. **数据类型**：字段类型必须符合规范
5. **数组长度**：unique_words最多50个元素

## 使用建议

1. **样本量**：建议使用3-5章代表性章节提取风格DNA，样本过少会影响准确性
2. **更新频率**：建议每创作10-20章后重新提取风格DNA，以适应创作风格的自然演变
3. **对比分析**：可以对比不同时期的风格DNA，观察创作风格的变化趋势
4. **个性化调整**：可以手动调整风格DNA中的参数，以更好地反映作者的写作风格
