# 写作执行层优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过三层约束（写作宪法 + 动态约束模板 + 程序化门禁）解决 AI 不遵守写作规则的问题，同时不影响现有菜单、记忆、发布等功能。

**Architecture:** 新增 3 个文件（宪法/模板/Gate 脚本），重构 SKILL.md 硬门禁部分为状态机流程，其余模块不动。

**Tech Stack:** Markdown（宪法+模板），Python 3（Gate 脚本，复用现有 `post_write_audit.py` 的词库和检测模式）

---

## 文件清单

| 文件 | 动作 | 职责 |
|------|------|------|
| `novel_creation_promax/references/writing_constitution.md` | 新增 | 写作底线规则（5条红线，~80行） |
| `novel_creation_promax/references/chapter_constraint_template.md` | 新增 | 每章约束注入模板（~40行） |
| `novel_creation_promax/scripts/writing_gate.py` | 新增 | Pass 1→2 之间的 5 项速检脚本（~150行） |
| `novel_creation_promax/SKILL.md` (lines 17-568) | 重写 | 硬门禁部分精简为状态机流程（~100行） |
| `novel_creation_promax/references/orchestrator.md` | 微调 | 正文创作执行链中引用 Gate 脚本 |

---

## Task 1: 创建写作宪法

**Files:**
- Create: `novel_creation_promax/references/writing_constitution.md`

- [ ] **Step 1: 创建写作宪法文件**

从现有知识库提炼 5 条红线规则，只保留"出现即废"的硬规则。

```markdown
# 写作宪法

> 每章写作时必须遵守的底线规则。违反任何一条 = 本章作废。
> 不替代写作速查卡，速查卡是"怎么做"，宪法是"不能做什么"。

## 第一条：原创性红线（绝对禁止）

- 不得抄袭/高度模仿任何已发表作品
- 不得出现元叙事工艺术语：切面、旁白、镜头、转场
- 不得用代码块格式写正文

## 第二条：字数与结构红线

- 每章字数符合本项目设定（从 `novel_state.json` 的 `word_count_range` 读取，未设置时按平台默认：番茄 2800-3200 / 起点 2000-4000 / 知乎 3000-5000）
- 前 300 字必须有冲突/悬念/动作（禁止平淡环境开场）
- 章末必须断在悬念/冲突处（禁止平淡收束）
- 严格在细纲截断点停笔，不蹭下一章内容

## 第三条：AI 味红线（Pass 2 必清零）

**绝对禁止词**（出现即废）：
从而、以此、进一步凸显、这表明、这说明、这反映了、总而言之、不言而喻、他是一个……的人

**高危限制词**（单章 ≤3 次）：
突然、微微、沉默、感觉、嘴角、然而、或许

**七大反模式**（写中自检）：

| 反模式 | 症状 | 治疗 |
|--------|------|------|
| 计时器心理 | "想了一秒/沉默了十秒/顿了五秒" | 删除计时，改为行为/感官暗示 |
| 废话对话 | "嗯/那/好吧"连续出现，不推动信息 | 删除或合并为一句有信息量的对话 |
| 凑字数重复 | 同一场景换说法反复写 | 只写一次，写透 |
| 乒乓球短句 | 连续 5 句纯对话无描写 | 每两句对话之间插入动作/环境/感官 |
| 通用动作 | 笑了笑/皱了皱眉/叹了口气 | 用角色行为指纹替换 |
| 直白情绪命名 | 她愤怒/他委屈/感到绝望 | 改为行为/生理反应 |
| 套路化结尾 | "够了"/"桃花瓣落下"/"一切都在继续" | 用独特信息/情绪收束 |

## 第四条：对话红线

- 对话占比 ≥ 25%
- 每段对话场景至少覆盖 2-3 个六要素（表情微反应/心理独白/听觉细节/环境烘托/节奏留顿/倾听者反应）
- 纯对话超过 3 轮必须插入动作/环境细节
- 禁止使用"他说""她问道"作为对话标签（用动作锚点代替）
- 禁止角色完整回答对方问题（要有回避/沉默/转移）
- 每句对话必须附带面部表情/眼神/微反应

## 第五条：人物红线

- 每个核心角色必须展现至少一个"矛盾特质"
- 禁止"形容词堆叠式"人物描写
- 情感表达优先级：行为 > 生理反应 > 心理活动 > 直接命名
- 禁止角色所有行为都与其主标签一致
- 禁止角色总做"最优选择"
```

- [ ] **Step 2: 验证宪法内容完整性**

对照以下来源确认无遗漏：

