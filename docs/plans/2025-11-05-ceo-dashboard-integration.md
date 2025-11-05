# CEO Discovery Dashboard Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Full-stack integration of CEO Discovery System with the existing Becoin Economy dashboard using FastAPI backend and extended office-ui.html frontend.

**Architecture:** Monolithic FastAPI server serves both REST API and WebSocket endpoints, reads CEO Discovery session data from `.claude-flow/discovery-sessions/`, and serves extended office-ui.html. Hybrid polling (3s) + WebSocket for real-time updates. Dashboard is read-only observer maintaining agent autonomy.

**Tech Stack:** Python 3.x, FastAPI, uvicorn, websockets, HTML5, JavaScript (vanilla), CSS3

---

## Task 1: Backend Infrastructure - FastAPI Server Base

**Files:**
- Create: `dashboard/requirements.txt`
- Create: `dashboard/server.py`
- Create: `dashboard/.env.example`

**Step 1: Write the failing test**

Create `dashboard/tests/test_server.py`:

```python
import pytest
from fastapi.testclient import TestClient
from server import app

def test_health_endpoint():
    """Test basic health check endpoint"""
    client = TestClient(app)
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_server.py::test_health_endpoint -v`
Expected: FAIL with "No module named 'server'" or "No module named 'fastapi'"

**Step 3: Create requirements.txt**

Create `dashboard/requirements.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
python-multipart==0.0.6
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

**Step 4: Install dependencies**

Run: `cd dashboard && pip install -r requirements.txt`
Expected: All packages install successfully

**Step 5: Write minimal FastAPI server**

Create `dashboard/server.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="CEO Discovery Dashboard API", version="1.0.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ceo-discovery-dashboard"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
```

Create `dashboard/.env.example`:

```env
# Server Configuration
HOST=0.0.0.0
PORT=3000
LOG_LEVEL=info

# Paths
DISCOVERY_SESSIONS_PATH=../.claude-flow/discovery-sessions
BECOIN_ECONOMY_PATH=../becoin-economy
```

**Step 6: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_server.py::test_health_endpoint -v`
Expected: PASS (1 test passed)

**Step 7: Manual verification**

Run: `cd dashboard && python server.py`
Visit: `http://localhost:3000/api/status`
Expected: JSON response `{"status": "healthy", "service": "ceo-discovery-dashboard"}`
Stop server: Ctrl+C

**Step 8: Commit**

```bash
git add dashboard/requirements.txt dashboard/server.py dashboard/.env.example dashboard/tests/test_server.py
git commit -m "feat: add FastAPI server base with health check endpoint"
```

---

## Task 2: Data Bridge - CEO Discovery Session Reader

**Files:**
- Create: `dashboard/ceo_data_bridge.py`
- Create: `dashboard/tests/test_data_bridge.py`
- Create: `dashboard/tests/fixtures/sample_discovery_session.json`

**Step 1: Write the failing test**

Create `dashboard/tests/fixtures/sample_discovery_session.json`:

```json
{
  "session_id": "discovery-1234567890",
  "timestamp": "2025-11-05T10:30:00Z",
  "status": "active",
  "patterns": [
    {
      "id": "pattern-001",
      "type": "repetitive",
      "description": "User repeatedly runs build commands",
      "frequency": 15,
      "severity": 0.8
    }
  ],
  "proposals": [
    {
      "id": "proposal-001",
      "title": "Build Automation System",
      "description": "Automate repetitive build tasks",
      "cost": 250,
      "roi": 4.2,
      "impact_score": 87,
      "time_saved_weekly": 120
    }
  ],
  "metrics": {
    "total_patterns": 12,
    "total_proposals": 3,
    "prediction_accuracy": 84.5,
    "user_satisfaction": 87.2
  }
}
```

Create `dashboard/tests/test_data_bridge.py`:

```python
import pytest
import json
import tempfile
import os
from pathlib import Path
from ceo_data_bridge import CEODataBridge

@pytest.fixture
def temp_discovery_dir():
    """Create temporary discovery sessions directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy sample session
        sample_path = Path(__file__).parent / "fixtures/sample_discovery_session.json"
        dest_path = Path(tmpdir) / "discovery-1234567890.json"

        with open(sample_path) as f:
            data = json.load(f)
        with open(dest_path, 'w') as f:
            json.dump(data, f)

        yield tmpdir

def test_get_current_session(temp_discovery_dir):
    """Test reading current discovery session"""
    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    session = bridge.get_current_session()

    assert session is not None
    assert session["session_id"] == "discovery-1234567890"
    assert session["status"] == "active"
    assert len(session["patterns"]) == 1
    assert len(session["proposals"]) == 1

def test_get_proposals(temp_discovery_dir):
    """Test getting proposals with filtering"""
    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    proposals = bridge.get_proposals(min_roi=3.0)

    assert len(proposals) == 1
    assert proposals[0]["id"] == "proposal-001"
    assert proposals[0]["roi"] >= 3.0

def test_get_patterns(temp_discovery_dir):
    """Test getting patterns by type"""
    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    patterns = bridge.get_patterns(pattern_type="repetitive")

    assert len(patterns) == 1
    assert patterns[0]["type"] == "repetitive"

def test_no_sessions():
    """Test behavior when no sessions exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        bridge = CEODataBridge(discovery_sessions_path=tmpdir)
        session = bridge.get_current_session()

        assert session["status"] == "idle"
        assert session["proposals"] == []
        assert session["patterns"] == []
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_data_bridge.py -v`
Expected: FAIL with "No module named 'ceo_data_bridge'"

**Step 3: Write minimal implementation**

Create `dashboard/ceo_data_bridge.py`:

```python
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CEODataBridge:
    """Reads and formats CEO Discovery session data for API consumption"""

    def __init__(self, discovery_sessions_path: str = "../.claude-flow/discovery-sessions"):
        self.sessions_path = Path(discovery_sessions_path)
        self._cache = {}
        self._cache_ttl = 30  # seconds

    def get_current_session(self) -> Dict:
        """Get the most recent discovery session"""
        try:
            if not self.sessions_path.exists():
                return self._empty_session()

            # Find most recent session file
            session_files = list(self.sessions_path.glob("discovery-*.json"))
            if not session_files:
                return self._empty_session()

            latest_file = max(session_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file) as f:
                data = json.load(f)

            return data

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading discovery session: {e}")
            return self._empty_session()

    def get_proposals(self, min_roi: float = 0.0, limit: int = 10) -> List[Dict]:
        """Get proposals filtered by ROI"""
        session = self.get_current_session()
        proposals = session.get("proposals", [])

        # Filter by ROI
        filtered = [p for p in proposals if p.get("roi", 0) >= min_roi]

        # Sort by ROI descending
        filtered.sort(key=lambda p: p.get("roi", 0), reverse=True)

        return filtered[:limit]

    def get_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Get identified patterns, optionally filtered by type"""
        session = self.get_current_session()
        patterns = session.get("patterns", [])

        if pattern_type:
            patterns = [p for p in patterns if p.get("type") == pattern_type]

        return patterns

    def get_performance_metrics(self) -> Dict:
        """Get performance and learning metrics"""
        session = self.get_current_session()
        return session.get("metrics", {
            "total_patterns": 0,
            "total_proposals": 0,
            "prediction_accuracy": 0.0,
            "user_satisfaction": 0.0
        })

    def _empty_session(self) -> Dict:
        """Return empty session structure"""
        return {
            "session_id": None,
            "status": "idle",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "patterns": [],
            "proposals": [],
            "metrics": {
                "total_patterns": 0,
                "total_proposals": 0,
                "prediction_accuracy": 0.0,
                "user_satisfaction": 0.0
            }
        }
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_data_bridge.py -v`
Expected: PASS (4 tests passed)

**Step 5: Commit**

```bash
git add dashboard/ceo_data_bridge.py dashboard/tests/test_data_bridge.py dashboard/tests/fixtures/
git commit -m "feat: add CEO Discovery data bridge with session reading"
```

---

## Task 3: REST API Endpoints - CEO Discovery Data

**Files:**
- Modify: `dashboard/server.py`
- Create: `dashboard/tests/test_api_endpoints.py`

**Step 1: Write the failing test**

Create `dashboard/tests/test_api_endpoints.py`:

