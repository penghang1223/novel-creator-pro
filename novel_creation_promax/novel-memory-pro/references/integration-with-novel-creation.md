# 与随心写小说联动

本参考用于把“小说记忆 Pro”与“随心写小说 / novel-creation-*”技能串成一条生产链。

## 目标分工

- 写作技能负责产出：设定、大纲、章纲、正文、改稿
- 记忆技能负责维护：风格、人物、剧情、上下文、创作历史

## 推荐链路

### 1. 立项后立刻建记忆

从写作技能产出的这些内容整理出 `project_bootstrap.json`：

- 项目标题
- 一句话 premise
- 主角与主要配角
- 主线 / 支线
- 当前大纲
- 风格样本路径（可选）

然后执行：

```bash
python scripts/memory_manager.py init --memory-dir ./memory_system
python scripts/memory_manager.py bootstrap-project --input project_bootstrap.json --memory-dir ./memory_system
```

如果有 3-5 章样本，再执行：

```bash
python scripts/style_dna_extractor.py --input ./style_samples --output ./memory_system/style_dna_seed.json --author 作者名
```

## 2. 每章开写前

先生成当前章节记忆包：

```bash
python scripts/memory_manager.py chapter-pack --chapter 12 --output active_memory_pack.json --memory-dir ./memory_system
```

再把这个包交给写作技能，让它据此写下一章。

## 3. 每章写完后

先不要把整章生硬塞进记忆系统。
先生成一份结构化章节摘要，再同步：

```bash
python scripts/memory_manager.py sync-chapter --input chapter_012_summary.json --memory-dir ./memory_system
```

## 4. 每 5-10 章

执行：

```bash
python scripts/memory_manager.py stats --memory-dir ./memory_system
python scripts/memory_manager.py review-pack --chapter 30 --output review_pack.json --memory-dir ./memory_system
```

然后由智能体根据统计和 pack 输出：

- 漂移风险
- 伏笔堆积
- 剧情拥堵点
- 人物状态冲突

## 联动时的核心要求

- 写作技能不直接维护所有记忆细节，只消费“active_memory_pack”
- 记忆技能不替代写作技能写正文，只负责提供约束和回填
- 当两边冲突时，以用户确认过的大纲 / 正文为准，再修记忆
