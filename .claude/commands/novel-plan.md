# 小说立项

Create or refine a novel project plan using `novel_creation_promax`.

**输入**：`/novel-plan [平台] [题材/创意]`

**执行**：
1. 读取 `novel_creation_promax/MODE_REGISTRY.md` 的 `onboarding` 模式。
2. 读取 `novel_creation_promax/docs/PIPELINE.md` 的创意→设定→大纲阶段。
3. 运行立项初始化：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py init --platform "{平台}" --title "{书名}" --genre "{题材}" --premise "{核心设定}"`
4. 读取平台规则和题材知识库，补齐创意、设定、大纲、8卷细纲、素材/小说信息.md、80_Projects 配置。
5. 最终复核运行：
   `python novel_creation_promax/scripts/project_bootstrap_pipeline.py seal --novel-dir "{小说目录}"`
6. `seal` 失败时禁止写正文；只有 `can_write_chapter=true` 后才能进入 `/novel-write`。

**示例**：`/novel-plan 番茄 都市异能，主角能看到物品未来价格`
