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
from typing import List, Optional, Dict
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
    from dashboard.llm_bridge import get_llm_bridge
    from dashboard.economy_bridge import get_economy_bridge
except ModuleNotFoundError:
    # When running directly, dashboard module not in path
    __version__ = "1.0.0"
    from ceo_data_bridge import CEODataBridge
    from websocket_manager import WebSocketManager
    from llm_bridge import get_llm_bridge
    from economy_bridge import get_economy_bridge

# Import personality loader
import sys
sys.path.append(str(Path(__file__).parent.parent / "autonomous_agents"))
try:
    from personalities.loader import load_personalities
    personality_loader = load_personalities()
    logger.info(f"✅ Loaded {len(personality_loader.personalities)} personalities")
except Exception as e:
    logger.warning(f"⚠️  Could not load personalities: {e}")
    personality_loader = None

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

# Economy integration
economy_lock = asyncio.Lock()  # For thread-safe economy operations


def load_or_create_economy():
    """
    Load existing BecoinEconomy instance or create a new one.

    Tries to:
    1. Load from existing JSON files in dashboard/becoin-economy/
    2. If not found, create a fresh economy with sensible defaults

    Returns:
        BecoinEconomy instance or None if unavailable
    """
    try:
        # Try to import BeCoin Economy
        import sys
        becoin_path = Path(__file__).parent.parent / "becoin_economy"
        if str(becoin_path) not in sys.path:
            sys.path.insert(0, str(becoin_path))

        from becoin_economy.engine import BecoinEconomy
        from becoin_economy.models import Treasury, Agent, Project

        # Check if we have existing economy data
        treasury_file = STATIC_DIR / "treasury.json"

        if treasury_file.exists():
            # Load from existing files
            logger.info("Loading existing economy from JSON files...")
            import json

            with open(treasury_file, 'r') as f:
                treasury_data = json.load(f)

            # Create treasury
            treasury = Treasury(
                balance=treasury_data.get("balance", 10000),
                start_capital=treasury_data.get("start_capital", 10000)
            )

            # Load agents from agent-roster.json
            agents = []
            roster_file = STATIC_DIR / "agent-roster.json"
            if roster_file.exists():
                with open(roster_file, 'r') as f:
                    roster_data = json.load(f)

                # Get all agents (founders + employees)
                all_agents = roster_data.get("founders", []) + roster_data.get("employees", [])

                for agent_data in all_agents:
                    agent = Agent(
                        id=agent_data.get("id", "unknown"),
                        name=agent_data.get("name", "Unknown"),
                        role=agent_data.get("agent_type", "autonomous"),  # BeCoin uses 'role' not 'agent_type'
                        status=agent_data.get("status", "idle"),
                        equity_share=agent_data.get("equityShare", 0.0)
                    )
                    agents.append(agent)

            # Load projects
            projects = []
            projects_file = STATIC_DIR / "projects.json"
            if projects_file.exists():
                with open(projects_file, 'r') as f:
                    projects_data = json.load(f)

                # Load active and pipeline projects
                for stage in ["active", "pipeline"]:
                    for proj_data in projects_data.get(stage, []):
                        project = Project(
                            id=proj_data.get("id", "unknown"),
                            name=proj_data.get("name", "Unknown Project"),
                            stage=stage,  # BeCoin uses 'stage' not 'status'
                            cost=proj_data.get("cost", 0),
                            value=proj_data.get("value", 0),
                            impact_score=proj_data.get("impactScore", 0),
                            team=proj_data.get("team", [])
                        )
                        projects.append(project)

            economy = BecoinEconomy(
                treasury=treasury,
                agents=agents if agents else None,
                projects=projects if projects else None
            )

            logger.info(f"✅ Loaded economy: {len(agents)} agents, {len(projects)} projects, {treasury.balance} Bc")
            return economy

        else:
            # Create fresh economy with defaults
            logger.info("Creating fresh economy with defaults...")

            treasury = Treasury(
                balance=10000,
                start_capital=10000
            )

            # Create default agents matching dashboard
            agents = [
                Agent(
                    id="agent-helio",
                    name="Helio",
                    role="Product Manager",
                    status="active",
                    equity_share=0.25
                ),
                Agent(
                    id="agent-nami",
                    name="Nami",
                    role="Backend Developer",
                    status="active",
                    equity_share=0.25
                ),
                Agent(
                    id="agent-atlas",
                    name="Atlas",
                    role="Financial Analyst",
                    status="active",
                    equity_share=0.25
                ),
                Agent(
                    id="agent-circe",
                    name="Circe",
                    role="DevOps Engineer",
                    status="active",
                    equity_share=0.25
                )
            ]

            economy = BecoinEconomy(
                treasury=treasury,
                agents=agents,
                projects=[]
            )

            logger.info(f"✅ Created fresh economy: 4 agents, 0 projects, 10000 Bc")
            return economy

    except ImportError as e:
        logger.error(f"❌ Could not import BeCoin Economy: {e}")
        logger.warning("⚠️  Economy Bridge will run in MOCK mode")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading/creating economy: {e}")
        logger.warning("⚠️  Economy Bridge will run in MOCK mode")
        return None


# Chat storage (in-memory for now, can be moved to database later)
chat_messages: List[Dict] = []
chat_connections: List[WebSocket] = []
chat_lock = asyncio.Lock()

# Chat history limit (prevent memory leaks)
MAX_CHAT_MESSAGES = 1000

