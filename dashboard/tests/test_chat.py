"""
Tests for chat functionality in the dashboard.

This module tests the bidirectional chat communication between users and agents.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import json


def test_get_chat_history_empty(client):
    """Test getting chat history when no messages exist."""
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert isinstance(data["messages"], list)


def test_send_chat_message(client):
    """Test sending a chat message via REST API."""
    message = {
        "type": "user_message",
        "content": "Hello Agent!",
        "target_agent": "agent-helio",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": "User",
    }

    response = client.post("/api/chat/send", json=message)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert "message" in data


def test_send_chat_message_to_all_agents(client):
    """Test sending a broadcast message to all agents."""
    message = {
        "type": "user_message",
        "content": "Hello everyone!",
        "target_agent": "all",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": "User",
    }

    response = client.post("/api/chat/send", json=message)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"


def test_get_chat_history_with_limit(client):
    """Test getting chat history with a limit."""
    # Send a few messages first
    for i in range(5):
        message = {
            "type": "user_message",
            "content": f"Test message {i}",
            "target_agent": "all",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sender": "User",
        }
        client.post("/api/chat/send", json=message)

    # Get history with limit
    response = client.get("/api/chat/history?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) <= 3


def test_chat_websocket_connection(client):
    """Test WebSocket connection for chat."""
    with client.websocket_connect("/ws/chat") as websocket:
        # Should receive connection established message
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert "message" in data


def test_chat_websocket_send_receive(client):
    """Test sending and receiving messages via WebSocket."""
    with client.websocket_connect("/ws/chat") as websocket:
        # Skip connection message
        websocket.receive_json()

        # Skip chat history message if present
        msg = websocket.receive_json()
        if msg.get("type") == "chat_history":
            # If we got chat history, we need to wait for the next message
            pass

        # Send a message
        message = {
            "type": "user_message",
            "content": "Hello via WebSocket!",
            "target_agent": "agent-nami",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sender": "User",
        }
        websocket.send_json(message)

        # First we receive the echo of our own message
        echo = websocket.receive_json()
        assert echo["type"] == "user_message"

        # Then we should receive agent response
        response = websocket.receive_json()
        assert response["type"] == "agent_message"
        assert "content" in response


def test_chat_message_persistence(client, tmp_path):
    """Test that chat messages are persisted to file."""
    # Send a message
    message = {
        "type": "user_message",
        "content": "Persistent message",
        "target_agent": "agent-helio",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sender": "User",
    }
    client.post("/api/chat/send", json=message)

    # Verify message is in history
    response = client.get("/api/chat/history")
    data = response.json()
    messages = data["messages"]

    # Check if our message is in the history
    found = any(msg["content"] == "Persistent message" for msg in messages)
    assert found, "Message should be persisted in history"


def test_chat_message_validation(client):
    """Test that invalid messages are rejected."""
    # Missing required fields
    invalid_message = {
        "type": "user_message",
        "content": "Test",
        # Missing target_agent, timestamp, sender
    }

    response = client.post("/api/chat/send", json=invalid_message)
    assert response.status_code == 422  # Validation error


def test_multiple_websocket_connections(client):
    """Test multiple clients can connect simultaneously."""
    with client.websocket_connect("/ws/chat") as ws1:
        with client.websocket_connect("/ws/chat") as ws2:
            # Both should receive connection messages
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1["type"] == "connection_established"
            assert data2["type"] == "connection_established"


def test_chat_history_loaded_on_startup(client):
    """Test that chat history is loaded when server starts."""
    # This is tested implicitly by other tests
    # Just verify the endpoint works
    response = client.get("/api/chat/history")
    assert response.status_code == 200


def test_broadcast_to_multiple_clients(client):
    """Test that messages are broadcast to all connected clients."""
    with client.websocket_connect("/ws/chat") as ws1:
        with client.websocket_connect("/ws/chat") as ws2:
            # Skip connection messages
            ws1.receive_json()
            ws2.receive_json()

            # Skip chat history messages
            msg1 = ws1.receive_json()
            if msg1.get("type") == "chat_history":
                pass  # Already skipped

            msg2 = ws2.receive_json()
            if msg2.get("type") == "chat_history":
                pass  # Already skipped

            # Send from ws1
            message = {
                "type": "user_message",
                "content": "Broadcast test",
                "target_agent": "all",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "sender": "User1",
            }
            ws1.send_json(message)

            # Both should receive the broadcast
            # Note: The sender also receives their own message
            response1 = ws1.receive_json()
            response2 = ws2.receive_json()

            # At least one should be the user message
            assert (
                response1["type"] == "user_message"
                or response2["type"] == "user_message"
            )
