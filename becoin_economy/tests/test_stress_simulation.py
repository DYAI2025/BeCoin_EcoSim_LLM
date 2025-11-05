"""Stress tests for the Becoin economy logic to expose weaknesses."""
from datetime import timedelta

import pytest

from becoin_economy.engine import InsufficientFundsError


def test_randomized_simulation_does_not_break_invariants(sample_economy, seeded_random):
    economy = sample_economy
    rng = seeded_random

    operations = ["start", "complete", "pay", "advance"]

    for _ in range(200):
        op = rng.choice(operations)

        if op == "start":
            pipeline_projects = [p for p in economy.projects.values() if p.stage == "pipeline"]
            if pipeline_projects:
                economy.start_project(rng.choice(pipeline_projects).id)
        elif op == "complete":
            active_projects = [p for p in economy.projects.values() if p.stage == "active"]
            if active_projects:
                economy.complete_project(rng.choice(active_projects).id)
        elif op == "pay":
            agent = rng.choice(list(economy.agents.values()))
            amount = rng.randint(50, 400)
            try:
                economy.pay_agent(agent.id, amount=amount, reason="Stress stipend")
            except InsufficientFundsError:
                # Expected in low-balance scenarios; ensure balance never becomes negative
                assert economy.treasury.balance >= 0
        elif op == "advance":
            hours = rng.choice([6, 12, 24])
            economy.advance_time(hours=hours)

        # Invariants after each step
        assert economy.treasury.balance >= 0
        for tx in economy.treasury.transactions:
            assert isinstance(tx.amount, (int, float))
            assert tx.type
            assert tx.timestamp is not None

    snapshot = economy.snapshot()
    assert snapshot.treasury.balance == pytest.approx(economy.treasury.balance)
    assert snapshot.treasury.metrics["burnRate"] >= 0
    assert snapshot.treasury.metrics["runwayHours"] >= 0


def test_snapshot_transactions_sorted(sample_economy):
    economy = sample_economy
    economy.start_project("PRJ-ALPHA")
    economy.complete_project("PRJ-ALPHA")
    economy.pay_agent("AGENT-101", amount=200, reason="QA bonus")

    snapshot = economy.snapshot()
    txs = snapshot.treasury.transactions
    assert txs == sorted(txs, key=lambda tx: tx.timestamp)
