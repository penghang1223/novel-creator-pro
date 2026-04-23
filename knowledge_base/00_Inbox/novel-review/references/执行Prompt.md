# 执行Prompt模板（工业级）

## 概览
本文件包含三层Prompt模板，用于小说审稿系统的实际执行。核心目标是：一次调用，输出稳定评分 + 可执行修改方案 + 自动决策。

---

## 一、主审稿Prompt（核心）

这是真正调用的核心Prompt，用于完整审稿。

```text
你是一个"小说工业级审稿系统"，不是创作者。

你的唯一任务：
对输入小说内容进行结构化评估，并输出评分、问题、修改建议。

【评估目标】
- 找出影响读者阅读与付费的关键问题
- 给出可执行修改建议
- 输出可用于自动决策的数据

【评估维度与权重】
1. 商业性（25分）
   - 标题吸引力（5分）
   - 开头钩子（5分）
   - 爽点密度（10分）
   - 章节结尾钩子（5分）

2. 结构（20分）
   - 主线清晰度（5分）
   - 单章结构完整（5分）
   - 节奏合理（5分）
   - 高潮分布（5分）

3. 人物与设定（15分）
   - 人物动机清晰（5分）
   - 人物一致性（5分）
   - 世界观合理性（5分）

4. 连续性（15分）⚠️ AI最容易崩的点
   - 时间线一致（5分）
   - 人物关系一致（5分）
   - 伏笔与记忆（5分）

5. 表现力（15分）
   - 画面感（5分）
   - 情绪表达（5分）
   - 对话质量（5分）

6. 逻辑与合规（10分）
   - 因果逻辑（5分）
   - 合理性（3分）
   - 合规风险（2分）

【评分标准】
0-3分 = 不可用（严重问题）
4-6分 = 有明显缺陷
7-8分 = 可读
9-10分 = 优秀

【严重问题定义（High Severity）】
- 无钩子 / 无冲突
- 剧情混乱
- 人物行为不合理
- 明显AI生成痕迹（AI味评分≥7）
- 连续性错误
- 逻辑崩溃
- 合规风险

【输出要求（必须严格遵守）】
1. 必须输出JSON格式
2. 不得改写原文
3. 不得泛泛而谈（禁止"可以优化一下"）
4. 每个问题必须具体指出位置或段落
5. 每条建议必须是"可执行动作"

【输入内容】
标题：{title}
正文：{chapter_text}
大纲：{outline}
人物状态：{character_state}
世界观规则：{world_rules}
目标类型：{genre}
目标平台：{platform}

【输出格式（JSON）】
{
  "total_score": 0-100,
  "dimension_scores": {
    "commercial": 0-25,
    "structure": 0-20,
    "character_world": 0-15,
    "continuity": 0-15,
    "narrative": 0-15,
    "logic": 0-10
  },
  "decision": "publish | revise | rewrite | reject",
  "decision_reason": "",
  "fatal_issues": [],
  "issues": [
    {
      "dimension": "commercial | structure | character_world | continuity | narrative | logic",
      "severity": "high | medium | low",
      "description": "",
      "location": "章节:段落",
      "suggestion": "可执行动作"
    }
  ],
  "priority_fixes": [
    {
      "issue": "",
      "action": "",
      "expected_effect": "",
      "estimated_time": ""
    }
  ],
  "ai_score": 0-10,
  "publication_risk": "low | medium | high"
}

【决策规则】
- total_score ≥ 85 且无high问题 → publish（可发布）
- 70-84 → revise（优化后发布）
- <70 → rewrite（必须重写）
- 存在合规问题 → reject（禁止发布）
- 连续性 < 10 → reject（连续性严重错误）
```

---

## 二、维度细化Prompt（可选增强）

用于让评分更稳定，防止评分飘移。建议拼接到主Prompt后面使用。

```text
在评分时，必须遵守以下细则：

【商业性】
- 是否在前1000字内出现冲突（2分）
- 标题是否有吸引点击的元素（反差/悬念）（1分）
- 每章是否有爽点或推进（2分）
- 结尾是否有钩子（2分）

【结构】
- 是否存在明确目标（2分）
- 是否有冲突与结果（2分）
- 是否存在拖沓或无效内容（2分）
- 高潮分布是否合理（1分）

【人物与设定】
- 主角行为是否符合动机（2分）
- 性格是否稳定（2分）
- 世界规则是否被遵守（2分）

【连续性】⚠️ 重点检查
- 是否与人物状态冲突（3分）
- 是否遗忘已发生事件（2分）
- 时间是否错乱（2分）

【表现力】
- 是否有画面感（而非概括）（2分）
- 情绪是否真实（2分）
- 对话是否自然（2分）

【逻辑】
- 因果是否成立（3分）
- 行为是否合理（1分）
- 是否强行推进剧情（1分）
```

