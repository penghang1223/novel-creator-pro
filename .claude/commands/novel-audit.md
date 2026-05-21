# 小说审计

Run hard audit pipeline for one chapter or all chapters.

**输入**：`/novel-audit [小说名] [第N章|all]`

**执行**：
`python novel_creation_promax/scripts/audit_pipeline.py --novel-dir "{小说目录}" --chapter N`

全量扫描：
`python novel_creation_promax/scripts/audit_pipeline.py --novel-dir "{小说目录}" --all`

**示例**：`/novel-audit 我在末世开便利店 第12章`

