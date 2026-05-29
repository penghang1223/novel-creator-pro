"""Scan novel_output/ to build Kanban board state."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from config import OUTPUT_DIR, PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from novel_creation_promax.core.jsonio import load_json
from novel_creation_promax.core.passport import passport_path, status_passed
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
    get_novel_state_path,
    get_summaries_dir,
    list_chapter_files,
)


def load_json_safe(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    return data if isinstance(data, dict) else {}


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
                chapters_written = max(chapters_written, len(list_chapter_files(novel_dir)))

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
        chapters = []
        novel_dir = get_novel_state_path(platform, novel_name).parent
        for ch_num, ch_file in list_chapter_files(novel_dir):
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
        passport = load_json_safe(passport_path(get_novel_state_path(platform, novel_name).parent, ch_num))

        # Determine stage and sub-stages
        stage, sub_stages = self._determine_stage(ch_num, state, summary, summary_path, passport)

        # Rhythm type from rhythm_dashboard
        rhythm_dashboard = state.get("rhythm_dashboard", [])
        rhythm_type = None
        if ch_num - 1 < len(rhythm_dashboard):
            rhythm_type = rhythm_dashboard[ch_num - 1].get("type")

        pipeline = passport.get("pipeline", {}) if isinstance(passport, dict) else {}
        audit_passed = status_passed(pipeline.get("post_write_audit")) if pipeline else summary.get("audit_passed")
        gate_passed = status_passed(pipeline.get("writing_gate")) if pipeline else summary.get("gate_passed")

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
        passport: dict | None = None,
    ) -> tuple[PipelineStage, dict[str, bool]]:
        """Infer which pipeline stage a chapter is in."""
        has_summary = summary_path.exists() and summary
        has_content = True  # if we found the file, it has content
        pipeline = passport.get("pipeline", {}) if isinstance(passport, dict) else {}
        gate_passed = status_passed(pipeline.get("writing_gate")) if pipeline else summary.get("gate_passed", False)
        audit_passed = status_passed(pipeline.get("post_write_audit")) if pipeline else summary.get("audit_passed", False)
        memory_synced = status_passed(pipeline.get("memory_sync")) if pipeline else summary.get("memory_synced", False)

        sub_stages = {
            "knowledge_pack": status_passed(pipeline.get("knowledge_pack")) if pipeline else False,
            "pre_write": status_passed(pipeline.get("pre_write_check")) if pipeline else summary.get("pre_write_score", 0) >= 70,
            "pass1": has_content,
            "gate": gate_passed,
            "pass2": gate_passed,  # implied if gate passed
            "audit": audit_passed,
            "truth": status_passed(pipeline.get("truth_delta")) if pipeline else False,
            "style": status_passed(pipeline.get("style_calibration")) if pipeline else summary.get("style_checked", False),
            "character": status_passed(pipeline.get("character_consistency")) if pipeline else summary.get("character_checked", False),
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
        ch_count = 0
        novel_dir = get_novel_state_path(platform, novel_name).parent
        ch_count = len(list_chapter_files(novel_dir))

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
        latest_passport = load_json_safe(passport_path(novel_dir, ch_count))
        pipeline = latest_passport.get("pipeline", {}) if isinstance(latest_passport, dict) else {}

        if status_passed(pipeline.get("memory_sync")) or latest_summary.get("memory_synced"):
            return PipelineStage.WRITING  # ready for next chapter
        elif status_passed(pipeline.get("post_write_audit")) or latest_summary.get("audit_passed"):
            return PipelineStage.MEMORY
        elif status_passed(pipeline.get("writing_gate")) or latest_summary.get("gate_passed"):
            return PipelineStage.WRITING
        elif latest_summary:
            return PipelineStage.WRITING

        return PipelineStage.WRITING
