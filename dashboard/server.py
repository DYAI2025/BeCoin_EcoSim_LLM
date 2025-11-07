"""
CEO Discovery Dashboard - FastAPI Server

This server provides REST and WebSocket APIs for the CEO Discovery Dashboard.
It integrates with the Becoin Economy system and supports autonomous agent operations.
"""
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)
security = HTTPBasic()

try:
    from dashboard import __version__
    from dashboard.ceo_data_bridge import CEODataBridge
    from dashboard.websocket_manager import WebSocketManager
except ModuleNotFoundError:
    # When running directly, dashboard module not in path
    __version__ = "1.0.0"
    from ceo_data_bridge import CEODataBridge
    from websocket_manager import WebSocketManager

# Load authentication credentials from environment
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
AUTH_ENABLED = bool(AUTH_USERNAME and AUTH_PASSWORD)

if not AUTH_ENABLED:
    logger.warning("⚠️  Authentication is DISABLED. Set AUTH_USERNAME and AUTH_PASSWORD environment variables to enable security.")
else:
    logger.info("✓ Authentication is ENABLED")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Verify HTTP Basic Auth credentials.

    Returns the username if valid, raises HTTPException if invalid.
    """
    if not AUTH_ENABLED:
        return "anonymous"

    # Use constant-time comparison to prevent timing attacks
    username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"),
        AUTH_USERNAME.encode("utf8")
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        AUTH_PASSWORD.encode("utf8")
    )

    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


# Initialize FastAPI app
app = FastAPI(
    title="CEO Discovery Dashboard",
    description="Real-time monitoring and control for autonomous AI agent firm",
    version=__version__
)

# Initialize data bridge and WebSocket manager
ceo_bridge = CEODataBridge()
ws_manager = WebSocketManager()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the dashboard directory path
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "becoin-economy"

# Mount static files directory if it exists
if STATIC_DIR.exists():
    app.mount("/becoin-economy", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard HTML page."""
    html_file = DASHBOARD_DIR / "office-ui.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
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
async def get_ceo_status(username: str = Depends(verify_credentials)):
    """Get current CEO Discovery session status."""
    return ceo_bridge.get_current_session()


@app.get("/api/ceo/proposals")
async def get_proposals(
    min_roi: float = Query(0.0, description="Minimum ROI threshold"),
    limit: int = Query(10, description="Maximum number of proposals"),
    username: str = Depends(verify_credentials)
):
    """Get CEO Discovery proposals with optional filtering."""
    return ceo_bridge.get_proposals(min_roi=min_roi, limit=limit)


@app.get("/api/ceo/patterns")
async def get_patterns(
    type: Optional[str] = Query(None, description="Filter by pattern type (repetitive, error, bottleneck, workflow)"),
    username: str = Depends(verify_credentials)
):
    """Get identified patterns, optionally filtered by type."""
    return ceo_bridge.get_patterns(pattern_type=type)


@app.get("/api/ceo/pain-points")
async def get_pain_points(username: str = Depends(verify_credentials)):
    """Get all identified pain points."""
    return ceo_bridge.get_pain_points()


@app.get("/api/ceo/history")
async def get_history(
    limit: int = Query(10, description="Maximum number of sessions to return"),
    username: str = Depends(verify_credentials)
):
    """Get historical discovery sessions."""
    return ceo_bridge.get_history(limit=limit)


# WebSocket Endpoint

@app.websocket("/ws/ceo")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time CEO Discovery updates.

    Clients connect to this endpoint to receive live updates about:
    - New proposals generated
    - Patterns discovered
    - Pain points identified
    - Status changes
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for any client messages
            # (currently we only broadcast server->client, but this allows bidirectional)
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")

            # Echo back for debugging (can be removed in production)
            await websocket.send_json({
                "type": "echo",
                "message": "Message received",
                "original": data
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
