"""
Rounds API Router.
Endpoints for ingesting and querying round data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from core.data_core.storage.database import get_db
from core.data_core.storage.models import Round

router = APIRouter()

@router.post("/", summary="Ingest a new round")
async def ingest_round(
    round_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a single round of data.
    Validates uniqueness via hash.
    """
    # Check for duplicates
    existing = await db.execute(
        select(Round).where(Round.hash == round_data.get("hash"))
    )
    if existing.scalar_one_or_none():
        return {"status": "duplicate", "round_id": round_data.get("round_id")}
    
    # Create new round
    new_round = Round(**round_data)
    db.add(new_round)
    await db.flush()
    
    return {
        "status": "created",
        "round_id": new_round.round_id,
        "id": new_round.id
    }

@router.get("/", summary="List rounds with pagination")
async def list_rounds(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    color: Optional[str] = None,
    band: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve paginated list of rounds.
    Filter by color/band optionally.
    """
    query = select(Round)
    
    if color:
        query = query.where(Round.color == color.lower())
    if band:
        query = query.where(Round.band == band.lower())
    
    query = query.order_by(Round.timestamp.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    rounds = result.scalars().all()
    
    return {
        "count": len(rounds),
        "offset": offset,
        "limit": limit,
        "data": [
            {
                "id": r.id,
                "round_id": r.round_id,
                "multiplier": r.multiplier,
                "color": r.color,
                "band": r.band,
                "timestamp": r.timestamp.isoformat()
            }
            for r in rounds
        ]
    }

@router.get("/stats", summary="Get aggregate statistics")
async def get_stats(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregate statistics for recent rounds.
    """
    cutoff = datetime.utcnow()
    
    result = await db.execute(
        select(
            func.count(Round.id),
            func.avg(Round.multiplier),
            func.max(Round.multiplier),
            func.min(Round.multiplier)
        ).where(Round.timestamp >= cutoff)
    )
    count, avg, max_val, min_val = result.one()
    
    return {
        "period_hours": hours,
        "round_count": count or 0,
        "avg_multiplier": float(avg) if avg else 0.0,
        "max_multiplier": float(max_val) if max_val else 0.0,
        "min_multiplier": float(min_val) if min_val else 0.0
    }

@router.get("/{round_id}", summary="Get specific round")
async def get_round(
    round_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific round by external ID.
    """
    result = await db.execute(
        select(Round).where(Round.round_id == round_id)
    )
    round_obj = result.scalar_one_or_none()
    
    if not round_obj:
        raise HTTPException(status_code=404, detail="Round not found")
    
    return {
        "id": round_obj.id,
        "round_id": round_obj.round_id,
        "multiplier": round_obj.multiplier,
        "color": round_obj.color,
        "band": round_obj.band,
        "timestamp": round_obj.timestamp.isoformat(),
        "source": round_obj.source
    }
