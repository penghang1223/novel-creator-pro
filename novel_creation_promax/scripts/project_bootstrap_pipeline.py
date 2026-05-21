#!/usr/bin/env python3
"""
新小说立项硬门禁。

init  创建标准目录和占位文件，但不放行正文。
check 逐项核验立项清单，写入 gate report 和 novel_state.json。
seal  等同最终复核；只有全部通过时才设置 can_write_chapter=true。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline_utils import load_json, now_iso, save_json


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_SCRIPT = PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "scripts" / "memory_manager.py"

REQUIRED_MEMORY_FILES = [
    "MEMORY.md",
    ".claude/memory/decisions/preferences.md",
    ".claude/memory/active_novels/progress.md",
    ".claude/memory/feedback/corrections.md",
    ".claude/memory/feedback/no-mer-names.md",
]

REQUIRED_KNOWLEDGE_FILES = [
    "knowledge_base/50_Quality/红线检查/红线系统.md",
    "knowledge_base/50_Quality/红线检查/章节前检查.md",
    "knowledge_base/40_Writing/05_降AI痕迹/降低AI痕迹.md",
    "knowledge_base/40_Writing/04_场景与描写/爽点设计.md",
]

PROJECT_DIRS = ["创意", "设定", "结构", "细纲", "正文", "摘要", "记忆", "素材"]
CONTENT_DIRS = ["创意", "设定", "结构"]
OUTLINE_FILES = [f"卷{name}.md" for name in "一二三四五六七八"]
MEMORY_BUCKETS = ["style_dna.json", "characters.json", "plot_logic.json", "context_relations.json", "creation_history.json"]

INFO_SECTIONS = [
    "基本信息",
    "三档简介",
    "标签",
    "主角信息",
    "封面AI绘画提示词",
    "发布平台适配信息",
    "作品详纲",
    "人物小传",
    "核心设定速查",
    "核心卖点",
    "角色命名禁忌",
]

SETTING_FOUNDATION_FILES = {
    "人物档案.md": {
        "min_chars": 1200,
        "sections": [
            "核心人物总表",
            "人物现实锚点",
            "职业与收入逻辑",
            "能力边界",
            "动机与恐惧",
            "行为指纹",
            "声纹档案",
            "OOC禁止清单",
        ],
    },
    "地点档案.md": {
        "min_chars": 800,
        "sections": [
            "核心地点总表",
            "居住逻辑",
            "工作地点",
            "通勤与距离",
            "消费水平",
            "场景使用规则",
        ],
    },
    "势力档案.md": {
        "min_chars": 800,
        "sections": [
            "势力总表",
            "组织结构",
            "资源与限制",
            "利益关系",
            "行动边界",
        ],
    },
    "事件档案.md": {
        "min_chars": 800,
        "sections": [
            "关键事件总表",
            "前因后果",
            "证据链",
            "影响范围",
            "后续债务",
        ],
    },
    "关系网络.md": {
        "min_chars": 800,
        "sections": [
            "人物关系矩阵",
            "信任等级",
            "利益冲突",
            "信息差",
            "关系变化规则",
        ],
    },
    "常识约束.md": {
        "min_chars": 1000,
        "sections": [
            "经济常识",
            "职业常识",
            "居住常识",
            "法律与流程常识",
            "技术能力常识",
            "禁止漂移清单",
        ],
    },
}

PLACEHOLDERS = [
    "TODO",
    "TBD",
    "待填写",
    "待补充",
    "未填写",
    "未确定",
    "占位",
    "这里填写",
    "示例：",
]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def write_if_missing(path: Path, text: str, force: bool = False) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def has_placeholder(text: str) -> bool:
    return any(token in text for token in PLACEHOLDERS)


def non_placeholder_text(path: Path, min_chars: int = 80) -> tuple[bool, str]:
    if not path.exists():
        return False, "文件不存在"
    text = read_text(path).strip()
    if len(text) < min_chars:
        return False, f"内容过短({len(text)}<{min_chars})"
    if has_placeholder(text):
        return False, "仍含占位词"
    return True, "已填写"


def add_result(results: list[dict[str, Any]], step: int, name: str, passed: bool, detail: str, path: Path | None = None) -> None:
    item: dict[str, Any] = {
        "step": step,
        "name": name,
        "status": "pass" if passed else "fail",
        "detail": detail,
    }
    if path is not None:
        item["path"] = rel(path)
    results.append(item)


def infer_title(novel_dir: Path, explicit_title: str = "") -> str:
    if explicit_title:
        return explicit_title
    state = load_json(novel_dir / "novel_state.json", {})
    for key in ("title", "book_title", "name"):
        value = state.get(key) if isinstance(state, dict) else ""
        if isinstance(value, str) and value.strip():
            return value.strip()
    bootstrap = load_json(novel_dir / "记忆" / "project_bootstrap.json", {})
    value = bootstrap.get("project", {}).get("title") if isinstance(bootstrap, dict) else ""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return novel_dir.name


def infer_platform(novel_dir: Path, explicit_platform: str = "") -> str:
    if explicit_platform:
        return explicit_platform
    state = load_json(novel_dir / "novel_state.json", {})
    value = state.get("platform") if isinstance(state, dict) else ""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return novel_dir.parent.name


def project_dir(platform: str, title: str, novel_dir: str = "") -> Path:
    if novel_dir:
        return resolve_path(novel_dir)
    return PROJECT_ROOT / "novel_output" / platform / title


def init_memory_system(memory_dir: Path) -> bool:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(MEMORY_SCRIPT), "init", "--memory-dir", str(memory_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode == 0


def memory_has_bootstrap(memory_dir: Path) -> bool:
    for bucket_name in MEMORY_BUCKETS:
        bucket = load_json(memory_dir / bucket_name, {})
        if not isinstance(bucket, dict):
            continue
        for item in bucket.get("memories", []):
            if item.get("metadata", {}).get("source") == "bootstrap-project":
                return True
    return False


def import_bootstrap_if_needed(novel_dir: Path, report: dict[str, Any]) -> bool:
    memory_dir = novel_dir / "记忆"
    bootstrap = memory_dir / "project_bootstrap.json"
    if memory_has_bootstrap(memory_dir):
        report["memory_bootstrap_import"] = "already_imported"
        return True
    if not bootstrap.exists():
        report["memory_bootstrap_import"] = "missing_project_bootstrap"
        return False

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [
            sys.executable,
            str(MEMORY_SCRIPT),
            "bootstrap-project",
            "--input",
            str(bootstrap),
            "--memory-dir",
            str(memory_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    report["memory_bootstrap_import"] = {
        "status": "pass" if result.returncode == 0 else "fail",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    return result.returncode == 0


def scaffold_project(args: argparse.Namespace) -> Path:
    novel_dir = project_dir(args.platform, args.title, args.novel_dir)
    for name in PROJECT_DIRS:
        (novel_dir / name).mkdir(parents=True, exist_ok=True)

    init_memory_system(novel_dir / "记忆")

    title = args.title or novel_dir.name
    platform = args.platform or novel_dir.parent.name
    genre = args.genre or "待填写"
    premise = args.premise or "待填写：用一句话写清主角、金手指、冲突和长期目标。"

    write_if_missing(
        novel_dir / "创意" / "创意方案.md",
        f"# {title} 创意方案\n\n- 平台：{platform}\n- 题材：{genre}\n- 核心设定：{premise}\n- 核心爽点：待填写\n- 对标作品：待填写\n",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "世界观与人物.md",
        f"# {title} 设定\n\n## 世界观\n\n待填写\n\n## 人物体系\n\n待填写\n\n## 地点体系\n\n待填写\n\n## 势力体系\n\n待填写\n\n## 事件体系\n\n待填写\n\n## 金手指规则\n\n待填写\n",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "人物档案.md",
        f"""# {title} 人物档案

