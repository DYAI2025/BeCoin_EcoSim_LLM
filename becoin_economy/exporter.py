"""Utilities for exporting Becoin economy state to dashboard-friendly JSON payloads."""
from __future__ import annotations

from typing import Dict

from becoin_economy.engine import BecoinEconomy


def build_dashboard_payload(economy: BecoinEconomy) -> Dict[str, dict]:
    """Generate dashboard JSON payloads from the current economy state."""
    snapshot = economy.snapshot()
    dashboard_payload = snapshot.to_dashboard_payload()

    return {
        "treasury.json": dashboard_payload["treasury"],
        "agent-roster.json": dashboard_payload["agent_roster"],
        "projects.json": dashboard_payload["projects"],
        "impact-ledger.json": dashboard_payload["impact_ledger"],
        "orchestrator-status.json": dashboard_payload["orchestrator_status"],
    }


__all__ = ["build_dashboard_payload"]
