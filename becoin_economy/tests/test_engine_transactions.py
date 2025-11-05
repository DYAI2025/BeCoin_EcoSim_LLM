"""Unit tests for the Becoin economy engine covering core workflows."""
from datetime import timedelta

import pytest

from becoin_economy.engine import InsufficientFundsError


def test_start_project_moves_pipeline_to_active(sample_economy):
    economy = sample_economy
    starting_balance = economy.treasury.balance

    economy.start_project("PRJ-ALPHA")

    assert economy.projects["PRJ-ALPHA"].stage == "active"
    assert economy.projects["PRJ-ALPHA"].started_at is not None
    assert economy.treasury.balance == starting_balance - economy.projects["PRJ-ALPHA"].cost
    assert any(tx.type == "PROJECT_COST" for tx in economy.treasury.transactions)


def test_complete_project_records_revenue_and_metrics(sample_economy):
    economy = sample_economy
    economy.start_project("PRJ-ALPHA")
    starting_balance = economy.treasury.balance

    economy.complete_project("PRJ-ALPHA")

    project = economy.projects["PRJ-ALPHA"]
    assert project.stage == "completed"
    assert project.completed_at is not None
    assert economy.treasury.balance == pytest.approx(starting_balance + project.value)

    # Team members should record completions and earnings
    for agent_id in project.team:
        agent = economy.agents[agent_id]
        assert agent.performance["projects_completed"] >= 1
        assert agent.performance["becoin_earned"] > 0

    assert any(tx.type == "PROJECT_REVENUE" for tx in economy.treasury.transactions)


def test_pay_agent_updates_treasury_and_agent(sample_economy):
    economy = sample_economy
    starting_balance = economy.treasury.balance

    economy.pay_agent("AGENT-101", amount=250, reason="Weekly stipend")

    assert economy.treasury.balance == starting_balance - 250
    agent = economy.agents["AGENT-101"]
    assert agent.performance["becoin_earned"] >= 250
    assert any(tx.type == "PAYROLL" and tx.metadata["agent_id"] == "AGENT-101" for tx in economy.treasury.transactions)


def test_prevents_overspending(sample_economy):
    economy = sample_economy

    with pytest.raises(InsufficientFundsError):
        economy.pay_agent("AGENT-101", amount=economy.treasury.balance + 1, reason="Overdraft attempt")


def test_snapshot_has_expected_structure(sample_economy):
    economy = sample_economy
    economy.start_project("PRJ-ALPHA")
    economy.complete_project("PRJ-ALPHA")
    economy.pay_agent("AGENT-101", amount=100, reason="Bonus")

    snapshot = economy.snapshot()
    payload = snapshot.to_dashboard_payload()

    assert set(payload.keys()) == {
        "treasury", "agent_roster", "projects", "impact_ledger", "orchestrator_status"
    }

    treasury = payload["treasury"]
    assert {"balance", "startCapital", "metrics", "transactions"}.issubset(treasury.keys())
    assert treasury["metrics"]["burnRate"] >= 0

    roster = payload["agent_roster"]
    assert "founders" in roster and "employees" in roster
    assert any(agent["id"] == "AGENT-001" for agent in roster["founders"])

    projects = payload["projects"]
    assert "completed" in projects and len(projects["completed"]) >= 1
    assert projects["completed"][0]["impactScore"] >= 0

    orchestrator = payload["orchestrator_status"]
    assert orchestrator["treasury"]["balance"] == treasury["balance"]
    assert len(orchestrator["agents"]) == len(roster["founders"] + roster["employees"])


def test_advance_time_reduces_balance_based_on_burn(sample_economy):
    economy = sample_economy
    economy.pay_agent("AGENT-101", amount=200, reason="Stipend")
    starting_balance = economy.treasury.balance

    economy.advance_time(hours=24)

    assert economy.treasury.balance < starting_balance
    assert economy.treasury.metrics["burnRate"] >= 0
    assert economy.treasury.metrics["runwayHours"] > 0


def test_transactions_sum_matches_balance_change(sample_economy):
    economy = sample_economy
    initial_balance = economy.treasury.start_capital

    economy.start_project("PRJ-ALPHA")
    economy.complete_project("PRJ-ALPHA")
    economy.pay_agent("AGENT-101", amount=100, reason="Bonus")

    total_delta = sum(tx.amount for tx in economy.treasury.transactions)
    expected_balance = initial_balance + total_delta
    assert economy.treasury.balance == pytest.approx(expected_balance)