## 核心人物总表

待填写：至少列出主角、核心搭档/女主、主要反派/压力源。每人包含姓名、年龄、职业、收入区间、学历/技能、家庭背景、当前处境。

## 人物现实锚点

待填写：每个人的居住地、收入来源、负债/资产、社会关系、日常作息。必须解释“为什么他现在住这里、做这份工作、处在这个阶层”。

## 职业与收入逻辑

待填写：每个职业的合理薪资、行业位置、被裁/升职/转岗的可信原因。技术强的人被裁员必须有组织政治、业务线收缩、合同风险或个人选择等原因。

## 能力边界

待填写：专业技能/金手指/资源能做什么、不能做什么、使用成本、冷却或代价、常识限制。

## 动机与恐惧

待填写：每个核心人物的外在目标、真实欲望、核心恐惧、短期底线、长期底线。

## 行为指纹

待填写：每个人独有的动作习惯、压力反应、决策方式。禁止只写“冷静、善良、聪明”这类标签。

## 声纹档案

待填写：每个人说话的句长、口头禅、专业词、禁用词、压力下的说话变化。

## OOC禁止清单

待填写：列出每个人绝不能无理由做出的行为、不能说的话、不能突然知道的信息。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "地点档案.md",
        f"""# {title} 地点档案

## 核心地点总表

待填写：列出主角住所、工作地点、关键冲突地点、反派据点、常用公共空间。

## 居住逻辑

待填写：房租/房价、面积、通勤、居住原因。高收入住老破小必须说明债务、家庭、通勤、隐藏身份或特殊目的。

## 工作地点

待填写：公司/店铺/机构的位置、规模、岗位、上下级、办公条件、行业惯例。

## 通勤与距离

待填写：地点之间的距离、交通方式、时间成本，防止一会儿城东一会儿城西还像隔壁。

## 消费水平

待填写：吃饭、房租、交通、医疗、社交消费的价格锚点。

## 场景使用规则

待填写：哪些地点适合谈判、打脸、调查、躲藏、公开冲突；哪些地点不能随便进入。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "势力档案.md",
        f"""# {title} 势力档案