```bash
# 确认绝对禁止词与 post_write_audit.py 的 ABSOLUTE_BANNED 一致
grep -A20 "ABSOLUTE_BANNED" novel_creation_promax/scripts/post_write_audit.py

# 确认高危词与 STRICT_LIMITED 一致
grep -A15 "STRICT_LIMITED" novel_creation_promax/scripts/post_write_audit.py

# 确认对话红线覆盖了速查卡 §二 的六要素
grep "表情/微反应\|心理独白\|听觉细节\|环境烘托\|节奏/留顿\|倾听者反应" novel_creation_promax/references/写作速查卡.md
```

预期：宪法中的词表与 `post_write_audit.py` 完全一致，对话六要素覆盖完整。

- [ ] **Step 3: 提交**

```bash
git add novel_creation_promax/references/writing_constitution.md
git commit -m "feat: add writing constitution — 5 red-line rules for chapter writing"
```

---

## Task 2: 创建动态约束注入模板

**Files:**
- Create: `novel_creation_promax/references/chapter_constraint_template.md`

- [ ] **Step 1: 创建约束模板文件**

```markdown
# 每章约束注入模板

> 写前自动填充，直接注入写作 prompt。替代手动"约束组装"过程。
> 填充规则：`{占位符}` 从对应来源读取数据替换。

---

【第{N}章 写中约束】

== 红线（写作宪法已加载，此处仅列本章高危项）==
• 本章字数目标：{word_count_range}
• 截断点：{chapter_cutoff_event}
• 标题关键词：{title_keywords}

== 人物约束 ==
• {character_A_name}：矛盾特质={contradictory_traits}，行为指纹={behavioral_fingerprint}
  本章负面约束：{negative_constraints}
• {character_B_name}：矛盾特质={contradictory_traits}，行为指纹={behavioral_fingerprint}
  本章负面约束：{negative_constraints}

== 对话约束 ==
本章对话场景类型：{dialogue_scene_type}
适用技法：{dialogue_techniques}
声纹要求：{voice_requirements}

== 节奏约束 ==
本章类型：{chapter_rhythm_type}
爽点设计：{climax_design}
情绪曲线：期待({tension_expect}) → 压制({tension_suppress}) → 反转({tension_reverse}) → 释放({tension_release})

== 去AI约束（Pass 2 重点）==
本章高危词：{high_risk_words_from_prev_audit}
速查卡 §七 三刀法则：本章重点"刀"哪几段：{three_cuts_focus}
```

- [ ] **Step 2: 验证模板占位符完整性**

确保所有 `{占位符}` 都能从现有数据源读取：

```bash
# 确认 novel_state.json 有 word_count_range 字段（或需要新增）
python3 -c "
import json
with open('novel_output/七猫/她眼里有我的未来/novel_state.json') as f:
    d = json.load(f)
print('word_count_range' in d, d.get('word_count_range'))
print('current_chapter' in d)
"
```

预期：如果 `word_count_range` 不存在，在 Task 5（验证）中补充默认值逻辑。

- [ ] **Step 3: 提交**

```bash
git add novel_creation_promax/references/chapter_constraint_template.md
git commit -m "feat: add chapter constraint injection template"
```

---

## Task 3: 创建 writing_gate.py

**Files:**
- Create: `novel_creation_promax/scripts/writing_gate.py`

- [ ] **Step 1: 创建 writing_gate.py 主体**

包含 5 项检查，与 `post_write_audit.py` 共享词库定义。

