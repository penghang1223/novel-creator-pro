# 审稿 Review Skill 实施计划

> **设计文档**：`2026-05-05-review-skill-design.md`
> **目标**：创建独立审稿子技能，对已写章节做知识库驱动的深度质量审查

---

## Step 1：创建 review-skill 目录结构

创建 `novel_creation_promax/review-skill/` 目录及子目录：

```bash
mkdir -p novel_creation_promax/review-skill/references
```

**产出**：空目录结构

---

## Step 2：编写 `references/review-dimensions.md`

从知识库原文中提取4个审查维度的具体检查清单。

**内容结构**：

```
# 审查维度标准

> 审稿时的评分依据。每个维度直接引用知识库原文。

## 一、对话质感（满分10分）
### 来源文件
- 03_人物与对话/对话质感完整框架.md
- 03_人物与对话/AI对话丰满化技法.md

### 检查清单
- [ ] 六要素覆盖（表情/心理/听觉/环境/节奏/倾听者）
- [ ] 声纹测试
- [ ] 9项对话审计清单
- [ ] 4条负约束
- [ ] 干涩检测5问

### 评分标准
- 9-10：六要素≥4项，声纹清晰，有潜台词
- 7-8：六要素≥3项，基本有声纹
- 5-6：六要素≥2项
- <5：对话干瘪，像文字记录

## 二、爽点节奏（满分10分）
## 三、章节结构（满分10分）
## 四、去AI化（满分10分）
```

每个维度：来源文件 → 检查清单 → 评分标准

**产出**：`review-skill/references/review-dimensions.md` (~8K)

---

## Step 3：编写 `references/review-report-template.md`

定义审查报告格式和评级标准。

**内容**：
- 单章精审报告模板（如设计文档 §6.1）
- 批量快审报告模板（如设计文档 §6.2）
- S/A/B/C/D 评级标准（如设计文档 §6.3）
- 修复优先级定义（高/中/低）

**产出**：`review-skill/references/review-report-template.md` (~3K)

---

## Step 4：编写 `review-skill/SKILL.md`

主入口文件，定义触发语、双模式执行链。

**内容结构**：

```markdown
---
name: review-skill
description: 审稿子技能，对已写章节做知识库驱动的深度质量审查
---

# 审稿 Review Skill

## 触发语
## 单章精审
### 执行链
Step 1: 自动检测
Step 2: 深度审查（读取 review-dimensions.md）
Step 3: 综合评级
Step 4: 用户确认→修复

## 批量快审
### 执行链
Step 1: 每章快速扫描
Step 2: 跨章节分析
Step 3: 整体报告

## 知识库集成
## 复用脚本
```

**产出**：`review-skill/SKILL.md` (~5K)

---

## Step 5：修改主 SKILL.md 的 `[10] 审稿评估`

将 SKILL.md §1227-1266 的空壳清单替换为入口链接：

```markdown
### [10] 审稿评估

对已有章节进行全面质量审查。详见 `review-skill/SKILL.md`。

**触发语**："审一下第N章"、"这章写得怎么样"、"审查一下这卷"
```

同时在自动触发规则中新增审稿触发条目。

**修改文件**：`novel_creation_promax/SKILL.md`

---

## Step 6：验证——对 Ch3 执行单章精审

读取 `review-skill/SKILL.md`，按执行链对 Ch3（母亲的遗言）执行完整单章精审：

1. 跑 `post_write_audit.py`
2. 读取对话质感完整框架，审查 Ch3 对话
3. 读取爽点设计，审查 Ch3 爽点节奏
4. 读取每章节奏公式，审查 Ch3 断章
5. 读取降低AI痕迹，审查 Ch3 去AI化
6. 输出完整审查报告

**产出**：Ch3 审查报告（验证 skill 可用）

---

## 验收标准

1. [x] 设计文档已批准
2. [ ] `review-skill/` 目录结构创建
3. [ ] `review-dimensions.md` 引用了知识库原文的具体文件
4. [ ] `review-report-template.md` 定义了报告格式和评级
5. [ ] `review-skill/SKILL.md` 定义了双模式执行链
6. [ ] 主 SKILL.md `[10]` 段落改为入口链接
7. [ ] Ch3 审查报告引用了知识库原文的规则（不是速查卡）
8. [ ] Ch3 审查覆盖4个维度，每个维度有具体评分

## 关键文件

- **新建**：`novel_creation_promax/review-skill/SKILL.md`
- **新建**：`novel_creation_promax/review-skill/references/review-dimensions.md`
- **新建**：`novel_creation_promax/review-skill/references/review-report-template.md`
- **修改**：`novel_creation_promax/SKILL.md`（[10] 段落 + 自动触发规则）
- **读取**：`knowledge_base/40_Writing/` 6-8个审查维度文件
- **复用**：`scripts/post_write_audit.py`、`scripts/plot_continuity_checker.py`、`scripts/character_consistency_checker.py`
