import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from exuviae_hub.adapters.http.routes import ConnectionManager

@pytest.mark.anyio
async def test_ws_manager_whitelist_enforcement():
    """Verify that ConnectionManager only broadcasts allowed message types from the contract."""
    manager = ConnectionManager()
    
    # Mock connections
    conn1 = AsyncMock()
    manager.active_connections = [conn1]
    
    # 1. Reject an unknown message type
    bad_msg = json.dumps({"type": "malicious_command", "target": "all"})
    await manager.broadcast(bad_msg)
    conn1.send_text.assert_not_called()
    
    # 2. Accept a valid message type from contract (e.g. command.capture_snapshot)
    # We use a known valid example structure
    valid_msg = json.dumps({
        "type": "command.capture_snapshot",
        "snapshot_id": "s-20260202-173012-4f2a9c10",
        "params": {"format": "jpeg", "resolution": "640x480"}
    })
    await manager.broadcast(valid_msg)
    conn1.send_text.assert_called_once_with(valid_msg)

@pytest.mark.anyio
async def test_ws_manager_garbage_rejection():
    """Verify that non-JSON or malformed messages are safely ignored."""
    manager = ConnectionManager()
    conn1 = AsyncMock()
    manager.active_connections = [conn1]
    
    await manager.broadcast("not-a-json")
    conn1.send_text.assert_not_called()
    
    await manager.broadcast('{"no_type": 1}')
    conn1.send_text.assert_not_called()

def test_whitelist_extraction_from_contract():
    """Verify that the manager correctly extracts types from the actual schema file."""
    manager = ConnectionManager()
    # Based on messages.schema.json, we expect at least these:
    expected_types = {"command.capture_snapshot", "ack", "error", "heartbeat"}
    assert expected_types.issubset(manager._whitelist)
    # Ensure no random guesswork
    assert "malicious_command" not in manager._whitelist
