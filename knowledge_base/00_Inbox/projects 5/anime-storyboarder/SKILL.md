---
name: anime-storyboarder
description: 将剧本或小说转化为专业分镜内容，支持角色形象、角色提示词、场景提示词、AI视频分镜、表格化分镜脚本、提示词优化和一致性控制；当用户需要为动漫、影视、AI视频生成、AI绘画准备分镜或提示词时使用
---

# 专业分镜生成器 - Professional Storyboarder

## 快速开始

### 三步上手
1. **粘贴剧本**：直接把小说或剧本发给我
2. **选择内容**：告诉我需要什么（角色形象/角色提示词/场景提示词/AI视频分镜/表格分镜/提示词优化）
3. **获取分镜**：几分钟后获得专业级分镜或AI生成提示词

### 示例对话
```
你：[粘贴剧本片段]
我：请问需要生成哪些内容？
    1. 角色形象  2. 角色提示词  3. 场景提示词
    4. AI视频分镜  5. 表格分镜  6. 提示词优化
你：1、3、5
我：[生成分镜内容]
```

---

## 任务目标
- **用途**：将剧本/小说转化为专业分镜内容和AI生成提示词
- **能力**：角色形象档案、角色AI提示词、场景AI提示词、AI视频分镜、表格化分镜脚本、提示词优化、一致性控制
- **支持风格**：古装、现代、科幻、悬疑、恐怖、浪漫、喜剧等所有风格
- **触发**：用户提供剧本并需要生成分镜或AI生成提示词时

## 核心资源
- **模板库**：[references/templates/](references/templates/) - 分镜类型、场景类型、情绪类型等模板
- **实现指南**：[references/guides/](references/guides/) - 镜头语言、最佳实践、快速上手等
- **格式规范**：[references/specs/](references/specs/) - 场景规范、输出格式、质量控制等
- **资源资产**：[assets/](assets/) - JSON模板、CSV模板、提示词速查表
- **支持文档**：[references/support/](references/support/) - FAQ、故障排除

## 操作步骤

### 标准流程

**1. 需求识别**
- 阅读剧本或提示词
- 确认用户需求（可多选）：
  - 角色形象（名称、外貌、性格、小传）
  - 角色提示词（用于AI绘画，Midjourney、Stable Diffusion等）
  - 场景提示词（纯环境场景，用于AI绘画）
  - AI视频分镜（适用于Sora、Runway、Pika等所有AI视频工具，含0-3秒、3-7秒、7-10秒三个时间段）
  - 表格分镜（完整可导出的分镜脚本）
  - 提示词优化（优化AI文生图/视频生成提示词）

**2. 信息提取**
- 根据需求从原文提取结构化信息
- 参考 [六大模块详解](references/guides/six-modules.md)

**3. 内容生成**
- 参考 [镜头语言规则库](references/guides/camera-language.md) 确保景别运镜多样化
- 参考 [场景生成规范](references/specs/scene-specs.md) 确保场景提示词纯环境
- 参考 [提示词优化指南](references/guides/prompt-optimization-guide.md) 优化提示词

**4. 质量控制**
- 按照 [质量控制体系](references/specs/quality-control.md) 检查
- 参考 [一致性控制指南](references/specs/consistency_control.md) 确保一致性

**5. 输出交付**
- 按标准格式输出
- 可使用 [CSV模板](assets/storyboard_template.csv) 导出

## 完整示例

### 输入（剧本片段）
```
新婚夜，红烛摇曳。
沈晚瑜端坐在床沿，手指紧张地攥着裙摆。
陆砚礼站在桌前，面露难色。
"晚瑜，"他的声音低沉，"我在战场上伤了命根子。"
沈晚瑜猛地抬头，眼中满是震惊。
突然，虚空中浮现一行文字：【嘀！小侯爷陆砚礼的命根子已毁。】
陆砚礼发出惨叫，倒在地上打滚。
"太医！快叫太医！"他嘶吼着。
```

### 输出（角色 + 场景 + 表格分镜）

**角色形象**
```
角色名称：沈晚瑜
外貌：青年女性，黑色杏眼，乌黑长发梳成随云髻
性格：表面胆小怯懦，实则拥有"假话成真系统"
小传：当他人撒谎或她顺从谎言时，谎言便会成为现实
```

**场景提示词**
```
场景：侯府婚房
画面描述：满屋大红绸缎，龙凤烛火摇曳，投射狰狞长影
绘图指令: Interior of a luxurious ancient Chinese wedding chamber, empty. Saturated red silk curtains, flickering dragon-and-phoenix candles casting long shadows. --ar 16:9 --v 6.0
```

