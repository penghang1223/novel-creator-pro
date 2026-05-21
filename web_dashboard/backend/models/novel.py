"""Novel and chapter data models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    IDEA = "创意"
    SETTING = "设定"
    OUTLINE = "大纲"
    DETAIL_OUTLINE = "细纲"
    WRITING = "正文"
    MEMORY = "记忆更新"
    REVIEW = "完结复盘"


STAGE_ORDER = [
    PipelineStage.IDEA,
    PipelineStage.SETTING,
    PipelineStage.OUTLINE,
    PipelineStage.DETAIL_OUTLINE,
    PipelineStage.WRITING,
    PipelineStage.MEMORY,
    PipelineStage.REVIEW,
]


class ChapterCard(BaseModel):
    chapter_number: int
    title: str
    stage: PipelineStage
    rhythm_type: Optional[str] = None
    word_count: Optional[int] = None
    audit_passed: Optional[bool] = None
    gate_passed: Optional[bool] = None
    last_updated: Optional[str] = None
    sub_stages: dict[str, bool] = Field(default_factory=dict)
    foreshadowing_planted: list[str] = Field(default_factory=list)
    foreshadowing_resolved: list[str] = Field(default_factory=list)


class NovelOverview(BaseModel):
    novel_name: str
    platform: str
    total_chapters_planned: int = 0
    chapters_written: int = 0
    current_stage: PipelineStage
    chapters: list[ChapterCard] = Field(default_factory=list)
    protagonist: dict[str, Any] = Field(default_factory=dict)
    last_updated: Optional[str] = None


class NovelListItem(BaseModel):
    novel_name: str
    platform: str
    chapters_written: int
    current_stage: PipelineStage
    last_updated: Optional[str] = None


class NovelState(BaseModel):
    """Raw novel_state.json wrapper."""
    novel_name: str = ""
    platform: str = ""
    chapters_written: int = 0
    data: dict[str, Any] = Field(default_factory=dict)
