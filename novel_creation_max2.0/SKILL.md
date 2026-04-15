---
name: novel_creation_max
description: 旗舰级小说创作系统，整合AI记忆中台、多风格创作引擎与质量约束系统，支持长篇连载的连贯性管理、短篇爆款内容快速生成与多题材风格融合校准；当用户需要创作原创小说、进行风格校准、连载续写、或跨题材改编时使用
dependency:
  python:
    - Pillow>=9.0.0
---

# 小说创作 Max (旗舰版)

## 概览

这是小说创作的**旗舰级系统**，整合了四大核心模块：

1. **AI记忆中台**：生产级记忆系统，确保长篇创作的连贯性、一致性和稳定性
2. **多风格创作引擎**：覆盖爆款爽文、人性写作、毒舌神回复、专业叙事等全风格谱系
3. **智能工作流**：从立项到连载、从大纲到正文、从改编到校准的全流程自动化
4. **质量约束系统**：红线系统、必答问题、强制读取验证，确保创作质量与一致性

## 核心约束系统

### 三大质量保障机制

**机制1：红线系统**
- 一级红线（绝对禁止）：原创性、人称使用、性别姓名
- 二级红线（质量约束）：风格漂移、人物OOC、剧情矛盾、伏笔丢失
- 三级红线（质量优化）：章节推进、字数规范、结构规范、悬念机制

**机制2：必答问题系统**
- 触发场景：长篇第1章创作、长篇第2章及以后续写
- 核心问题：9个关键问题（章节位置、情节团、悬念承接、伏笔处理等）
- 验证标准：必须用1句话清晰描述核心推进事件

**机制3：记忆系统输出格式**
- 章节前记忆唤醒：输出唤醒确认，包含大纲、追踪、章节文件的读取证明
- 章节后记忆回填：输出回填确认，包含摘要、人物状态、伏笔状态等
- 风格校准：输出校准报告，包含风格DNA、偏离度、修正建议

### 约束优先级

1. 一级红线 > 必答问题 > 记忆唤醒 > 创作执行
2. 红线检测（实时）> 必答问题验证（创作前）> 记忆回填（创作后）
3. 质量修正 > 继续创作 > 交付结果

## 适用场景

- **长篇连载创作**：需要长期维护人物设定、剧情走向、风格统一的网文
- **短篇爆款写作**：需要快速生产符合平台算法的热门内容
- **AI漫剧改编**：将小说改编为AI漫剧的分镜和脚本
- **多题材融合**：将不同题材进行创新性融合和重构
- **风格迁移**：在保持故事内核的前提下改变写作风格
- **平台适配**：针对番茄/起点/晋江等平台的规则和读者偏好优化作品
- **剧情可视化**：将小说剧情片段转换为Seedance视频生成提示词

## 快速入门

### 长篇连载创作（核心流程）

1. **项目立项**：确定题材、风格、核心冲突、目标读者
2. **记忆初始化**：`python scripts/memory_manager.py init --memory-dir ./my_novel`
3. **大纲设计**：总章节规划、分卷设计、核心情节点、伏笔布局
4. **章节创作**：
   - 章节前记忆唤醒：`python scripts/memory_manager.py chapter-pack --chapter N`
   - 执行创作（遵守红线系统和必答问题）
   - 章节后记忆回填：`python scripts/memory_manager.py sync-chapter --input chapter_summary.json`
5. **阶段性回顾**：每5-10章生成回顾报告，优化记忆系统

### 短篇爆款创作

1. **快速选题**：追踪热点、选择题材、确定目标读者
2. **结构设计**：选择模板、设计核心冲突、规划反转
3. **内容创作**：开场钩子→铺垫→冲突→高潮→收尾
4. **爆款优化**：强化钩子密度、爽点、反转冲击力

## 智能体与脚本的职责分工

| 任务类型 | 执行方 | 说明 |
|---------|--------|------|
| 内容创作、文案生成 | 智能体 | 充分利用语言理解和生成能力 |
| 人物一致性分析 | 智能体 | 对比人物档案与文本，判断是否OOC |
| 剧情连贯性检查 | 智能体 | 阅读前后文，推理分析逻辑漏洞 |
| 记忆系统管理 | 脚本 | 文件CRUD操作，`memory_manager.py` |
| 风格DNA提取 | 脚本 | 文本统计分析，`style_dna_extractor.py` |
| 风格校准 | 脚本 | 统计偏离度计算，`style_calibrator.py` |
| 封面生成 | 脚本 | 图像处理，`generate_cover.py` |
| 人物命名 | 脚本 | 随机选名+撞名检查，`name_generator.py` |

## 核心脚本使用指南

### memory_manager.py（记忆管理器）

```bash
# 初始化记忆系统
python scripts/memory_manager.py init --memory-dir ./my_novel

# 导入项目基础信息
python scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ./my_novel

# 生成章节记忆包
python scripts/memory_manager.py chapter-pack --chapter 12 --memory-dir ./my_novel --output chapter_12_pack.json

# 同步章节摘要
python scripts/memory_manager.py sync-chapter --input chapter_12_summary.json --memory-dir ./my_novel

# 阶段性回顾
python scripts/memory_manager.py review-pack --chapter 50 --memory-dir ./my_novel --output review_50.json

# 查看记忆统计
python scripts/memory_manager.py stats --memory-dir ./my_novel
```

### style_dna_extractor.py（风格DNA提取器）

