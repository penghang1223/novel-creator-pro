#!/usr/bin/env python3
"""
实体图谱管理器

管理角色/地点/物品/势力/功法的结构化追踪，
支持关系边、别名解析、状态时间线和生命周期管理。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not os.path.exists(path):
        return default or {}
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


ENTITY_TYPES = {"character", "location", "item", "faction", "technique"}
STATUSES = {"active", "warm", "archived"}


class EntityGraphManager:
    def __init__(self, graph_path: str):
        self.graph_path = graph_path
        self.graph: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        self.graph = load_json(self.graph_path, {"entities": {}, "edges": [], "next_entity_id": 1})

    def _save(self) -> None:
        save_json(self.graph_path, self.graph)

    def _next_id(self, entity_type: str, canonical_name: str) -> str:
        return f"{entity_type}_{canonical_name}"

    # ── Entity CRUD ──────────────────────────────────────────────

    def add_entity(
        self,
        entity_type: str,
        canonical_name: str,
        aliases: Optional[List[str]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        chapter: int = 1,
    ) -> str:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unknown entity type: {entity_type}. Must be one of {ENTITY_TYPES}")

        entity_id = self._next_id(entity_type, canonical_name)
        if entity_id in self.graph["entities"]:
            return entity_id  # already exists

        entity = {
            "entity_id": entity_id,
            "type": entity_type,
            "canonical_name": canonical_name,
            "aliases": aliases or [],
            "state_timeline": [{"chapter": chapter, "state": initial_state or {}}],
            "first_appearance": chapter,
            "last_active_chapter": chapter,
            "status": "active",
        }
        self.graph["entities"][entity_id] = entity
        self._save()
        return entity_id

    def update_state(self, entity_id: str, state_delta: Dict[str, Any], chapter: int) -> None:
        entity = self.graph["entities"].get(entity_id)
        if not entity:
            return
        # Merge with last state
        last = entity["state_timeline"][-1] if entity["state_timeline"] else {"state": {}}
        merged = {**last.get("state", {}), **state_delta}
        entity["state_timeline"].append({"chapter": chapter, "state": merged})
        entity["last_active_chapter"] = chapter
        entity["status"] = "active"
        self._save()

    def add_alias(self, entity_id: str, alias: str) -> None:
        entity = self.graph["entities"].get(entity_id)
        if entity and alias not in entity["aliases"] and alias != entity["canonical_name"]:
            entity["aliases"].append(alias)
            self._save()

    def resolve_alias(self, name: str) -> Optional[str]:
        """Resolve a name (canonical or alias) to an entity_id."""
        for eid, entity in self.graph["entities"].items():
            if entity["canonical_name"] == name or name in entity["aliases"]:
                return eid
        return None

    # ── Edge CRUD ────────────────────────────────────────────────

    def add_edge(
        self,
        source: str,
        target: str,
        relation_type: str,
        polarity: str = "neutral",
        strength: int = 5,
        chapter: int = 1,
        event: str = "",
    ) -> None:
        # Check for existing edge
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target and edge["status"] == "active":
                old_type = edge["relation_type"]
                old_polarity = edge["polarity"]
                old_strength = edge["strength"]
                edge["relation_type"] = relation_type
                edge["polarity"] = polarity
                edge["strength"] = strength
                edge["last_updated_chapter"] = chapter
                # 记录时间线条目
                edge.setdefault("timeline", []).append({
                    "chapter": chapter,
                    "relation_type": relation_type,
                    "polarity": polarity,
                    "strength": strength,
                    "event": event or f"关系更新: {old_type}({old_polarity},{old_strength}) → {relation_type}({polarity},{strength})",
                })
                self._save()
                return

        new_edge = {
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "polarity": polarity,
            "strength": strength,
            "established_chapter": chapter,
            "last_updated_chapter": chapter,
            "status": "active",
            "timeline": [{
                "chapter": chapter,
                "relation_type": relation_type,
                "polarity": polarity,
                "strength": strength,
                "event": event or f"关系建立: {relation_type}",
            }],
        }
        self.graph["edges"].append(new_edge)
        self._save()

    def dissolve_edge(self, source: str, target: str, chapter: int = 0, reason: str = "") -> None:
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target and edge["status"] == "active":
                edge["status"] = "dissolved"
                edge["dissolved_chapter"] = chapter
                edge.setdefault("timeline", []).append({
                    "chapter": chapter,
                    "event": reason or "关系解除",
                    "polarity": "neutral",
                    "strength": 0,
                })
        self._save()

    def add_edge_event(self, source: str, target: str, chapter: int, event: str, **kwargs: Any) -> None:
        """在关系边上记录一个事件（不改变关系类型/强度，只记事件）。"""
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target and edge["status"] == "active":
                entry: dict[str, Any] = {
                    "chapter": chapter,
                    "event": event,
                }
                entry.update(kwargs)
                edge.setdefault("timeline", []).append(entry)
                edge["last_updated_chapter"] = chapter
                self._save()
                return
        # 边不存在时自动创建
        self.add_edge(source, target, relation_type=kwargs.get("relation_type", "unknown"), chapter=chapter, event=event)

    def get_edge_timeline(self, source: str, target: str) -> list[dict[str, Any]]:
        """获取两个实体之间的关系时间线。"""
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target:
                return edge.get("timeline", [])
            if edge["source"] == target and edge["target"] == source:
                return edge.get("timeline", [])
        return []

    def get_entity_relationship_history(self, entity_id: str) -> list[dict[str, Any]]:
        """获取某个实体的所有关系历史（含时间线摘要）。"""
        history: list[dict[str, Any]] = []
        for edge in self.graph["edges"]:
            if edge["source"] == entity_id or edge["target"] == entity_id:
                other = edge["target"] if edge["source"] == entity_id else edge["source"]
                timeline = edge.get("timeline", [])
                history.append({
                    "other_entity": other,
                    "relation_type": edge["relation_type"],
                    "polarity": edge["polarity"],
                    "strength": edge["strength"],
                    "status": edge["status"],
                    "established_chapter": edge.get("established_chapter", 0),
                    "timeline_entries": len(timeline),
                    "latest_event": timeline[-1]["event"] if timeline else "",
                })
        return history

    # ── Queries ──────────────────────────────────────────────────

    def query_active(self, chapter: int, window: int = 5) -> List[Dict[str, Any]]:
        """Return entities active within `window` chapters of `chapter`."""
        result = []
        for entity in self.graph["entities"].values():
            last = entity.get("last_active_chapter", 0)
            if last >= chapter - window:
                result.append(entity)
        return result

    def query_connections(self, entity_id: str) -> List[Dict[str, Any]]:
        """Return all active edges involving the entity."""
        return [
            edge for edge in self.graph["edges"]
            if edge["status"] == "active" and (edge["source"] == entity_id or edge["target"] == entity_id)
        ]

    def query_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.graph["entities"].values() if e["type"] == entity_type]

    # ── Lifecycle ────────────────────────────────────────────────

    def update_lifecycle(self, current_chapter: int) -> int:
        """Update entity statuses based on activity recency. Returns count of updated entities."""
        updated = 0
        for entity in self.graph["entities"].values():
            last = entity.get("last_active_chapter", 0)
            gap = current_chapter - last
            old_status = entity["status"]
            if gap <= 5:
                entity["status"] = "active"
            elif gap <= 15:
                entity["status"] = "warm"
            else:
                entity["status"] = "archived"
            if entity["status"] != old_status:
                updated += 1
        if updated:
            self._save()
        return updated

    # ── Chapter sync ─────────────────────────────────────────────

    def sync_chapter(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process new_entities and relationship_changes from a chapter summary."""
        chapter = summary.get("chapter", 0)
        result = {"entities_added": 0, "edges_updated": 0}

        for item in summary.get("new_entities", []):
            entity_type = item.get("type", "character")
            canonical_name = item.get("canonical_name", "")
            if canonical_name:
                self.add_entity(entity_type, canonical_name, chapter=chapter)
                result["entities_added"] += 1

        for change in summary.get("relationship_changes", []):
            source = change.get("source", "")
            target = change.get("target", "")
            action = change.get("action", "create")
            details = change.get("details", {})
            event = change.get("event", "")
            if action == "create":
                self.add_edge(
                    source, target,
                    relation_type=details.get("relation_type", ""),
                    polarity=details.get("polarity", "neutral"),
                    strength=details.get("strength", 5),
                    chapter=chapter,
                    event=event,
                )
            elif action == "dissolve":
                self.dissolve_edge(source, target, chapter=chapter, reason=event)
            elif action == "update":
                self.add_edge(
                    source, target,
                    relation_type=details.get("relation_type", ""),
                    polarity=details.get("polarity", "neutral"),
                    strength=details.get("strength", 5),
                    chapter=chapter,
                    event=event,
                )
            elif action == "event":
                self.add_edge_event(source, target, chapter, event, **details)
            result["edges_updated"] += 1

        self.update_lifecycle(chapter)
        return result

    # ── Chapter pack injection ───────────────────────────────────

    def get_entity_context(self, chapter: int) -> Dict[str, Any]:
        """Get active entities and their edges for chapter pack injection."""
        active = self.query_active(chapter)
        active_ids = {e["entity_id"] for e in active}
        active_edges = [
            edge for edge in self.graph["edges"]
            if edge["status"] == "active" and edge["source"] in active_ids and edge["target"] in active_ids
        ]
        # 为每条边附带近期时间线（最近5条）
        edges_with_context = []
        for edge in active_edges:
            edge_copy = dict(edge)
            timeline = edge.get("timeline", [])
            edge_copy["recent_timeline"] = timeline[-5:] if len(timeline) > 5 else timeline
            edges_with_context.append(edge_copy)

        return {
            "active_entities": [
                {
                    "entity_id": e["entity_id"],
                    "type": e["type"],
                    "canonical_name": e["canonical_name"],
                    "aliases": e["aliases"],
                    "current_state": e["state_timeline"][-1]["state"] if e["state_timeline"] else {},
                }
                for e in active
            ],
            "active_edges": edges_with_context,
        }

    # ── Stats ────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        entities = list(self.graph["entities"].values())
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for e in entities:
            by_type[e["type"]] = by_type.get(e["type"], 0) + 1
            by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        return {
            "total_entities": len(entities),
            "total_edges": len(self.graph["edges"]),
            "by_type": by_type,
            "by_status": by_status,
        }


