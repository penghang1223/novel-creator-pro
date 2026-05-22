# 小说立项

Create or refine a novel project plan using `novel_creation_promax`.

**输入**：`/novel-plan [平台] [题材/创意]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `onboarding` 模式。
2. 读取 `novel_creation_promax/docs/PIPELINE.md` 的创意→设定→大纲阶段。
3. **知识库预读（在设计角色/设定之前必须完成）**：
   - `knowledge_base/60_Platform/平台规则.md` — 目标平台的写作规范和节奏要求
   - `knowledge_base/20_Characters/` 下全部文件 — 角色设计方法论（三维度、四维动机模型、原型参考、弧线模板）
   - `knowledge_base/10_WorldBuilding/题材知识库/` 中对应题材的知识包
   - `knowledge_base/30_Plot/大纲模板.md` + `长篇节奏循环引擎.md` + `伏笔设计.md` — 大纲/细纲结构设计（前10章节拍、小循环、四新、爽点密度、情绪曲线）
   - `knowledge_base/50_Quality/红线检查/` — 红线系统和质量约束
   - **知识库是参考工具，不是唯一标准**。用它提升决策质量（比如避免俗套人设、检查动机是否有内部冲突），但最终设计由创意判断决定，不盲从模板。
   - ⚠️ **不读不准写内容**。seal 会检查：人物档案是否含四维动机/角色弧线/群像功能/OOC清单等框架标记；大纲是否含前10章/小循环/四新/情绪曲线等 30_Plot 框架标记。缺失直接 FAIL。
4. 运行立项初始化：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "{平台}" --title "{书名}" --genre "{题材}" --premise "{核心设定}"`
5. 用知识库方法论补齐创意、设定、大纲、8卷细纲、素材/小说信息.md、80_Projects 配置。重点：
   - 角色设计用 `人物动机设计框架.md` 的四维模型检查（欲望/恐惧/创伤/缺陷，四维之间必须有内部冲突）
   - 角色职业/背景用 `角色原型参考.md` 的趋势判断是否贴合目标读者
   - 大纲/细纲用 `长篇节奏循环引擎.md` 的框架：前10章逐章节拍表、每卷四新原则、小循环公式（目标→阻碍→压制→爆发→余波）、爽点密度表、情绪曲线
   - 避免凭模板硬套，每个设计选择要能回答"为什么这样设计"
6. 最终复核运行：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "{小说目录}"`
7. `seal` 失败时禁止写正文；只有 `can_write_chapter=true` 后才能进入 `/novel-write`。

**示例**：`/novel-plan 番茄 都市异能，主角能看到物品未来价格`