## 势力总表

待填写：列出公司、家族、平台、监管方、地下组织、行业圈层等势力。

## 组织结构

待填写：每个势力的负责人、核心成员、层级、汇报关系、派系。

## 资源与限制

待填写：每个势力有什么钱、人、渠道、信息、法律边界；不能做到什么。

## 利益关系

待填写：势力之间谁合作、谁竞争、谁互相利用、谁有历史矛盾。

## 行动边界

待填写：势力采取行动需要什么理由、流程、代价，禁止反派无成本万能。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "事件档案.md",
        f"""# {title} 事件档案

## 关键事件总表

待填写：列出开篇事件、旧案、主线转折、卷末事件。

## 前因后果

待填写：每个事件为什么发生、谁推动、谁受益、谁受损。

## 证据链

待填写：事件留下哪些文件、证人、物品、数据、谎言和漏洞。

## 影响范围

待填写：事件影响哪些人物、地点、势力、资金、名誉和后续选择。

## 后续债务

待填写：事件埋下哪些未解决问题，计划在哪些章节回收。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "关系网络.md",
        f"""# {title} 关系网络

## 人物关系矩阵

待填写：用表格列出人物A、人物B、关系类型、关系证据、当前状态。

## 信任等级

待填写：0-5级标记人物之间的信任程度，并写清变化条件。

## 利益冲突

待填写：谁和谁目标一致，谁和谁利益冲突，冲突点是什么。

## 信息差

待填写：每个人知道什么、不知道什么、误以为什么。禁止角色突然知道不该知道的信息。

## 关系变化规则

