"""
Test suite for CEO Discovery Data Bridge.

This test ensures the data bridge correctly reads and formats
CEO Discovery session data for API consumption.
"""
import pytest
import json
import tempfile
from pathlib import Path


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


def test_data_bridge_imports():
    """Test that data bridge module can be imported"""
    try:
        from dashboard.ceo_data_bridge import CEODataBridge
        assert CEODataBridge is not None
    except ImportError:
        pytest.fail("Failed to import CEODataBridge")


def test_get_current_session(temp_discovery_dir):
    """Test reading current discovery session"""
    from dashboard.ceo_data_bridge import CEODataBridge

    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    session = bridge.get_current_session()

    assert session is not None
    assert session["session_id"] == "discovery-1234567890"
    assert session["status"] == "active"
    assert len(session["patterns"]) == 1
    assert len(session["proposals"]) == 1


def test_get_proposals(temp_discovery_dir):
    """Test getting proposals with filtering"""
    from dashboard.ceo_data_bridge import CEODataBridge

    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    proposals = bridge.get_proposals(min_roi=3.0)

    assert len(proposals) == 1
    assert proposals[0]["id"] == "proposal-001"
    assert proposals[0]["roi"] >= 3.0


def test_get_proposals_below_threshold(temp_discovery_dir):
    """Test filtering proposals below ROI threshold"""
    from dashboard.ceo_data_bridge import CEODataBridge

    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    proposals = bridge.get_proposals(min_roi=5.0)

    assert len(proposals) == 0


def test_get_patterns(temp_discovery_dir):
    """Test getting patterns by type"""
    from dashboard.ceo_data_bridge import CEODataBridge

    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    patterns = bridge.get_patterns(pattern_type="repetitive")

    assert len(patterns) == 1
    assert patterns[0]["type"] == "repetitive"


def test_get_all_patterns(temp_discovery_dir):
    """Test getting all patterns without filtering"""
    from dashboard.ceo_data_bridge import CEODataBridge

    bridge = CEODataBridge(discovery_sessions_path=temp_discovery_dir)
    patterns = bridge.get_patterns()

    assert len(patterns) == 1


def test_no_sessions():
    """Test behavior when no sessions exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        from dashboard.ceo_data_bridge import CEODataBridge

        bridge = CEODataBridge(discovery_sessions_path=tmpdir)
        session = bridge.get_current_session()

        assert session["status"] == "idle"
        assert session["proposals"] == []
        assert session["patterns"] == []


def test_invalid_json():
    """Test handling of corrupted JSON files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        from dashboard.ceo_data_bridge import CEODataBridge

        # Create invalid JSON file
        invalid_path = Path(tmpdir) / "discovery-9999999999.json"
        with open(invalid_path, 'w') as f:
            f.write("{ invalid json }")

        bridge = CEODataBridge(discovery_sessions_path=tmpdir)
        session = bridge.get_current_session()

        # Should fall back to empty session
        assert session["status"] == "idle"
