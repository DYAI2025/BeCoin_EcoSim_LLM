"""
Test suite for WebSocket Manager.

This test ensures WebSocket connections work correctly for
real-time CEO Discovery updates.
"""
import pytest
from fastapi.testclient import TestClient


def test_websocket_manager_imports():
    """Test that WebSocketManager can be imported"""
    try:
        from dashboard.websocket_manager import WebSocketManager
        assert WebSocketManager is not None
    except ImportError:
        pytest.fail("Failed to import WebSocketManager")


def test_websocket_manager_initialization():
    """Test WebSocketManager initialization"""
    from dashboard.websocket_manager import WebSocketManager

    manager = WebSocketManager()
    assert manager is not None
    assert hasattr(manager, 'active_connections')
    assert len(manager.active_connections) == 0


def test_websocket_connection():
    """Test WebSocket connection establishment"""
    from dashboard.server import app

    client = TestClient(app)

    with client.websocket_connect("/ws/ceo") as websocket:
        # Should connect successfully and receive connection message
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] == "connection_established"
        assert "message" in data
        assert "timestamp" in data


def test_websocket_multiple_connections():
    """Test multiple WebSocket connections"""
    from dashboard.server import app

    client = TestClient(app)

    # Connect first client
    with client.websocket_connect("/ws/ceo") as ws1:
        msg1 = ws1.receive_json()
        assert msg1["type"] == "connection_established"

        # Connect second client
        with client.websocket_connect("/ws/ceo") as ws2:
            msg2 = ws2.receive_json()
            assert msg2["type"] == "connection_established"


@pytest.mark.asyncio
async def test_websocket_broadcast():
    """Test broadcast functionality"""
    from dashboard.websocket_manager import WebSocketManager
    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()

    # Create mock WebSocket
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()

    # Add to connections
    manager.active_connections.append(mock_ws)

    # Broadcast message
    test_message = {"type": "test", "data": "hello"}
    await manager.broadcast(test_message)

    # Verify send was called
    mock_ws.send_json.assert_called_once_with(test_message)


@pytest.mark.asyncio
async def test_websocket_broadcast_new_proposal():
    """Test broadcast new proposal event"""
    from dashboard.websocket_manager import WebSocketManager
    from unittest.mock import AsyncMock, MagicMock

    manager = WebSocketManager()
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()
    manager.active_connections.append(mock_ws)

    proposal = {
        "id": "proposal-001",
        "title": "Test Proposal",
        "roi": 4.2
    }

    await manager.broadcast_new_proposal(proposal)

    # Verify correct message structure
    call_args = mock_ws.send_json.call_args[0][0]
    assert call_args["type"] == "new_proposal"
    assert call_args["proposal"] == proposal
    assert "timestamp" in call_args


@pytest.mark.asyncio
async def test_websocket_disconnect_cleanup():
    """Test disconnection cleanup"""
    from dashboard.websocket_manager import WebSocketManager
    from unittest.mock import MagicMock

    manager = WebSocketManager()

    # Create mock WebSockets
    mock_ws1 = MagicMock()
    mock_ws2 = MagicMock()

    manager.active_connections.extend([mock_ws1, mock_ws2])
    assert len(manager.active_connections) == 2

    # Disconnect one
    manager.disconnect(mock_ws1)
    assert len(manager.active_connections) == 1
    assert mock_ws2 in manager.active_connections
    assert mock_ws1 not in manager.active_connections
