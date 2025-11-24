"""Economy-aware context helpers for autonomous agents.

This module bridges the BeCoin EcoSim engine into the autonomous agent
experience so LLM-powered personalities can reason about treasury health,
project pipelines, and agent availability while they plan or chat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from becoin_economy.engine import BecoinEconomy
from becoin_economy.models import Agent, Project, Treasury


@dataclass
class EconomyContext:
    """Lightweight view of the simulated BeCoin economy."""

    balance: float
    burn_rate: float
    runway_hours: float | None
    profit_margin: float
    founders: List[Agent]
    employees: List[Agent]
    active_projects: List[Project]
    pipeline_projects: List[Project]
    completed_projects: List[Project]

    def describe(self) -> str:
        """Render a human-readable description for prompts."""

        agent_summary = _summarize_agents(self.founders + self.employees)
        project_summary = _summarize_projects(
            self.active_projects, self.pipeline_projects, self.completed_projects
        )

        runway = "∞" if self.runway_hours is None else f"{self.runway_hours:.1f}h"

        return "\n".join(
            [
                f"Treasury balance: {self.balance:.2f} BeCoins",
                f"Burn rate (last window): {self.burn_rate:.2f} BC/h",
                f"Runway remaining: {runway}",
                f"Profit margin: {self.profit_margin:.2f}%",
                "",
                "Agent availability:",
                agent_summary,
                "",
                "Projects:",
                project_summary,
            ]
        )


def build_default_economy() -> BecoinEconomy:
    """Create a default BecoinEconomy used by autonomous agents.

    The defaults mirror the deterministic fixtures used in the economy test
    suite so chat sessions and orchestrator prompts share the same baseline.
    """

    treasury = Treasury(start_capital=10000, balance=10000)

    agents: Iterable[Agent] = [
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

    projects: Iterable[Project] = [
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
            stage="active",
            cost=2200,
            value=6200,
            impact_score=88,
            team=["AGENT-002", "AGENT-003"],
        ),
        Project(
            id="PRJ-GAMMA",
            name="Acquisition Experiment",
            stage="completed",
            cost=1200,
            value=2600,
            impact_score=61,
            team=["AGENT-001", "AGENT-002"],
        ),
    ]

    economy = BecoinEconomy(
        treasury=treasury,
        agents=agents,
        projects=projects,
    )

    # Let the economy compute baseline metrics so the summary stays realistic.
    economy.advance_time(hours=24)

    return economy


def summarize_economy(economy: BecoinEconomy) -> EconomyContext:
    """Build an EconomyContext snapshot for prompt injection."""

    snapshot = economy.snapshot()
    treasury = snapshot.treasury

    agents = list(snapshot.agents.values())
    founders = [agent for agent in agents if agent.is_founder]
    employees = [agent for agent in agents if not agent.is_founder]

    projects = list(snapshot.projects.values())
    active = [project for project in projects if project.stage == "active"]
    pipeline = [project for project in projects if project.stage == "pipeline"]
    completed = [project for project in projects if project.stage == "completed"]

    runway = treasury.metrics.get("runwayHours")
    runway_hours = None if runway is None or runway == float("inf") else runway

    return EconomyContext(
        balance=treasury.balance,
        burn_rate=treasury.metrics.get("burnRate", 0.0),
        runway_hours=runway_hours,
        profit_margin=treasury.metrics.get("profitMargin", 0.0),
        founders=founders,
        employees=employees,
        active_projects=active,
        pipeline_projects=pipeline,
        completed_projects=completed,
    )


def _summarize_agents(agents: Iterable[Agent]) -> str:
    by_status: Dict[str, List[Agent]] = {}
    for agent in agents:
        by_status.setdefault(agent.status, []).append(agent)

    lines: List[str] = []
    for status, status_agents in sorted(by_status.items()):
        names = ", ".join(agent.name for agent in status_agents)
        lines.append(f"- {status}: {names}")

    return "\n".join(lines) if lines else "- No agents registered"


def _summarize_projects(
    active: Iterable[Project],
    pipeline: Iterable[Project],
    completed: Iterable[Project],
) -> str:
    sections: List[Tuple[str, Iterable[Project]]] = [
        ("Active", active),
        ("Pipeline", pipeline),
        ("Completed", completed),
    ]

    lines: List[str] = []
    for title, projects in sections:
        projects_list = list(projects)
        if not projects_list:
            lines.append(f"- {title}: none")
            continue

        for project in projects_list:
            lines.append(
                "- {title}: {name} (cost {cost:.0f} → value {value:.0f}, impact {impact})".format(
                    title=title,
                    name=project.name,
                    cost=project.cost,
                    value=project.value,
                    impact=project.impact_score,
                )
            )

    return "\n".join(lines)


__all__ = [
    "EconomyContext",
    "build_default_economy",
    "summarize_economy",
]
