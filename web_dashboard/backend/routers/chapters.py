"""Chapter read/edit API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chapter_service import ChapterService
from services.novel_scanner import NovelScanner

router = APIRouter(prefix="/api/novels/{platform}/{name:path}/chapters", tags=["chapters"])
chapter_svc = ChapterService()
scanner = NovelScanner()


@router.get("")
def list_chapters(platform: str, name: str):
    """List all chapters with metadata."""
    overview = scanner.scan_novel(platform, name)
    return [card.model_dump() for card in overview.chapters]


@router.get("/{num}")
def get_chapter(platform: str, name: str, num: int):
    """Get chapter content + summary."""
    content = chapter_svc.get_chapter_content(platform, name, num)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Chapter {num} not found")
    summary = chapter_svc.get_chapter_summary(platform, name, num)
    return {
        "content": content.model_dump(),
        "summary": summary,
    }


class SaveChapterRequest(BaseModel):
    content: str


@router.put("/{num}")
def save_chapter(platform: str, name: str, num: int, body: SaveChapterRequest):
    """Save chapter content."""
    ok = chapter_svc.save_chapter_content(platform, name, num, body.content)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Chapter {num} not found")
    return {"ok": True, "word_count": len(body.content)}


@router.get("/{num}/summary")
def get_summary(platform: str, name: str, num: int):
    """Get chapter summary JSON."""
    return chapter_svc.get_chapter_summary(platform, name, num)
