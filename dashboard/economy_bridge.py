"""
Economy Bridge für Dashboard-Chat Integration

Verbindet Dashboard-Chat mit der BeCoin Economy Engine und ermöglicht:
- Context-Bereitstellung für LLM (Treasury, Projekte, Metriken)
- Action-Execution (Projekte starten, Treasury prüfen, etc.)
- Treasury-Safety Guardrails (Balance niemals <0)
- Dashboard-Updates nach Aktionen
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Try to import BeCoin Economy components
try:
    import sys
    becoin_path = Path(__file__).parent.parent / "becoin_economy"
    sys.path.insert(0, str(becoin_path))

    from becoin_economy.engine import BecoinEconomy
    from becoin_economy.models import Project, Agent, Treasury, Transaction
    from becoin_economy.exporter import build_dashboard_payload

    BECOIN_AVAILABLE = True
    logger.info("✅ BeCoin Economy imported successfully")
except ImportError as e:
    BECOIN_AVAILABLE = False
    logger.warning(f"⚠️  BeCoin Economy not available: {e}")


class EconomyBridge:
    """
    Bridge zwischen Dashboard-Chat und BeCoin Economy Engine.

    Ermöglicht:
    1. Context-Bereitstellung für LLM-Prompts
    2. Action-Execution mit Treasury-Safety
    3. Dashboard-Updates nach Änderungen
    """

    def __init__(self, economy: Optional['BecoinEconomy'] = None):
        """
        Initialisiert Economy Bridge.

        Args:
            economy: BecoinEconomy Instanz (optional, kann später gesetzt werden)
        """
        self.economy = economy
        self._mock_mode = not BECOIN_AVAILABLE or economy is None

        if self._mock_mode:
            logger.warning("⚠️  Economy Bridge running in MOCK mode")
        else:
            logger.info("✅ Economy Bridge initialized with real economy")

    def set_economy(self, economy: 'BecoinEconomy'):
        """
        Setzt Economy-Instanz (wenn später initialisiert).

        Args:
            economy: BecoinEconomy Instanz
        """
        self.economy = economy
        self._mock_mode = False
        logger.info("✅ Economy Bridge switched to real mode")

    def get_context_for_chat(self) -> Dict:
        """
        Liefert aktuellen Firmen-Context für LLM-Prompts.

        Returns:
            Dict mit Treasury, Projekten, Agenten, Metrics
        """
        if self._mock_mode:
            return self._get_mock_context()

        try:
            snapshot = self.economy.snapshot()

            # Calculate metrics
            burn_rate = self._calculate_burn_rate(snapshot)
            runway_hours = self._calculate_runway(snapshot.treasury.balance, burn_rate)

            return {
                "treasury": {
                    "balance": snapshot.treasury.balance,
                    "start_capital": snapshot.treasury.start_capital,
                    "burn_rate": burn_rate,
                    "runway_hours": runway_hours
                },
                "projects": {
                    "active": [self._project_summary(p) for p in snapshot.projects_active],
                    "pipeline": [self._project_summary(p) for p in snapshot.projects_pipeline],
                    "completed": len(snapshot.projects_completed)
                },
                "agents": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "status": agent.status,
                        "equity": agent.equity_share,
                        "earned": getattr(agent.metrics, 'becoins_earned', 0)
                    }
                    for agent in snapshot.agents
                ]
            }
        except Exception as e:
            logger.error(f"Error getting economy context: {e}")
            return self._get_mock_context()

    def _get_mock_context(self) -> Dict:
        """Gibt Mock-Context zurück (für Tests oder wenn Economy nicht verfügbar)."""
        return {
            "treasury": {
                "balance": 5000,
                "start_capital": 10000,
                "burn_rate": 50.0,
                "runway_hours": 100.0
            },
            "projects": {
                "active": [
                    {"id": "mock-1", "name": "Dashboard Chat", "value": 1000, "stage": "active"}
                ],
                "pipeline": [
                    {"id": "mock-2", "name": "Analytics", "value": 1500, "stage": "pipeline"}
                ],
                "completed": 3
            },
            "agents": [
                {"id": "agent-helio", "name": "Helio", "status": "active", "equity": 0.25, "earned": 2500},
                {"id": "agent-nami", "name": "Nami", "status": "active", "equity": 0.25, "earned": 2300}
            ]
        }

    def execute_agent_action(self, agent_id: str, action: Dict) -> Dict:
        """
        Führt Agent-Aktion aus (z.B. Projekt starten, Treasury prüfen).

        Args:
            agent_id: Agent-Identifikator
            action: Aktion-Dict mit type, parameters

        Returns:
            Result-Dict mit status, message, changes
        """
        action_type = action.get("type")

        if action_type == "start_project":
            return self._start_project(
                agent_id=agent_id,
                project_name=action.get("project_name", "Unnamed Project"),
                budget=action.get("budget", 0)
            )

        elif action_type == "check_treasury":
            return self._check_treasury()

        elif action_type == "complete_project":
            return self._complete_project(
                project_id=action.get("project_id", "")
            )

        elif action_type == "analyze_burn_rate":
            return self._analyze_burn_rate()

        else:
            return {
                "status": "error",
                "message": f"❌ Unbekannte Aktion: {action_type}"
            }

    def _start_project(self, agent_id: str, project_name: str, budget: int) -> Dict:
        """
        Startet neues Projekt (mit Treasury-Safety-Check).

        Args:
            agent_id: Agent-ID der das Projekt startet
            project_name: Projekt-Name
            budget: Projekt-Budget in Bc

        Returns:
            Result-Dict mit status, message, changes
        """
        if self._mock_mode:
            return {
                "status": "success",
                "message": f"✅ [MOCK] Projekt '{project_name}' würde gestartet. Budget: {budget} Bc",
                "mock": True
            }

        try:
            # Treasury-Safety-Check
            current_balance = self.economy.treasury.balance

            if current_balance < budget:
                return {
                    "status": "rejected",
                    "message": f"❌ TREASURY SAFETY: Insufficient funds. Balance: {current_balance:,} Bc, Required: {budget:,} Bc",
                    "guardrail": "TREASURY_SAFETY",
                    "balance": current_balance,
                    "required": budget
                }

            # Runway-Check: Mind. 24h Runway nach Projekt-Start
            burn_rate = self._calculate_burn_rate(self.economy.snapshot())
            new_balance = current_balance - budget
            runway_hours = self._calculate_runway(new_balance, burn_rate)

            if runway_hours < 24:
                return {
                    "status": "rejected",
                    "message": f"❌ RUNWAY SAFETY: Nur {runway_hours:.1f}h Runway nach Projekt. Mindestens 24h erforderlich.",
                    "guardrail": "RUNWAY_SAFETY",
                    "runway_hours": runway_hours
                }

            # Projekt erstellen und starten
            project_id = f"project-{project_name.lower().replace(' ', '-')}"
            project = Project(
                id=project_id,
                name=project_name,
                value=budget,
                team=[agent_id],
                status="active"
            )

            self.economy.start_project(project)

            logger.info(f"✅ Project '{project_name}' started by {agent_id}. Budget: {budget} Bc")

            return {
                "status": "success",
                "message": f"✅ Projekt '{project_name}' gestartet. Budget: {budget:,} Bc. Neue Balance: {new_balance:,} Bc",
                "project_id": project_id,
                "changes": {
                    "treasury": -budget,
                    "active_projects": +1,
                    "new_balance": new_balance,
                    "runway_hours": runway_hours
                }
            }

        except Exception as e:
            logger.error(f"Error starting project '{project_name}': {e}")
            return {
                "status": "error",
                "message": f"❌ Fehler beim Projektstart: {str(e)}",
                "error": str(e)
            }

    def _check_treasury(self) -> Dict:
        """
        Gibt Treasury-Status zurück.

        Returns:
            Result-Dict mit Treasury-Daten
        """
        if self._mock_mode:
            return {
                "status": "success",
                "message": "📊 [MOCK] Treasury Status",
                "data": self._get_mock_context()["treasury"],
                "mock": True
            }

        try:
            snapshot = self.economy.snapshot()
            treasury = snapshot.treasury

            burn_rate = self._calculate_burn_rate(snapshot)
            runway_hours = self._calculate_runway(treasury.balance, burn_rate)

            # Recent transactions (last 5)
            recent_txs = sorted(
                treasury.transactions,
                key=lambda tx: tx.timestamp,
                reverse=True
            )[:5]

            return {
                "status": "success",
                "message": f"📊 Treasury Balance: {treasury.balance:,} Bc | Burn Rate: {burn_rate:.1f} Bc/h | Runway: {runway_hours:.1f}h",
                "data": {
                    "balance": treasury.balance,
                    "start_capital": treasury.start_capital,
                    "burn_rate": burn_rate,
                    "runway_hours": runway_hours,
                    "runway_days": runway_hours / 24,
                    "health_percent": (treasury.balance / treasury.start_capital) * 100,
                    "recent_transactions": [
                        {
                            "type": tx.type,
                            "amount": tx.amount,
                            "timestamp": tx.timestamp,
                            "description": tx.description
                        }
                        for tx in recent_txs
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Error checking treasury: {e}")
            return {
                "status": "error",
                "message": f"❌ Fehler beim Treasury-Check: {str(e)}",
                "error": str(e)
            }

    def _complete_project(self, project_id: str) -> Dict:
        """
        Schließt ein Projekt ab.

        Args:
            project_id: Projekt-ID

        Returns:
            Result-Dict
        """
        if self._mock_mode:
            return {
                "status": "success",
                "message": f"✅ [MOCK] Projekt '{project_id}' würde abgeschlossen",
                "mock": True
            }

        try:
            # Find project in active projects
            snapshot = self.economy.snapshot()
            project = None

            for p in snapshot.projects_active:
                if p.id == project_id or p.name.lower().replace(" ", "-") == project_id:
                    project = p
                    break

            if not project:
                return {
                    "status": "error",
                    "message": f"❌ Projekt '{project_id}' nicht in aktiven Projekten gefunden"
                }

            # Complete project
            self.economy.complete_project(project.id)

            logger.info(f"✅ Project '{project.name}' completed")

            return {
                "status": "success",
                "message": f"✅ Projekt '{project.name}' abgeschlossen und ausgeliefert!",
                "project_id": project.id,
                "changes": {
                    "active_projects": -1,
                    "completed_projects": +1
                }
            }

        except Exception as e:
            logger.error(f"Error completing project '{project_id}': {e}")
            return {
                "status": "error",
                "message": f"❌ Fehler beim Projektabschluss: {str(e)}",
                "error": str(e)
            }

    def _analyze_burn_rate(self) -> Dict:
        """
        Analysiert Burn Rate und gibt Empfehlungen.

        Returns:
            Result-Dict mit Analyse
        """
        if self._mock_mode:
            context = self._get_mock_context()
            burn_rate = context["treasury"]["burn_rate"]
            runway = context["treasury"]["runway_hours"]

            return {
                "status": "success",
                "message": f"📊 [MOCK] Burn Rate: {burn_rate:.1f} Bc/h | Runway: {runway:.1f}h",
                "data": {
                    "burn_rate": burn_rate,
                    "runway_hours": runway,
                    "runway_days": runway / 24
                },
                "mock": True
            }

        try:
            snapshot = self.economy.snapshot()
            burn_rate = self._calculate_burn_rate(snapshot)
            balance = snapshot.treasury.balance
            runway_hours = self._calculate_runway(balance, burn_rate)

            # Analysis
            status = "healthy"
            if runway_hours < 24:
                status = "critical"
            elif runway_hours < 72:
                status = "warning"

            recommendations = []
            if status == "critical":
                recommendations.append("🔴 KRITISCH: Sofort Revenue generieren oder Kosten senken!")
                recommendations.append("Empfehlung: Nur essenzielle Projekte starten")
            elif status == "warning":
                recommendations.append("🟡 WARNUNG: Burn Rate überwachen")
                recommendations.append("Empfehlung: ROI-starke Projekte priorisieren")
            else:
                recommendations.append("🟢 GESUND: Burn Rate im grünen Bereich")

            return {
                "status": "success",
                "message": f"📊 Burn Rate Analyse: {status.upper()}",
                "data": {
                    "burn_rate": burn_rate,
                    "burn_rate_per_day": burn_rate * 24,
                    "runway_hours": runway_hours,
                    "runway_days": runway_hours / 24,
                    "status": status,
                    "recommendations": recommendations
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing burn rate: {e}")
            return {
                "status": "error",
                "message": f"❌ Fehler bei Burn Rate Analyse: {str(e)}",
                "error": str(e)
            }

    def _project_summary(self, project: 'Project') -> Dict:
        """Erstellt Projekt-Zusammenfassung für Context."""
        return {
            "id": project.id,
            "name": project.name,
            "value": project.value,
            "stage": getattr(project, 'status', 'unknown'),
            "team_size": len(getattr(project, 'team', []))
        }

    def _calculate_burn_rate(self, snapshot) -> float:
        """
        Berechnet Burn Rate (Bc/Stunde).

        Args:
            snapshot: Economy Snapshot

        Returns:
            Burn Rate in Bc/h
        """
        # Simple calculation: total costs / hours elapsed
        # This is a simplified version; real implementation would be more sophisticated

        treasury = snapshot.treasury

        if not treasury.transactions:
            return 0.0

        # Calculate total costs (negative transactions)
        total_costs = sum(
            abs(tx.amount)
            for tx in treasury.transactions
            if tx.amount < 0 and tx.type in ["COST_AGENT_PAYMENT", "COST_PROJECT", "COST_OPERATIONAL"]
        )

        # Estimate hours (simplified: assume 1 week = 168 hours)
        # In real implementation, this would use actual timestamps
        estimated_hours = 168.0  # 1 week

        burn_rate = total_costs / estimated_hours if estimated_hours > 0 else 0.0

        return round(burn_rate, 2)

    def _calculate_runway(self, balance: float, burn_rate: float) -> float:
        """
        Berechnet Runway in Stunden.

        Args:
            balance: Aktuelle Treasury Balance
            burn_rate: Burn Rate in Bc/h

        Returns:
            Runway in Stunden
        """
        if burn_rate <= 0:
            return float('inf')

        runway = balance / burn_rate
        return round(runway, 1)


# Singleton instance
_economy_bridge = None


def get_economy_bridge() -> EconomyBridge:
    """
    Gibt Singleton-Instanz des Economy Bridge zurück.

    Returns:
        EconomyBridge Instanz
    """
    global _economy_bridge
    if _economy_bridge is None:
        _economy_bridge = EconomyBridge()
    return _economy_bridge


def set_economy_instance(economy: 'BecoinEconomy'):
    """
    Setzt Economy-Instanz für den Bridge.

    Args:
        economy: BecoinEconomy Instanz
    """
    bridge = get_economy_bridge()
    bridge.set_economy(economy)
