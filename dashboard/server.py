"""
CEO Discovery Dashboard - FastAPI Server

This server provides REST and WebSocket APIs for the CEO Discovery Dashboard.
It integrates with the Becoin Economy system and supports autonomous agent operations.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

try:
    from dashboard import __version__
    from dashboard.ceo_data_bridge import CEODataBridge
except ModuleNotFoundError:
    # When running directly, dashboard module not in path
    __version__ = "1.0.0"
    from ceo_data_bridge import CEODataBridge


# Initialize FastAPI app
app = FastAPI(
    title="CEO Discovery Dashboard",
    description="Real-time monitoring and control for autonomous AI agent firm",
    version=__version__
)

# Initialize data bridge
ceo_bridge = CEODataBridge()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - provides service information."""
    return {
        "message": "CEO Discovery Dashboard API",
        "version": __version__,
        "service": "ceo-discovery-dashboard",
        "status": "operational"
    }


@app.get("/api/status")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "operational",
        "service": "ceo-discovery-dashboard",
        "version": __version__
    }


# CEO Discovery Endpoints

@app.get("/api/ceo/status")
async def get_ceo_status():
    """Get current CEO Discovery session status."""
    return ceo_bridge.get_current_session()


@app.get("/api/ceo/proposals")
async def get_proposals(
    min_roi: float = Query(0.0, description="Minimum ROI threshold"),
    limit: int = Query(10, description="Maximum number of proposals")
):
    """Get CEO Discovery proposals with optional filtering."""
    return ceo_bridge.get_proposals(min_roi=min_roi, limit=limit)


@app.get("/api/ceo/patterns")
async def get_patterns(
    type: Optional[str] = Query(None, description="Filter by pattern type (repetitive, error, bottleneck, workflow)")
):
    """Get identified patterns, optionally filtered by type."""
    return ceo_bridge.get_patterns(pattern_type=type)


@app.get("/api/ceo/pain-points")
async def get_pain_points():
    """Get all identified pain points."""
    return ceo_bridge.get_pain_points()


@app.get("/api/ceo/history")
async def get_history(
    limit: int = Query(10, description="Maximum number of sessions to return")
):
    """Get historical discovery sessions."""
    return ceo_bridge.get_history(limit=limit)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
