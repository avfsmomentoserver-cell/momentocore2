"""Placeholder router for agents."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_agents():
    return {"agents": ["orchestrator", "research", "helpdesk", "data_engineer"]}
