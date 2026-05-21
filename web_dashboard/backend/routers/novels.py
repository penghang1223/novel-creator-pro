"""Novel list/detail API routes."""

from fastapi import APIRouter, HTTPException

from models.novel import NovelListItem, NovelOverview
from services.novel_scanner import NovelScanner

router = APIRouter(prefix="/api/novels", tags=["novels"])
scanner = NovelScanner()


@router.get("", response_model=list[NovelListItem])
def list_novels():
    """List all novels across all platforms."""
    return scanner.list_novels()


@router.get("/{platform}/{name:path}", response_model=NovelOverview)
def get_novel(platform: str, name: str):
    """Get full Kanban state for one novel."""
    try:
        return scanner.scan_novel(platform, name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Novel not found: {platform}/{name} - {e}")


@router.get("/{platform}/{name:path}/state")
def get_novel_state(platform: str, name: str):
    """Get raw novel_state.json."""
    from utils.paths import get_novel_state_path
    from services.novel_scanner import load_json_safe

    state = load_json_safe(get_novel_state_path(platform, name))
    if not state:
        raise HTTPException(status_code=404, detail="novel_state.json not found")
    return state
