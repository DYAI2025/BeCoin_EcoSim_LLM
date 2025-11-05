import random
from datetime import datetime, timezone

import pytest

from becoin_economy.engine import BecoinEconomy
from becoin_economy.models import Agent, Project, Treasury


@pytest.fixture
def sample_economy():
    """Create a baseline economy with deterministic data for tests."""
    treasury = Treasury(start_capital=10000, balance=10000)

    agents = [
        Agent(
            id="AGENT-001",
            name="CEO-Sales",
            role="Revenue Strategist",
            status="IDLE",
            equity_share=0.4,
            is_founder=True,
        ),
        Agent(
            id="AGENT-002",
            name="CTO-Engineer",
            role="Platform Engineer",
            status="IDLE",
            equity_share=0.35,
            is_founder=True,
        ),
        Agent(
            id="AGENT-003",
            name="CDO-Design",
            role="Product Designer",
            status="IDLE",
            equity_share=0.25,
            is_founder=True,
        ),
        Agent(
            id="AGENT-101",
            name="Ops Analyst",
            role="Operations",
            status="IDLE",
            equity_share=0.0,
            is_founder=False,
        ),
    ]

    projects = [
        Project(
            id="PRJ-ALPHA",
            name="Enterprise Outreach",
            stage="pipeline",
            cost=1500,
            value=3500,
            impact_score=72,
            team=["AGENT-001", "AGENT-101"],
        ),
        Project(
            id="PRJ-BETA",
            name="Automation Toolkit",
            stage="pipeline",
            cost=2200,
            value=6200,
            impact_score=88,
            team=["AGENT-002", "AGENT-003"],
        ),
    ]

    return BecoinEconomy(treasury=treasury, agents=agents, projects=projects)


@pytest.fixture
def seeded_random():
    """Deterministic random generator for stress tests."""
    return random.Random(42)