待填写：什么事件会让关系升温、破裂、反转或结盟。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "设定" / "常识约束.md",
        f"""# {title} 常识约束

## 经济常识

待填写：收入、房租、负债、消费、资产价格、赔偿金额、投资金额的合理区间。

## 职业常识

待填写：行业岗位、能力要求、被裁/晋升/降薪/转岗的合理流程和原因。

## 居住常识

待填写：人物住处与收入、家庭、通勤、债务、隐私需求之间的对应关系。

## 法律与流程常识

待填写：报警、仲裁、法拍、劳动纠纷、合同、证据提交等流程限制。

## 技术能力常识

待填写：人物技术能力能解决哪些问题，不能跳过哪些流程，需要哪些工具和权限。

## 禁止漂移清单

待填写：列出本书最容易漂移的常识，例如高薪却无解释住城中村、技术强却无原因被裁、反派无成本调动资源、角色突然说不符合阶层/职业的话。
""",
        args.force,
    )
    write_if_missing(
        novel_dir / "结构" / "主线结构.md",
        f"# {title} 主线结构\n\n## 主线目标\n\n待填写\n\n## 阶段推进\n\n待填写\n\n## 伏笔总表\n\n待填写\n",
        args.force,
    )
    write_if_missing(
        novel_dir / "outline.md",
        f"# {title} 总纲\n\n## 核心设定\n\n待填写\n\n## 人物体系\n\n待填写\n\n## 八卷结构\n\n" + "\n".join(f"### 卷{name}\n\n待填写" for name in "一二三四五六七八") + "\n\n## 伏笔清单\n\n待填写\n",
        args.force,
    )
    for name in "一二三四五六七八":
        write_if_missing(
            novel_dir / "细纲" / f"卷{name}.md",
            f"# 卷{name}细纲\n\n## 核心任务\n\n待填写\n\n## 关键事件\n\n待填写\n\n## 爽点\n\n待填写\n\n## 伏笔\n\n待填写\n",
            args.force,
        )

    write_if_missing(
        novel_dir / "素材" / "小说信息.md",
        f"""# {title} 小说信息

## 基本信息

| 项目 | 内容 |
| --- | --- |
| 书名 | {title} |
| 作者 | 待填写 |
| 平台 | {platform} |
| 分类 | {genre} |
| 字数 | 待填写 |
| 状态 | 立项中 |

## 三档简介

待填写

## 标签

待填写

## 主角信息表

待填写

## 封面AI绘画提示词

待填写

## 发布平台适配信息

待填写

## 作品详纲

待填写

## 人物小传

待填写

## 核心设定速查

待填写

## 核心卖点

待填写

## 角色命名禁忌

所有角色名禁止包含“默”字。
""",
        args.force,
    )

    bootstrap = {
        "project": {
            "title": title,
            "premise": premise,
            "genre": genre,
            "style": "待填写",
            "platform": platform,
        },
        "style_dna": {
            "sentence_features": {"baseline": "待填写"},
            "description_style": {"baseline": "待填写"},
            "dialogue_style": {"baseline": "待填写"},
            "word_usage": {"high_freq_words": []},
        },
        "characters": [
            {
                "entity_id": "char_001",
                "basic_info": {
                    "name": "待填写",
                    "age": 0,
                    "gender": "待填写",
                    "occupation": "待填写",
                    "income_range": "待填写",
                    "residence": "待填写",
                    "education_or_skill": "待填写",
                },
                "reality_anchor": {
                    "economic_status": "待填写",
                    "housing_reason": "待填写",
                    "job_logic": "待填写",
                    "resources": [],
                    "constraints": [],
                },
                "personality": {
                    "core_traits": ["待填写"],
                    "contradictions": [{"trait1": "待填写", "trait2": "待填写", "context": "待填写"}],
                    "growth_direction": "待填写",
                },
                "motivation": {
                    "external_goal": "待填写",
                    "inner_desire": "待填写",
                    "core_fear": "待填写",
                    "bottom_line": "待填写",
                },
                "speech_style": {
                    "catchphrases": [],
                    "word_preference": {"formal_level": "待填写", "vocabulary_style": "待填写"},
                    "sentence_patterns": ["待填写"],
                    "forbidden_lines": ["待填写"],
                },
                "behavior_pattern": {
                    "decision_style": {"style": "待填写", "based_on": "待填写", "example": "待填写"},
                    "stress_response": {"typical_response": "待填写", "physical_signs": [], "coping_mechanism": "待填写"},
                },
                "background": {"family": "待填写", "past_events": ["待填写"]},
                "current_state": {},
            }
        ],
        "plots": [
            {
                "plot_type": "main",
                "plot_name": "待填写",
                "description": "待填写",
                "start_chapter": 1,
                "status": "进行中",
                "key_events": [],
            }
        ],
        "contexts": [{"chapter": 0, "title": "项目初始化", "summary": "待填写"}],
        "history": [{"chapter": 0, "title": "项目初始化", "content_summary": "待填写", "key_events": ["项目立项"]}],
        "entity_graph": {"entities": {}, "edges": [], "next_entity_id": 1},
    }
    bootstrap_path = novel_dir / "记忆" / "project_bootstrap.json"
    if args.force or not bootstrap_path.exists():
        save_json(bootstrap_path, bootstrap)

    style_path = novel_dir / "记忆" / "style_dna_baseline.json"
    if args.force or not style_path.exists():
        save_json(
            style_path,
            {
                "source": "manual-baseline",
                "status": "draft",
                "sentence_features": {"baseline": "待填写"},
                "description_style": {"baseline": "待填写"},
                "dialogue_style": {"baseline": "待填写"},
                "word_usage": {"high_freq_words": []},
            },
        )

    state_path = novel_dir / "novel_state.json"
    state = load_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("title", title)
    state.setdefault("platform", platform)
    state.setdefault("genre", genre)
    state.setdefault("current_chapter", 0)
    state.setdefault("word_count", 0)
    state.setdefault("chapters", {})
    gate = state.setdefault("workflow_gate", {})
    gate.update(
        {
            "bootstrap_status": "initialized",
            "can_write_chapter": False,
            "last_checklist_step": 5,
            "bootstrap_report": "素材/project_bootstrap_gate.json",
            "updated_at": now_iso(),
        }
    )
    save_json(state_path, state)

    kb_config = PROJECT_ROOT / "knowledge_base" / "80_Projects" / title / "_config.md"
    write_if_missing(
        kb_config,
        f"# {title}\n\n- 平台：{platform}\n- 题材：{genre}\n- 状态：立项中\n- 项目目录：{rel(novel_dir)}\n- 当前进度：待填写\n",
        args.force,
    )

    print(f"[OK] 项目结构已初始化: {novel_dir}")
    print("[NEXT] 请补全占位内容，然后运行 project_bootstrap_pipeline.py seal")
    return novel_dir


