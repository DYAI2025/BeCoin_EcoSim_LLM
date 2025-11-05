"""Tests for translating economy snapshots into dashboard JSON payloads."""

from becoin_economy.exporter import build_dashboard_payload


def test_payload_files_match_dashboard_expectations(sample_economy):
    economy = sample_economy
    economy.start_project("PRJ-ALPHA")
    economy.complete_project("PRJ-ALPHA")

    payload = build_dashboard_payload(economy)

    expected_files = {
        "treasury.json",
        "agent-roster.json",
        "projects.json",
        "impact-ledger.json",
        "orchestrator-status.json",
    }

    assert set(payload.keys()) == expected_files

    treasury = payload["treasury.json"]
    assert treasury["balance"] == economy.treasury.balance
    assert treasury["metrics"]["runwayHours"] >= 0
    assert len(treasury["transactions"]) == len(economy.treasury.transactions)

    roster = payload["agent-roster.json"]
    assert roster["founders"]
    assert all("equityShare" in agent for agent in roster["founders"])

    projects = payload["projects.json"]
    assert any(project["stage"] == "completed" for project in projects["completed"])

    orchestrator = payload["orchestrator-status.json"]
    assert orchestrator["treasury"]["metrics"]["burnRate"] == treasury["metrics"]["burnRate"]
    assert orchestrator["agents"]


def test_payload_transactions_are_serializable(sample_economy):
    economy = sample_economy
    economy.start_project("PRJ-ALPHA")
    payload = build_dashboard_payload(economy)

    # Ensure no datetime objects leak through serialization boundary
    for tx in payload["treasury.json"]["transactions"]:
        assert isinstance(tx["timestamp"], str)