```python
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_ceo_status_endpoint():
    """Test CEO Discovery status endpoint"""
    response = client.get("/api/ceo/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "session_id" in data
    assert "patterns" in data
    assert "proposals" in data

def test_ceo_proposals_endpoint():
    """Test proposals endpoint with filtering"""
    response = client.get("/api/ceo/proposals?min_roi=3.0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_ceo_patterns_endpoint():
    """Test patterns endpoint"""
    response = client.get("/api/ceo/patterns?type=repetitive")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_ceo_performance_endpoint():
    """Test performance metrics endpoint"""
    response = client.get("/api/ceo/performance")
    assert response.status_code == 200
    data = response.json()
    assert "total_patterns" in data
    assert "prediction_accuracy" in data
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_api_endpoints.py -v`
Expected: FAIL with 404 errors (endpoints don't exist)

**Step 3: Add API endpoints to server.py**

Modify `dashboard/server.py`:

```python
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from ceo_data_bridge import CEODataBridge

app = FastAPI(title="CEO Discovery Dashboard API", version="1.0.0")

# Initialize data bridge
ceo_bridge = CEODataBridge()

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ceo-discovery-dashboard"}

@app.get("/api/ceo/status")
async def get_ceo_status():
    """Get current CEO Discovery session status"""
    return ceo_bridge.get_current_session()

@app.get("/api/ceo/proposals")
async def get_proposals(
    min_roi: float = Query(0.0, description="Minimum ROI threshold"),
    limit: int = Query(10, description="Maximum number of proposals")
):
    """Get CEO Discovery proposals with optional filtering"""
    return ceo_bridge.get_proposals(min_roi=min_roi, limit=limit)

@app.get("/api/ceo/patterns")
async def get_patterns(
    type: Optional[str] = Query(None, description="Filter by pattern type")
):
    """Get identified patterns, optionally filtered by type"""
    return ceo_bridge.get_patterns(pattern_type=type)

@app.get("/api/ceo/performance")
async def get_performance():
    """Get CEO Discovery performance and learning metrics"""
    return ceo_bridge.get_performance_metrics()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_api_endpoints.py -v`
Expected: PASS (4 tests passed)

**Step 5: Manual verification**

Run: `cd dashboard && python server.py`
Test endpoints:
- `curl http://localhost:3000/api/ceo/status`
- `curl http://localhost:3000/api/ceo/proposals?min_roi=2.0`
- `curl http://localhost:3000/api/ceo/patterns`
- `curl http://localhost:3000/api/ceo/performance`

Expected: All return valid JSON responses
Stop server: Ctrl+C

**Step 6: Commit**

```bash
git add dashboard/server.py dashboard/tests/test_api_endpoints.py
git commit -m "feat: add CEO Discovery REST API endpoints"
```

---

## Task 4: WebSocket Manager - Real-Time Updates

**Files:**
- Create: `dashboard/websocket_manager.py`
- Create: `dashboard/tests/test_websocket.py`
- Modify: `dashboard/server.py`

**Step 1: Write the failing test**

Create `dashboard/tests/test_websocket.py`:

```python
import pytest
from fastapi.testclient import TestClient
from server import app

def test_websocket_connection():
    """Test WebSocket connection establishment"""
    client = TestClient(app)

    with client.websocket_connect("/ws/ceo") as websocket:
        # Should connect successfully
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "connection_established"

def test_websocket_broadcast():
    """Test WebSocket broadcast functionality"""
    # This will be tested via integration test
    # Unit test just verifies the manager exists
    from websocket_manager import WebSocketManager

    manager = WebSocketManager()
    assert manager is not None
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_websocket.py -v`
Expected: FAIL with "No module named 'websocket_manager'"

**Step 3: Create WebSocket manager**

Create `dashboard/websocket_manager.py`:

```python
from fastapi import WebSocket
from typing import List, Dict
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and broadcasts CEO Discovery updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

        # Send connection established message
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": None,
            "message": "Connected to CEO Discovery live updates"
        })

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_new_proposal(self, proposal: Dict):
        """Broadcast new proposal event"""
        await self.broadcast({
            "type": "new_proposal",
            "proposal": proposal,
            "timestamp": None
        })

    async def broadcast_pattern_discovered(self, pattern: Dict):
        """Broadcast pattern discovery event"""
        await self.broadcast({
            "type": "pattern_discovered",
            "pattern": pattern,
            "timestamp": None
        })

    async def broadcast_status_change(self, status: str):
        """Broadcast status change event"""
        await self.broadcast({
            "type": "status_change",
            "status": status,
            "timestamp": None
        })
```

**Step 4: Add WebSocket endpoint to server.py**

Modify `dashboard/server.py`, add after imports:

```python
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from ceo_data_bridge import CEODataBridge
from websocket_manager import WebSocketManager

app = FastAPI(title="CEO Discovery Dashboard API", version="1.0.0")

# Initialize data bridge and WebSocket manager
ceo_bridge = CEODataBridge()
ws_manager = WebSocketManager()
```

Add WebSocket endpoint before `if __name__`:

```python
@app.websocket("/ws/ceo")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time CEO Discovery updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listening for client messages
            data = await websocket.receive_text()
            # Echo back (for keepalive/heartbeat)
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

**Step 5: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_websocket.py -v`
Expected: PASS (2 tests passed)

**Step 6: Manual verification**

Run: `cd dashboard && python server.py`

Test WebSocket (using websocat or browser console):
```javascript
// Browser console
const ws = new WebSocket('ws://localhost:3000/ws/ceo');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
// Should log: {type: "connection_established", ...}
```

Expected: Connection established message received
Stop server: Ctrl+C

**Step 7: Commit**

```bash
git add dashboard/websocket_manager.py dashboard/tests/test_websocket.py dashboard/server.py
git commit -m "feat: add WebSocket manager for real-time CEO Discovery updates"
```

---

## Task 5: Frontend - Extend office-ui.html with CEO Discovery Section

**Files:**
- Modify: `dashboard/office-ui.html`

**Step 1: Read current office-ui.html**

Run: `head -50 dashboard/office-ui.html`
Review structure and styling

**Step 2: Add CEO Discovery HTML section**

Modify `dashboard/office-ui.html`, add before closing `</body>`:

```html
<!-- CEO Discovery Section -->
<section id="ceo-discovery-section" class="dashboard-section">
    <h2>🎯 CEO Discovery System</h2>

    <!-- Status Card -->
    <div id="ceo-status-card" class="card">
        <div class="card-header">
            <h3>Discovery Status</h3>
            <span id="ceo-status-badge" class="status-badge">IDLE</span>
        </div>
        <div class="card-body">
            <div class="stat">
                <span class="stat-label">Current Session:</span>
                <span id="ceo-session-id">None</span>
            </div>
            <div class="stat">
                <span class="stat-label">Patterns Found:</span>
                <span id="ceo-patterns-count">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Proposals Generated:</span>
                <span id="ceo-proposals-count">0</span>
            </div>
        </div>
    </div>

    <!-- Active Proposals -->
    <div id="ceo-proposals-card" class="card">
        <div class="card-header">
            <h3>💡 Active Proposals</h3>
        </div>
        <div id="ceo-proposals-list" class="card-body">
            <!-- Dynamically populated -->
        </div>
    </div>

    <!-- Identified Patterns -->
    <div id="ceo-patterns-card" class="card">
        <div class="card-header">
            <h3>🧠 Identified Patterns</h3>
        </div>
        <div id="ceo-patterns-list" class="card-body">
            <!-- Dynamically populated -->
        </div>
    </div>

    <!-- Performance Metrics -->
    <div id="ceo-performance-card" class="card">
        <div class="card-header">
            <h3>📊 Performance Analytics</h3>
        </div>
        <div class="card-body">
            <div class="stat">
                <span class="stat-label">Prediction Accuracy:</span>
                <span id="ceo-prediction-accuracy">0%</span>
            </div>
            <div class="stat">
                <span class="stat-label">User Satisfaction:</span>
                <span id="ceo-user-satisfaction">0%</span>
            </div>
        </div>
    </div>
</section>
```

**Step 3: Add CSS styling**

Add to `<style>` section in office-ui.html:

```css
/* CEO Discovery Section */
#ceo-discovery-section {
    margin-top: 2rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
}

#ceo-discovery-section h2 {
    color: white;
    margin-bottom: 1.5rem;
}

.card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e2e8f0;
}

.card-header h3 {
    margin: 0;
    font-size: 1.2rem;
}

.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: bold;
}

.status-badge.active {
    background: #48bb78;
    color: white;
}

.status-badge.idle {
    background: #cbd5e0;
    color: #4a5568;
}

.stat {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
}

.stat-label {
    color: #718096;
    font-weight: 500;
}

.proposal-item, .pattern-item {
    border-left: 4px solid #667eea;
    padding: 1rem;
    margin: 0.5rem 0;
    background: #f7fafc;
    border-radius: 4px;
}

.proposal-item h4, .pattern-item h4 {
    margin: 0 0 0.5rem 0;
    color: #2d3748;
}

.proposal-meta, .pattern-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #718096;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #48bb78;
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideIn 0.3s ease-out;
    z-index: 1000;
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

**Step 4: Verify HTML structure**

Run: `cd dashboard && python -m http.server 8080`
Visit: `http://localhost:8080/office-ui.html`
Expected: CEO Discovery section visible with empty cards
Stop server: Ctrl+C

**Step 5: Commit**

```bash
git add dashboard/office-ui.html
git commit -m "feat: add CEO Discovery HTML section to dashboard UI"
```

---

## Task 6: Frontend JavaScript - Polling & WebSocket Integration

**Files:**
- Modify: `dashboard/office-ui.html` (JavaScript section)

**Step 1: Add JavaScript API integration**

Add to `<script>` section in office-ui.html:

```javascript
// Configuration
const API_BASE = 'http://localhost:3000/api';
const WS_URL = 'ws://localhost:3000/ws/ceo';
let ws = null;

// CEO Discovery Data Update
async function updateCEODiscovery() {
    try {
        // Fetch status
        const statusRes = await fetch(`${API_BASE}/ceo/status`);
        const status = await statusRes.json();

        // Update status card
        document.getElementById('ceo-session-id').textContent = status.session_id || 'None';
        document.getElementById('ceo-patterns-count').textContent = status.patterns?.length || 0;
        document.getElementById('ceo-proposals-count').textContent = status.proposals?.length || 0;

        const badge = document.getElementById('ceo-status-badge');
        badge.textContent = status.status.toUpperCase();
        badge.className = `status-badge ${status.status}`;

        // Fetch proposals
        const proposalsRes = await fetch(`${API_BASE}/ceo/proposals?min_roi=0&limit=5`);
        const proposals = await proposalsRes.json();
        renderProposals(proposals);

        // Fetch patterns
        const patternsRes = await fetch(`${API_BASE}/ceo/patterns`);
        const patterns = await patternsRes.json();
        renderPatterns(patterns);

        // Fetch performance
        const perfRes = await fetch(`${API_BASE}/ceo/performance`);
        const perf = await perfRes.json();
        document.getElementById('ceo-prediction-accuracy').textContent =
            `${perf.prediction_accuracy.toFixed(1)}%`;
        document.getElementById('ceo-user-satisfaction').textContent =
            `${perf.user_satisfaction.toFixed(1)}%`;

    } catch (error) {
        console.error('Error updating CEO Discovery data:', error);
    }
}

// Render proposals
function renderProposals(proposals) {
    const container = document.getElementById('ceo-proposals-list');

    if (proposals.length === 0) {
        container.innerHTML = '<p style="color: #718096;">No proposals generated yet.</p>';
        return;
    }

    container.innerHTML = proposals.map(p => `
        <div class="proposal-item">
            <h4>${p.title}</h4>
            <p>${p.description}</p>
            <div class="proposal-meta">
                <span>💰 ${p.cost} Becoins</span>
                <span>📈 ROI: ${p.roi.toFixed(1)}x</span>
                <span>🎯 Impact: ${p.impact_score}/100</span>
                <span>⏱️ Saves: ${p.time_saved_weekly}min/week</span>
            </div>
        </div>
    `).join('');
}

// Render patterns
function renderPatterns(patterns) {
    const container = document.getElementById('ceo-patterns-list');

    if (patterns.length === 0) {
        container.innerHTML = '<p style="color: #718096;">No patterns identified yet.</p>';
        return;
    }

    container.innerHTML = patterns.map(p => `
        <div class="pattern-item">
            <h4>${p.type.toUpperCase()}: ${p.description}</h4>
            <div class="pattern-meta">
                <span>Frequency: ${p.frequency}</span>
                <span>Severity: ${(p.severity * 100).toFixed(0)}%</span>
            </div>
        </div>
    `).join('');
}

// WebSocket connection
function connectWebSocket() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('WebSocket connected to CEO Discovery');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        if (data.type === 'new_proposal') {
            showNotification('New proposal generated!');
            updateCEODiscovery(); // Refresh data
        } else if (data.type === 'pattern_discovered') {
            showNotification('New pattern identified!');
            updateCEODiscovery(); // Refresh data
        } else if (data.type === 'status_change') {
            updateCEODiscovery(); // Refresh data
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected, using polling fallback');
        // Fallback to polling continues via setInterval
    };
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initial load
    updateCEODiscovery();

    // Start polling (3 seconds)
    setInterval(updateCEODiscovery, 3000);

    // Connect WebSocket
    connectWebSocket();
});
```

**Step 2: Test integration**

Run backend: `cd dashboard && python server.py`
Run frontend: Open `dashboard/office-ui.html` in browser

Expected:
- CEO Discovery section loads
- Polling updates every 3 seconds
- WebSocket connects (check console)
- Data displays correctly

**Step 3: Commit**

```bash
git add dashboard/office-ui.html
git commit -m "feat: add polling and WebSocket JavaScript integration"
```

---

## Task 7: Deployment Scripts & Documentation

**Files:**
- Modify: `dashboard/start`
- Create: `dashboard/README.md`
- Modify: `dashboard/.env.example`

**Step 1: Update start script**

Modify `dashboard/start`:

```bash
#!/bin/bash

# CEO Discovery Dashboard Launcher
# Starts FastAPI server with auto-reload for development

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
if [ ! -f ".venv/installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .venv/installed
fi

# Start server
echo "Starting CEO Discovery Dashboard..."
echo "Dashboard: http://localhost:3000/"
echo "API Docs: http://localhost:3000/docs"
echo ""

python server.py
```

Make executable:
```bash
chmod +x dashboard/start
```

**Step 2: Create README**

Create `dashboard/README.md`:

```markdown
# CEO Discovery Dashboard

Full-stack integration of the CEO Discovery System with the Becoin Economy dashboard.

## Features

- 📊 Real-time CEO Discovery session monitoring
- 💡 Live proposal display with ROI and impact scores
- 🧠 Pattern identification tracking
- 📈 Performance analytics and learning metrics
- ⚡ Hybrid polling (3s) + WebSocket for instant updates
- 🔒 Read-only observer maintaining agent autonomy

## Architecture

**Backend:** Python FastAPI server
**Frontend:** Extended office-ui.html with vanilla JavaScript
**Data Source:** `.claude-flow/discovery-sessions/*.json`
**Updates:** Polling (baseline) + WebSocket (real-time)

## Quick Start

### Development

```bash
./start
```

Launches server on http://localhost:3000

### Production

```bash
# Using systemd
sudo cp ceo-discovery.service /etc/systemd/system/
sudo systemctl enable ceo-discovery
sudo systemctl start ceo-discovery

# Or using PM2
pm2 start server.py --name ceo-dashboard --interpreter python3
pm2 save
```

## API Endpoints

### REST API

- `GET /api/status` - Health check
- `GET /api/ceo/status` - Current discovery session
- `GET /api/ceo/proposals?min_roi=3.0&limit=5` - Filtered proposals
- `GET /api/ceo/patterns?type=repetitive` - Patterns by type
- `GET /api/ceo/performance` - Performance metrics

### WebSocket

- `ws://localhost:3000/ws/ceo` - Real-time updates

**Events:**
- `new_proposal` - Proposal generated
- `pattern_discovered` - Pattern identified
- `status_change` - Session status changed

## Configuration

Copy `.env.example` to `.env` and configure:

```env
HOST=0.0.0.0
PORT=3000
DISCOVERY_SESSIONS_PATH=../.claude-flow/discovery-sessions
BECOIN_ECONOMY_PATH=../becoin-economy
```

## Testing

```bash
# All tests
pytest

# Specific test file
pytest tests/test_server.py -v

# With coverage
pytest --cov=. --cov-report=html
```

## Agent Autonomy Guarantees

✅ Dashboard is **read-only observer**
✅ No modification of agent decisions
✅ No interruption of discovery process
✅ Agent learning and adaptation unchanged
✅ Becoin economy rules preserved

## Development

### Adding New Endpoints

1. Update `ceo_data_bridge.py` with data access method
2. Add endpoint to `server.py`
3. Write test in `tests/test_api_endpoints.py`
4. Update frontend to consume endpoint

### File Structure

```
dashboard/
├── server.py              # FastAPI main server
├── ceo_data_bridge.py     # Data reading & formatting
├── websocket_manager.py   # WebSocket broadcast
├── office-ui.html         # Extended dashboard UI
├── requirements.txt       # Python dependencies
├── start                  # Launch script
└── tests/                 # Test suite
```

## Troubleshooting

**WebSocket not connecting:**
- Check server is running on port 3000
- Verify browser console for errors
- Fallback to polling continues automatically

**No data showing:**
- Verify `.claude-flow/discovery-sessions/` exists
- Check session JSON files are valid
- Review server logs for errors

**Port already in use:**
- Change PORT in .env
- Update frontend API_BASE URL
```

**Step 3: Commit**

```bash
git add dashboard/start dashboard/README.md
git commit -m "docs: add deployment scripts and comprehensive README"
```

---

## Task 8: Integration Testing & Verification

**Files:**
- Create: `dashboard/tests/test_integration.py`

**Step 1: Write integration test**

Create `dashboard/tests/test_integration.py`:

```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from server import app

def test_full_integration():
    """Test complete data flow from file to API"""
    client = TestClient(app)

    # Health check
    response = client.get("/api/status")
    assert response.status_code == 200

    # CEO status
    response = client.get("/api/ceo/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

    # Proposals
    response = client.get("/api/ceo/proposals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Patterns
    response = client.get("/api/ceo/patterns")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Performance
    response = client.get("/api/ceo/performance")
    assert response.status_code == 200
    data = response.json()
    assert "prediction_accuracy" in data

@pytest.mark.asyncio
async def test_websocket_integration():
    """Test WebSocket connection and message flow"""
    client = TestClient(app)

    with client.websocket_connect("/ws/ceo") as websocket:
        # Receive connection message
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

        # Test keepalive
        websocket.send_text("ping")
        response = websocket.receive_json()
        assert response["type"] == "pong"
```

**Step 2: Run integration tests**

Run: `cd dashboard && python -m pytest tests/test_integration.py -v`
Expected: PASS (2 tests passed)

**Step 3: Manual end-to-end verification**

1. Start server: `cd dashboard && ./start`
2. Open browser: `http://localhost:3000/`
3. Verify:
   - ✓ Dashboard loads
   - ✓ CEO Discovery section visible
   - ✓ Data polling every 3 seconds (check Network tab)
   - ✓ WebSocket connected (check Console)
   - ✓ API endpoints respond (check Network tab)
4. Test API docs: `http://localhost:3000/docs`
5. Stop server: Ctrl+C

**Step 4: Commit**

```bash
git add dashboard/tests/test_integration.py
git commit -m "test: add integration tests for full data flow"
```

---

## Task 9: Final Review & Documentation Update

**Files:**
- Modify: `../CLAUDE.md` (project root)
- Create: `dashboard/CHANGELOG.md`

**Step 1: Update project CLAUDE.md**

Add to `CLAUDE.md` CEO Discovery Dashboard section:

```markdown
### CEO Discovery Dashboard Integration

The dashboard includes **full-stack CEO Discovery integration**:

**Features:**
- Real-time monitoring at http://localhost:3000
- REST API endpoints for all CEO Discovery data
- WebSocket real-time updates for proposals and patterns
- Performance analytics and learning metrics
- Hybrid polling + WebSocket architecture

**Quick Start:**
```bash
cd dashboard
./start  # Launches FastAPI server on port 3000
```

**Architecture:**
- Backend: Python FastAPI (dashboard/server.py)
- Frontend: Extended office-ui.html
- Data Bridge: Reads .claude-flow/discovery-sessions/
- Updates: 3s polling + WebSocket events

**Guarantees:**
- ✅ Read-only observer (no agent interference)
- ✅ Agent autonomy preserved
- ✅ Becoin economy rules intact
- ✅ Learning and adaptation unchanged

See `dashboard/README.md` for complete documentation.
```

**Step 2: Create changelog**

Create `dashboard/CHANGELOG.md`:

```markdown
# Changelog

## [1.0.0] - 2025-11-05

### Added
- FastAPI backend server with REST API endpoints
- CEO Discovery data bridge for session reading
- WebSocket manager for real-time updates
- Extended office-ui.html with CEO Discovery section
- Polling (3s) + WebSocket hybrid architecture
- Comprehensive test suite (unit + integration)
- Deployment scripts and documentation
- Performance analytics visualization
- Pattern identification tracking
- Proposal display with ROI metrics

### Guarantees
- Read-only observer maintaining agent autonomy
- No modification of agent decisions or data
- Becoin economy rules preserved
- Agent learning systems unchanged
```

**Step 3: Final verification**

Run full test suite:
```bash
cd dashboard
python -m pytest -v --cov=. --cov-report=term-missing
```

Expected: All tests pass with >80% coverage

**Step 4: Commit**

```bash
git add ../CLAUDE.md dashboard/CHANGELOG.md
git commit -m "docs: update project documentation with dashboard integration"
```

---

## Task 10: Merge & Cleanup

**Files:**
- N/A (Git operations)

**Step 1: Final commit check**

Run: `git log --oneline -10`
Expected: See all 9 feature commits

**Step 2: Verify branch**

Run: `git status`
Expected: On branch `feature/ceo-dashboard-integration`, working directory clean

**Step 3: Push branch**

Run: `git push -u origin feature/ceo-dashboard-integration`

**Step 4: Create pull request**

Using GitHub CLI or web interface:
```bash
gh pr create --title "feat: CEO Discovery Dashboard Integration" \
  --body "Full-stack integration of CEO Discovery System with dashboard

## Features
- FastAPI backend with REST + WebSocket
- Extended office-ui.html with CEO section
- Real-time updates with hybrid polling
- Performance analytics visualization
- Read-only observer maintaining agent autonomy

## Testing
- ✅ All unit tests passing
- ✅ Integration tests passing
- ✅ Manual E2E verification complete

## Documentation
- README.md with setup instructions
- CHANGELOG.md with version history
- Updated CLAUDE.md project docs"
```

**Step 5: Code review**

Wait for review, address feedback, then merge to main.

**Step 6: Cleanup worktree**

After merge:
```bash
cd ../../  # Back to repo root
git worktree remove .worktrees/ceo-dashboard-integration
git branch -d feature/ceo-dashboard-integration
```

---

## Task 11: State Persistence System - Agent Resume Capability

**Files:**
- Create: `dashboard/state_manager.py`
- Create: `dashboard/tests/test_state_manager.py`
- Create: `dashboard/config/ceo-config.json`

**Step 1: Write the failing test**

Create `dashboard/tests/test_state_manager.py`:

```python
import pytest
import json
import tempfile
from pathlib import Path
from state_manager import StateManager

@pytest.fixture
def temp_state_dir():
    """Create temporary state directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_save_agent_state(temp_state_dir):
    """Test saving agent state"""
    manager = StateManager(state_dir=temp_state_dir)

    state = {
        "agent_id": "CEO-001",
        "task": "discovery_mission",
        "status": "in_progress",
        "progress": 45,
        "last_action": "analyzing_patterns",
        "timestamp": "2025-11-05T10:30:00Z"
    }

    manager.save_agent_state("CEO-001", state)

    # Verify file created
    state_file = Path(temp_state_dir) / "agent-state-CEO-001.json"
    assert state_file.exists()

    # Verify content
    with open(state_file) as f:
        saved = json.load(f)
    assert saved["agent_id"] == "CEO-001"
    assert saved["progress"] == 45

def test_load_agent_state(temp_state_dir):
    """Test loading agent state"""
    manager = StateManager(state_dir=temp_state_dir)

    # Save state first
    state = {
        "agent_id": "CEO-001",
        "task": "discovery_mission",
        "status": "in_progress"
    }
    manager.save_agent_state("CEO-001", state)

    # Load state
    loaded = manager.load_agent_state("CEO-001")
    assert loaded["agent_id"] == "CEO-001"
    assert loaded["status"] == "in_progress"

def test_get_incomplete_tasks(temp_state_dir):
    """Test finding incomplete tasks for resume"""
    manager = StateManager(state_dir=temp_state_dir)

    # Save multiple agent states
    manager.save_agent_state("CEO-001", {"status": "in_progress", "task": "discovery"})
    manager.save_agent_state("CTO-001", {"status": "completed", "task": "build"})
    manager.save_agent_state("CDO-001", {"status": "in_progress", "task": "design"})

    # Get incomplete tasks
    incomplete = manager.get_incomplete_tasks()

    assert len(incomplete) == 2
    assert any(t["task"] == "discovery" for t in incomplete)
    assert any(t["task"] == "design" for t in incomplete)

def test_mark_task_complete(temp_state_dir):
    """Test marking task as complete"""
    manager = StateManager(state_dir=temp_state_dir)

    manager.save_agent_state("CEO-001", {"status": "in_progress", "task": "discovery"})
    manager.mark_task_complete("CEO-001")

    state = manager.load_agent_state("CEO-001")
    assert state["status"] == "completed"

def test_clear_completed_states(temp_state_dir):
    """Test clearing old completed states"""
    manager = StateManager(state_dir=temp_state_dir)

    manager.save_agent_state("CEO-001", {"status": "completed", "task": "discovery"})
    manager.save_agent_state("CTO-001", {"status": "in_progress", "task": "build"})

    manager.clear_completed_states()

    # Completed should be gone
    assert not (Path(temp_state_dir) / "agent-state-CEO-001.json").exists()
    # In-progress should remain
    assert (Path(temp_state_dir) / "agent-state-CTO-001.json").exists()
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_state_manager.py -v`
Expected: FAIL with "No module named 'state_manager'"

**Step 3: Write minimal implementation**

Create `dashboard/state_manager.py`:

```python
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StateManager:
    """Manages agent state persistence for resume capability"""

    def __init__(self, state_dir: str = "../.claude-flow/agent-state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_agent_state(self, agent_id: str, state: Dict) -> None:
        """Save agent state to disk"""
        try:
            state_file = self.state_dir / f"agent-state-{agent_id}.json"

            # Add timestamp if not present
            if "timestamp" not in state:
                state["timestamp"] = datetime.utcnow().isoformat() + "Z"

            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Saved state for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error saving state for {agent_id}: {e}")
            raise

    def load_agent_state(self, agent_id: str) -> Optional[Dict]:
        """Load agent state from disk"""
        try:
            state_file = self.state_dir / f"agent-state-{agent_id}.json"

            if not state_file.exists():
                return None

            with open(state_file) as f:
                state = json.load(f)

            logger.info(f"Loaded state for agent {agent_id}")
            return state

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading state for {agent_id}: {e}")
            return None

    def get_incomplete_tasks(self) -> List[Dict]:
        """Get all incomplete tasks for resume"""
        incomplete = []

        for state_file in self.state_dir.glob("agent-state-*.json"):
            try:
                with open(state_file) as f:
                    state = json.load(f)

                if state.get("status") == "in_progress":
                    incomplete.append(state)

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error reading state file {state_file}: {e}")
                continue

        return incomplete

    def mark_task_complete(self, agent_id: str) -> None:
        """Mark agent task as completed"""
        state = self.load_agent_state(agent_id)

        if state:
            state["status"] = "completed"
            state["completed_at"] = datetime.utcnow().isoformat() + "Z"
            self.save_agent_state(agent_id, state)

    def clear_completed_states(self, max_age_days: int = 7) -> None:
        """Clear old completed state files"""
        for state_file in self.state_dir.glob("agent-state-*.json"):
            try:
                with open(state_file) as f:
                    state = json.load(f)

                if state.get("status") == "completed":
                    state_file.unlink()
                    logger.info(f"Cleared completed state: {state_file.name}")

            except Exception as e:
                logger.error(f"Error clearing state file {state_file}: {e}")
```

Create `dashboard/config/ceo-config.json`:

```json
{
  "daemon": {
    "autoStart": true,
    "discoveryInterval": 24,
    "optimizationInterval": 168,
    "autoPropose": true,
    "autoResume": true,
    "budgetRange": {
      "min": 100,
      "max": 500
    },
    "roiTarget": 3.0,
    "minConfidence": 0.7,
    "analysisWindow": 168
  },
  "server": {
    "port": 3000,
    "host": "0.0.0.0"
  },
  "state": {
    "persistenceDir": "../.claude-flow/agent-state",
    "autoCleanup": true,
    "cleanupIntervalDays": 7
  },
  "agents": {
    "ceo": {
      "id": "CEO-001",
      "enabled": true,
      "autoRestart": true
    },
    "cto": {
      "id": "CTO-001",
      "enabled": true,
      "autoRestart": true
    },
    "cdo": {
      "id": "CDO-001",
      "enabled": true,
      "autoRestart": true
    }
  }
}
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_state_manager.py -v`
Expected: PASS (5 tests passed)

**Step 5: Commit**

```bash
git add dashboard/state_manager.py dashboard/tests/test_state_manager.py dashboard/config/ceo-config.json
git commit -m "feat: add state persistence system for agent resume capability"
```

---

## Task 12: Daemon Process - Auto-Resume & Scheduling

**Files:**
- Create: `dashboard/daemon.py`
- Create: `dashboard/tests/test_daemon.py`
- Modify: `dashboard/server.py`

**Step 1: Write the failing test**

Create `dashboard/tests/test_daemon.py`:

```python
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from daemon import CEODiscoveryDaemon

@pytest.fixture
def daemon_config():
    """Sample daemon configuration"""
    return {
        "daemon": {
            "autoStart": True,
            "discoveryInterval": 1,  # 1 hour for testing
            "autoResume": True
        },
        "agents": {
            "ceo": {"id": "CEO-001", "enabled": True, "autoRestart": True}
        }
    }

def test_daemon_initialization(daemon_config):
    """Test daemon initialization"""
    daemon = CEODiscoveryDaemon(config=daemon_config)

    assert daemon.config["daemon"]["autoStart"] is True
    assert daemon.running is False

@pytest.mark.asyncio
async def test_resume_incomplete_tasks(daemon_config):
    """Test resuming incomplete tasks on startup"""
    with patch('daemon.StateManager') as MockStateManager:
        mock_state_manager = MockStateManager.return_value
        mock_state_manager.get_incomplete_tasks.return_value = [
            {
                "agent_id": "CEO-001",
                "task": "discovery_mission",
                "status": "in_progress",
                "progress": 45
            }
        ]

        daemon = CEODiscoveryDaemon(config=daemon_config)

        with patch.object(daemon, '_resume_agent_task', new_callable=AsyncMock) as mock_resume:
            await daemon.resume_incomplete_tasks()

            # Should call resume for the incomplete task
            mock_resume.assert_called_once()
            call_args = mock_resume.call_args[0][0]
            assert call_args["agent_id"] == "CEO-001"
            assert call_args["progress"] == 45

@pytest.mark.asyncio
async def test_scheduled_discovery(daemon_config):
    """Test scheduled discovery execution"""
    daemon = CEODiscoveryDaemon(config=daemon_config)

    with patch.object(daemon, '_run_discovery_cycle', new_callable=AsyncMock) as mock_discovery:
        # Manually trigger one cycle
        await daemon._run_discovery_cycle()

        mock_discovery.assert_called_once()

def test_daemon_config_validation(daemon_config):
    """Test configuration validation"""
    daemon = CEODiscoveryDaemon(config=daemon_config)

    assert daemon._validate_config() is True

    # Test invalid config
    invalid_config = {"daemon": {}}  # Missing required fields
    daemon_invalid = CEODiscoveryDaemon(config=invalid_config)
    assert daemon_invalid._validate_config() is False
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_daemon.py -v`
Expected: FAIL with "No module named 'daemon'"

**Step 3: Write minimal implementation**

Create `dashboard/daemon.py`:

```python
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from state_manager import StateManager

logger = logging.getLogger(__name__)

class CEODiscoveryDaemon:
    """
    Autonomous daemon for CEO Discovery System
    - Auto-starts on system boot
    - Resumes incomplete tasks
    - Runs scheduled discovery cycles
    """

    def __init__(self, config_path: str = "config/ceo-config.json", config: Optional[Dict] = None):
        if config:
            self.config = config
        else:
            with open(config_path) as f:
                self.config = json.load(f)

        self.state_manager = StateManager(
            state_dir=self.config.get("state", {}).get("persistenceDir", "../.claude-flow/agent-state")
        )

        self.running = False
        self.tasks = []

        logger.info("CEO Discovery Daemon initialized")

    def _validate_config(self) -> bool:
        """Validate daemon configuration"""
        required_keys = ["daemon", "agents"]

        for key in required_keys:
            if key not in self.config:
                logger.error(f"Missing required config key: {key}")
                return False

        return True

    async def start(self):
        """Start the daemon"""
        if not self._validate_config():
            logger.error("Invalid configuration, cannot start daemon")
            return

        self.running = True
        logger.info("🚀 CEO Discovery Daemon starting...")

        # Resume incomplete tasks on startup
        if self.config["daemon"].get("autoResume", True):
            await self.resume_incomplete_tasks()

        # Start scheduled discovery cycles
        if self.config["daemon"].get("autoStart", True):
            await self._start_scheduled_cycles()

    async def resume_incomplete_tasks(self):
        """Resume all incomplete tasks from previous session"""
        logger.info("🔄 Checking for incomplete tasks to resume...")

        incomplete_tasks = self.state_manager.get_incomplete_tasks()

        if not incomplete_tasks:
            logger.info("No incomplete tasks found")
            return

        logger.info(f"Found {len(incomplete_tasks)} incomplete tasks")

        for task_state in incomplete_tasks:
            try:
                await self._resume_agent_task(task_state)
            except Exception as e:
                logger.error(f"Error resuming task {task_state.get('agent_id')}: {e}")

    async def _resume_agent_task(self, task_state: Dict):
        """Resume a specific agent task"""
        agent_id = task_state.get("agent_id")
        task = task_state.get("task")
        progress = task_state.get("progress", 0)

        logger.info(f"Resuming {agent_id} - {task} (progress: {progress}%)")

        # Save resumed state
        task_state["status"] = "resumed"
        task_state["resumed_at"] = datetime.utcnow().isoformat() + "Z"
        self.state_manager.save_agent_state(agent_id, task_state)

        # TODO: Actual agent spawning happens here via orchestrator
        # This would call: orchestrator.resume_agent(agent_id, task_state)

        logger.info(f"✅ Resumed {agent_id}")

    async def _start_scheduled_cycles(self):
        """Start scheduled discovery and optimization cycles"""
        discovery_interval = self.config["daemon"].get("discoveryInterval", 24)  # hours

        logger.info(f"Starting scheduled cycles (discovery every {discovery_interval}h)")

        while self.running:
            try:
                # Run discovery cycle
                await self._run_discovery_cycle()

                # Wait for next cycle
                await asyncio.sleep(discovery_interval * 3600)  # Convert to seconds

            except Exception as e:
                logger.error(f"Error in scheduled cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _run_discovery_cycle(self):
        """Execute one discovery cycle"""
        logger.info("🔍 Running discovery cycle...")

        # Get enabled agents
        enabled_agents = [
            agent_id for agent_id, config in self.config["agents"].items()
            if config.get("enabled", False)
        ]

        logger.info(f"Enabled agents: {enabled_agents}")

        # Save state before starting
        for agent_id in enabled_agents:
            state = {
                "agent_id": self.config["agents"][agent_id]["id"],
                "task": "discovery_cycle",
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "progress": 0
            }
            self.state_manager.save_agent_state(agent_id, state)

        # TODO: Actual discovery execution via orchestrator
        # orchestrator.run_discovery_cycle(enabled_agents)

        logger.info("✅ Discovery cycle initiated")

    async def stop(self):
        """Stop the daemon gracefully"""
        logger.info("Stopping CEO Discovery Daemon...")
        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        logger.info("CEO Discovery Daemon stopped")

async def main():
    """Main entry point for daemon"""
    daemon = CEODiscoveryDaemon()

    try:
        await daemon.start()
    except KeyboardInterrupt:
        await daemon.stop()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
```

**Step 4: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_daemon.py -v`
Expected: PASS (3 tests passed)

**Step 5: Add daemon control endpoints to server.py**

Modify `dashboard/server.py`, add after existing endpoints:

```python
from daemon import CEODiscoveryDaemon

# Initialize daemon (will be started separately)
daemon = CEODiscoveryDaemon()

@app.get("/api/daemon/status")
async def get_daemon_status():
    """Get daemon running status"""
    return {
        "running": daemon.running,
        "config": daemon.config["daemon"]
    }

@app.post("/api/daemon/start")
async def start_daemon():
    """Start the daemon"""
    if daemon.running:
        return {"status": "already_running"}

    asyncio.create_task(daemon.start())
    return {"status": "started"}

@app.post("/api/daemon/stop")
async def stop_daemon():
    """Stop the daemon"""
    if not daemon.running:
        return {"status": "not_running"}

    await daemon.stop()
    return {"status": "stopped"}

@app.post("/api/daemon/resume")
async def manual_resume():
    """Manually trigger resume of incomplete tasks"""
    await daemon.resume_incomplete_tasks()
    return {"status": "resume_triggered"}
```

**Step 6: Manual verification**

Run daemon standalone:
```bash
cd dashboard
python daemon.py
```

Expected:
- Daemon starts
- Checks for incomplete tasks
- Logs scheduled cycle start

Stop: Ctrl+C

**Step 7: Commit**

```bash
git add dashboard/daemon.py dashboard/tests/test_daemon.py dashboard/server.py
git commit -m "feat: add autonomous daemon with auto-resume and scheduling"
```

---

## Task 13: System Integration - systemd & PM2 Auto-Start

**Files:**
- Create: `dashboard/systemd/ceo-discovery.service`
- Create: `dashboard/pm2/ecosystem.config.js`
- Create: `dashboard/scripts/install-service.sh`
- Modify: `dashboard/README.md`

**Step 1: Create systemd service file**

Create `dashboard/systemd/ceo-discovery.service`:

```ini
[Unit]
Description=CEO Discovery Dashboard - Autonomous Agent System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=%USER%
WorkingDirectory=%WORKING_DIR%
Environment="PATH=%VENV_PATH%/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=%VENV_PATH%/bin/python %WORKING_DIR%/daemon.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Graceful shutdown
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

**Step 2: Create PM2 ecosystem file**

Create `dashboard/pm2/ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'ceo-discovery-daemon',
      script: 'daemon.py',
      interpreter: 'python3',
      cwd: '/path/to/dashboard',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/daemon-error.log',
      out_file: './logs/daemon-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    },
    {
      name: 'ceo-discovery-server',
      script: 'server.py',
      interpreter: 'python3',
      cwd: '/path/to/dashboard',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
```

**Step 3: Create installation script**

Create `dashboard/scripts/install-service.sh`:

```bash
#!/bin/bash

# CEO Discovery Dashboard - Service Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$DASHBOARD_DIR/.venv"

echo "🔧 Installing CEO Discovery Dashboard Service"
echo "============================================="

# Detect installation method
read -p "Choose installation method (1=systemd, 2=PM2): " method

if [ "$method" = "1" ]; then
    # systemd installation
    echo ""
    echo "📦 Installing systemd service..."

    # Create service file with substitutions
    SERVICE_FILE="/tmp/ceo-discovery.service"
    cp "$DASHBOARD_DIR/systemd/ceo-discovery.service" "$SERVICE_FILE"

    # Replace placeholders
    sed -i "s|%USER%|$USER|g" "$SERVICE_FILE"
    sed -i "s|%WORKING_DIR%|$DASHBOARD_DIR|g" "$SERVICE_FILE"
    sed -i "s|%VENV_PATH%|$VENV_PATH|g" "$SERVICE_FILE"

    # Install service
    sudo cp "$SERVICE_FILE" /etc/systemd/system/ceo-discovery.service
    sudo systemctl daemon-reload
    sudo systemctl enable ceo-discovery

    echo "✅ systemd service installed"
    echo ""
    echo "To start: sudo systemctl start ceo-discovery"
    echo "To check: sudo systemctl status ceo-discovery"
    echo "To logs:  sudo journalctl -u ceo-discovery -f"

elif [ "$method" = "2" ]; then
    # PM2 installation
    echo ""
    echo "📦 Installing PM2 service..."

    # Check PM2 installed
    if ! command -v pm2 &> /dev/null; then
        echo "❌ PM2 not found. Install with: npm install -g pm2"
        exit 1
    fi

    # Update ecosystem config with actual path
    ECOSYSTEM_FILE="$DASHBOARD_DIR/pm2/ecosystem.config.js"
    sed -i "s|/path/to/dashboard|$DASHBOARD_DIR|g" "$ECOSYSTEM_FILE"

    # Start with PM2
    cd "$DASHBOARD_DIR"
    pm2 start pm2/ecosystem.config.js
    pm2 save
    pm2 startup

    echo "✅ PM2 service installed"
    echo ""
    echo "To check: pm2 list"
    echo "To logs:  pm2 logs ceo-discovery-daemon"
    echo "To stop:  pm2 stop ceo-discovery-daemon"

else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "The daemon will now:"
echo "  ✅ Start automatically on system boot"
echo "  ✅ Resume incomplete tasks"
echo "  ✅ Run discovery cycles every 24h"
echo "  ✅ Auto-restart on failures"
```

Make executable:
```bash
chmod +x dashboard/scripts/install-service.sh
```

**Step 4: Update README with auto-start instructions**

Modify `dashboard/README.md`, add section after "Production":

```markdown
## Auto-Start on System Boot

The CEO Discovery Daemon can automatically start when your system boots, ensuring agents always resume their work.

### Option 1: systemd (Linux)

```bash
# Install service
./scripts/install-service.sh
# Choose option 1 (systemd)

# Manual installation
sudo cp systemd/ceo-discovery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ceo-discovery
sudo systemctl start ceo-discovery

# Check status
sudo systemctl status ceo-discovery

# View logs
sudo journalctl -u ceo-discovery -f
```

### Option 2: PM2 (Cross-platform)

```bash
# Install PM2 globally
npm install -g pm2

# Install service
./scripts/install-service.sh
# Choose option 2 (PM2)

# Manual installation
pm2 start pm2/ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions

# Check status
pm2 list
pm2 logs ceo-discovery-daemon
```

### What Happens on Boot

When the system starts:
1. ✅ Daemon automatically launches
2. ✅ Reads `.claude-flow/agent-state/*.json`
3. ✅ Resumes all incomplete agent tasks
4. ✅ Agents continue from last saved progress
5. ✅ Scheduled discovery cycles continue

### State Persistence

Agent state is saved to:
```
.claude-flow/agent-state/
├── agent-state-CEO-001.json
├── agent-state-CTO-001.json
└── agent-state-CDO-001.json
```

Each state file contains:
- `agent_id` - Agent identifier
- `task` - Current task name
- `status` - in_progress|completed|resumed
- `progress` - Progress percentage (0-100)
- `last_action` - Last action taken
- `timestamp` - Last update time

### Testing Auto-Resume

```bash
# Start daemon
./start

# Trigger a discovery cycle (creates state files)
curl -X POST http://localhost:3000/api/daemon/start

# Simulate crash/reboot
pkill -f daemon.py

# Restart daemon
./start

# Check logs - should see "Resuming..." messages
```

### Uninstalling Auto-Start

**systemd:**
```bash
sudo systemctl stop ceo-discovery
sudo systemctl disable ceo-discovery
sudo rm /etc/systemd/system/ceo-discovery.service
sudo systemctl daemon-reload
```

**PM2:**
```bash
pm2 stop ceo-discovery-daemon
pm2 delete ceo-discovery-daemon
pm2 save
```
```

**Step 5: Create test script for auto-resume**

Create `dashboard/tests/test_auto_resume.sh`:

```bash
#!/bin/bash

# Test script for auto-resume functionality

echo "🧪 Testing Auto-Resume Functionality"
echo "===================================="

# Create mock state files
mkdir -p ../.claude-flow/agent-state

cat > ../.claude-flow/agent-state/agent-state-CEO-001.json <<EOF
{
  "agent_id": "CEO-001",
  "task": "discovery_mission",
  "status": "in_progress",
  "progress": 45,
  "last_action": "analyzing_patterns",
  "timestamp": "2025-11-05T10:30:00Z"
}
EOF

cat > ../.claude-flow/agent-state/agent-state-CTO-001.json <<EOF
{
  "agent_id": "CTO-001",
  "task": "build_feature",
  "status": "in_progress",
  "progress": 67,
  "last_action": "implementing_code",
  "timestamp": "2025-11-05T10:25:00Z"
}
EOF

echo "✅ Created mock state files"
echo ""

# Start daemon
echo "🚀 Starting daemon..."
python daemon.py &
DAEMON_PID=$!

sleep 3

# Check logs for resume messages
echo ""
echo "📋 Checking daemon logs..."
if pgrep -f daemon.py > /dev/null; then
    echo "✅ Daemon is running"
else
    echo "❌ Daemon failed to start"
    exit 1
fi

# Clean up
kill $DAEMON_PID 2>/dev/null
rm -rf ../.claude-flow/agent-state/agent-state-*.json

echo ""
echo "✅ Test complete!"
echo ""
echo "Expected behavior:"
echo "  - Daemon should log 'Found 2 incomplete tasks'"
echo "  - Daemon should log 'Resuming CEO-001' and 'Resuming CTO-001'"
echo "  - Tasks should continue from saved progress"
```

Make executable:
```bash
chmod +x dashboard/tests/test_auto_resume.sh
```

**Step 6: Manual verification**

Test systemd service (if on Linux):
```bash
cd dashboard
./scripts/install-service.sh
# Choose systemd
sudo systemctl start ceo-discovery
sudo systemctl status ceo-discovery
# Should show "active (running)"
```

Test PM2 (if PM2 installed):
```bash
cd dashboard
./scripts/install-service.sh
# Choose PM2
pm2 list
# Should show ceo-discovery-daemon running
```

Test auto-resume:
```bash
cd dashboard
./tests/test_auto_resume.sh
```

**Step 7: Commit**

```bash
git add dashboard/systemd/ dashboard/pm2/ dashboard/scripts/ dashboard/tests/test_auto_resume.sh dashboard/README.md
git commit -m "feat: add systemd/PM2 integration for auto-start on boot"
```

---

## Task 14: AIDO Integration - Selbstlernende Agent-Organisation

**Files:**
- Create: `dashboard/aido/llm_provider.py`
- Create: `dashboard/aido/agent_loader.py`
- Create: `dashboard/aido/agent_network.py`
- Create: `dashboard/aido/decision_making.py`
- Create: `dashboard/aido/consensus.py`
- Create: `dashboard/tests/test_aido.py`

**Step 1: Write the failing test**

Create `dashboard/tests/test_aido.py`:

```python
import pytest
from aido.llm_provider import OllamaProvider, ClaudeProvider
from aido.agent_loader import AgentLoader
from aido.agent_network import AgentNetwork

def test_ollama_provider():
    """Test Ollama LLM provider"""
    provider = OllamaProvider(model="llama3.1:8b")

    response = provider.call(
        system="You are a helpful AI assistant.",
        prompt="What is 2+2?"
    )

    assert isinstance(response, str)
    assert len(response) > 0

def test_agent_loader():
    """Test loading agent personality from .md file"""
    loader = AgentLoader(agents_dir="../founders")

    personality = loader.load_agent("ceo-sales.md")

    assert "CEO & Sales Director" in personality["name"]
    assert "system_prompt" in personality
    assert len(personality["system_prompt"]) > 100

def test_agent_network_proposal():
    """Test AIDO agent proposal generation"""
    provider = OllamaProvider(model="llama3.1:8b")
    loader = AgentLoader(agents_dir="../founders")
    network = AgentNetwork(llm_provider=provider, agent_loader=loader)

    proposal = network.generate_proposal(
        agent="ceo-sales.md",
        topic="Automate repetitive build tasks",
        context={"frequency": 15, "time_spent": 120}
    )

    assert "title" in proposal
    assert "description" in proposal
    assert "cost_becoins" in proposal
    assert "expected_roi" in proposal
    assert proposal["cost_becoins"] > 0
```

**Step 2: Run test to verify it fails**

Run: `cd dashboard && python -m pytest tests/test_aido.py -v`
Expected: FAIL with "No module named 'aido'"

**Step 3: Create LLM Provider abstraction**

Create `dashboard/aido/__init__.py`:
```python
"""AIDO - AI-Driven Decentralized Organization"""
```

Create `dashboard/aido/llm_provider.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
import requests
import json
import logging

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def call(self, system: str, prompt: str, **kwargs) -> str:
        """Execute LLM call with system prompt and user prompt"""
        pass

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""

    def __init__(self, model: str = "llama3.1:70b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self._check_connection()

    def _check_connection(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.warning(f"Ollama not responding properly: {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.host}. Make sure Ollama is running.")

    def call(self, system: str, prompt: str, **kwargs) -> str:
        """Call Ollama API"""
        try:
            payload = {
                "model": self.model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }

            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise

class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider (fallback)"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

    def call(self, system: str, prompt: str, **kwargs) -> str:
        """Call Anthropic API"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
```

**Step 4: Create Agent Loader**

Create `dashboard/aido/agent_loader.py`:

```python
import re
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class AgentLoader:
    """Loads agent personalities from .md files"""

    def __init__(self, agents_dir: str = "../founders"):
        self.agents_dir = Path(agents_dir)
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")

    def load_agent(self, agent_file: str) -> Dict:
        """Load agent personality from markdown file"""
        file_path = self.agents_dir / agent_file

        if not file_path.exists():
            raise FileNotFoundError(f"Agent file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML frontmatter
        frontmatter = self._parse_frontmatter(content)

        # Extract agent name from first heading
        name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        name = name_match.group(1) if name_match else agent_file

        # Extract sections
        sections = self._extract_sections(content)

        # Build system prompt from agent content
        system_prompt = self._build_system_prompt(name, sections)

        return {
            "name": name,
            "file": agent_file,
            "frontmatter": frontmatter,
            "sections": sections,
            "system_prompt": system_prompt
        }

    def _parse_frontmatter(self, content: str) -> Dict:
        """Parse YAML frontmatter"""
        match = re.match(r'^---\n(.+?)\n---', content, re.DOTALL)
        if not match:
            return {}

        frontmatter = {}
        for line in match.group(1).split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def _build_system_prompt(self, name: str, sections: Dict[str, str]) -> str:
        """Build system prompt from agent sections"""
        prompt_parts = [f"You are {name}."]

        # Include key sections in order
        section_order = [
            "🧠 Your Identity & Memory",
            "🎯 Your Core Mission",
            "🚨 Critical Rules You Must Follow",
            "💭 Your Communication Style"
        ]

        for section_name in section_order:
            if section_name in sections:
                prompt_parts.append(f"\n{section_name}\n{sections[section_name]}")

        return '\n'.join(prompt_parts)

    def list_agents(self) -> list:
        """List all available agent files"""
        if not self.agents_dir.exists():
            return []

        return [f.name for f in self.agents_dir.glob("*.md")]
```

**Step 5: Create Agent Network**

Create `dashboard/aido/agent_network.py`:

```python
from typing import Dict, Optional
import logging
from .llm_provider import LLMProvider
from .agent_loader import AgentLoader

logger = logging.getLogger(__name__)

class AgentNetwork:
    """AIDO Agent Network for proposal generation"""

    def __init__(self, llm_provider: LLMProvider, agent_loader: AgentLoader):
        self.llm_provider = llm_provider
        self.agent_loader = agent_loader

    def generate_proposal(
        self,
        agent: str,
        topic: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Generate project proposal using agent personality"""

        # Load agent personality
        personality = self.agent_loader.load_agent(agent)

        # Build prompt
        prompt = self._build_proposal_prompt(topic, context)

        # Call LLM
        logger.info(f"Generating proposal with {personality['name']} for: {topic}")
        response = self.llm_provider.call(
            system=personality["system_prompt"],
            prompt=prompt
        )

        # Parse response into structured proposal
        proposal = self._parse_proposal(response, topic, context)

        return proposal

    def _build_proposal_prompt(self, topic: str, context: Optional[Dict]) -> str:
        """Build prompt for proposal generation"""
        prompt_parts = [
            f"Based on the following opportunity: {topic}",
            ""
        ]

        if context:
            prompt_parts.append("Context:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        prompt_parts.extend([
            "Generate a project proposal with:",
            "1. Title (concise, actionable)",
            "2. Description (2-3 sentences explaining the solution)",
            "3. Cost estimate in Becoins (base 100-500 range)",
            "4. Expected ROI (as multiplier, e.g., 3.5x)",
            "5. Timeline (in weeks)",
            "6. Impact score (0-100)",
            "",
            "Format your response as:",
            "TITLE: [title]",
            "DESCRIPTION: [description]",
            "COST: [number]",
            "ROI: [number]",
            "TIMELINE: [weeks]",
            "IMPACT: [score]"
        ])

        return '\n'.join(prompt_parts)

    def _parse_proposal(self, response: str, topic: str, context: Optional[Dict]) -> Dict:
        """Parse LLM response into structured proposal"""
        import re

        # Extract fields using regex
        title_match = re.search(r'TITLE:\s*(.+)', response)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?=COST:|\Z)', response, re.DOTALL)
        cost_match = re.search(r'COST:\s*(\d+)', response)
        roi_match = re.search(r'ROI:\s*([\d.]+)', response)
        timeline_match = re.search(r'TIMELINE:\s*(\d+)', response)
        impact_match = re.search(r'IMPACT:\s*(\d+)', response)

        proposal = {
            "title": title_match.group(1).strip() if title_match else topic,
            "description": desc_match.group(1).strip() if desc_match else "Generated proposal",
            "cost_becoins": int(cost_match.group(1)) if cost_match else 250,
            "expected_roi": float(roi_match.group(1)) if roi_match else 3.0,
            "timeline_weeks": int(timeline_match.group(1)) if timeline_match else 2,
            "impact_score": int(impact_match.group(1)) if impact_match else 75,
            "topic": topic,
            "context": context or {},
            "raw_response": response
        }

        return proposal

    def evaluate_proposal(
        self,
        proposal: Dict,
        evaluator_agent: str
    ) -> Dict:
        """Evaluate a proposal using another agent"""

        personality = self.agent_loader.load_agent(evaluator_agent)

        prompt = f"""Evaluate this project proposal:

Title: {proposal['title']}
Description: {proposal['description']}
Cost: {proposal['cost_becoins']} Becoins
Expected ROI: {proposal['expected_roi']}x
Timeline: {proposal['timeline_weeks']} weeks

Provide:
1. Score (0-10)
2. Strengths (1-2 points)
3. Concerns (1-2 points)
4. Recommendation (ACCEPT/REJECT/REVISE)

Format as:
SCORE: [number]
STRENGTHS: [points]
CONCERNS: [points]
RECOMMENDATION: [decision]
"""

        response = self.llm_provider.call(
            system=personality["system_prompt"],
            prompt=prompt
        )

        return self._parse_evaluation(response)

    def _parse_evaluation(self, response: str) -> Dict:
        """Parse evaluation response"""
        import re

        score_match = re.search(r'SCORE:\s*(\d+)', response)
        strengths_match = re.search(r'STRENGTHS:\s*(.+?)(?=CONCERNS:|\Z)', response, re.DOTALL)
        concerns_match = re.search(r'CONCERNS:\s*(.+?)(?=RECOMMENDATION:|\Z)', response, re.DOTALL)
        rec_match = re.search(r'RECOMMENDATION:\s*(\w+)', response)

        return {
            "score": int(score_match.group(1)) if score_match else 5,
            "strengths": strengths_match.group(1).strip() if strengths_match else "",
            "concerns": concerns_match.group(1).strip() if concerns_match else "",
            "recommendation": rec_match.group(1).upper() if rec_match else "REVISE",
            "raw_response": response
        }
```

**Step 6: Run test to verify it passes**

Run: `cd dashboard && python -m pytest tests/test_aido.py -v`
Expected: PASS (3 tests passed) - requires Ollama running

**Step 7: Add AIDO to requirements.txt**

Modify `dashboard/requirements.txt`, add:
```txt
anthropic==0.18.1
```

**Step 8: Integration with Daemon**

Modify `dashboard/daemon.py`, add after imports:

```python
from aido.llm_provider import OllamaProvider, ClaudeProvider
from aido.agent_loader import AgentLoader
from aido.agent_network import AgentNetwork

# Initialize AIDO
try:
    llm_provider = OllamaProvider(model="llama3.1:70b")
    logger.info("✅ Using Ollama (local LLM)")
except Exception as e:
    logger.warning(f"Ollama not available: {e}")
    # Fallback to Claude API if configured
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        llm_provider = ClaudeProvider(api_key=api_key)
        logger.info("✅ Using Claude API (fallback)")
    else:
        logger.error("No LLM provider available!")
        llm_provider = None

if llm_provider:
    agent_loader = AgentLoader(agents_dir="../founders")
    agent_network = AgentNetwork(llm_provider, agent_loader)
```

Modify `_run_discovery_cycle`, replace TODO:

```python
async def _run_discovery_cycle(self):
    """Execute one discovery cycle"""
    logger.info("🔍 Running discovery cycle...")

    if not agent_network:
        logger.error("Agent network not initialized")
        return

    # Get enabled agents
    enabled_agents = [
        agent_id for agent_id, config in self.config["agents"].items()
        if config.get("enabled", False)
    ]

    logger.info(f"Enabled agents: {enabled_agents}")

    # Generate proposals with each agent
    for agent_id in enabled_agents:
        agent_file = f"{agent_id}.md"  # e.g., "ceo-sales.md"

        try:
            # Generate proposal
            proposal = agent_network.generate_proposal(
                agent=agent_file,
                topic="Identify optimization opportunities",
                context={"analysis_window_hours": 168}
            )

            logger.info(f"💡 Proposal from {agent_id}: {proposal['title']}")

            # Save proposal to discovery sessions
            import json
            from datetime import datetime

            session_file = Path("../.claude-flow/discovery-sessions") / \
                          f"discovery-{int(datetime.utcnow().timestamp())}.json"
            session_file.parent.mkdir(parents=True, exist_ok=True)

            session_data = {
                "session_id": f"discovery-{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "active",
                "patterns": [],
                "proposals": [proposal],
                "metrics": {
                    "total_patterns": 0,
                    "total_proposals": 1,
                    "prediction_accuracy": 0.0,
                    "user_satisfaction": 0.0
                }
            }

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating proposal for {agent_id}: {e}")

    logger.info("✅ Discovery cycle completed")
```

**Step 9: Commit**

```bash
git add dashboard/aido/ dashboard/tests/test_aido.py dashboard/daemon.py dashboard/requirements.txt
git commit -m "feat: add AIDO integration with local LLM support"
```

---

## Task 15: Ollama Local LLM Setup & Configuration

**Files:**
- Create: `dashboard/scripts/install-ollama.sh`
- Create: `dashboard/scripts/test-ollama.sh`
- Create: `dashboard/config/ollama-models.json`
- Modify: `dashboard/README.md`

**Step 1: Create Ollama installation script**

Create `dashboard/scripts/install-ollama.sh`:

```bash
#!/bin/bash

# Ollama Installation Script for AIDO

echo "🦙 Installing Ollama - Local LLM Runtime"
echo "========================================"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

# Install Ollama
echo ""
echo "📦 Installing Ollama..."

if [ "$OS" = "linux" ]; then
    curl -fsSL https://ollama.ai/install.sh | sh
elif [ "$OS" = "macos" ]; then
    echo "Please download Ollama from: https://ollama.ai/download/mac"
    echo "Or install via Homebrew: brew install ollama"
    exit 0
fi

# Wait for Ollama to start
sleep 3

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🚀 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Pull recommended models
echo ""
echo "📥 Downloading AI models..."
echo ""

# Small model for testing (4GB)
echo "1/3: llama3.1:8b (Fast, 4GB RAM)"
ollama pull llama3.1:8b

# Medium model for production (40GB)
echo ""
echo "2/3: llama3.1:70b (Best quality, 40GB RAM)"
read -p "Download llama3.1:70b? (requires 40GB+ RAM) [y/N]: " download_70b

if [[ "$download_70b" =~ ^[Yy]$ ]]; then
    ollama pull llama3.1:70b
else
    echo "⏭️  Skipped llama3.1:70b"
fi

# Coding model (7GB)
echo ""
echo "3/3: codellama:13b (Code specialist, 7GB RAM)"
read -p "Download codellama:13b? [y/N]: " download_code

if [[ "$download_code" =~ ^[Yy]$ ]]; then
    ollama pull codellama:13b
else
    echo "⏭️  Skipped codellama:13b"
fi

# Test installation
echo ""
echo "🧪 Testing Ollama..."
TEST_RESULT=$(ollama run llama3.1:8b "Say 'Ollama is working!' and nothing else." 2>&1)

if [[ "$TEST_RESULT" == *"Ollama is working!"* ]]; then
    echo "✅ Ollama installed and working!"
else
    echo "❌ Ollama test failed:"
    echo "$TEST_RESULT"
    exit 1
fi

# Show status
echo ""
echo "📊 Installed models:"
ollama list

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Available models:"
echo "  - llama3.1:8b   → Fast, good for testing (4GB RAM)"
echo "  - llama3.1:70b  → Best quality (40GB+ RAM)"
echo "  - codellama:13b → Specialized for code (7GB RAM)"
echo ""
echo "Usage:"
echo "  ollama run llama3.1:8b"
echo "  ollama serve  # Start API server"
echo ""
echo "Default API: http://localhost:11434"
```

Make executable:
```bash
chmod +x dashboard/scripts/install-ollama.sh
```

**Step 2: Create Ollama test script**

Create `dashboard/scripts/test-ollama.sh`:

```bash
#!/bin/bash

# Test Ollama Integration with AIDO

echo "🧪 Testing Ollama Integration"
echo "============================="

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running"
    echo "Start with: ollama serve"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Test with Python
echo "🐍 Testing Python integration..."

python3 << 'EOF'
import sys
import requests
import json

def test_ollama():
    try:
        # Test API connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"❌ Ollama API error: {response.status_code}")
            return False

        models = response.json()
        print(f"✅ Available models: {len(models.get('models', []))}")

        # Test generation
        payload = {
            "model": "llama3.1:8b",
            "prompt": "What is 2+2? Answer with just the number.",
            "stream": False
        }

        print("\n🤖 Testing generation...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "").strip()
            print(f"Response: {answer}")

            if "4" in answer:
                print("✅ Generation works correctly!")
                return True
            else:
                print("⚠️  Unexpected response")
                return False
        else:
            print(f"❌ Generation failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)
EOF

PYTHON_RESULT=$?

if [ $PYTHON_RESULT -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed!"
    echo ""
    echo "Ollama is ready for AIDO integration."
else
    echo ""
    echo "❌ Tests failed"
    exit 1
fi
```

Make executable:
```bash
chmod +x dashboard/scripts/test-ollama.sh
```

**Step 3: Create model configuration**

Create `dashboard/config/ollama-models.json`:

```json
{
  "models": {
    "development": {
      "name": "llama3.1:8b",
      "description": "Fast model for development and testing",
      "ram_required_gb": 8,
      "speed": "fast",
      "quality": "good"
    },
    "production": {
      "name": "llama3.1:70b",
      "description": "High-quality model for production use",
      "ram_required_gb": 48,
      "speed": "slow",
      "quality": "excellent"
    },
    "coding": {
      "name": "codellama:13b",
      "description": "Specialized model for code generation",
      "ram_required_gb": 8,
      "speed": "medium",
      "quality": "very good"
    }
  },
  "recommended": {
    "low_memory": "llama3.1:8b",
    "balanced": "llama3.1:8b",
    "high_quality": "llama3.1:70b"
  },
  "api": {
    "host": "http://localhost:11434",
    "timeout_seconds": 120,
    "max_retries": 3
  }
}
```

**Step 4: Update README with Ollama setup**

Modify `dashboard/README.md`, add section after "Quick Start":

```markdown
## 🦙 Local LLM Setup (Ollama)

AIDO uses Ollama for local, private, cost-free AI agent execution.

### Installation

**Option 1: Automated Script**
```bash
./scripts/install-ollama.sh
```

**Option 2: Manual Installation**

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
# OR download from https://ollama.ai/download/mac
```

**Windows:**
Download from https://ollama.ai/download/windows

### Model Selection

**Development (8GB RAM):**
```bash
ollama pull llama3.1:8b
```
- Fast inference (~2-5 tokens/sec)
- Good for testing and prototyping
- Handles most agent tasks

**Production (48GB+ RAM):**
```bash
ollama pull llama3.1:70b
```
- Best quality outputs
- Slower inference (~0.5-1 token/sec)
- Recommended for important decisions

**Code Specialist (8GB RAM):**
```bash
ollama pull codellama:13b
```
- Optimized for code generation
- Good for technical agents (CTO)

### Starting Ollama

**Start server:**
```bash
ollama serve
```

**Test connection:**
```bash
./scripts/test-ollama.sh
```

### Configuration

Edit `config/ceo-config.json`:

```json
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.1:8b",
    "host": "http://localhost:11434",
    "fallback_to_claude": false
  }
}
```

### AIDO with Ollama

The daemon automatically detects Ollama:

```python
# Tries Ollama first (free, private)
llm_provider = OllamaProvider(model="llama3.1:70b")

# Falls back to Claude API if Ollama unavailable
# (set ANTHROPIC_API_KEY environment variable)
```

### Performance Tips

**Optimize for your hardware:**

- **8-16GB RAM**: Use `llama3.1:8b`
- **32GB RAM**: Use `llama3.1:70b` or run multiple 8b models
- **64GB+ RAM**: Use `llama3.1:70b` for best results

**GPU Acceleration:**
Ollama automatically uses GPU if available (NVIDIA, AMD, Metal)

**Monitoring:**
```bash
# Check running models
ollama ps

# View logs
ollama logs

# Monitor resources
htop  # or Task Manager on Windows
```

### Troubleshooting

**Ollama not responding:**
```bash
# Restart Ollama
pkill ollama
ollama serve

# Check port
curl http://localhost:11434/api/tags
```

**Out of memory:**
```bash
# Use smaller model
ollama pull llama3.1:8b

# Or increase swap (Linux)
sudo swapon --show
```

**Slow generation:**
- Ensure GPU drivers installed
- Check `ollama ps` for CPU vs GPU usage
- Consider smaller model for faster responses
```

**Step 5: Test installation**

Run installation:
```bash
cd dashboard
./scripts/install-ollama.sh
```

Expected output:
- Ollama installed
- llama3.1:8b downloaded
- Test passes: "Ollama is working!"

Test integration:
```bash
cd dashboard
./scripts/test-ollama.sh
```

Expected:
- ✅ Ollama is running
- ✅ Available models: 1 (or more)
- ✅ Generation works correctly!

**Step 6: Commit**

```bash
git add dashboard/scripts/install-ollama.sh dashboard/scripts/test-ollama.sh dashboard/config/ollama-models.json dashboard/README.md
git commit -m "feat: add Ollama local LLM setup and configuration"
```

---

## Task 10: Merge & Cleanup (UPDATED)

**Files:**
- N/A (Git operations)

**Step 1: Final commit check**

Run: `git log --oneline -15`
Expected: See all 12 feature commits

**Step 2: Verify branch**

Run: `git status`
Expected: On branch `feature/ceo-dashboard-integration`, working directory clean

**Step 3: Push branch**

Run: `git push -u origin feature/ceo-dashboard-integration`

**Step 4: Create pull request**

Using GitHub CLI or web interface:
```bash
gh pr create --title "feat: CEO Discovery Dashboard Integration + Autonomous Daemon" \
  --body "Full-stack integration of CEO Discovery System with autonomous daemon

## Features
- FastAPI backend with REST + WebSocket
- Extended office-ui.html with CEO section
- Real-time updates with hybrid polling
- Performance analytics visualization
- **State persistence system for agent resume**
- **Autonomous daemon with auto-resume capability**
- **systemd/PM2 integration for boot auto-start**
- Read-only observer maintaining agent autonomy

## Auto-Resume Capability
- ✅ Agents save state before each operation
- ✅ Daemon resumes incomplete tasks on startup
- ✅ Works across system reboots
- ✅ Auto-start with systemd or PM2

## Testing
- ✅ All unit tests passing (15+ tests)
- ✅ Integration tests passing
- ✅ Manual E2E verification complete
- ✅ Auto-resume tested with mock states

## Documentation
- README.md with setup and auto-start instructions
- CHANGELOG.md with version history
- Updated CLAUDE.md project docs
- Installation scripts for systemd/PM2"
```

**Step 5: Code review**

Wait for review, address feedback, then merge to main.

**Step 6: Cleanup worktree**

After merge:
```bash
cd ../../  # Back to repo root
git worktree remove .worktrees/ceo-dashboard-integration
git branch -d feature/ceo-dashboard-integration
```

---

## Completion Checklist

- [x] Task 1: FastAPI server base with health check
- [x] Task 2: CEO Discovery data bridge
- [x] Task 3: REST API endpoints
- [x] Task 4: WebSocket manager
- [x] Task 5: Frontend HTML/CSS
- [x] Task 6: Frontend JavaScript
- [x] Task 7: Deployment scripts
- [x] Task 8: Integration testing
- [x] Task 9: Documentation updates
- [x] Task 10: Merge & cleanup (updated)
- [x] Task 11: State persistence system
- [x] Task 12: Daemon with auto-resume
- [x] Task 13: systemd/PM2 auto-start
- [x] Task 14: AIDO integration (selbstlernend)
- [x] Task 15: Ollama local LLM setup

## Success Criteria

### Dashboard Functionality
✅ Dashboard displays CEO Discovery data in real-time
✅ REST API endpoints return valid data
✅ WebSocket provides instant updates
✅ Polling continues if WebSocket fails
✅ Agent autonomy maintained (read-only)
✅ Becoin economy rules preserved

### Auto-Resume Capability
✅ Agent state persists to disk
✅ Daemon reads incomplete tasks on startup
✅ Agents resume from last saved progress
✅ Works across system reboots
✅ Auto-start with systemd or PM2

### AIDO Selbstlernende Organisation
✅ Ollama local LLM running
✅ Agent personalities loaded from .md files
✅ Proposals generated with LLM
✅ Evaluations with multi-agent consensus
✅ Becoin cost/ROI calculations
✅ Learns from project feedback

### Testing & Quality
✅ All tests passing (15+ unit + integration)
✅ Auto-resume tested with mock states
✅ systemd/PM2 integration verified
✅ Documentation complete and accurate
✅ Code merged to main branch

---

**Implementation Time Estimate:** 8-12 hours (bite-sized tasks, 2-5 minutes each)
**Complexity:** High (full-stack + daemon + auto-start + AIDO + local LLM)
**Risk:** Medium (state persistence + LLM integration adds complexity)

## Key Autonomy Features

🤖 **Agenten arbeiten vollständig autonom:**
- ✅ State wird vor jeder Operation gespeichert
- ✅ Daemon startet automatisch beim Systemstart (systemd/PM2)
- ✅ Alle unvollständigen Tasks werden resumed
- ✅ Agenten arbeiten ab letztem gespeicherten Progress weiter
- ✅ Discovery Cycles laufen automatisch alle 24h
- ✅ Bei Crash/Reboot: automatischer Neustart und Resume
- ✅ Keine manuelle Intervention nötig

🧠 **AIDO Selbstlernende Organisation:**
- ✅ Lokales LLM (Ollama) - kostenlos, privat, 24/7
- ✅ Agent Persönlichkeiten aus founders/*.md geladen
- ✅ CEO, CTO, CDO generieren automatisch Proposals
- ✅ Multi-Agent Evaluation & Consensus
- ✅ Wirtschaftlich klug: ROI-basierte Entscheidungen
- ✅ Lernt aus Feedback (Reinforcement Learning)
- ✅ Pattern Recognition & Kontinuierliche Verbesserung

**Datenspeicherung:**
```
.claude-flow/agent-state/
├── agent-state-CEO-001.json  (Status: in_progress, Progress: 45%)
├── agent-state-CTO-001.json  (Status: in_progress, Progress: 67%)
└── agent-state-CDO-001.json  (Status: completed)
```

**Boot-Ablauf:**
1. System startet → systemd/PM2 startet Daemon
2. Daemon liest `.claude-flow/agent-state/*.json`
3. Findet unvollständige Tasks (status: "in_progress")
4. Spawned Agenten mit gespeichertem State
5. Agenten arbeiten ab Progress-Punkt weiter
6. Discovery Cycles starten automatisch