def check_required_files(results: list[dict[str, Any]]) -> None:
    for item in REQUIRED_MEMORY_FILES:
        path = PROJECT_ROOT / item
        add_result(results, 1, f"共享记忆: {item}", path.exists(), "存在" if path.exists() else "缺失", path)
    for item in REQUIRED_KNOWLEDGE_FILES:
        path = PROJECT_ROOT / item
        add_result(results, 2, f"创作前知识库: {item}", path.exists(), "存在" if path.exists() else "缺失", path)


def check_bootstrap_json(novel_dir: Path, title: str, results: list[dict[str, Any]]) -> None:
    path = novel_dir / "记忆" / "project_bootstrap.json"
    payload = load_json(path, {})
    if not path.exists() or not isinstance(payload, dict):
        add_result(results, 7, "project_bootstrap.json", False, "缺失或 JSON 无效", path)
        return

    failures: list[str] = []
    project = payload.get("project", {})
    if not isinstance(project, dict):
        failures.append("project 无效")
    else:
        if not str(project.get("title", "")).strip():
            failures.append("project.title 为空")
        if len(str(project.get("premise", "")).strip()) < 20:
            failures.append("premise 过短")
        if not str(project.get("genre", "")).strip():
            failures.append("genre 为空")
        if has_placeholder(json.dumps(project, ensure_ascii=False)):
            failures.append("project 仍含占位词")

    style = payload.get("style_dna", {})
    if not isinstance(style, dict) or not any(style.get(key) for key in ("sentence_features", "description_style", "dialogue_style", "word_usage")):
        failures.append("style_dna 未填写")
    elif has_placeholder(json.dumps(style, ensure_ascii=False)):
        failures.append("style_dna 仍含占位词")

    characters = payload.get("characters", [])
    valid_names = []
    if isinstance(characters, list):
        for item in characters:
            if isinstance(item, dict):
                name = str(item.get("basic_info", {}).get("name", "")).strip()
                if name and not has_placeholder(name):
                    valid_names.append(name)
                if "默" in name:
                    failures.append(f"角色名含禁字: {name}")
                char_text = json.dumps(item, ensure_ascii=False)
                required_character_blocks = [
                    "reality_anchor",
                    "motivation",
                    "speech_style",
                    "behavior_pattern",
                ]
                missing_blocks = [key for key in required_character_blocks if key not in item]
                if missing_blocks:
                    failures.append(f"{name or '角色'} 缺少人物深设字段: {', '.join(missing_blocks)}")
                if not has_placeholder(name) and len(char_text) < 500:
                    failures.append(f"{name} 人物档案过薄")
    if len(valid_names) < 2:
        failures.append("有效角色少于2个")

    plots = payload.get("plots", [])
    valid_plots = [
        item
        for item in plots
        if isinstance(item, dict)
        and str(item.get("plot_name", "")).strip()
        and str(item.get("description", "")).strip()
        and not has_placeholder(str(item.get("plot_name", "")) + str(item.get("description", "")))
    ]
    if not valid_plots:
        failures.append("主线剧情未填写")

    detail = "已填写" if not failures else "；".join(failures)
    add_result(results, 7, "project_bootstrap.json 完整性", not failures, detail, path)


