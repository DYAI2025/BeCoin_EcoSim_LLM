"""
CEO Discovery Dashboard - FastAPI Server

This server provides REST and WebSocket APIs for the CEO Discovery Dashboard.
It integrates with the Becoin Economy system and supports autonomous agent operations.
"""

import asyncio
from datetime import datetime, timezone
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Callable, Dict, List, Optional
import subprocess
import time
import urllib.request
import shutil
from pydantic import BaseModel
import logging
import os
import secrets
from pathlib import Path
import contextlib
import json

logger = logging.getLogger(__name__)
security = HTTPBasic(auto_error=False)  # Don't auto-raise 401 if no credentials

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
WS_POLL_INTERVAL = float(os.getenv("CEO_DASHBOARD_WS_POLL_INTERVAL", "5"))

if not AUTH_ENABLED:
    logger.warning(
        "⚠️  Authentication is DISABLED. Set AUTH_USERNAME and AUTH_PASSWORD environment variables to enable security."
    )
else:
    logger.info("✓ Authentication is ENABLED")


def verify_credentials(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
) -> str:
    """
    Verify HTTP Basic Auth credentials.

    Returns the username if valid, raises HTTPException if invalid.
    If AUTH is disabled, returns 'anonymous' without requiring credentials.
    """
    if not AUTH_ENABLED:
        return "anonymous"

    # If auth is enabled but no credentials provided
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Use constant-time comparison to prevent timing attacks
    username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"), AUTH_USERNAME.encode("utf8")
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"), AUTH_PASSWORD.encode("utf8")
    )

    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


# Pydantic models for chat
class ChatMessage(BaseModel):
    type: str
    content: str
    target_agent: str
    timestamp: str
    sender: str


# Initialize FastAPI app
app = FastAPI(
    title="CEO Discovery Dashboard",
    description="Real-time monitoring and control for autonomous AI agent firm",
    version=__version__,
)

# Initialize data bridge and WebSocket manager
DISCOVERY_SESSIONS_PATH = os.getenv(
    "DISCOVERY_SESSIONS_PATH", "../.claude-flow/discovery-sessions"
)
ceo_bridge = CEODataBridge(discovery_sessions_path=DISCOVERY_SESSIONS_PATH)
ws_manager = WebSocketManager()

# Chat storage (in-memory for now, can be moved to database later)
chat_messages: List[Dict] = []
chat_connections: List[WebSocket] = []
# Use chat_lock to protect all accesses (reads/writes) to chat_messages for concurrency safety.
chat_lock = asyncio.Lock()


def _ping_ollama() -> bool:
    """Return True if an Ollama instance responds on the default port."""

    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=1
        ) as response:
            return response.status == 200
    except Exception:
        return False


def _start_ollama() -> bool:
    """Attempt to start Ollama locally."""

    if _ping_ollama():
        return True

    if not shutil.which("ollama"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ollama binary not available in PATH",
        )

    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    time.sleep(2)
    return _ping_ollama()


def _write_economy_snapshot() -> bool:
    """Generate dashboard payload files using the economy engine."""

    from becoin_economy import (  # type: ignore
        Agent,
        BecoinEconomy,
        Project,
        Treasury,
        build_dashboard_payload,
    )

    treasury = Treasury(start_capital=10000, balance=8500)
    agents = [
        Agent(
            id="agent-001",
            name="Frontend Developer",
            role="Frontend",
            status="active",
            equity_share=0.25,
        ),
        Agent(
            id="agent-002",
            name="Backend Architect",
            role="Backend",
            status="active",
            equity_share=0.25,
        ),
        Agent(
            id="agent-003",
            name="AI Engineer",
            role="AI/ML",
            status="idle",
            equity_share=0.25,
        ),
        Agent(
            id="agent-004",
            name="DevOps Automator",
            role="DevOps",
            status="active",
            equity_share=0.25,
        ),
    ]
    projects = [
        Project(
            id="proj-001",
            name="Dashboard Redesign",
            stage="active",
            cost=2000,
            value=3000,
            impact_score=85,
            team=["agent-001"],
        ),
        Project(
            id="proj-002",
            name="API Integration",
            stage="completed",
            cost=1500,
            value=2500,
            impact_score=92,
            team=["agent-002"],
        ),
        Project(
            id="proj-003",
            name="CI/CD Pipeline",
            stage="active",
            cost=1800,
            value=2700,
            impact_score=78,
            team=["agent-004"],
        ),
        Project(
            id="proj-004",
            name="LLM Integration",
            stage="pipeline",
            cost=2500,
            value=4000,
            impact_score=95,
            team=[],
        ),
    ]

    economy = BecoinEconomy(
        treasury=treasury,
        agents=agents,
        projects=projects,
        baseline_hourly_burn=120.0,
    )

    payload = build_dashboard_payload(economy)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    for filename, data in payload.items():
        with open(STATIC_DIR / filename, "w") as fh:
            json.dump(data, fh, indent=2)

    return True


