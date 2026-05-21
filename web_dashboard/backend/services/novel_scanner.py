"""Scan novel_output/ to build Kanban board state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config import OUTPUT_DIR, STAGES
from models.novel import (
    ChapterCard,
    NovelListItem,
    NovelOverview,
    PipelineStage,
    STAGE_ORDER,
)
from utils.paths import (
    count_chinese_chars,
    extract_chapter_number,
    extract_chapter_title,
    get_chapters_dir,
    get_memory_dir,
    get_novel_state_path,
    get_summaries_dir,
)


def load_json_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


class NovelScanner:
    """Read the filesystem to build Kanban board state."""

    def list_novels(self) -> list[NovelListItem]:
        """Scan all platforms and novels."""
        novels = []
        if not OUTPUT_DIR.exists():
            return novels

        for platform_dir in sorted(OUTPUT_DIR.iterdir()):
            if not platform_dir.is_dir() or platform_dir.name.startswith("."):
                continue
            platform = platform_dir.name
            for novel_dir in sorted(platform_dir.iterdir()):
                if not novel_dir.is_dir() or novel_dir.name.startswith("."):
                    continue
                state = load_json_safe(get_novel_state_path(platform, novel_dir.name))
                chapters_written = state.get("chapters_written", 0)
                # Count actual chapter files
                ch_dir = get_chapters_dir(platform, novel_dir.name)
                if ch_dir.exists():
                    ch_count = len(list(ch_dir.glob("第*.md")))
                    chapters_written = max(chapters_written, ch_count)

                novels.append(
                    NovelListItem(
                        novel_name=novel_dir.name,
                        platform=platform,
                        chapters_written=chapters_written,
                        current_stage=self._infer_current_stage(platform, novel_dir.name, state),
                        last_updated=state.get("updated_at"),
                    )
                )
        return novels

    def scan_novel(self, platform: str, novel_name: str) -> NovelOverview:
        """Build full Kanban state for one novel."""
        state = load_json_safe(get_novel_state_path(platform, novel_name))
        ch_dir = get_chapters_dir(platform, novel_name)

        chapters = []
        if ch_dir.exists():
            for ch_file in sorted(ch_dir.glob("第*.md")):
                ch_num = extract_chapter_number(ch_file.name)
                if ch_num is None:
                    continue
                card = self._build_chapter_card(platform, novel_name, ch_num, ch_file, state)
                chapters.append(card)

        chapters_written = len(chapters)
        protagonist = {}
        char_tracking = state.get("character_tracking", {})
        if char_tracking:
            for name, info in char_tracking.items():
                if info.get("role") == "protagonist" or info.get("role") == "main":
                    protagonist = {"name": name, **info}
                    break

        return NovelOverview(
            novel_name=novel_name,
            platform=platform,
            total_chapters_planned=state.get("total_chapters_planned", 0),
            chapters_written=chapters_written,
            current_stage=self._infer_current_stage(platform, novel_name, state),
            chapters=chapters,
            protagonist=protagonist,
            last_updated=state.get("updated_at"),
        )

    def _build_chapter_card(
        self,
        platform: str,
        novel_name: str,
        ch_num: int,
        ch_file: Path,
        state: dict,
    ) -> ChapterCard:
        """Build a ChapterCard from filesystem state."""
        title = extract_chapter_title(ch_file.name)
        content = ch_file.read_text(encoding="utf-8")
        word_count = count_chinese_chars(content)

        # Load summary
        summary_dir = get_summaries_dir(platform, novel_name)
        summary_path = summary_dir / f"chapter_{ch_num:03d}_summary.json"
        summary = load_json_safe(summary_path)

        # Determine stage and sub-stages
        stage, sub_stages = self._determine_stage(ch_num, state, summary, summary_path)

        # Rhythm type from rhythm_dashboard
        rhythm_dashboard = state.get("rhythm_dashboard", [])
        rhythm_type = None
        if ch_num - 1 < len(rhythm_dashboard):
            rhythm_type = rhythm_dashboard[ch_num - 1].get("type")

        # Audit/gate status from summary
        audit_passed = summary.get("audit_passed")
        gate_passed = summary.get("gate_passed")

        return ChapterCard(
            chapter_number=ch_num,
            title=title,
            stage=stage,
            rhythm_type=rhythm_type,
            word_count=word_count,
            audit_passed=audit_passed,
            gate_passed=gate_passed,
            last_updated=summary.get("generated_at"),
            sub_stages=sub_stages,
            foreshadowing_planted=[
                f.get("description", f) if isinstance(f, dict) else str(f)
                for f in summary.get("foreshadowing_planted", [])
            ],
            foreshadowing_resolved=[
                f.get("description", f) if isinstance(f, dict) else str(f)
                for f in summary.get("foreshadowing_resolved", [])
            ],
        )

    def _determine_stage(
        self,
        ch_num: int,
        state: dict,
        summary: dict,
        summary_path: Path,
    ) -> tuple[PipelineStage, dict[str, bool]]:
        """Infer which pipeline stage a chapter is in."""
        has_summary = summary_path.exists() and summary
        has_content = True  # if we found the file, it has content
        gate_passed = summary.get("gate_passed", False)
        audit_passed = summary.get("audit_passed", False)
        memory_synced = summary.get("memory_synced", False)

        sub_stages = {
            "pre_write": summary.get("pre_write_score", 0) >= 70,
            "pass1": has_content,
            "gate": gate_passed,
            "pass2": gate_passed,  # implied if gate passed
            "audit": audit_passed,
            "style": summary.get("style_checked", False),
            "character": summary.get("character_checked", False),
            "memory_sync": memory_synced,
        }

        if memory_synced:
            return PipelineStage.MEMORY, sub_stages
        elif audit_passed:
            return PipelineStage.MEMORY, sub_stages
        elif gate_passed:
            return PipelineStage.WRITING, sub_stages
        elif has_content:
            return PipelineStage.WRITING, sub_stages
        elif has_summary:
            return PipelineStage.DETAIL_OUTLINE, sub_stages
        else:
            # No summary, check if this is the next chapter to write
            chapters_written = state.get("chapters_written", 0)
            if ch_num <= chapters_written:
                return PipelineStage.DETAIL_OUTLINE, sub_stages
            return PipelineStage.DETAIL_OUTLINE, sub_stages

    def _infer_current_stage(
        self, platform: str, novel_name: str, state: dict
    ) -> PipelineStage:
        """Infer the novel's overall current stage."""
        ch_dir = get_chapters_dir(platform, novel_name)
        ch_count = 0
        if ch_dir.exists():
            ch_count = len(list(ch_dir.glob("第*.md")))

        if ch_count == 0:
            # No chapters written, check what stage we're at
            outline_dir = get_novel_state_path(platform, novel_name).parent / "细纲"
            setting_dir = get_novel_state_path(platform, novel_name).parent / "设定"
            if outline_dir.exists() and any(outline_dir.iterdir()):
                return PipelineStage.DETAIL_OUTLINE
            elif setting_dir.exists() and any(setting_dir.iterdir()):
                return PipelineStage.OUTLINE
            return PipelineStage.IDEA

        # Check latest chapter status
        summary_dir = get_summaries_dir(platform, novel_name)
        latest_summary = load_json_safe(summary_dir / f"chapter_{ch_count:03d}_summary.json")

        if latest_summary.get("memory_synced"):
            return PipelineStage.WRITING  # ready for next chapter
        elif latest_summary.get("audit_passed"):
            return PipelineStage.MEMORY
        elif latest_summary.get("gate_passed"):
            return PipelineStage.WRITING
        elif latest_summary:
            return PipelineStage.WRITING

        return PipelineStage.WRITING