```python
#!/usr/bin/env python3
"""
写作门禁脚本 (Writing Gate) — Pass 1 → Pass 2 之间的轻量检查。

用法:
  python writing_gate.py --chapter "正文/第003章-xxx.md" --novel-dir "novel_output/七猫/小说名/"

退出码:
  0 = 通过，可以进入 Pass 2
  1 = 不通过，需要重写/修复
"""

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 词库（与 post_write_audit.py 保持一致）
# ============================================================

ABSOLUTE_BANNED = [
    "从而", "以此", "进一步凸显", "这表明", "这说明", "这反映了",
    "总而言之", "不言而喻", "他是一个",
]

# ============================================================
# 平台默认字数
# ============================================================

PLATFORM_DEFAULTS = {
    "番茄": (2800, 3200),
    "七猫": (2800, 3200),
    "起点": (2000, 4000),
    "知乎": (3000, 5000),
}


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    return sum(1 for c in text if '一' <= c <= '鿿')


def load_word_count_range(novel_dir: str) -> tuple:
    """从 novel_state.json 读取字数范围，未设置则按平台默认"""
    state_path = Path(novel_dir) / "novel_state.json"
    if state_path.exists():
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        if "word_count_range" in state:
            r = state["word_count_range"]
            return (r[0], r[1])
    # 按目录名推断平台
    for platform, default in PLATFORM_DEFAULTS.items():
        if platform in novel_dir:
            return default
    return (2800, 3200)  # 最终兜底


def check_word_count(text: str, novel_dir: str) -> tuple:
    """检查1：字数。返回 (passed, message)"""
    count = count_chinese_chars(text)
    lo, hi = load_word_count_range(novel_dir)
    if lo <= count <= hi:
        return True, f"字数 {count}（范围 {lo}-{hi}）✓"
    return False, f"字数 {count}（范围 {lo}-{hi}）✗ 需调整"


def check_chapter_boundary(text: str, novel_dir: str) -> tuple:
    """检查2：章节边界。检查章末是否包含下一章核心事件"""
    state_path = Path(novel_dir) / "novel_state.json"
    if not state_path.exists():
        return True, "无 novel_state.json，跳过边界检查"
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    hook = state.get("next_chapter_hook", "")
    if not hook:
        return True, "无 next_chapter_hook，跳过边界检查"
    # 取章末 500 字检查
    tail = text[-500:] if len(text) > 500 else text
    if hook in tail:
        return False, f"章末出现下一章核心事件「{hook[:20]}...」✗ 可能串章"
    return True, "章节边界 ✓"


def check_ping_pong(text: str) -> tuple:
    """检查3：乒乓球对话。连续 ≥5 行纯对话无描写"""
    lines = text.split("\n")
    max_consecutive = 0
    current = 0
    for line in line_stripped := [l.strip() for l in lines if l.strip()]:
        # 判断是否为对话行（包含引号或以引号相关标点开头）
        is_dialogue = bool(re.search(r'["""「」『』""' ']', line))
        # 排除包含动作描写的行
        has_action = bool(re.search(r'[，。]([^"「」]+)[，。]', line)) and not is_dialogue
        if is_dialogue and not has_action:
            current += 1
            max_consecutive = max(max_consecutive, current)
        else:
            current = 0
    if max_consecutive >= 5:
        return False, f"乒乓球对话：最长连续 {max_consecutive} 行纯对话 ✗（≤5 行）"
    return True, f"乒乓球对话：最长连续 {max_consecutive} 行 ✓"


def check_absolute_banned(text: str) -> tuple:
    """检查4：绝对禁止词"""
    found = []
    for word in ABSOLUTE_BANNED:
        if word in text:
            found.append(word)
    if found:
        return False, f"绝对禁止词出现：{', '.join(found)} ✗"
    return True, "绝对禁止词 ✓"


def check_dialogue_ratio(text: str) -> tuple:
    """检查5：对话占比速检（WARN 级别，不阻断）"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return True, "空文件"
    dialogue_lines = sum(1 for l in lines if re.search(r'["""「」『』""' ']', l))
    ratio = dialogue_lines / len(lines)
    if ratio < 0.25:
        return True, f"对话占比 {ratio:.1%} ⚠ 偏低（建议 ≥25%，不阻断）"
    return True, f"对话占比 {ratio:.1%} ✓"


def main():
    parser = argparse.ArgumentParser(description="写作门禁 — Pass 1 → Pass 2 轻量检查")
    parser.add_argument("--chapter", required=True, help="章节文件路径")
    parser.add_argument("--novel-dir", required=True, help="小说根目录")
    args = parser.parse_args()

    chapter_path = Path(args.chapter)
    if not chapter_path.exists():
        print(f"错误：文件不存在 {chapter_path}", file=sys.stderr)
        sys.exit(1)

    text = chapter_path.read_text(encoding="utf-8")

    checks = [
        ("字数检查", check_word_count(text, args.novel_dir)),
        ("章节边界", check_chapter_boundary(text, args.novel_dir)),
        ("乒乓球对话", check_ping_pong(text)),
        ("绝对禁止词", check_absolute_banned(text)),
        ("对话占比", check_dialogue_ratio(text)),
    ]

    all_passed = True
    print(f"\n{'='*50}")
    print(f"写作门禁检查 — {chapter_path.name}")
    print(f"{'='*50}")

    for name, (passed, msg) in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {msg}")
        if not passed:
            all_passed = False

    print(f"{'='*50}")
    if all_passed:
        print("结果：通过 ✓ 可以进入 Pass 2")
        sys.exit(0)
    else:
        print("结果：不通过 ✗ 需要修复后重跑")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 用现有章节测试 Gate 脚本**

```bash
python3 novel_creation_promax/scripts/writing_gate.py \
  --chapter "novel_output/七猫/她眼里有我的未来/正文/第003章-母亲的遗言.md" \
  --novel-dir "novel_output/七猫/她眼里有我的未来/"