def _economy_payload_present() -> bool:
    """Check whether the dashboard payload exists."""

    required_files = [
        STATIC_DIR / "treasury.json",
        STATIC_DIR / "agent-roster.json",
        STATIC_DIR / "projects.json",
        STATIC_DIR / "impact-ledger.json",
        STATIC_DIR / "orchestrator-status.json",
    ]
    return all(path.exists() for path in required_files)


def _warm_autonomous_agents() -> bool:
    """Ensure autonomous agent modules are importable."""

    import autonomous_agents.orchestrator  # noqa: F401

    return True


def _ensure_chat_storage() -> bool:
    """Make sure chat history persistence is available."""

    CHAT_HISTORY_FILE.touch(exist_ok=True)
    load_chat_history()
    return True


ServiceChecker = Callable[[], bool]


SERVICES: Dict[str, Dict[str, object]] = {
    "becoin-server": {
        "name": "BeCoin Server",
        "description": "FastAPI-Dashboard mit Discovery- und Chat-Endpunkten.",
        "status_fn": lambda: True,
        "start_fn": lambda: True,
    },
    "ollama-llm": {
        "name": "Lokaler LLM (Ollama)",
        "description": "LLM-Endpunkt für autonome Agents über Ollama.",
        "status_fn": _ping_ollama,
        "start_fn": _start_ollama,
    },
    "becoin-economy": {
        "name": "BeCoin Economy Export",
        "description": "Schreibt aktuelle Treasury-, Agenten- und Projekt-Snapshots ins Dashboard.",
        "status_fn": _economy_payload_present,
        "start_fn": _write_economy_snapshot,
    },
    "autonomous-agents": {
        "name": "Autonome Agents",
        "description": "Persönlichkeiten und Orchestrator-Modul laden.",
        "status_fn": _warm_autonomous_agents,
        "start_fn": _warm_autonomous_agents,
    },
    "agent-chat": {
        "name": "Agent Chat",
        "description": "Speichert Chatverlauf und WebSocket-Kommunikation.",
        "status_fn": _ensure_chat_storage,
        "start_fn": _ensure_chat_storage,
    },
}


# Configure CORS
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://becoin-ecosim-llm.fly.dev",
    "https://becoin-ecosystem.fly.dev",
]


def _load_allowed_origins(env_value: Optional[str]) -> List[str]:
    """Return the CORS allowlist based on the provided environment value."""

    if env_value:
        if origins := [
            origin.strip() for origin in env_value.split(",") if origin.strip()
        ]:
            return origins
    return DEFAULT_ALLOWED_ORIGINS


ENV_ALLOWED_ORIGINS = os.getenv("DASHBOARD_ALLOW_ORIGINS")
ALLOWED_ORIGINS = _load_allowed_origins(ENV_ALLOWED_ORIGINS)
ALLOW_ALL_ORIGINS = "*" in ALLOWED_ORIGINS

# When allow_origins includes "*", FastAPI requires allow_credentials=False to avoid
# sending cookies/tokens to arbitrary origins. Otherwise credentials are permitted.
if ALLOW_ALL_ORIGINS:
    ALLOWED_ORIGINS = ["*"]
    ALLOW_CREDENTIALS = False
else:
    ALLOW_CREDENTIALS = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the dashboard directory path
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "becoin-economy"

# Chat history file path
CHAT_HISTORY_FILE = DASHBOARD_DIR / "chat_history.json"

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
            "status": "operational",
        }


@app.get("/api/status")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "operational",
        "service": "ceo-discovery-dashboard",
        "version": __version__,
    }