# Global economy instance
economy_instance = None

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
        origins = [origin.strip() for origin in env_value.split(",") if origin.strip()]
        if origins:
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
    """Save chat history to file with automatic trimming."""
    global chat_messages
    try:
        # Trim history if it exceeds MAX_CHAT_MESSAGES (prevent memory leaks)
        if len(chat_messages) > MAX_CHAT_MESSAGES:
            trimmed_count = len(chat_messages) - MAX_CHAT_MESSAGES
            chat_messages = chat_messages[-MAX_CHAT_MESSAGES:]
            logger.info(f"Trimmed {trimmed_count} old messages (limit: {MAX_CHAT_MESSAGES})")

        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(chat_messages, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {len(chat_messages)} chat messages to history")
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


def _get_economy_context() -> Dict:
    """
    Lädt aktuellen Economy-Context für LLM-Prompts.

    Returns:
        Dict mit Treasury, Projekten, Metriken
    """
    economy_bridge = get_economy_bridge()
    return economy_bridge.get_context_for_chat()


async def _create_agent_message(target_agent: str, user_content: str) -> Dict:
    """
    Erstellt Agent-Antwort via Ollama LLM.

    Args:
        target_agent: Agent-ID (z.B. "agent-helio")
        user_content: User-Nachricht

    Returns:
        Agent-Nachricht als Dict
    """
    llm_bridge = get_llm_bridge()

    # Check Ollama health
    is_healthy = await llm_bridge.check_ollama_health()

    if not is_healthy:
        logger.warning("Ollama not available, using fallback response")
        # Fallback to old behavior
        content = _build_agent_response_content(user_content)
        return {
            "type": "agent_message",
            "content": f"⚠️ LLM-Service offline. Fallback-Antwort: {content}",
            "target_agent": target_agent,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sender": target_agent,
            "llm_enabled": False
        }

    # Load personality
    personality = None
    if personality_loader:
        personality = personality_loader.get_personality_for_dashboard_agent(target_agent)

    if not personality:
        logger.warning(f"No personality found for {target_agent}, using default")
        personality = {
            "name": target_agent,
            "role": "AI Agent",
            "expertise": ["General"],
            "communication_style": "Professionell"
        }

    # Load economy context
    economy_context = _get_economy_context()

    # Generate LLM response
    try:
        llm_response = await llm_bridge.generate_agent_response(
            agent_id=target_agent,
            agent_personality=personality,
            user_message=user_content,
            context=economy_context
        )

        # Parse actions from response
        actions = llm_bridge.parse_agent_actions(llm_response)

        return {
            "type": "agent_message",
            "content": llm_response,
            "target_agent": target_agent,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sender": target_agent,
            "llm_enabled": True,
            "personality": personality["name"],
            "actions": actions if actions else []
        }

    except Exception as e:
        logger.error(f"Error generating LLM response for {target_agent}: {e}")
        # Fallback
        content = _build_agent_response_content(user_content)
        return {
            "type": "agent_message",
            "content": f"⚠️ Fehler bei LLM: {content}",
            "target_agent": target_agent,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sender": target_agent,
            "llm_enabled": False,
            "error": str(e)
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
        agent_response = await _create_agent_message(
            target_agent=message.target_agent, user_content=message.content
        )

        # Execute actions if any (with economy lock for concurrency safety)
        actions = agent_response.get("actions", [])
        if actions:
            economy_bridge = get_economy_bridge()
            action_results = []

            # Use lock to prevent concurrent economy modifications
            async with economy_lock:
                for action in actions:
                    result = economy_bridge.execute_agent_action(
                        agent_id=message.target_agent,
                        action=action
                    )
                    action_results.append(result)

                    logger.info(f"Action executed: {action['type']} -> {result['status']}")

            # Append action results to agent response
            if action_results:
                result_messages = "\n\n".join([r["message"] for r in action_results])
                agent_response["content"] += f"\n\n**Aktionen ausgeführt:**\n{result_messages}"
                agent_response["action_results"] = action_results

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
                agent_response = await _create_agent_message(
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
    """Initialize economy, check services, and load chat history on startup."""
    global economy_instance

    # 1. Load or create economy
    logger.info("=" * 60)
    logger.info("🚀 Starting Dashboard Server...")
    logger.info("=" * 60)

    economy_instance = load_or_create_economy()

    if economy_instance:
        # Set economy in economy_bridge
        from dashboard.economy_bridge import set_economy_instance
        set_economy_instance(economy_instance)
        logger.info("✅ Economy Bridge connected to live economy")
    else:
        logger.warning("⚠️  Economy Bridge running in MOCK mode (no economy available)")

    # 2. Check Ollama health
    llm_bridge = get_llm_bridge()
    is_ollama_healthy = await llm_bridge.check_ollama_health()

    if is_ollama_healthy:
        logger.info(f"✅ Ollama LLM available (model: {llm_bridge.model})")
    else:
        logger.warning("⚠️  Ollama LLM NOT available!")
        logger.warning("   → Chat will use fallback responses (no AI generation)")
        logger.warning("   → Start Ollama with: ollama serve")
        logger.warning(f"   → Required model: {llm_bridge.model}")

    # 3. Load chat history
    load_chat_history()
    logger.info(f"✅ Loaded {len(chat_messages)} chat messages from history")

    logger.info("=" * 60)
    logger.info("✅ Dashboard Server ready!")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)