def check_setting_foundation(novel_dir: Path, results: list[dict[str, Any]]) -> None:
    setting_dir = novel_dir / "设定"
    for file_name, rule in SETTING_FOUNDATION_FILES.items():
        path = setting_dir / file_name
        ok, detail = non_placeholder_text(path, int(rule["min_chars"]))
        if ok:
            text = read_text(path)
            missing = [section for section in rule["sections"] if section not in text]
            if missing:
                ok = False
                detail = "缺少栏目: " + ", ".join(missing)
        add_result(results, 8, f"设定底座: {file_name}", ok, detail, path)


def check_project_artifacts(novel_dir: Path, title: str, results: list[dict[str, Any]]) -> None:
    for name in PROJECT_DIRS:
        path = novel_dir / name
        add_result(results, 5, f"项目目录: {name}", path.exists() and path.is_dir(), "存在" if path.exists() else "缺失", path)

    for name in CONTENT_DIRS:
        path = novel_dir / name
        files = [p for p in path.glob("*.md")] if path.exists() else []
        valid = [p for p in files if non_placeholder_text(p, 80)[0]]
        add_result(results, 5, f"{name}/ 非空内容", bool(valid), f"有效文件 {len(valid)} 个", path)

    outline = novel_dir / "outline.md"
    outline_ok, outline_detail = non_placeholder_text(outline, 600)
    if outline_ok:
        text = read_text(outline)
        volume_count = sum(1 for marker in ["卷一", "卷二", "卷三", "卷四", "卷五", "卷六", "卷七", "卷八"] if marker in text)
        if volume_count < 8:
            outline_ok = False
            outline_detail = f"八卷结构不完整({volume_count}/8)"
        for keyword in ["核心设定", "人物", "伏笔"]:
            if keyword not in text:
                outline_ok = False
                outline_detail = f"缺少 {keyword}"
                break
    add_result(results, 9, "outline.md 总纲", outline_ok, outline_detail, outline)

    for file_name in OUTLINE_FILES:
        path = novel_dir / "细纲" / file_name
        ok, detail = non_placeholder_text(path, 180)
        if ok:
            text = read_text(path)
            missing = [key for key in ["核心任务", "关键事件", "爽点", "伏笔"] if key not in text]
            if missing:
                ok = False
                detail = "缺少栏目: " + ", ".join(missing)
        add_result(results, 9, f"分卷细纲: {file_name}", ok, detail, path)

    info = novel_dir / "素材" / "小说信息.md"
    info_ok, info_detail = non_placeholder_text(info, 800)
    if info_ok:
        text = read_text(info)
        missing = [section for section in INFO_SECTIONS if section not in text]
        if missing:
            info_ok = False
            info_detail = "缺少栏目: " + ", ".join(missing)
    add_result(results, 9, "素材/小说信息.md", info_ok, info_detail, info)

    state = novel_dir / "novel_state.json"
    payload = load_json(state, {})
    state_ok = isinstance(payload, dict) and bool(payload.get("title")) and bool(payload.get("platform")) and "workflow_gate" in payload
    add_result(results, 10, "novel_state.json", state_ok, "含基础状态和 workflow_gate" if state_ok else "缺少基础状态或 workflow_gate", state)