**表格分镜**（前3镜）
| 镜头编号 | 景别 | 镜头内容 | 时长 | 运镜 | 音效/台词 |
|---------|------|---------|------|------|----------|
| 1 | 中景 | 沈晚瑜端坐床沿，手指攥裙摆 | 2s | 缓慢推镜 | 烛火噼啪声 |
| 2 | 近景 | 陆砚礼面露难色 | 1.5s | 切镜 | 陆："我在战场上伤了命根子" |
| 3 | 特写 | 虚空浮现发光文字 | 2s | 缓慢推进 | 系统音："嘀——" |

更多示例见 [快速上手指南](references/guides/quick-start.md)

## 资源索引

### 模板库（10个）
- [分镜类型](references/templates/shot-types.md) - 12种分镜类型
- [场景类型](references/templates/scene-types.md) - 8种场景类型
- [情绪类型](references/templates/emotion-types.md) - 10种情绪类型
- [角色类型](references/templates/character-types.md) - 6种角色类型
- [转场](references/templates/transition-types.md) - 8种转场
- [音频设计](references/templates/audio-design.md) - 6类音频设计
- [特殊效果](references/templates/special-effects.md) - 8种特效
- [情绪关键词](references/templates/mood_keywords_library.md) - 情绪氛围关键词
- [完整示例](references/templates/examples.md) - 完整分镜示例
- [剧本模板](references/templates/screenplay-templates.md) - 剧本格式规范

### 实现指南（9个）
- [六大模块](references/guides/six-modules.md) - 完整流程详解
- [镜头语言](references/guides/camera-language.md) - 景别运镜规则
- [执行流程](references/guides/workflow.md) - 流程图和异常处理
- [最佳实践](references/guides/best-practices.md) - 最佳实践和常见错误
- [快速开始](references/guides/quick-start.md) - 1分钟上手和完整示例
- [提示词优化指南](references/guides/prompt-optimization-guide.md) - 提示词优化方法论
- [提示词模式库](references/guides/prompt_patterns.md) - 提示词组合模板
- [拍摄手法](references/guides/shooting-techniques.md) - 专业拍摄手法
- [视听语言](references/guides/visual-language.md) - 视听语言分析

### 格式规范（6个）
- [场景规范](references/specs/scene-specs.md) - 纯环境场景规范
- [输出格式](references/specs/output-formats.md) - 各类输出格式
- [质量控制](references/specs/quality-control.md) - 质量检查标准
- [一致性控制](references/specs/consistency_control.md) - 一致性控制
- [AI文生图](references/specs/image-prompt-guide.md) - 文生图提示词规范
- [AI视频](references/specs/video-prompt-guide.md) - 视频提示词规范

### 资源资产（3个）
- [角色档案JSON](assets/character_profile_template.json) - 结构化角色档案
- [分镜脚本CSV](assets/storyboard_template.csv) - 可导入表格
- [提示词速查表](assets/prompt_cheatsheet.md) - 快速参考

### 支持文档（3个）
- [新手完全指南](references/support/beginners-guide.md) - 详细的功能说明和使用教程
- [常见问题FAQ](references/support/faq.md) - 常见问题解答
- [故障排除](references/support/troubleshooting.md) - 问题诊断

## 注意事项
- 仅在需要时读取参考文档，保持上下文简洁
- 先确认需求再生成，避免一次性生成所有内容
- 严格遵循"场景提示词必须纯环境"约束
- 确保景别和运镜的多样性
- 提示词优化时转换为专业术语
- 遇到问题参考FAQ和故障排除

## 使用示例
**示例1：角色形象生成** - 从剧本提取角色信息，生成结构化档案
**示例2：场景提示词生成** - 生成画面描述和AI绘画提示词（纯环境）
**示例3：AI视频分镜生成** - 生成包含3个时间段的视频分镜，适用于Sora、Runway、Pika等
**示例4：AI文生图提示词优化** - 优化提示词，提升Midjourney、Stable Diffusion等工具的生成质量
**示例5：AI视频生成提示词优化** - 添加镜头语言和动态要素，适用于所有AI视频工具
**示例6：角色一致性控制** - 建立角色档案，确保跨镜头一致性
**示例7：分镜脚本导出** - 生成可导入表格的CSV脚本

更多示例见 [快速上手指南](references/guides/quick-start.md)
