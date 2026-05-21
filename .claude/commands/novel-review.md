# 小说深度审稿

Run LLM-based deep review.

**输入**：`/novel-review [小说名] [第N章|章节范围|全本]`

**执行**：
1. 先运行基础审计：`audit_pipeline.py`。
2. 再读取 `novel_creation_promax/review-skill/SKILL.md`。
3. 输出五维审稿报告。

**示例**：`/novel-review 我在末世开便利店 第12章`