def check_memory_artifacts(novel_dir: Path, results: list[dict[str, Any]]) -> None:
    memory_dir = novel_dir / "记忆"
    for bucket in MEMORY_BUCKETS:
        path = memory_dir / bucket
        payload = load_json(path, {})
        ok = path.exists() and isinstance(payload, dict) and payload.get("memory_type")
        add_result(results, 6, f"记忆桶: {bucket}", ok, "已初始化" if ok else "缺失或无效", path)

    style_path = memory_dir / "style_dna_baseline.json"
    ok, detail = False, "缺失"
    if style_path.exists():
        payload = load_json(style_path, {})
        text = json.dumps(payload, ensure_ascii=False)
        ok = isinstance(payload, dict) and len(text) > 80 and not has_placeholder(text)
        detail = "已填写" if ok else "仍含占位或内容不足"
    add_result(results, 8, "style_dna_baseline.json", ok, detail, style_path)

    imported = memory_has_bootstrap(memory_dir)
    add_result(results, 7, "project_bootstrap 已导入记忆系统", imported, "已导入" if imported else "未导入", memory_dir)


def check_external_sync(novel_dir: Path, title: str, results: list[dict[str, Any]]) -> None:
    kb_config = PROJECT_ROOT / "knowledge_base" / "80_Projects" / title / "_config.md"
    if not kb_config.exists() and title != novel_dir.name:
        alt = PROJECT_ROOT / "knowledge_base" / "80_Projects" / novel_dir.name / "_config.md"
        if alt.exists():
            kb_config = alt
    ok, detail = non_placeholder_text(kb_config, 80)
    add_result(results, 10, "80_Projects/_config.md", ok, detail, kb_config)

    memory = PROJECT_ROOT / "MEMORY.md"
    text = read_text(memory) if memory.exists() else ""
    names = [title, novel_dir.name]
    found = any(name and name in text for name in names)
    add_result(results, 11, "MEMORY.md 项目索引", found, "已包含项目名" if found else f"未找到 {title}", memory)


