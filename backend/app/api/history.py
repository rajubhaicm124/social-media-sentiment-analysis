"""History and profile endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import repository
from app.core.errors import NotFoundError
from app.database import get_db
from app.schemas import ProfileRequest

router = APIRouter(tags=["history"])


@router.get("/history")
def get_history(
    user_name: str | None = None,
    platform: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List saved analyses, newest first."""
    return {"analyses": repository.list_history(db, user_name=user_name, platform=platform, limit=limit)}


@router.get("/history/{analysis_id}")
def get_history_item(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()
    return repository.history_row(analysis)


@router.delete("/history/{analysis_id}")
def delete_history(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete an analysis and its records."""
    if not repository.delete_analysis(db, analysis_id):
        raise NotFoundError()
    return {"deleted": True, "analysis_id": analysis_id}


@router.get("/profile/{user_name}")
def get_profile(user_name: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Aggregate profile statistics for the dashboard header and settings page."""
    return repository.user_stats(db, user_name)


@router.get("/profile")
def get_profile_default(user_name: str | None = Query(default=None), db: Session = Depends(get_db)) -> dict[str, Any]:
    return repository.user_stats(db, user_name)


@router.post("/profile/rename")
def rename_profile(payload: ProfileRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Reassign stored analyses from ``previous_name`` to the new display name."""
    from sqlalchemy import update

    from app.models import Analysis

    new_name = payload.user_name
    previous = payload.previous_name
    if previous and previous != new_name:
        moved = db.execute(
            update(Analysis).where(Analysis.user_name == previous).values(user_name=new_name)
        )
        db.commit()
        if moved.rowcount:
            return {"renamed": True, "user_name": new_name, "analyses_moved": moved.rowcount}
        return {
            "renamed": False,
            "user_name": new_name,
            "message": "No stored analyses were associated with the previous name.",
        }
    return {
        "renamed": True,
        "user_name": new_name,
        "analyses_moved": 0,
        "message": "Display name updated locally; no stored analyses needed reassignment.",
    }