```bash
# 从参考作品提取风格DNA
python scripts/style_dna_extractor.py --input sample.txt --output style_dna.json --author "作者名"
```

### style_calibrator.py（风格校准器）

```bash
# 检查新章节的风格漂移
python scripts/style_calibrator.py --input chapter_12.txt --style-dna style_dna.json --mode realtime --output report.json
```

### generate_cover.py（封面生成器）

```bash
# 生成封面
python scripts/generate_cover.py --title "小说标题" --author "作者名" --style auto --output cover.png
```

### name_generator.py（人物命名器）

```bash
# 生成5个古风雅致男性名
python scripts/name_generator.py --gender male --style ancient_elegant --count 5

# 生成3个仙侠女性名
python scripts/name_generator.py --gender female --style xianxia --count 3

# 生成10个随机名字（不限风格）
python scripts/name_generator.py --count 10

# 排除特定姓氏
python scripts/name_generator.py --gender male --exclude-surnames 叶 林 萧

# 仅使用复姓
python scripts/name_generator.py --surname-tier compound --count 5
```

**风格选项**：ancient_elegant / martial / xianxia / modern / rustic / dark / gentle / strong / neutral

脚本自动避开知名小说角色撞名和AI同质化命名模式。

## 资源索引

### 参考文档

- **质量约束系统**：[references/quality-constraints/](references/quality-constraints/) - 创作红线、必答问题、记忆系统输出格式
- **技术基础**：[references/technical-foundations/](references/technical-foundations/) - 创作技术规范、叙事技巧、人性化写作；含[进阶叙事技法](references/technical-foundations/advanced-narrative-techniques.md)（双线镜像叙事、灰色人设、硬核智斗、诗化语言）
- **模板工具**：[references/template-tools/](references/template-tools/) - 短篇模板、开场钩子、人设原型、大纲模板
- **题材与商业化**：[references/genre-and-commercialization/](references/genre-and-commercialization/) - 题材指南、商业化可行性、创新指南
- **平台适配**：[references/platform-adaptation/](references/platform-adaptation/) - 番茄/起点/晋江平台规则、黄金三章、开篇模板
- **专项工作流**：[references/special-workflows/](references/special-workflows/) - 题材适配流程、侦探工作流、短剧改编；含[Seedance视频提示词转换](references/special-workflows/seedance-video-prompt.md)
- **记忆系统**：[references/memory-system/](references/memory-system/) - 人物档案、风格DNA格式、章节同步、记忆优化；含[人物小传模板](references/memory-system/character-biography-template.md)（叙事化角色构思）
- **评估系统**：[references/evaluation-system/](references/evaluation-system/) - 内容评估、创意评估、大纲评估等；含[低AI痕迹润色](references/evaluation-system/low-ai-trace-polish.md)
- **风格指南**：[references/style-guides/](references/style-guides/) - 作家风格解析、毒舌风格、题材融合
- **连贯性系统**：[references/continuity-system/](references/continuity-system/) - 偏差处理、大纲执行、审查机制；含[伏笔铺设指南](references/continuity-system/foreshadowing-design.md)
- **创作指南**：[references/writing-guides/](references/writing-guides/) - 内置提示词、写作指南、工作流；含[人物命名指南](references/writing-guides/naming-guide.md)（反AI同质化命名+避撞名）
- **交互模板**：[references/interaction-templates/](references/interaction-templates/) - 各阶段交互模板
- **题材与技法**：[references/genre-and-skills.md](references/genre-and-skills.md) - 各题材特点与写作技法

### 语料库

- **神回复库**：[assets/corpus/witty-replies-110.md](assets/corpus/witty-replies-110.md)、[assets/corpus/witty-replies-315.md](assets/corpus/witty-replies-315.md)
- **毒舌语料**：[assets/corpus/sarcastic-ai-examples.md](assets/corpus/sarcastic-ai-examples.md)、[assets/corpus/sarcastic-knowledge.md](assets/corpus/sarcastic-knowledge.md)
- **其他语料**：[assets/corpus/nonsense-buddha.md](assets/corpus/nonsense-buddha.md)
- **名字数据库**：[assets/corpus/name-database.json](assets/corpus/name-database.json)（供 `name_generator.py` 使用，含姓氏/名/避坑名单）

### 模板与配置

- **项目初始化模板**：[assets/templates/project-bootstrap.json](assets/templates/project-bootstrap.json)
- **章节摘要模板**：[assets/templates/chapter-summary.json](assets/templates/chapter-summary.json)
- **示例风格DNA**：[assets/examples/sample-style-dna.json](assets/examples/sample-style-dna.json)
- **默认配置**：[assets/config/default-config.json](assets/config/default-config.json)

## 注意事项

- 创作前务必阅读相关参考文档，特别是质量约束系统的指导
- 长篇连载必须严格执行记忆系统的初始化、唤醒、回填流程
- 遵守红线系统的约束，确保创作质量和一致性
- 针对目标平台创作时，参考平台适配指南调整开篇结构和节奏
- 人物一致性检查和剧情连贯性检查由智能体完成，无需调用脚本
- 仅在需要技术性处理时调用脚本（如记忆管理、风格校准等）
- 脚本已内置输入验证，传入无效参数会输出明确的错误信息
- 创作完成后可使用低AI痕迹润色指南进行终稿优化
- 为角色命名时，优先使用 `name_generator.py` 生成名字，避免AI同质化命名和知名小说撞名