```

预期：输出 5 项检查结果。字数和绝对禁止词应通过（Ch3 审计显示 3198 字，0 个绝对禁止词）。

- [ ] **Step 3: 测试失败场景**

创建一个临时测试文件，包含绝对禁止词：

```bash
echo "从而这反映了一个问题" > /tmp/test_gate_fail.md
python3 novel_creation_promax/scripts/writing_gate.py \
  --chapter /tmp/test_gate_fail.md \
  --novel-dir "novel_output/七猫/她眼里有我的未来/"
rm /tmp/test_gate_fail.md
```

预期：退出码 1，绝对禁止词检查显示 FAIL。

- [ ] **Step 4: 提交**

```bash
git add novel_creation_promax/scripts/writing_gate.py
git commit -m "feat: add writing_gate.py — Pass 1→2 lightweight audit (5 checks)"
```

---

## Task 4: 重构 SKILL.md 硬门禁部分

**Files:**
- Modify: `novel_creation_promax/SKILL.md` (lines 17-568 → ~100行)

- [ ] **Step 1: 备份当前 SKILL.md**

```bash
cp novel_creation_promax/SKILL.md novel_creation_promax/SKILL.md.bak
```

- [ ] **Step 2: 替换硬门禁部分**

将 SKILL.md 的 lines 17-568（从 `## ⛔ 硬门禁` 到 `硬门禁 5` 结尾的 `---` 分隔线之前）替换为：

```markdown
## ⛔ 写作流程（状态机）

**写作底线规则见 [`references/writing_constitution.md`](references/writing_constitution.md)（写作宪法），每章必读。**

### 阶段 0：写前准备

1. **加载写作宪法** → [`references/writing_constitution.md`](references/writing_constitution.md)
2. **9问必答** → `scripts/pre_write_check.py`，总分 ≥ 70 分
3. **写前5项检查**：AI词黑名单已加载 / 上一章已读取 / 人物对话档案已加载 / 标题关键词已提取 / 前300字有冲突
4. **约束组装** → 从 [`references/chapter_constraint_template.md`](references/chapter_constraint_template.md) 自动填充本章约束
5. **套路预判** → 参照速查卡 §九，列出本章可能涉及的套路+绕开策略

未完成以上任何一项 → 禁止开始写正文。

### 阶段 1：Pass 1 剧情稿

**目标**：写出完整剧情逻辑，不管 AI 词。

**规则**：
- 写的时候完全忽略 AI 词
- 专注于：剧情推进、角色行为逻辑、章节边界、对话信息量
- 每 300-500 字自检：有没有无聊？有没有重复？有没有推进？
- **对话写作参照**：速查卡 §二对话六要素 + §三对话五大技法
- **爽点节奏参照**：速查卡 §五爽点设计

**禁止在 Pass 1 做的事**：不检查 AI 词、不检查对话比例、不做风格校准。

### → Gate 检查（writing_gate.py）

```bash
python scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
```

5 项速检：字数 / 章节边界 / 乒乓球对话 / 绝对禁止词 / 对话占比。
不通过 → 回到 Pass 1 修复对应问题。

### 阶段 2：Pass 2 AI 词清理

**目标**：在保留剧情逻辑和对话风格的前提下，清理 AI 词。

**规则**：
- 以 Pass 1 输出为基准，只改词汇，不动叙事结构
- 对话修改保证：角色说话方式不变
- 如果替换导致语义不通，跳过该替换
- **去AI化参照**：速查卡 §七"每段三刀"法则 + §八 20 条硬性禁止

### → 完整审计（post_write_audit.py）

不通过 → 定点修复，不重写全章。

### 阶段 3：记忆同步

`memory_manager.py sync-chapter` → 更新记忆。

### 违规后果

| 违规行为 | 后果 |
|----------|------|
| 跳过 9 问必答系统 | 本章作废，回答 9 问后重写 |
| 跳过写前检查/约束组装 | 本章作废，完成后重写 |
| Pass 1 不通过 Gate 就进入 Pass 2 | 本章作废，修复 Gate 问题后重跑 |
| 写中放飞自我，写完发现 AI 味/废话/通用动作 | 本章作废，写的时候就该注意到 |
| 不跑完整审计就交付 | 本章视为未完成，必须补跑 |
| 审计不达标仍交付 | 本章作废，修复后重新审计 |
| 因果断裂（角色知道不该知道的信息） | 本章作废，修正信息流后重写 |
| 为了凑字数/对话占比而塞废话 | 本章作废，删废话后重新审计 |
```

