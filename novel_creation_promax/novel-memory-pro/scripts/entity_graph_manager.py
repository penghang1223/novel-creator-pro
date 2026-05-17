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
    ) -> None:
        # Check for existing edge
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target and edge["status"] == "active":
                edge["relation_type"] = relation_type
                edge["polarity"] = polarity
                edge["strength"] = strength
                self._save()
                return

        self.graph["edges"].append({
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "polarity": polarity,
            "strength": strength,
            "established_chapter": chapter,
            "status": "active",
        })
        self._save()

    def dissolve_edge(self, source: str, target: str) -> None:
        for edge in self.graph["edges"]:
            if edge["source"] == source and edge["target"] == target and edge["status"] == "active":
                edge["status"] = "dissolved"
        self._save()

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
            if action == "create":
                self.add_edge(
                    source, target,
                    relation_type=details.get("relation_type", ""),
                    polarity=details.get("polarity", "neutral"),
                    strength=details.get("strength", 5),
                    chapter=chapter,
                )
            elif action == "dissolve":
                self.dissolve_edge(source, target)
            elif action == "update":
                self.add_edge(
                    source, target,
                    relation_type=details.get("relation_type", ""),
                    polarity=details.get("polarity", "neutral"),
                    strength=details.get("strength", 5),
                    chapter=chapter,
                )
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
            "active_edges": active_edges,
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
