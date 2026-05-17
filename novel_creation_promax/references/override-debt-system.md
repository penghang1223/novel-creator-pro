# 覆盖合同 + 债务系统 (Override Contract + Debt System)

> 允许写作时违反约束，但必须"记账还债"。防止规则僵化，同时保证质量底线。

---

## 核心概念

**覆盖合同 (Override Contract)**：当写作需要违反某条约束时，创建一份合同记录：违反了什么、为什么、怎么还。

**债务 (Debt)**：合同创建后产生的"欠账"。每过一章未还，债务+1（利息）。债务累积到阈值会升级严重程度。

---

## 覆盖合同结构

```json
{
  "contract_id": "OC-{N}",
  "chapter_created": 0,
  "constraint_violated": "约束名称（如：对话占比≥25%）",
  "severity": "soft",
  "rationale": "为什么需要违反（如：本章是纯动作场景，对话会打断节奏）",
  "payback_plan": "怎么还（如：下章对话占比提升到40%）",
  "deadline": 0,
  "debt": 1,
  "status": "open|repaid|escalated|expired"
}
```

### severity 级别

| 级别 | 含义 | 能否覆盖 |
|------|------|---------|
| `soft` | 质量建议类约束（如对话占比、爽点密度） | 可以覆盖 |
| `medium` | 质量红线类约束（如断章有效性、六要素覆盖） | 需用户确认 |
| `hard` | 绝对禁止类约束（如原创性、人称一致性） | 不可覆盖 |

### 规则
- 只有 `soft` 级别的约束可以自动创建覆盖合同
- `medium` 级别需要用户明确说"这里可以灵活"才能覆盖
- `hard` 级别（一级红线）永远不能覆盖

---

## 债务机制

### 利息计算

```
每过1章未偿还 → debt += 1
```

### 升级阈值

| 债务值 | 严重度变化 | 后果 |
|--------|-----------|------|
| 1-2 | 保持 soft | 正常，提醒注意 |
| 3 | soft → medium | 升级为中等优先级，必须在下章处理 |
| 6 | medium → hard | 升级为高优先级，必须本章处理，否则标记为违规 |

### 偿还方式
- 按 `payback_plan` 执行（如"下章对话占比提升到40%"）
- 偿还后 `status` 改为 `repaid`，债务清零
- 如果 `deadline` 到了仍未偿还，`status` 改为 `expired`，记录为违规

---

## 并发限制

**最大同时开放合同数：3**

- 已有 3 个 open 合同 → 硬性阻止新增第 4 个
- 必须先偿还/关闭至少 1 个合同，才能创建新的
- 防止"无限赊账"

---

## 写作流程集成

### 写前（约束组装阶段）
- 检查当前 open 合同数（0-3）
- 检查是否有 debt ≥ 3 的合同需要本章处理
- 注入 `== 债务状态 ==` 区块到约束模板

### 写中（Pass 1）
- 如果需要违反约束，暂停并创建覆盖合同
- 记录 rationale（为什么必须违反）和 payback_plan（怎么还）

### 写后（阶段 3）
- 检查本章是否偿还了之前的合同
- 更新合同状态（repaid/escalated）
- 同步到章节摘要的 `overrides[]` 和 `debt_events[]`

### 审稿
- 每个维度评分时，扣除债务修正分：每笔未偿债务 -1 分，最多 -2 分
- 有 open 合同的维度在报告中标注 `[有债务]`

---

## 存储位置

| 数据 | 存储位置 |
|------|---------|
| 债务总账 | `project-bootstrap.json` → `debt_ledger` |
| 章节级事件 | `chapter-summary.json` → `overrides[]` + `debt_events[]` |
| 约束注入 | `chapter_constraint_template.md` → `== 债务状态 ==` |

---

## 示例

### 场景：第12章需要跳过对话占比检查

```
第12章是纯战斗场景（C6 等级突破），对话占比只有15%（低于25%目标）。

创建合同：
- contract_id: OC-3
- constraint_violated: "对话占比≥25%"
- severity: soft
- rationale: "本章是C6等级突破高潮，全程战斗描写，插入对话会打断节奏"
- payback_plan: "第13章开头加一段长对话场景，对话占比提升至35%"
- deadline: 14
- debt: 1

第13章执行 payback_plan → 对话占比35% → status=repaid → 债务清零
```

### 场景：债务升级

```
OC-5 在第20章创建，deadline=22。
第21章未偿还 → debt=2
第22章（deadline）仍未偿还 → debt=3 → soft→medium
第23章必须处理，否则 debt=4 继续累积...
第26章 debt=6 → medium→hard → 必须本章处理
```