def _service_payload(service_id: str) -> Dict:
    """Return a serializable payload for a configured service."""

    service = SERVICES.get(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown service")

    status_fn: ServiceChecker = service["status_fn"]  # type: ignore[assignment]
    is_running = bool(status_fn())

    return {
        "id": service_id,
        "name": service.get("name", service_id),
        "description": service.get("description", ""),
        "status": "running" if is_running else "stopped",
        "startable": True,
    }


@app.get("/api/services")
async def list_services(username: str = Depends(verify_credentials)):
    """List configured runtime services with their current status."""

    return [_service_payload(service_id) for service_id in SERVICES]


@app.post("/api/services/{service_id}/start")
async def start_service(service_id: str, username: str = Depends(verify_credentials)):
    """Start a supported service if it is not already running."""

    service = SERVICES.get(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown service")

    start_fn: ServiceChecker = service["start_fn"]  # type: ignore[assignment]
    try:
        start_fn()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive catch for runtime ops
        logger.error("Failed to start %s: %s", service_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service {service_id} could not be started: {exc}",
        ) from exc

    return _service_payload(service_id)


# CEO Discovery Endpoints


@app.get("/api/ceo/status")
async def get_ceo_status(username: str = Depends(verify_credentials)):
    """Get current CEO Discovery session status."""
    return ceo_bridge.get_current_session()


@app.get("/api/ceo/proposals")
async def get_proposals(
    min_roi: float = Query(
        0.0,
        description="Minimum ROI threshold",
        ge=0.0,
        le=1000.0,
    ),
    limit: int = Query(
        10,
        description="Maximum number of proposals",
        ge=1,
        le=100,
    ),
    username: str = Depends(verify_credentials),
):
    """Get CEO Discovery proposals with optional filtering."""
    return ceo_bridge.get_proposals(min_roi=min_roi, limit=limit)


@app.get("/api/ceo/patterns")
async def get_patterns(
    type: Optional[str] = Query(
        None,
        description="Filter by pattern type (repetitive, error, bottleneck, workflow)",
    ),
    username: str = Depends(verify_credentials),
):
    """Get identified patterns, optionally filtered by type."""
    return ceo_bridge.get_patterns(pattern_type=type)


@app.get("/api/ceo/pain-points")
async def get_pain_points(username: str = Depends(verify_credentials)):
    """Get all identified pain points."""
    return ceo_bridge.get_pain_points()


@app.get("/api/ceo/history")
async def get_history(
    limit: int = Query(
        10,
        description="Maximum number of sessions to return",
        ge=1,
        le=100,
    ),
    username: str = Depends(verify_credentials),
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

    stream_task = asyncio.create_task(_stream_ceo_session_updates(websocket))

    try:
        while True:
            # Keep connection alive and listen for optional client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected normally")
    except Exception as e:  # pragma: no cover - safety net
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
    finally:
        stream_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await stream_task


async def _stream_ceo_session_updates(websocket: WebSocket) -> None:
    """Continuously push CEO session snapshots to clients."""

    last_signature = None

    while True:
        try:
            session = ceo_bridge.get_current_session()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to read CEO session for WebSocket: {exc}")
            await asyncio.sleep(WS_POLL_INTERVAL)
            continue

        signature = (
            session.get("session_id"),
            session.get("status"),
            len(session.get("proposals", [])),
            len(session.get("patterns", [])),
            len(session.get("pain_points", [])),
        )

        if signature != last_signature:
            await websocket.send_json(
                {
                    "type": "session_update",
                    "timestamp": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "session": session,
                }
            )
            last_signature = signature

        await asyncio.sleep(max(0.1, WS_POLL_INTERVAL))


# Chat Endpoints


def load_chat_history() -> List[Dict]:
    """Load chat history from file."""
    global chat_messages
    try:
        if CHAT_HISTORY_FILE.exists():
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                chat_messages = json.load(f)
                logger.info(f"Loaded {len(chat_messages)} chat messages from history")
        else:
            chat_messages = []
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        chat_messages = []
    return chat_messages


def save_chat_history():
    """Save chat history to file."""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_messages, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(chat_messages)} chat messages to history")
    except Exception as e:
        logger.error(f"Error saving chat history: {e}")


def _build_agent_response_content(user_message: str) -> str:
    """Create a contextual agent reply using the latest discovery session data."""

    session = ceo_bridge.get_current_session()

    if session.get("status") == "idle":
        return (
            "Nachricht erhalten. Aktuell liegen keine Discovery-Daten vor; "
            "ich gebe Bescheid, sobald neue Erkenntnisse verfügbar sind."
        )

    proposals = session.get("proposals", [])
    patterns = session.get("patterns", [])
    pain_points = session.get("pain_points", [])

    parts = [f"Nachricht erhalten: '{user_message}'."]

    if proposals:
        top = max(proposals, key=lambda p: p.get("roi", 0))
        parts.append(
            "Top-Vorschlag: {title} (ROI {roi}x, Zeitplan {timeline}, Kosten {cost}).".format(
                title=top.get("title", ""),
                roi=top.get("roi", "?"),
                timeline=top.get("timeline", "unbekannt"),
                cost=top.get("cost_becoins", "unbekannt"),
            )
        )

    if pain_points:
        primary = pain_points[0]
        parts.append(
            "Wichtigster Pain Point: {title} (≈{time} Min/Woche, Schwere {severity}).".format(
                title=primary.get("title", "Unbekannt"),
                time=primary.get("time_cost_minutes", "?"),
                severity=primary.get("severity", "?"),
            )
        )

    if patterns:
        pattern = patterns[0]
        parts.append(
            "Beobachtetes Muster: {description}".format(
                description=pattern.get("description", ""),
            )
        )

    parts.append("Ich setze die genannten Maßnahmen jetzt um und melde Fortschritt im Chat.")

    return " ".join(parts)


def _create_agent_message(target_agent: str, user_content: str) -> Dict:
    """Build an agent response payload enriched with discovery insights."""

    content = _build_agent_response_content(user_content)
    return {
        "type": "agent_message",
        "content": content,
        "target_agent": target_agent,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": target_agent,
    }


@app.get("/api/chat/history")
async def get_chat_history(
    limit: int = Query(100, description="Maximum number of messages", ge=1, le=1000),
    username: str = Depends(verify_credentials),
):
    """Get chat message history."""
    load_chat_history()
    return {"messages": chat_messages[-limit:] if chat_messages else []}


@app.post("/api/chat/send")
async def send_chat_message(
    message: ChatMessage, username: str = Depends(verify_credentials)
):
    """Send a chat message (REST API fallback)."""
    message_dict = message.model_dump()
    chat_messages.append(message_dict)
    save_chat_history()

    # Broadcast to all connected chat WebSocket clients
    await broadcast_to_chat_clients(message_dict)

    if message.target_agent != "all":
        agent_response = _create_agent_message(
            target_agent=message.target_agent, user_content=message.content
        )
        chat_messages.append(agent_response)
        save_chat_history()
        await broadcast_to_chat_clients(agent_response)

    return {"status": "sent", "message": message_dict}


async def broadcast_to_chat_clients(message: Dict):
    """Broadcast message to all connected chat clients."""
    disconnected = []
    for connection in chat_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to chat client: {e}")
            disconnected.append(connection)

    # Clean up disconnected clients
    for connection in disconnected:
        if connection in chat_connections:
            chat_connections.remove(connection)


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for bidirectional chat communication.

    Clients connect to this endpoint to send and receive chat messages
    in real-time with agents.
    """
    await websocket.accept()
    chat_connections.append(websocket)
    logger.info(f"Chat WebSocket connected. Total connections: {len(chat_connections)}")

    # Send welcome message and chat history
    await websocket.send_json(
        {
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": "Chat verbunden - Sie können jetzt mit Agenten kommunizieren",
        }
    )

    # Send recent chat history
    load_chat_history()
    if chat_messages:
        await websocket.send_json(
            {"type": "chat_history", "messages": chat_messages[-50:]}
        )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Store message
            chat_messages.append(message)
            save_chat_history()

            # Broadcast to other clients
            await broadcast_to_chat_clients(message)

            if message.get("target_agent") and message.get("target_agent") != "all":
                agent_response = _create_agent_message(
                    target_agent=message.get("target_agent", "Agent"),
                    user_content=message.get("content", ""),
                )
                chat_messages.append(agent_response)
                save_chat_history()
                await broadcast_to_chat_clients(agent_response)

    except WebSocketDisconnect:
        chat_connections.remove(websocket)
        logger.info(
            f"Chat WebSocket disconnected. Total connections: {len(chat_connections)}"
        )
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        if websocket in chat_connections:
            chat_connections.remove(websocket)


# Load chat history on startup
@app.on_event("startup")
async def startup_event():
    """Load chat history on application startup."""
    load_chat_history()
    logger.info("Application started, chat history loaded")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)
