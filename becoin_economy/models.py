"""Core domain models for the Becoin economy simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from math import isinf
from typing import Dict, List, Optional


@dataclass
class Transaction:
    """Record of a treasury movement."""

    timestamp: datetime
    type: str
    amount: float
    description: str
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "type": self.type,
            "amount": round(self.amount, 2),
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class Treasury:
    """Represents the shared treasury across the Becoin economy."""

    start_capital: float
    balance: float
    burn_window_hours: int = 72
    transactions: List[Transaction] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=lambda: {
        "burnRate": 0.0,
        "runwayHours": float("inf"),
        "profitMargin": 0.0,
    })
    _total_revenue: float = 0.0
    _total_cost: float = 0.0

    def apply_transaction(self, transaction: Transaction) -> None:
        self.balance += transaction.amount
        self.transactions.append(transaction)

        if transaction.amount >= 0:
            self._total_revenue += transaction.amount
        else:
            self._total_cost += abs(transaction.amount)

        self._update_metrics()

    def _update_metrics(self) -> None:
        window_start = datetime.now(timezone.utc) - timedelta(hours=self.burn_window_hours)
        recent_costs = [
            -tx.amount
            for tx in self.transactions
            if tx.amount < 0 and tx.timestamp >= window_start
        ]
        burn_rate = sum(recent_costs) / max(self.burn_window_hours, 1)
        self.metrics["burnRate"] = round(burn_rate, 2)

        if burn_rate > 0:
            self.metrics["runwayHours"] = round(self.balance / burn_rate, 2)
        else:
            self.metrics["runwayHours"] = float("inf")

        if self._total_revenue > 0:
            profit_margin = (self._total_revenue - self._total_cost) / self._total_revenue * 100
            self.metrics["profitMargin"] = round(profit_margin, 2)
        else:
            self.metrics["profitMargin"] = -100.0 if self._total_cost else 0.0


@dataclass
class Agent:
    """Represents an autonomous agent participating in the economy."""

    id: str
    name: str
    role: str
    status: str
    equity_share: float
    is_founder: bool = True
    current_task: Optional[str] = None
    performance: Dict[str, float] = field(default_factory=lambda: {
        "becoin_earned": 0.0,
        "projects_completed": 0,
    })

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "equityShare": self.equity_share,
            "current_task": self.current_task,
            "performance": {
                "becoinEarned": round(self.performance.get("becoin_earned", 0), 2),
                "projectsCompleted": int(self.performance.get("projects_completed", 0)),
            },
        }


@dataclass
class Project:
    """Represents a project within the economy."""

    id: str
    name: str
    stage: str
    cost: float
    value: float
    impact_score: int
    team: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "stage": self.stage,
            "value": round(self.value, 2),
            "impactScore": self.impact_score,
            "team": self.team,
        }


@dataclass
class ImpactRecord:
    """Aggregated impact metrics for dashboard display."""

    project_id: str
    impact_score: int
    roi: float
    notes: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, object]:
        return {
            "projectId": self.project_id,
            "impactScore": self.impact_score,
            "roi": round(self.roi, 2),
            "notes": self.notes,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }


@dataclass
class EconomySnapshot:
    """Immutable snapshot of the economy for export and dashboard usage."""

    treasury: Treasury
    agents: Dict[str, Agent]
    projects: Dict[str, Project]
    impact_records: List[ImpactRecord]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dashboard_payload(self) -> Dict[str, object]:
        founders = [agent.to_dict() for agent in self.agents.values() if agent.is_founder]
        employees = [agent.to_dict() for agent in self.agents.values() if not agent.is_founder]

        active = [p.to_dict() for p in self.projects.values() if p.stage == "active"]
        pipeline = [p.to_dict() for p in self.projects.values() if p.stage == "pipeline"]
        completed = [p.to_dict() for p in self.projects.values() if p.stage == "completed"]

        runway = self.treasury.metrics["runwayHours"]
        runway_serializable = None if isinf(runway) else round(runway, 2)

        treasury_dict = {
            "balance": round(self.treasury.balance, 2),
            "startCapital": self.treasury.start_capital,
            "metrics": {
                "burnRate": self.treasury.metrics["burnRate"],
                "runwayHours": runway_serializable,
                "profitMargin": self.treasury.metrics["profitMargin"],
            },
            "transactions": [tx.to_dict() for tx in sorted(self.treasury.transactions, key=lambda tx: tx.timestamp)],
        }

        return {
            "treasury": treasury_dict,
            "agent_roster": {
                "founders": founders,
                "employees": employees,
            },
            "projects": {
                "active": active,
                "pipeline": pipeline,
                "completed": completed,
            },
            "impact_ledger": {
                "records": [record.to_dict() for record in self.impact_records],
                "totalImpactScore": sum(record.impact_score for record in self.impact_records),
            },
            "orchestrator_status": {
                "lastUpdate": self.generated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "agents": founders + employees,
                "treasury": {
                    "balance": treasury_dict["balance"],
                    "metrics": treasury_dict["metrics"],
                },
                "activeProjects": active,
            },
        }
