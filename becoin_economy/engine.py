"""Simulation engine for the Becoin economy."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from becoin_economy.models import Agent, EconomySnapshot, ImpactRecord, Project, Transaction, Treasury


class EconomyError(Exception):
    """Base exception for economy issues."""


class InsufficientFundsError(EconomyError):
    """Raised when an operation would result in a negative treasury balance."""


class UnknownProjectError(EconomyError):
    """Raised when a project cannot be found."""


class UnknownAgentError(EconomyError):
    """Raised when an agent cannot be found."""


class BecoinEconomy:
    """Encapsulates treasury, agent, and project orchestration."""

    def __init__(
        self,
        treasury: Treasury,
        agents: Iterable[Agent],
        projects: Iterable[Project],
        impact_records: Optional[List[ImpactRecord]] = None,
        baseline_hourly_burn: float = 120.0,
    ) -> None:
        self.treasury = treasury
        self.agents: Dict[str, Agent] = {agent.id: agent for agent in agents}
        self.projects: Dict[str, Project] = {project.id: project for project in projects}
        self.impact_records: List[ImpactRecord] = list(impact_records or [])
        self.baseline_hourly_burn = baseline_hourly_burn

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def start_project(self, project_id: str) -> None:
        project = self._get_project(project_id)
        if project.stage not in {"pipeline", "paused"}:
            return

        self._spend(
            amount=project.cost,
            tx_type="PROJECT_COST",
            description=f"Kickoff for {project.name}",
            metadata={"project_id": project.id},
        )

        project.stage = "active"
        project.started_at = datetime.now(timezone.utc)

        for agent_id in project.team:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            agent.status = "ACTIVE"
            agent.current_task = project.name

    def complete_project(self, project_id: str) -> None:
        project = self._get_project(project_id)
        if project.stage != "active":
            return

        self._earn(
            amount=project.value,
            tx_type="PROJECT_REVENUE",
            description=f"Revenue from {project.name}",
            metadata={"project_id": project.id},
        )

        project.stage = "completed"
        project.completed_at = datetime.now(timezone.utc)

        allocation = project.value * 0.1
        per_agent_bonus = allocation / max(len(project.team), 1)

        for agent_id in project.team:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            agent.status = "IDLE"
            agent.current_task = None
            agent.performance["projects_completed"] = agent.performance.get("projects_completed", 0) + 1
            agent.performance["becoin_earned"] = agent.performance.get("becoin_earned", 0) + per_agent_bonus

        roi = project.value / project.cost if project.cost else 0
        self.impact_records.append(
            ImpactRecord(
                project_id=project.id,
                impact_score=project.impact_score,
                roi=roi,
                notes=f"Project {project.name} delivered",
            )
        )

    def pay_agent(self, agent_id: str, amount: float, reason: str) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")

        agent = self.agents.get(agent_id)
        if not agent:
            raise UnknownAgentError(agent_id)

        self._spend(
            amount=amount,
            tx_type="PAYROLL",
            description=reason,
            metadata={"agent_id": agent_id},
        )

        agent.performance["becoin_earned"] = agent.performance.get("becoin_earned", 0) + amount

    def advance_time(self, hours: int) -> None:
        if hours <= 0:
            raise ValueError("hours must be positive")

        effective_burn_rate = max(self.treasury.metrics.get("burnRate", 0.0), self.baseline_hourly_burn)
        spend = min(effective_burn_rate * hours, self.treasury.balance)

        if spend == 0:
            return

        self._spend(
            amount=spend,
            tx_type="OPERATIONS_COST",
            description=f"Operational runway burn for {hours}h",
            metadata={"hours": hours, "burnRate": effective_burn_rate},
        )

    def snapshot(self) -> EconomySnapshot:
        return EconomySnapshot(
            treasury=self.treasury,
            agents=self.agents,
            projects=self.projects,
            impact_records=list(self.impact_records),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_project(self, project_id: str) -> Project:
        try:
            return self.projects[project_id]
        except KeyError as exc:
            raise UnknownProjectError(project_id) from exc

    def _spend(self, amount: float, tx_type: str, description: str, metadata: Optional[Dict[str, object]] = None) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")

        signed_amount = -abs(amount)
        if self.treasury.balance + signed_amount < 0:
            raise InsufficientFundsError(f"Treasury balance would drop below zero (attempted spend: {amount})")

        transaction = Transaction(
            timestamp=datetime.now(timezone.utc),
            type=tx_type,
            amount=signed_amount,
            description=description,
            metadata=metadata or {},
        )
        self.treasury.apply_transaction(transaction)

    def _earn(self, amount: float, tx_type: str, description: str, metadata: Optional[Dict[str, object]] = None) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")

        transaction = Transaction(
            timestamp=datetime.now(timezone.utc),
            type=tx_type,
            amount=abs(amount),
            description=description,
            metadata=metadata or {},
        )
        self.treasury.apply_transaction(transaction)


__all__ = [
    "BecoinEconomy",
    "EconomyError",
    "InsufficientFundsError",
    "UnknownProjectError",
    "UnknownAgentError",
]
