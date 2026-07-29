"""
FastAPI Application Entry Point.
Main API server with routers, middleware, and lifecycle events.
"""
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import init_db, close_db, get_db
from .routers import rounds, signals, sessions, agents

# Environment configuration
ENV = os.getenv("ENV", "development")
VERSION = "1.0.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"[STARTUP] Initializing MomentoCore API v{VERSION}...")
    await init_db()
    print("[STARTUP] Database connected")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Closing database connections...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="MomentoCore API",
    description="Military-grade algorithmic trading signal platform",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev
        "http://localhost:8000",  # API docs
        "*"  # Allow all in dev (restrict in prod)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(rounds.router, prefix="/api/v1/rounds", tags=["Rounds"])
app.include_router(signals.router, prefix="/api/v1/signals", tags=["Signals"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])

# Health Check Endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check for load balancers.
    """
    return {"status": "healthy", "version": VERSION}

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "MomentoCore API",
        "version": VERSION,
        "environment": ENV,
        "docs": "/docs",
        "health": "/health"
    }

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"[ERROR] Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "status_code": 500
    }