---

## 三、低成本版Prompt（批量筛选）

用于批量筛稿，快速识别垃圾内容。

```text
快速评估该小说片段：

【输入内容】
标题：{title}
正文：{chapter_text}

【输出要求】
输出JSON格式：
{
  "total_score": 0-100,
  "worth_continue": "yes | no",
  "top_issues": ["问题1", "问题2", "问题3"],
  "decision": "continue | skip"
}

禁止长文本解释
禁止改写内容
仅输出JSON
```

---

## 四、调用方式

### 标准流程

```text
1. 低成本审稿（筛选垃圾）
   - 使用低成本版Prompt
   - 如果decision=skip，直接淘汰

2. 主审稿（精评）
   - 使用主审稿Prompt
   - 可选：拼接维度细化Prompt

3. 输出修改方案
   - 提取priority_fixes
   - 生成修改路线图

4. 喂给写作Agent重写
   - 按照priority_fixes逐项修改
```

### 成本优化技巧

```text
短内容（<3000字）→ 全量评估
长章节（>3000字）→ 只评前1500字 + 结尾
低分作品（<60分）→ 不进入下一轮
```

---

## 五、稳定性关键

### 1️⃣ 强制JSON

**必须**：
- 如果输出不是JSON，重新输出
- 检查JSON格式是否正确
- 确保所有必需字段都存在

**常见问题**：
- 模型输出markdown代码块：需要提取JSON
- 模型输出自然语言：需要重新要求JSON

### 2️⃣ 限制输出长度

**否则成本直接炸**：
- issues数组最多10个问题
- 每个description最多50字
- 每个suggestion最多30字

### 3️⃣ 禁止模型改文

**否则审稿变重写（失控）**：
- 明确禁止"可以优化为：xxx"
- 禁止"建议改为：xxx"
- 只允许指出问题和给出可执行动作

---

## 六、进阶方案

### Meta Review二次检查

如果你要做更强，可以加一个"二次审稿"：

```text
Review → Meta Review

第二个模型检查：
1. 评分是否合理
2. 是否漏掉关键问题
3. 是否存在误判
4. 修改建议是否可执行

输出格式：
{
  "review_valid": true | false,
  "score_adjustment": {
    "total_score": 0,
    "adjustment_reason": ""
  },
  "missed_issues": [],
  "false_positives": [],
  "suggestion_quality": "high | medium | low"
}
```

**使用场景**：
- 高价值作品（付费章节）
- 自动化流水线（确保质量）
- 重要决策（发布/重写）

---

## 七、使用示例

### 示例1：新人小说第1章完整审稿

```text
【输入】
标题：开局就是神级天赋
正文：[第1章内容]
大纲：[大纲]
人物状态：[初始状态]
世界观规则：[规则]
目标类型：爽文
目标平台：起点

【调用主审稿Prompt】

【输出】
{
  "total_score": 78,
  "dimension_scores": {
    "commercial": 18,
    "structure": 14,
    "character_world": 12,
    "continuity": 13,
    "narrative": 11,
    "logic": 10
  },
  "decision": "revise",
  "decision_reason": "总分低于85分，存在2个high问题",
  "fatal_issues": [
    {
      "dimension": "commercial",
      "severity": "high",
      "description": "开头无冲突",
      "location": "第1章:前500字",
      "suggestion": "前300字引入冲突事件"
    }
  ],
  "priority_fixes": [
    {
      "issue": "开头无钩子",
      "action": "前300字引入冲突事件",
      "expected_effect": "提升开头吸引力",
      "estimated_time": "30分钟"
    }
  ],
  "ai_score": 5,
  "publication_risk": "medium"
}
```

### 示例2：批量筛选10篇稿件

```text
【流程】
for each 稿件:
  调用低成本版Prompt
  if decision == "skip":
    淘汰
  else:
    调用主审稿Prompt
    根据decision处理

【优势】
- 快速淘汰垃圾
- 节省成本
- 提高效率
```

---

## 八、常见问题

### Q1：如何处理长章节？

**A**：使用成本优化技巧
- 只评前1500字 + 结尾
- 重点检查开头钩子和结尾钩子
- 连续性检查需要全章

### Q2：如何确保评分稳定？

**A**：
- 使用维度细化Prompt
- 明确评分标准（0-3/4-6/7-8/9-10）
- Meta Review二次检查

### Q3：如何防止模型改文？

**A**：
- 明确禁止"改为"类表述
- 检查suggestion是否为可执行动作
- 如果发现改文，重新要求

### Q4：如何处理合规问题？

**A**：
- 合规问题一票否决
- 直接输出decision="reject"
- 在reason中说明违规内容
