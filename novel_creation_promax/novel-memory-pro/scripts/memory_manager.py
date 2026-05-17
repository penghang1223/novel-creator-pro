#!/usr/bin/env python3
"""
记忆系统管理器

提供五层记忆的初始化、CRUD、项目导入、章节记忆包生成、
章节摘要回填、导出和统计能力。
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Entity graph integration (optional import)
try:
    from entity_graph_manager import EntityGraphManager
except ImportError:
    EntityGraphManager = None  # type: ignore[assignment,misc]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_json(path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not os.path.exists(path):
        return default or {}
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def nested_get(obj: Dict[str, Any], path: str) -> Any:
    current: Any = obj
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


@dataclass
class Memory:
    memory_id: str
    memory_type: str
    created_at: str
    updated_at: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", "active"))

    @status.setter
    def status(self, value: str) -> None:
        self.metadata["status"] = value


def _recency_score(chapters_since_ref: int) -> int:
    if chapters_since_ref <= 2:
        return 40
    if chapters_since_ref <= 5:
        return 30
    if chapters_since_ref <= 10:
        return 20
    if chapters_since_ref <= 15:
        return 10
    return 0


def _importance_score(memory: Memory) -> int:
    mt = memory.memory_type
    if mt == "character":
        role = nested_get(memory.data, "basic_info.name")
        return 30 if role else 15  # 主角档案默认 30
    if mt == "plot":
        return 25 if memory.data.get("plot_type") == "main" else 15
    if mt == "style_dna":
        return 25
    if mt == "context":
        return 10
    if mt == "history":
        return 10
    return 10


def _connection_score(memory: Memory, active_names: set, chapter: int) -> int:
    score = 0
    name = nested_get(memory.data, "basic_info.name") or memory.data.get("name", "")
    if name and name in active_names:
        score += 15
    last_ref = safe_int(memory.metadata.get("last_relevant_chapter"), 0)
    if last_ref and last_ref >= chapter - 3:
        score += 10
    return min(score, 30)


def relevance_score(memory: Memory, chapter: int, active_names: set) -> int:
    last_ref = safe_int(memory.metadata.get("last_relevant_chapter"), 0) or safe_int(
        memory.data.get("chapter"), 0
    )
    chapters_since = max(chapter - last_ref, 0) if last_ref else 99
    return (
        _recency_score(chapters_since)
        + _importance_score(memory)
        + _connection_score(memory, active_names, chapter)
    )


class MemoryManager:
    def __init__(self, memory_dir: str = "./memory_system"):
        self.memory_dir = memory_dir
        self.memory_files = {
            "style_dna": "style_dna.json",
            "character": "characters.json",
            "plot": "plot_logic.json",
            "context": "context_relations.json",
            "history": "creation_history.json",
        }
        self.memories: Dict[str, Memory] = {}

    def _file_path(self, memory_type: str) -> str:
        return os.path.join(self.memory_dir, self.memory_files[memory_type])

    def _empty_bucket(self, memory_type: str) -> Dict[str, Any]:
        timestamp = now_iso()
        return {
            "memory_type": memory_type,
            "memories": [],
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    def init_system(self) -> bool:
        try:
            ensure_dir(self.memory_dir)
            for memory_type in self.memory_files:
                path = self._file_path(memory_type)
                if not os.path.exists(path):
                    save_json(path, self._empty_bucket(memory_type))
            print(f"记忆系统已初始化: {self.memory_dir}")
            return True
        except Exception as exc:
            print(f"初始化失败: {exc}")
            return False

    def load_memories(self) -> bool:
        self.memories = {}
        try:
            for memory_type in self.memory_files:
                bucket = load_json(self._file_path(memory_type), self._empty_bucket(memory_type))
                for item in bucket.get("memories", []):
                    memory = Memory(
                        memory_id=item["memory_id"],
                        memory_type=memory_type,
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        data=item.get("data", {}),
                        metadata=item.get("metadata", {}),
                    )
                    self.memories[memory.memory_id] = memory
            return True
        except Exception as exc:
            print(f"加载记忆失败: {exc}")
            return False

    def _write_bucket(self, memory_type: str) -> None:
        path = self._file_path(memory_type)
        bucket = self._empty_bucket(memory_type)
        bucket["memories"] = [
            m.to_dict()
            for m in sorted(
                self.memories.values(),
                key=lambda value: value.created_at,
            )
            if m.memory_type == memory_type
        ]
        bucket["updated_at"] = now_iso()
        save_json(path, bucket)

    def _save_memory(self, memory: Memory) -> None:
        self.memories[memory.memory_id] = memory
        self._write_bucket(memory.memory_type)

    def _next_id(self, memory_type: str) -> str:
        return f"{memory_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def _chapter_of(self, memory: Memory) -> int:
        return safe_int(memory.data.get("chapter") or memory.metadata.get("last_updated_chapter"), 0)

    def create_memory(
        self,
        memory_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        timestamp = now_iso()
        memory = Memory(
            memory_id=self._next_id(memory_type),
            memory_type=memory_type,
            created_at=timestamp,
            updated_at=timestamp,
            data=data,
            metadata=metadata or {},
        )
        self._save_memory(memory)
        return memory

    def update_memory(
        self,
        memory_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        if memory_id not in self.memories:
            raise KeyError(f"未找到记忆: {memory_id}")
        memory = self.memories[memory_id]
        memory.data.update(data)
        if metadata:
            memory.metadata.update(metadata)
        memory.updated_at = now_iso()
        self._save_memory(memory)
        return memory

    def delete_memory(self, memory_id: str) -> bool:
        if memory_id not in self.memories:
            return False
        memory_type = self.memories[memory_id].memory_type
        del self.memories[memory_id]
        self._write_bucket(memory_type)
        return True

    def query_memory(
        self,
        memory_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        results: List[Memory] = []
        for memory in self.memories.values():
            if memory_type and memory.memory_type != memory_type:
                continue
            if filters and not self._match_filters(memory, filters):
                continue
            results.append(memory)
        return sorted(results, key=lambda item: item.created_at)

    def _match_filters(self, memory: Memory, filters: Dict[str, Any]) -> bool:
        for raw_key, expected in filters.items():
            if raw_key.startswith("metadata."):
                value = nested_get(memory.metadata, raw_key[len("metadata.") :])
            elif raw_key.startswith("data."):
                value = nested_get(memory.data, raw_key[len("data.") :])
            else:
                value = nested_get(memory.data, raw_key)
                if value is None:
                    value = nested_get(memory.metadata, raw_key)
            if isinstance(value, list):
                if expected not in value:
                    return False
            elif str(value) != str(expected):
                return False
        return True

    def export_memories(self, output_path: str) -> Dict[str, Any]:
        payload = {
            "export_time": now_iso(),
            "memory_types": {},
        }
        for memory_type in self.memory_files:
            items = self.query_memory(memory_type=memory_type)
            payload["memory_types"][memory_type] = {
                "count": len(items),
                "memories": [item.to_dict() for item in items],
            }
        save_json(output_path, payload)
        return payload

    def get_memory_stats(self) -> Dict[str, Any]:
        stats = {"total_memories": len(self.memories), "by_type": {}}
        for memory_type in self.memory_files:
            items = self.query_memory(memory_type=memory_type)
            stats["by_type"][memory_type] = {
                "count": len(items),
                "latest_update": max((item.updated_at for item in items), default=None),
            }
        return stats

    def bootstrap_project(self, input_path: str) -> Dict[str, int]:
        payload = load_json(input_path, {})
        counts = {"style_dna": 0, "character": 0, "plot": 0, "context": 0, "history": 0}

        style_dna = payload.get("style_dna")
        if style_dna:
            self.create_memory(
                "style_dna",
                style_dna,
                {"source": "bootstrap-project", "project_title": nested_get(payload, "project.title")},
            )
            counts["style_dna"] += 1

        for memory_type, source_key in [
            ("character", "characters"),
            ("plot", "plots"),
            ("context", "contexts"),
            ("history", "history"),
        ]:
            for item in payload.get(source_key, []):
                self.create_memory(
                    memory_type,
                    item,
                    {"source": "bootstrap-project", "project_title": nested_get(payload, "project.title")},
                )
                counts[memory_type] += 1

        project_meta = payload.get("project")
        if project_meta:
            self.create_memory(
                "history",
                {
                    "chapter": 0,
                    "version": 1,
                    "title": "项目初始化",
                    "content_summary": project_meta.get("premise", ""),
                    "characters_involved": [c.get("basic_info", {}).get("name") for c in payload.get("characters", []) if c.get("basic_info", {}).get("name")],
                    "key_events": ["项目立项"],
                    "creative_decisions": [{"decision": "初始化记忆系统", "reason": "建立长期创作记忆"}],
                    "modifications": [],
                    "calibration_records": [],
                },
                {"source": "bootstrap-project", "project_title": project_meta.get("title", "")},
            )
            counts["history"] += 1

        # Entity graph initialization
        graph_data = payload.get("entity_graph")
        if graph_data:
            graph_path = os.path.join(self.memory_dir, "entity_graph.json")
            save_json(graph_path, graph_data)

        return counts

    def _active_character_names(
        self,
        chapter: int,
        recent_contexts: List[Memory],
        recent_history: List[Memory],
    ) -> List[str]:
        names: List[str] = []
        for context in recent_contexts:
            for state in context.data.get("character_states", []):
                name = state.get("name")
                if name:
                    names.append(name)
        for history in recent_history:
            names.extend([name for name in history.data.get("characters_involved", []) if name])
        for plot in self.query_memory(memory_type="plot"):
            plot_chapter = safe_int(plot.data.get("current_chapter"), 0)
            if plot_chapter >= max(0, chapter - 5):
                for event in plot.data.get("key_events", [])[-3:]:
                    for name in event.get("characters_involved", []) or []:
                        if name:
                            names.append(name)
        return list(dict.fromkeys(names))

    def _memory_temperature(self, chapter: int, memory: Memory) -> str:
        memory_chapter = self._chapter_of(memory)
        gap = max(0, chapter - memory_chapter)
        if gap <= 3:
            return "active"
        if gap <= 10:
            return "warm"
        return "archive"

    def _archive_candidate_contexts(self, chapter: int) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for context in self.query_memory(memory_type="context"):
            unresolved = context.data.get("unresolved_questions", [])
            planted = context.data.get("foreshadowing", {}).get("planted", [])
            has_open_foreshadowing = any(not item.get("resolved") for item in planted)
            if self._chapter_of(context) <= chapter - 8 and not unresolved and not has_open_foreshadowing:
                candidates.append(
                    {
                        "memory_id": context.memory_id,
                        "chapter": context.data.get("chapter"),
                        "title": context.data.get("title", ""),
                        "reason": "章节较旧，且未留下待处理问题或未回收伏笔",
                    }
                )
        return candidates

    def _archive_candidate_history(self, chapter: int) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for history in self.query_memory(memory_type="history"):
            if self._chapter_of(history) <= chapter - 8:
                candidates.append(
                    {
                        "memory_id": history.memory_id,
                        "chapter": history.data.get("chapter"),
                        "title": history.data.get("title", ""),
                        "reason": "可压缩为阶段摘要，避免历史记录过长抢占上下文",
                    }
                )
        return candidates

    def _stale_plot_risks(self, chapter: int) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []
        for plot in self.query_memory(memory_type="plot"):
            status = plot.data.get("status", "")
            current_chapter = safe_int(plot.data.get("current_chapter"), 0)
            if status != "已完成" and current_chapter <= chapter - 6:
                risks.append(
                    {
                        "memory_id": plot.memory_id,
                        "plot_name": plot.data.get("plot_name", ""),
                        "status": status,
                        "last_progress_chapter": current_chapter,
                        "risk": "剧情线超过 6 章未推进，可能已漂移或被遗忘",
                    }
                )
        return risks

    def _stale_character_risks(self, chapter: int) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []
        for character in self.query_memory(memory_type="character"):
            last_updated = safe_int(character.metadata.get("last_updated_chapter"), 0)
            if last_updated and last_updated <= chapter - 8:
                risks.append(
                    {
                        "memory_id": character.memory_id,
                        "name": nested_get(character.data, "basic_info.name") or "",
                        "last_updated_chapter": last_updated,
                        "risk": "人物状态长期未刷新，建议确认是否仍是活跃角色",
                    }
                )
        return risks

    def _resolve_foreshadowing_and_questions(self, resolved_items: List[str], chapter: int) -> int:
        if not resolved_items:
            return 0
        resolved = 0
        normalized = {item.strip() for item in resolved_items if item and item.strip()}
        if not normalized:
            return 0
        for context in self.query_memory(memory_type="context"):
            changed = False
            planted = context.data.get("foreshadowing", {}).get("planted", [])
            for item in planted:
                description = str(item.get("description", "")).strip()
                if description in normalized and not item.get("resolved"):
                    item["resolved"] = True
                    item["resolved_chapter"] = chapter
                    changed = True
                    resolved += 1
            unresolved_questions = context.data.get("unresolved_questions", [])
            filtered_questions = [item for item in unresolved_questions if str(item).strip() not in normalized]
            if filtered_questions != unresolved_questions:
                resolved += len(unresolved_questions) - len(filtered_questions)
                context.data["unresolved_questions"] = filtered_questions
                if "foreshadowing" in context.data and isinstance(context.data["foreshadowing"], dict):
                    foreshadowing_unresolved = context.data["foreshadowing"].get("unresolved", [])
                    context.data["foreshadowing"]["unresolved"] = [
                        item for item in foreshadowing_unresolved if str(item).strip() not in normalized
                    ]
                changed = True
            if changed:
                self.update_memory(context.memory_id, context.data)
        return resolved

    def build_review_pack(self, chapter: int) -> Dict[str, Any]:
        recent_contexts = [m for m in self.query_memory(memory_type="context") if self._chapter_of(m) <= chapter][-5:]
        recent_history = [m for m in self.query_memory(memory_type="history") if self._chapter_of(m) <= chapter][-5:]
        active_names = self._active_character_names(chapter, recent_contexts, recent_history)
        active_plots = [
            {
                "plot_name": item.data.get("plot_name", ""),
                "status": item.data.get("status", ""),
                "current_chapter": item.data.get("current_chapter"),
            }
            for item in self.query_memory(memory_type="plot")
            if self._memory_temperature(chapter, item) == "active" or item.data.get("status") != "已完成"
        ]
        unresolved_questions = []
        for context in recent_contexts:
            unresolved_questions.extend(context.data.get("unresolved_questions", []))
        stale_plot_risks = self._stale_plot_risks(chapter)
        stale_character_risks = self._stale_character_risks(chapter)
        archive_contexts = self._archive_candidate_contexts(chapter)
        archive_history = self._archive_candidate_history(chapter)

        # Auto-archiving: update memory statuses based on lifecycle rules
        auto_archived = 0
        for memory in self.memories.values():
            last_ref = safe_int(memory.metadata.get("last_relevant_chapter"), 0) or self._chapter_of(memory)
            gap = chapter - last_ref
            old_status = memory.status
            if old_status == "active" and gap > 5:
                memory.status = "warm"
            elif old_status == "warm" and gap > 15:
                memory.status = "archived"
            if memory.status != old_status:
                auto_archived += 1
        if auto_archived:
            for mt in self.memory_files:
                self._write_bucket(mt)

        recommended_actions: List[str] = []
        if stale_plot_risks:
            recommended_actions.append("优先检查长期未推进的剧情线，决定推进、合并或完结。")
        if stale_character_risks:
            recommended_actions.append("确认长期未刷新的角色是否仍应保持活跃，否则降为 warm/archive。")
        if archive_contexts or archive_history:
            recommended_actions.append("把已完成章节压缩为阶段摘要，减少下章输入体积。")
        if not recommended_actions:
            recommended_actions.append("当前记忆结构健康，可以继续沿用现有节奏写作。")

        return {
            "generated_at": now_iso(),
            "review_chapter": chapter,
            "stats": self.get_memory_stats(),
            "active_window": {
                "chapters_considered": [item.data.get("chapter") for item in recent_contexts],
                "active_characters": active_names,
                "active_plots": active_plots,
                "unresolved_questions": list(dict.fromkeys([item for item in unresolved_questions if item])),
            },
            "drift_risks": {
                "plots": stale_plot_risks,
                "characters": stale_character_risks,
            },
            "archive_candidates": {
                "contexts": archive_contexts,
                "history": archive_history,
            },
            "recommended_actions": recommended_actions,
        }

    def _extract_search_keywords(
        self,
        chapter: int,
        active_characters: List[Dict[str, Any]],
        plot_items: List[Memory],
        recent_contexts: List[Memory],
    ) -> List[str]:
        """Extract search keywords from active context for LLM keyword retrieval."""
        keywords: List[str] = []
        # Character names
        for ch in active_characters:
            name = ch.get("name", "")
            if name:
                keywords.append(name)
        # Active plot names
        for item in plot_items:
            if item.data.get("status") != "已完成":
                pname = item.data.get("plot_name", "")
                if pname:
                    keywords.append(pname)
        # Recent chapter titles (last 3)
        for ctx in recent_contexts[-3:]:
            title = ctx.data.get("title", "")
            if title:
                keywords.append(title)
        # Unresolved questions (last 5)
        for ctx in recent_contexts:
            for q in ctx.data.get("unresolved_questions", [])[-5:]:
                if q and q not in keywords:
                    keywords.append(q)
        # Foreshadowing IDs
        for ctx in recent_contexts:
            planted = ctx.data.get("foreshadowing", {}).get("planted", [])
            for f in planted:
                fid = f.get("id", "")
                if fid and not f.get("resolved"):
                    keywords.append(fid)
        return keywords[:10]  # cap at 10 keywords

    def _temporal_distance_check(
        self,
        chapter: int,
        recent_contexts: List[Memory],
    ) -> Dict[str, Any]:
        """Flag information items by temporal distance for content deduplication."""
        skip_items = []  # 1-2 chapters ago
        modify_items = []  # 3-5 chapters ago
        brief_items = []  # 6-10 chapters ago
        for ctx in recent_contexts:
            ctx_ch = int(ctx.data.get("chapter", 0))
            dist = chapter - ctx_ch
            if dist <= 0:
                continue
            events = [e.get("event", "") for e in ctx.data.get("key_events", []) if e.get("event")]
            if dist <= 2:
                skip_items.extend(events[:3])
            elif dist <= 5:
                modify_items.extend(events[:3])
            elif dist <= 10:
                brief_items.extend(events[:3])
        return {
            "skip_1to2ch": skip_items[:5],
            "modify_3to5ch": modify_items[:5],
            "brief_6to10ch": brief_items[:5],
        }

    def generate_chapter_pack(self, chapter: int) -> Dict[str, Any]:
        style_items = self.query_memory(memory_type="style_dna")
        character_items = self.query_memory(memory_type="character")
        plot_items = self.query_memory(memory_type="plot")
        context_items = self.query_memory(memory_type="context")
        history_items = self.query_memory(memory_type="history")

        latest_style = style_items[-1].data if style_items else {}

        # First pass: get active names from simple heuristic for relevance scoring
        prelim_contexts = [m for m in context_items if int(m.data.get("chapter", 0)) < chapter][-5:]
        prelim_history = [m for m in history_items if int(m.data.get("chapter", 0)) < chapter][-5:]
        active_names = self._active_character_names(chapter, prelim_contexts, prelim_history)

        # Relevance filtering: score and filter by threshold
        recent_contexts = []
        for m in context_items:
            if int(m.data.get("chapter", 0)) >= chapter:
                continue
            if m.status == "archived" or m.status == "compressed":
                continue
            score = relevance_score(m, chapter, active_names)
            if score >= 30:  # at least summary injection
                recent_contexts.append(m)
        recent_contexts = recent_contexts[-5:]  # cap at 5

        recent_history = []
        for m in history_items:
            if int(m.data.get("chapter", 0)) >= chapter:
                continue
            if m.status == "archived" or m.status == "compressed":
                continue
            score = relevance_score(m, chapter, active_names)
            if score >= 30:
                recent_history.append(m)
        recent_history = recent_history[-5:]

        active_characters = []
        latest_state_by_name: Dict[str, Dict[str, Any]] = {}
        for context in recent_contexts:
            for state in context.data.get("character_states", []):
                latest_state_by_name[state.get("name", "")] = state

        for item in character_items:
            name = nested_get(item.data, "basic_info.name")
            if not name:
                continue
            if active_names and name not in active_names:
                continue
            active_characters.append(
                {
                    "name": name,
                    "core_traits": nested_get(item.data, "personality.core_traits") or [],
                    "catchphrases": nested_get(item.data, "speech_style.catchphrases") or [],
                    "growth_direction": nested_get(item.data, "personality.growth_direction") or "",
                    "current_state": latest_state_by_name.get(name, {}),
                }
            )
        if not active_characters:
            for item in character_items[:6]:
                name = nested_get(item.data, "basic_info.name")
                if not name:
                    continue
                active_characters.append(
                    {
                        "name": name,
                        "core_traits": nested_get(item.data, "personality.core_traits") or [],
                        "catchphrases": nested_get(item.data, "speech_style.catchphrases") or [],
                        "growth_direction": nested_get(item.data, "personality.growth_direction") or "",
                        "current_state": latest_state_by_name.get(name, {}),
                    }
                )

        unresolved = []
        foreshadowing = []
        for context in recent_contexts:
            unresolved.extend(context.data.get("unresolved_questions", []))
            unresolved.extend(context.data.get("foreshadowing", {}).get("unresolved", []))
            foreshadowing.extend(
                [item for item in context.data.get("foreshadowing", {}).get("planted", []) if not item.get("resolved")]
            )

        pack = {
            "generated_at": now_iso(),
            "target_chapter": chapter,
            "memory_focus": {
                "active_characters_count": len(active_characters),
                "active_plots_count": sum(1 for item in plot_items if item.data.get("status") != "已完成"),
                "recent_context_count": len(recent_contexts),
            },
            "style_guardrails": {
                "sentence_features": latest_style.get("sentence_features", {}),
                "description_style": latest_style.get("description_style", {}),
                "dialogue_style": latest_style.get("dialogue_style", {}),
                "top_words": [item["word"] for item in latest_style.get("word_usage", {}).get("high_freq_words", [])[:10]],
            },
            "active_characters": active_characters,
            "active_plots": [
                {
                    "plot_name": item.data.get("plot_name", ""),
                    "description": item.data.get("description", ""),
                    "status": item.data.get("status", ""),
                    "current_chapter": item.data.get("current_chapter"),
                    "latest_events": item.data.get("key_events", [])[-3:],
                }
                for item in plot_items
                if item.data.get("status") != "已完成"
            ],
            "must_remember": {
                "recent_chapter_summaries": [
                    {
                        "chapter": item.data.get("chapter"),
                        "title": item.data.get("title"),
                        "summary": item.data.get("summary") or item.data.get("content_summary", ""),
                    }
                    for item in recent_contexts
                ],
                "unresolved_questions": list(dict.fromkeys([q for q in unresolved if q])),
                "open_foreshadowing": foreshadowing[-10:],
            },
            "recent_history": [
                {
                    "chapter": item.data.get("chapter"),
                    "title": item.data.get("title"),
                    "key_events": item.data.get("key_events", []),
                    "creative_decisions": item.data.get("creative_decisions", []),
                }
                for item in recent_history
            ],
        }

        # Entity graph integration
        graph_path = os.path.join(self.memory_dir, "entity_graph.json")
        if os.path.exists(graph_path) and EntityGraphManager is not None:
            try:
                egm = EntityGraphManager(graph_path)
                pack["entity_context"] = egm.get_entity_context(chapter)
            except Exception:
                pass  # entity graph is optional, don't block chapter pack

        # LLM keyword retrieval: extract search keywords from active context
        # (AI_NovelGenerator concept: generate keywords before retrieval)
        pack["search_keywords"] = self._extract_search_keywords(
            chapter, active_characters, plot_items, recent_contexts
        )

        # Content temporal distance: flag items that were recently written about
        pack["temporal_distance_flags"] = self._temporal_distance_check(
            chapter, recent_contexts
        )

        return pack

    def sync_chapter(self, input_path: str) -> Dict[str, Any]:
        summary = load_json(input_path, {})
        chapter = int(summary.get("chapter", 0))
        title = summary.get("title", f"第{chapter}章")
        synced = {
            "context_created": False,
            "history_created": False,
            "plots_updated": 0,
            "characters_touched": 0,
            "foreshadowing_resolved": 0,
        }

        context_data = {
            "chapter": chapter,
            "title": title,
            "summary": summary.get("summary", ""),
            "key_elements": summary.get("key_elements", []),
            "chapter_metrics": summary.get("chapter_metrics", {}),
            "foreshadowing": {
                "planted": [
                    {"description": item, "chapter": chapter, "resolved": False, "resolved_chapter": None}
                    for item in summary.get("foreshadowing_planted", [])
                ],
                "unresolved": summary.get("unresolved_questions", []),
            },
            "character_states": summary.get("character_states", []),
            "unresolved_questions": summary.get("unresolved_questions", []),
        }
        self.create_memory("context", context_data, {"source": "sync-chapter"})
        synced["context_created"] = True

        history_data = {
            "chapter": chapter,
            "version": 1,
            "title": title,
            "content_summary": summary.get("summary", ""),
            "characters_involved": summary.get("characters_involved", []),
            "key_events": summary.get("key_events", []),
            "creative_decisions": summary.get("creative_decisions", []),
            "modifications": [],
            "calibration_records": [],
        }
        self.create_memory("history", history_data, {"source": "sync-chapter"})
        synced["history_created"] = True
        synced["foreshadowing_resolved"] = self._resolve_foreshadowing_and_questions(
            summary.get("foreshadowing_resolved", []),
            chapter,
        )

        for update in summary.get("plot_updates", []):
            plot_name = update.get("plot_name")
            existing = None
            for plot in self.query_memory(memory_type="plot"):
                if plot.data.get("plot_name") == plot_name:
                    existing = plot
                    break
            event = update.get("event")
            if existing:
                key_events = existing.data.get("key_events", [])
                if event:
                    key_events.append(
                        {
                            "chapter": chapter,
                            "event": event,
                            "characters_involved": summary.get("characters_involved", []),
                            "impact": update.get("impact", ""),
                        }
                    )
                self.update_memory(
                    existing.memory_id,
                    {
                        "current_chapter": chapter,
                        "status": update.get("status", existing.data.get("status", "进行中")),
                        "key_events": key_events,
                    },
                )
            else:
                self.create_memory(
                    "plot",
                    {
                        "plot_type": update.get("plot_type", "sub"),
                        "plot_name": plot_name or f"plot-{chapter}",
                        "description": update.get("description", ""),
                        "start_chapter": update.get("start_chapter", chapter),
                        "current_chapter": chapter,
                        "status": update.get("status", "进行中"),
                        "key_events": [
                            {
                                "chapter": chapter,
                                "event": event or "新剧情更新",
                                "characters_involved": summary.get("characters_involved", []),
                                "impact": update.get("impact", ""),
                            }
                        ],
                    },
                    {"source": "sync-chapter"},
                )
            synced["plots_updated"] += 1

        states = {item.get("name"): item for item in summary.get("character_states", []) if item.get("name")}
        for character in self.query_memory(memory_type="character"):
            name = nested_get(character.data, "basic_info.name")
            if name and name in states:
                self.update_memory(
                    character.memory_id,
                    {"current_state": states[name]},
                    {"last_updated_chapter": chapter},
                )
                synced["characters_touched"] += 1

        # Entity graph sync
        graph_path = os.path.join(self.memory_dir, "entity_graph.json")
        if os.path.exists(graph_path) and EntityGraphManager is not None:
            try:
                egm = EntityGraphManager(graph_path)
                egm_result = egm.sync_chapter(summary)
                synced["entities_added"] = egm_result.get("entities_added", 0)
                synced["edges_updated"] = egm_result.get("edges_updated", 0)
            except Exception:
                pass  # entity graph is optional

        return synced


def print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def parse_filter_args(items: Optional[List[str]]) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    for item in items or []:
        key, value = item.split("=", 1)
        filters[key] = value
    return filters


def main() -> None:
    parser = argparse.ArgumentParser(description="小说记忆系统管理器")
    subparsers = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--memory-dir", default="./memory_system", help="记忆系统目录")

    subparsers.add_parser("init", parents=[common], help="初始化记忆系统")

    create_parser = subparsers.add_parser("create", parents=[common], help="创建记忆")
    create_parser.add_argument("--type", required=True, choices=["style_dna", "character", "plot", "context", "history"])
    create_parser.add_argument("--data", required=True, help="JSON字符串")
    create_parser.add_argument("--metadata", help="JSON字符串")

    update_parser = subparsers.add_parser("update", parents=[common], help="更新记忆")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--data", required=True, help="JSON字符串")
    update_parser.add_argument("--metadata", help="JSON字符串")

    query_parser = subparsers.add_parser("query", parents=[common], help="查询记忆")
    query_parser.add_argument("--type", choices=["style_dna", "character", "plot", "context", "history"])
    query_parser.add_argument("--filter", action="append", help="格式 key=value，支持 basic_info.name=沈知言")

    delete_parser = subparsers.add_parser("delete", parents=[common], help="删除记忆")
    delete_parser.add_argument("--id", required=True)

    export_parser = subparsers.add_parser("export", parents=[common], help="导出记忆")
    export_parser.add_argument("--output", required=True)

    subparsers.add_parser("stats", parents=[common], help="统计记忆")

    bootstrap_parser = subparsers.add_parser("bootstrap-project", parents=[common], help="导入项目基础记忆")
    bootstrap_parser.add_argument("--input", required=True, help="project_bootstrap.json")

    pack_parser = subparsers.add_parser("chapter-pack", parents=[common], help="生成章节前记忆包")
    pack_parser.add_argument("--chapter", required=True, type=int)
    pack_parser.add_argument("--output", help="输出到JSON文件")

    sync_parser = subparsers.add_parser("sync-chapter", parents=[common], help="章节摘要回填")
    sync_parser.add_argument("--input", required=True, help="chapter_summary.json")

    review_parser = subparsers.add_parser("review-pack", parents=[common], help="生成阶段性记忆体检包")
    review_parser.add_argument("--chapter", required=True, type=int)
    review_parser.add_argument("--output", help="输出到JSON文件")

    # 兼容旧参数
    parser.add_argument("--init", action="store_true", help="兼容旧版初始化入口")
    parser.add_argument("--query", choices=["style_dna", "character", "plot", "context", "history"], help="兼容旧版查询入口")
    parser.add_argument("--name", help="兼容旧版按人物名查询")
    parser.add_argument("--memory-dir", default="./memory_system", help="记忆系统目录")

    args = parser.parse_args()

    if args.init:
        MemoryManager(args.memory_dir).init_system()
        return

    if args.query:
        manager = MemoryManager(args.memory_dir)
        manager.load_memories()
        filters = {"basic_info.name": args.name} if args.name else {}
        memories = manager.query_memory(memory_type=args.query, filters=filters)
        print_json({"count": len(memories), "memories": [m.to_dict() for m in memories]})
        return

    if not args.command:
        parser.print_help()
        return

    manager = MemoryManager(args.memory_dir)
    if args.command == "init":
        manager.init_system()
        return

    manager.load_memories()

    if args.command == "create":
        data = json.loads(args.data)
        metadata = json.loads(args.metadata) if args.metadata else None
        memory = manager.create_memory(args.type, data, metadata)
        print_json(memory.to_dict())
    elif args.command == "update":
        data = json.loads(args.data)
        metadata = json.loads(args.metadata) if args.metadata else None
        memory = manager.update_memory(args.id, data, metadata)
        print_json(memory.to_dict())
    elif args.command == "query":
        filters = parse_filter_args(args.filter)
        memories = manager.query_memory(memory_type=args.type, filters=filters)
        print_json({"count": len(memories), "memories": [m.to_dict() for m in memories]})
    elif args.command == "delete":
        ok = manager.delete_memory(args.id)
        print_json({"deleted": ok, "memory_id": args.id})
    elif args.command == "export":
        payload = manager.export_memories(args.output)
        print_json(payload)
    elif args.command == "stats":
        print_json(manager.get_memory_stats())
    elif args.command == "bootstrap-project":
        result = manager.bootstrap_project(args.input)
        print_json(result)
    elif args.command == "chapter-pack":
        payload = manager.generate_chapter_pack(args.chapter)
        if args.output:
            save_json(args.output, payload)
        print_json(payload)
    elif args.command == "sync-chapter":
        result = manager.sync_chapter(args.input)
        print_json(result)
    elif args.command == "review-pack":
        payload = manager.build_review_pack(args.chapter)
        if args.output:
            save_json(args.output, payload)
        print_json(payload)


if __name__ == "__main__":
    main()
