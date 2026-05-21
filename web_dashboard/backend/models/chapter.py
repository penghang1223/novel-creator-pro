"""Chapter-related models."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChapterContent(BaseModel):
    chapter_number: int
    title: str
    content: str
    word_count: int = 0


class ChapterMetrics(BaseModel):
    narrative_tension: int = 5
    emotional_change: int = 0
    foreshadowing_density: str = "medium"
    information_release: str = "medium"
    relationship_shift: str = "none"
    knowledge_reference_count: int = 0


class ChapterSummary(BaseModel):
    chapter: int = 0
    title: str = ""
    summary: str = ""
    key_elements: list[str] = Field(default_factory=list)
    characters_involved: list[str] = Field(default_factory=list)
    chapter_metrics: Optional[ChapterMetrics] = None
    strand: dict[str, Any] = Field(default_factory=dict)
    key_events: list[dict[str, Any]] = Field(default_factory=list)
    foreshadowing_planted: list[Any] = Field(default_factory=list)
    foreshadowing_resolved: list[Any] = Field(default_factory=list)


class PreWriteQuestion(BaseModel):
    id: int = 0
    name: str = ""
    weight: int = 0
    score: int = 0
    note: str = ""


class PreWriteReport(BaseModel):
    chapter: int
    total_score: int = 0
    passed: bool = False
    questions: list[PreWriteQuestion] = Field(default_factory=list)


class AuditViolation(BaseModel):
    word: str = ""
    count: int = 0
    limit: int = 0
    severity: str = ""


class AuditResult(BaseModel):
    chapter: int
    ai_word_violations: list[AuditViolation] = Field(default_factory=list)
    dialogue_ratio: float = 0.0
    word_count: int = 0
    word_count_range: tuple[int, int] = (2800, 3200)
    banned_word_hits: list[str] = Field(default_factory=list)
    passed: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class GateCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class GateResult(BaseModel):
    chapter: int
    passed: bool = False
    checks: list[GateCheck] = Field(default_factory=list)
