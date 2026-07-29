"""Placeholder router for signals."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_signals():
    return {"signals": []}