def build_report(novel_dir: Path, title: str, platform: str, mode: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [item for item in results if item["status"] != "pass"]
    return {
        "generated_at": now_iso(),
        "mode": mode,
        "project": {
            "title": title,
            "platform": platform,
            "novel_dir": rel(novel_dir),
        },
        "status": "pass" if not failed else "fail",
        "can_write_chapter": not failed,
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }


def update_gate_state(novel_dir: Path, report: dict[str, Any]) -> None:
    state_path = novel_dir / "novel_state.json"
    state = load_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("title", report["project"]["title"])
    state.setdefault("platform", report["project"]["platform"])
    gate = state.setdefault("workflow_gate", {})
    gate.update(
        {
            "bootstrap_status": report["status"],
            "bootstrap_report": "素材/project_bootstrap_gate.json",
            "can_write_chapter": bool(report["can_write_chapter"]),
            "last_checklist_step": 20 if report["can_write_chapter"] else max((item["step"] for item in report["results"] if item["status"] == "pass"), default=0),
            "updated_at": now_iso(),
        }
    )
    if report.get("memory_bootstrap_import"):
        gate["memory_bootstrap_import"] = report["memory_bootstrap_import"]
    state["updated_at"] = now_iso()
    save_json(state_path, state)


def run_check(args: argparse.Namespace, *, seal: bool = False) -> tuple[bool, dict[str, Any]]:
    novel_dir = resolve_path(args.novel_dir)
    title = infer_title(novel_dir, args.title)
    platform = infer_platform(novel_dir, args.platform)
    results: list[dict[str, Any]] = []

    check_required_files(results)
    check_project_artifacts(novel_dir, title, results)
    check_setting_foundation(novel_dir, results)
    check_bootstrap_json(novel_dir, title, results)

    prereq_failed = [item for item in results if item["status"] != "pass" and item["step"] in {5, 7, 8, 9, 10}]
    report_stub: dict[str, Any] = {}
    if not prereq_failed:
        import_bootstrap_if_needed(novel_dir, report_stub)

    check_memory_artifacts(novel_dir, results)
    check_external_sync(novel_dir, title, results)

    report = build_report(novel_dir, title, platform, "seal" if seal else "check", results)
    if report_stub:
        report["memory_bootstrap_import"] = report_stub["memory_bootstrap_import"]
        if isinstance(report_stub["memory_bootstrap_import"], dict) and report_stub["memory_bootstrap_import"].get("status") != "pass":
            report["status"] = "fail"
            report["can_write_chapter"] = False
            report["failed"] += 1
    report_path = novel_dir / "素材" / "project_bootstrap_gate.json"
    save_json(report_path, report)
    update_gate_state(novel_dir, report)
    return bool(report["can_write_chapter"]), report


def print_report(report: dict[str, Any]) -> None:
    print("=" * 64)
    print(f"新书立项门禁: {report['status'].upper()} ({report['passed']} pass / {report['failed']} fail)")
    print(f"项目: {report['project']['platform']} / {report['project']['title']}")
    print("=" * 64)
    for item in report["results"]:
        status = "[OK]" if item["status"] == "pass" else "[FAIL]"
        print(f"{status} Step {item['step']:02d} {item['name']} - {item['detail']}")
    print("=" * 64)
    if report["can_write_chapter"]:
        print("[OK] 立项门禁已通过，可以进入章节写作流水线。")
    else:
        print("[BLOCKED] 立项门禁未通过，禁止开始正文。先补齐 FAIL 项后重跑 seal。")


def main() -> int:
    parser = argparse.ArgumentParser(description="新小说立项硬门禁")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="创建标准项目结构和占位文件")
    init_parser.add_argument("--platform", default="番茄", help="平台，默认番茄")
    init_parser.add_argument("--title", required=True, help="书名")
    init_parser.add_argument("--genre", default="", help="题材")
    init_parser.add_argument("--premise", default="", help="核心设定/一句话故事")
    init_parser.add_argument("--novel-dir", default="", help="自定义小说目录")
    init_parser.add_argument("--force", action="store_true", help="覆盖已有占位文件")

    for name in ("check", "seal"):
        sub = subparsers.add_parser(name, help="检查/最终封存立项门禁")
        sub.add_argument("--novel-dir", required=True, help="小说项目目录")
        sub.add_argument("--title", default="", help="书名，默认从 novel_state 或目录推断")
        sub.add_argument("--platform", default="", help="平台，默认从 novel_state 或父目录推断")

    args = parser.parse_args()
    if args.command == "init":
        scaffold_project(args)
        return 0

    ok, report = run_check(args, seal=args.command == "seal")
    print_report(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