# ── CLI ──────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="实体图谱管理器")
    parser.add_argument("--graph", required=True, help="entity_graph.json 路径")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("stats", help="显示统计")
    sub.add_parser("list-active", help="列出活跃实体").add_argument("--chapter", type=int, required=True)

    add_p = sub.add_parser("add-entity", help="添加实体")
    add_p.add_argument("--type", required=True, choices=sorted(ENTITY_TYPES))
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--chapter", type=int, default=1)

    add_e = sub.add_parser("add-edge", help="添加关系")
    add_e.add_argument("--source", required=True)
    add_e.add_argument("--target", required=True)
    add_e.add_argument("--relation", required=True)
    add_e.add_argument("--polarity", default="neutral")
    add_e.add_argument("--strength", type=int, default=5)
    add_e.add_argument("--chapter", type=int, default=1)

    conn_p = sub.add_parser("connections", help="查询关系")
    conn_p.add_argument("--entity", required=True)

    tl_p = sub.add_parser("timeline", help="查询关系时间线")
    tl_p.add_argument("--source", required=True)
    tl_p.add_argument("--target", required=True)

    hist_p = sub.add_parser("history", help="查询实体关系历史")
    hist_p.add_argument("--entity", required=True)

    event_p = sub.add_parser("add-event", help="记录关系事件")
    event_p.add_argument("--source", required=True)
    event_p.add_argument("--target", required=True)
    event_p.add_argument("--chapter", type=int, required=True)
    event_p.add_argument("--event", required=True)

    args = parser.parse_args()
    mgr = EntityGraphManager(args.graph)

    if args.command == "stats":
        print(json.dumps(mgr.stats(), ensure_ascii=False, indent=2))
    elif args.command == "list-active":
        active = mgr.query_active(args.chapter)
        for e in active:
            print(f"  {e['entity_id']} ({e['type']}) - {e['canonical_name']}")
    elif args.command == "add-entity":
        eid = mgr.add_entity(args.type, args.name, chapter=args.chapter)
        print(f"Added: {eid}")
    elif args.command == "add-edge":
        mgr.add_edge(args.source, args.target, args.relation, args.polarity, args.strength, args.chapter)
        print(f"Edge added: {args.source} -> {args.target}")
    elif args.command == "connections":
        edges = mgr.query_connections(args.entity)
        for e in edges:
            other = e["target"] if e["source"] == args.entity else e["source"]
            print(f"  {e['relation_type']} ({e['polarity']}) -> {other}")
    elif args.command == "timeline":
        timeline = mgr.get_edge_timeline(args.source, args.target)
        if not timeline:
            print("  (无时间线数据)")
        for entry in timeline:
            ch = entry.get("chapter", "?")
            event = entry.get("event", "")
            print(f"  第{ch}章: {event}")
    elif args.command == "history":
        history = mgr.get_entity_relationship_history(args.entity)
        for h in history:
            status_icon = "●" if h["status"] == "active" else "○"
            print(f"  {status_icon} → {h['other_entity']}: {h['relation_type']} ({h['polarity']}, 强度{h['strength']}) [{h['timeline_entries']}条记录]")
            if h["latest_event"]:
                print(f"    最新: {h['latest_event']}")
    elif args.command == "add-event":
        mgr.add_edge_event(args.source, args.target, args.chapter, args.event)
        print(f"Event recorded: {args.source} <-> {args.target} @ ch{args.chapter}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
