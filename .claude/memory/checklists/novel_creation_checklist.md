# 新小说立项强制检查清单

> 每次接新小说创作任务时，必须逐项打勾，少一个勾都不能开始写正文。
> 违反此流程 = 跳过必要步骤 = 质量不达标。

---

## 阶段一：创作前准备（必须全部完成）

- [ ] **1. 读取双端共享记忆**
  - MEMORY.md
  - .claude/memory/decisions/preferences.md
  - .claude/memory/active_novels/progress.md
  - .claude/memory/feedback/ 下所有文件

- [ ] **2. 读取创作前必读知识库（4个文件，缺一不可）**
  - [ ] `knowledge_base/50_Quality/红线检查/红线系统.md`
  - [ ] `knowledge_base/50_Quality/红线检查/章节前检查.md`
  - [ ] `knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md`
  - [ ] `knowledge_base/40_Writing/04_场景与描写/爽点设计.md`

- [ ] **3. 和用户确认立项信息（逐一确认，不能假设）**
  - [ ] 书名
  - [ ] 平台（番茄/七猫/起点/晋江/知乎等）
  - [ ] 类型/题材
  - [ ] 核心设定（金手指规则、世界观）
  - [ ] 人设（男女主+核心配角）
  - [ ] 目标篇幅（章节数/字数）
  - [ ] 核心爽点方向
  - [ ] 对标作品（如有）

- [ ] **4. 确认优化方向**
  - 如基于参考文档创作，需明确哪些保留、哪些改动
  - 用户说"可以参考但不能照搬"时，必须提出具体优化建议并获确认

---

## 阶段二：项目初始化（必须串行执行，不能并行）

- [ ] **5. 创建项目目录结构**
  - `novel_output/{平台}/{书名}/{创意,设定,结构,细纲,正文,摘要,记忆,素材}`

- [ ] **6. 初始化记忆系统**
  - `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py init --memory-dir novel_output/{平台}/{书名}/记忆`

- [ ] **7. 生成 project_bootstrap.json 并导入记忆系统**
  - 按模板填写项目信息、人物设定、剧情线
  - `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ...`

- [ ] **8. 提取风格DNA基线（新项目必须做）**
  - `python novel_creation_promax/scripts/style_dna_extractor.py --input 样章.txt --output style_dna_baseline.json`
  - 无样章时，先写第1章初稿，再提取

- [ ] **9. 生成大纲（必须完整，不能只做一部分）**
  - [ ] 总纲：outline.md（8卷结构+核心设定+人物+伏笔清单）
  - [ ] 分卷细纲：细纲/卷一.md 到 卷八.md（每卷至少包含核心任务+关键事件+爽点+伏笔）
  - [ ] 素材信息：素材/小说信息.md（必须按标准结构，参考已有项目）
    - [ ] 基本信息（表格：书名、作者、平台、分类、字数、状态）
    - [ ] 三档简介（短50字/标准150字/长300字）
    - [ ] 标签
    - [ ] 主角信息表
    - [ ] 封面AI绘画提示词（中英文）
    - [ ] 发布平台适配信息
    - [ ] 作品详纲（一句话故事、梗概、核心主题、卷结构、节奏设计）
    - [ ] 人物小传（女主/男主/核心配角，含外貌、性格、核心矛盾、弧光）
    - [ ] 核心设定速查（时间线、人物关系图）
    - [ ] 核心卖点
    - [ ] 角色命名禁忌

- [ ] **10. 写入 80_Projects 配置**
  - `knowledge_base/80_Projects/{书名}/_config.md`

- [ ] **11. 更新 MEMORY.md**
  - 在"长篇连载"列表中添加新项目

---

## 阶段三：章节创作（每章都必须）

- [ ] **12. 执行章节前检查（9问）**
  - 按 `knowledge_base/50_Quality/红线检查/章节前检查.md` 回答9个问题
  - 评分≥70分方可开始创作
  - 检查结果必须记录到 `novel_state.json.workflow_gate.pre_check_score`

- [ ] **13. 生成章节记忆包（续写时）**
  - `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py chapter-pack --chapter N --memory-dir ...`

- [ ] **14. 撰写正文**
  - 平台字数要求：七猫3000-4000字/章，番茄2800-3200字/章
  - 第三人称（除非用户明确要求第一人称）

- [ ] **15. 自检AI味**
  - 用32项指标扫描（见 `降低AI痕迹.md`）
  - 重点清零：`停了一秒`、`沉默了两秒`、`过了三秒` 等精确计时心理/反应描写
  - 重点关注：句式单一、连接词过度、抽象词过多、Show vs Tell失衡
  - ⚠️ **不要过度清除常用词**：目标是"降低频率至自然水平"，不是"清零"。"看到""很"等词在自然文本中必然出现，控制到合理密度即可，宁可保留少量常用词，也不要让文本变得生硬不自然

- [ ] **16. 自检爽点结构**
  - 对照 `爽点设计.md`
  - 每章至少1个小爽点，每3章1个中爽点

- [ ] **17. 字数检查与写后审计凭证**
  - 七猫：3000-4000字
  - 番茄：2800-3200字
  - 必须按单章运行写后审计并同步状态：
    ```bash
    python novel_creation_promax/scripts/post_write_audit.py \
      --chapter-file 正文/章节文件.md \
      --title "章节标题" \
      --output 摘要/audit_chNNN.json \
      --novel-state novel_state.json
    ```
  - 审计报告必须落盘，且 `novel_state.json.workflow_gate.audit_status` 必须为 `passed`
  - 字数红线或一级红线未通过时，不得进入章节完成/记忆回填

- [ ] **18. 同步章节摘要到记忆系统**
  - `python novel_creation_promax/novel-memory-pro/scripts/memory_manager.py sync-chapter --input chapter_NNN_summary.json --memory-dir ...`

- [ ] **19. 更新项目状态**
  - novel_state.json（当前章节、字数、伏笔状态）
  - novel_state.json.workflow_gate（last_checklist_step、pre_check_score、audit_status、last_audit_report）
  - 80_Projects/_config.md（进度摘要从 novel_state.json 派生）
  - MEMORY.md（进度摘要从 novel_state.json 派生）

---

- [ ] **20. 最终复核（写正文前必须做）**
  - [ ] 对照本清单，逐项确认所有19步已完成，无跳步
  - [ ] 检查项目目录下是否有空文件夹（应有内容的文件夹不能为空）
  - [ ] 检查 outline.md 和细纲目录是否完整
  - [ ] 检查素材目录是否有小说信息
  - [ ] 检查写后审计 JSON 凭证存在，且 audit_status 为 passed

---

## 常见错误（本清单就是用来防止这些的）

| 错误 | 后果 | 本清单对应步骤 |
|------|------|-------------|
| 只读2个知识库就开写 | 漏掉降AI技巧和爽点设计 | 步骤2 |
| 并行执行初始化步骤 | 遗漏或出错 | 阶段二标题 |
| 不提取风格DNA | 后续章节风格漂移无法检测 | 步骤8 |
| 不执行9问检查 | 写出"水章节"或"原地踏步" | 步骤12 |
| 写完不自检AI味 | AI味重，平台拒稿 | 步骤15 |
| 过度清除"看到""很" | 文本不自然、生硬 | 步骤15备注 |
| 不更新MEMORY.md | 双端记忆不同步 | 步骤11、19 |