- [ ] **Step 3: 验证 SKILL.md 完整性**

```bash
# 确认自动触发规则未被影响
grep -n "## 自动触发规则" novel_creation_promax/SKILL.md

# 确认菜单功能未被影响
grep -n "### \[0\] 新手模式\|### \[1\] 自由创作" novel_creation_promax/SKILL.md

# 确认总行数减少（原1556行，减少约300行）
wc -l novel_creation_promax/SKILL.md

# 确认没有残留的旧硬门禁编号
grep -n "硬门禁 [0-9]" novel_creation_promax/SKILL.md
```

预期：
- 自动触发规则仍在原位置（原 line 570 附近，新位置会前移）
- 菜单功能完整
- 总行数约 1250-1300
- 无旧硬门禁编号残留

- [ ] **Step 4: 删除备份**

```bash
rm novel_creation_promax/SKILL.md.bak
```

- [ ] **Step 5: 提交**

```bash
git add novel_creation_promax/SKILL.md
git commit -m "refactor: restructure SKILL.md hard gates into state machine flow
- Replace ~400 lines of scattered hard gates with ~100 line state machine
- Reference writing_constitution.md for bottom-line rules
- Insert writing_gate.py as Pass 1→2 checkpoint
- Keep auto-trigger rules, menu features, and all other sections unchanged"
```

---

## Task 5: 更新 orchestrator.md 引用

**Files:**
- Modify: `novel_creation_promax/references/orchestrator.md`

- [ ] **Step 1: 在正文创作执行链中添加 Gate 步骤**

在 orchestrator.md 的"二、正文创作执行链"中，Pass 1 和 Pass 2 之间插入 Gate 检查步骤。

找到现有内容中 `4. PASS 1` 和后续的审计部分，在两者之间添加：

```markdown
    │
    ▼
══════════════════════════════════════
4.5 GATE 检查（Pass 1→2 断点）
══════════════════════════════════════
    │
    ▼
python scripts/writing_gate.py --chapter {文件} --novel-dir {目录}
    │
    ├── exit 0 → 进入 Pass 2
    └── exit 1 → 回到 Pass 1 修复
```

- [ ] **Step 2: 验证 orchestrator 连贯性**

```bash
# 确认执行链顺序正确
grep -n "PASS 1\|Gate\|PASS 2\|审计" novel_creation_promax/references/orchestrator.md
```

- [ ] **Step 3: 提交**

```bash
git add novel_creation_promax/references/orchestrator.md
git commit -m "docs: add writing_gate.py step to orchestrator execution chain"
```

---

## Task 6: 端到端验证

- [ ] **Step 1: 验证宪法可读**

```bash
# 确认宪法文件存在且内容完整
wc -l novel_creation_promax/references/writing_constitution.md
# 预期：~80行
```

- [ ] **Step 2: 验证模板可读**

```bash
wc -l novel_creation_promax/references/chapter_constraint_template.md
# 预期：~40行
```

- [ ] **Step 3: 用真实章节跑 Gate**

```bash
python3 novel_creation_promax/scripts/writing_gate.py \
  --chapter "novel_output/七猫/她眼里有我的未来/正文/第001章-她看到了他的未来.md" \
  --novel-dir "novel_output/七猫/她眼里有我的未来/"
```

预期：5 项检查全部输出结果。

- [ ] **Step 4: 确认 SKILL.md 自动触发规则完整**

```bash
grep -c "自动读取" novel_creation_promax/SKILL.md
# 预期：与修改前一致
```

- [ ] **Step 5: 确认 post_write_audit.py 未被修改**

```bash
git diff novel_creation_promax/scripts/post_write_audit.py
# 预期：无输出（未修改）
```

- [ ] **Step 6: 最终提交**

```bash
git add -A
git commit -m "chore: verify writing enforcement redesign — all components operational"
```

---

## 回滚指南

如需回滚：

```bash
# 查看本次改动的提交历史
git log --oneline -6

# 方案A：整体回滚到优化前
git revert HEAD~5..HEAD

# 方案B：只删新增文件，保留 SKILL.md 改动
git checkout HEAD~5 -- novel_creation_promax/references/writing_constitution.md
git checkout HEAD~5 -- novel_creation_promax/references/chapter_constraint_template.md
rm novel_creation_promax/scripts/writing_gate.py

# 方案C：完全恢复 SKILL.md 原版
git checkout HEAD~4 -- novel_creation_promax/SKILL.md
```

不会丢失任何创作数据（novel_state.json、memory、chapter files 均未改动）。
