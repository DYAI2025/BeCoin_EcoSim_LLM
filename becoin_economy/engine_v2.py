#!/usr/bin/env python3
"""
BeCoin Economy System v2.0
Complete autonomous economy with agent payments, taxes, and token tracking.
"""

import json
import time
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable
from enum import Enum

# ============================================================================
# MODELS
# ============================================================================

class AgentStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    TRAINING = "training"

class ProjectStage(Enum):
    PIPELINE = "pipeline"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Treasury:
    """Company treasury with transaction history."""
    start_capital: float
    balance: float
    transactions: List[dict] = field(default_factory=list)
    
    def apply_transaction(self, tx_type: str, amount: float, description: str, metadata: dict = None):
        tx = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": tx_type,
            "amount": round(amount, 2),
            "description": description,
            "metadata": metadata or {}
        }
        self.transactions.append(tx)
        self.balance = round(self.balance + amount, 2)
    
    def metrics(self) -> dict:
        hourly_burn = self.calculate_burn_rate()
        revenue = self.revenue_generated()
        start = self.start_capital
        current = self.balance
        
        return {
            "burnRate": hourly_burn,
            "runwayHours": current / hourly_burn if hourly_burn > 0 else 0,
            "profitMargin": ((current - start) / start * 100) if start > 0 else 0,
            "taxPaid": self.tax_paid(),
            "revenueGenerated": revenue,
            "netProfit": current - start,
            "totalTransactions": len(self.transactions)
        }
    
    def calculate_burn_rate(self) -> float:
        if not self.transactions:
            return 120.0
        ops_costs = sum(
            t["amount"] * -1 for t in self.transactions 
            if t["type"] == "OPERATIONS_COST" and t["amount"] < 0
        )
        hours = 1  # Simplified
        return ops_costs / hours if hours > 0 else 120.0
    
    def tax_paid(self) -> float:
        return sum(
            t["amount"] * -1 for t in self.transactions 
            if t["type"] == "TAX_DEDUCTION" and t["amount"] < 0
        )
    
    def revenue_generated(self) -> float:
        return sum(
            t["amount"] for t in self.transactions 
            if t["type"] == "PROJECT_REVENUE"
        )

@dataclass
class Agent:
    """Autonomous agent with performance tracking."""
    id: str
    name: str
    role: str
    hourly_rate: float = 25.0
    status: str = "idle"
    current_task: str = None
    equity_share: float = 0.25
    performance: dict = field(default_factory=lambda: {
        "hours_worked": 0,
        "tokens_consumed": 0,
        "projects_completed": 0,
        "becoin_earned": 0.0,
        "becoin_spent": 0.0,
        "questions_asked": 0,
        "blockers_encountered": 0
    })
    last_activity: str = None

@dataclass
class Project:
    """Project with team and progress tracking."""
    id: str
    name: str
    stage: str = "pipeline"
    cost: float = 0.0
    value: float = 0.0
    impact_score: float = 50.0
    team: List[str] = field(default_factory=list)
    progress: float = 0.0
    metrics: dict = field(default_factory=lambda: {
        "hours_spent": 0,
        "tokens_used": 0,
        "cost_to_date": 0.0
    })

# ============================================================================
# ECONOMY ENGINE
# ============================================================================

class BeCoinEconomy:
    """Complete autonomous economy system."""
    
    # Economy Parameters
    START_CAPITAL = 10_000
    BASELINE_BURN_PER_HOUR = 120.0
    AGENT_COSTS = {
        "frontend": 25.0,
        "backend": 30.0,
        "ai": 35.0,
        "devops": 25.0
    }
    TAX_RATE = 0.15
    TOKEN_COST_PER_1K = 0.01  # Local Ollama is cheap!
    BONUS_POOL = 0.10  # 10% of project value
    
    def __init__(self, data_dir: str = "dashboard/becoin-economy"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Treasury
        self.treasury = Treasury(
            start_capital=self.START_CAPITAL,
            balance=self.START_CAPITAL
        )
        
        # Initialize Agents
        self.agents = {
            "agent-001": Agent(
                id="agent-001",
                name="Frontend Developer",
                role="frontend",
                hourly_rate=self.AGENT_COSTS["frontend"]
            ),
            "agent-002": Agent(
                id="agent-002",
                name="Backend Architect",
                role="backend",
                hourly_rate=self.AGENT_COSTS["backend"]
            ),
            "agent-003": Agent(
                id="agent-003",
                name="AI Engineer",
                role="ai",
                hourly_rate=self.AGENT_COSTS["ai"]
            ),
            "agent-004": Agent(
                id="agent-004",
                name="DevOps Automator",
                role="devops",
                hourly_rate=self.AGENT_COSTS["devops"]
            ),
        }
        
        # Initialize Projects
        self.projects = {
            "proj-001": Project(
                id="proj-001",
                name="Dashboard Redesign",
                stage="active",
                cost=2000,
                value=3000,
                impact_score=85,
                team=["agent-001", "agent-004"]
            ),
            "proj-002": Project(
                id="proj-002",
                name="API Integration",
                stage="completed",
                cost=1500,
                value=2500,
                impact_score=92,
                team=["agent-002"]
            ),
            "proj-003": Project(
                id="proj-003",
                name="CI/CD Pipeline",
                stage="active",
                cost=1800,
                value=2700,
                impact_score=78,
                team=["agent-004"]
            ),
            "proj-004": Project(
                id="proj-004",
                name="LLM Integration",
                stage="pipeline",
                cost=2500,
                value=4000,
                impact_score=95,
                team=["agent-003", "agent-002"]
            ),
        }
        
        self.cycle_count = 0
        self.hours_elapsed = 0
        self.running = False
        
        # Save initial state
        self.export_dashboard()
    
    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------
    
    def pay_hourly_agent_costs(self) -> dict:
        """Deduct hourly agent costs from treasury."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_payments": [],
            "total_cost": 0.0
        }
        
        for agent_id, agent in self.agents.items():
            if agent.status == "active":
                cost = agent.hourly_rate
                self.treasury.apply_transaction(
                    tx_type="AGENT_SALARY",
                    amount=-cost,
                    description=f"Salary for {agent.name} (1h)",
                    metadata={"agent_id": agent_id, "rate": cost}
                )
                
                agent.performance["hours_worked"] += 1
                agent.performance["becoin_earned"] += cost
                agent.performance["becoin_spent"] += cost
                agent.last_activity = datetime.now(timezone.utc).isoformat()
                
                report["agent_payments"].append({
                    "agent": agent.name,
                    "role": agent.role,
                    "amount": cost,
                    "hours_total": agent.performance["hours_worked"]
                })
                report["total_cost"] += cost
        
        return report
    
    def deduct_tax(self) -> dict:
        """Daily tax deduction to 'Finanzamt'."""
        # Calculate daily burn (24 hours × baseline)
        daily_burn = self.BASELINE_BURN_PER_HOUR * 24
        tax_amount = daily_burn * self.TAX_RATE
        
        if self.treasury.balance > tax_amount:
            self.treasury.apply_transaction(
                tx_type="TAX_DEDUCTION",
                amount=-tax_amount,
                description=f"Daily tax deduction (15% of ${daily_burn}/day)",
                metadata={"daily_burn": daily_burn, "tax_rate": self.TAX_RATE}
            )
            
            return {
                "tax_amount": round(tax_amount, 2),
                "balance_after": self.treasury.balance,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        return {"tax_amount": 0, "message": "Insufficient funds for tax"}
    
    def track_token_usage(self, agent_id: str, tokens: int) -> float:
        """Track LLM token usage and deduct cost."""
        cost = (tokens / 1000) * self.TOKEN_COST_PER_1K
        
        if agent_id in self.agents:
            self.agents[agent_id].performance["tokens_consumed"] += tokens
        
        self.treasury.apply_transaction(
            tx_type="TOKEN_COST",
            amount=-cost,
            description=f"Token usage: {tokens} tokens",
            metadata={"agent_id": agent_id, "tokens": tokens, "cost_per_1k": self.TOKEN_COST_PER_1K}
        )
        
        return cost
    
    def advance_time(self, hours: int = 1) -> dict:
        """Advance simulation time by hours."""
        report = {
            "hours_advanced": hours,
            "agent_payments": self.pay_hourly_agent_costs(),
            "tax_deducted": None,
            "balance_before": self.treasury.balance,
            "balance_after": 0,
            "agents_status": {},
            "projects_progress": {}
        }
        
        self.hours_elapsed += hours
        self.cycle_count += 1
        
        # Deduct baseline operations cost
        burn = self.BASELINE_BURN_PER_HOUR * hours
        self.treasury.apply_transaction(
            tx_type="OPERATIONS_COST",
            amount=-burn,
            description=f"Operations burn for {hours}h",
            metadata={"hours": hours, "rate": self.BASELINE_BURN_PER_HOUR}
        )
        
        # Tax deduction every 24 hours
        if self.hours_elapsed % 24 == 0:
            report["tax_deducted"] = self.deduct_tax()
        
        # Update project progress for active agents
        for agent_id, agent in self.agents.items():
            report["agents_status"][agent_id] = {
                "name": agent.name,
                "status": agent.status,
                "hours_worked": agent.performance["hours_worked"]
            }
        
        for proj_id, project in self.projects.items():
            if project.stage == "active":
                # Random progress based on team size
                progress_increment = 5.0 / max(len(project.team), 1)
                project.progress = min(100.0, project.progress + progress_increment)
                project.metrics["hours_spent"] += hours
                
                report["projects_progress"][proj_id] = {
                    "name": project.name,
                    "progress": round(project.progress, 1),
                    "hours_total": project.metrics["hours_spent"]
                }
                
                # Check completion
                if project.progress >= 100:
                    self.complete_project(proj_id)
        
        report["balance_after"] = self.treasury.balance
        report["hours_elapsed"] = self.hours_elapsed
        
        # Export dashboard data
        self.export_dashboard()
        
        return report
    
    def complete_project(self, project_id: str) -> dict:
        """Complete a project and distribute rewards."""
        project = self.projects.get(project_id)
        if not project or project.stage != "active":
            return {"error": "Project not active"}
        
        project.stage = "completed"
        project.completed_at = datetime.now(timezone.utc).isoformat()
        
        # Revenue to treasury
        self.treasury.apply_transaction(
            tx_type="PROJECT_REVENUE",
            amount=project.value,
            description=f"Revenue from {project.name}",
            metadata={"project_id": project_id, "value": project.value}
        )
        
        # Calculate bonuses
        bonus_pool = project.value * self.BONUS_POOL
        per_agent = bonus_pool / max(len(project.team), 1)
        
        report = {
            "project": project.name,
            "revenue": project.value,
            "bonus_pool": bonus_pool,
            "agent_bonuses": []
        }
        
        for agent_id in project.team:
            agent = self.agents.get(agent_id)
            if agent:
                self.treasury.apply_transaction(
                    tx_type="AGENT_BONUS",
                    amount=per_agent,
                    description=f"Bonus for {project.name}",
                    metadata={"agent_id": agent_id, "project": project_id}
                )
                agent.performance["projects_completed"] += 1
                agent.performance["becoin_earned"] += per_agent
                agent.status = "IDLE"
                agent.current_task = None
                
                report["agent_bonuses"].append({
                    "agent": agent.name,
                    "bonus": round(per_agent, 2)
                })
        
        return report
    
    def get_agent_chat_reports(self) -> List[dict]:
        """Generate autonomous agent reports for chat."""
        reports = []
        
        for agent_id, agent in self.agents.items():
            # Determine if agent needs input
            blockers = []
            questions = []
            recommendations = []
            
            # Check current project
            if agent.current_task:
                proj = next(
                    (p for p in self.projects.values() if agent_id in p.team and p.stage == "active"),
                    None
                )
                if proj:
                    if proj.progress < 30:
                        blockers.append("Just started, gathering requirements")
                    elif proj.progress < 70:
                        questions.append(f"Should I prioritize {proj.name} features or refactor?")
                    else:
                        recommendations.append(f"{proj.name} is almost done - review needed")
            
            # Financial status
            earned = agent.performance["becoin_earned"]
            hours = agent.performance["hours_worked"]
            efficiency = earned / hours if hours > 0 else 0
            
            report = {
                "agent": {
                    "id": agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "status": agent.status
                },
                "current_task": agent.current_task or "Idle",
                "performance": {
                    "hours_worked": hours,
                    "tokens_consumed": agent.performance["tokens_consumed"],
                    "projects_completed": agent.performance["projects_completed"],
                    "becoin_earned": round(earned, 2),
                    "efficiency_score": round(efficiency, 2)
                },
                "blockers": blockers,
                "questions": questions,
                "recommendations": recommendations,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            reports.append(report)
        
        return reports
    
    def export_dashboard(self) -> dict:
        """Export all dashboard data as JSON files."""
        data = {
            "treasury": {
                "balance": self.treasury.balance,
                "startCapital": self.treasury.start_capital,
                "metrics": self.treasury.metrics()
            },
            "agents": {
                aid: {
                    "id": aid,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "hourly_rate": a.hourly_rate,
                    "current_task": a.current_task,
                    "equity_share": a.equity_share,
                    "performance": a.performance
                }
                for aid, a in self.agents.items()
            },
            "projects": {
                pid: {
                    "id": pid,
                    "name": p.name,
                    "stage": p.stage,
                    "cost": p.cost,
                    "value": p.value,
                    "progress": round(p.progress, 1),
                    "team": p.team,
                    "metrics": p.metrics
                }
                for pid, p in self.projects.items()
            },
            "autonomous_loop": {
                "status": "running" if self.running else "stopped",
                "cycles_completed": self.cycle_count,
                "hours_elapsed": self.hours_elapsed,
                "last_update": datetime.now(timezone.utc).isoformat(),
                "config": {
                    "baseline_burn_per_hour": self.BASELINE_BURN_PER_HOUR,
                    "agent_costs": self.AGENT_COSTS,
                    "tax_rate": self.TAX_RATE,
                    "token_cost_per_1k": self.TOKEN_COST_PER_1K,
                    "bonus_pool_percent": self.BONUS_POOL * 100
                }
            }
        }
        
        # Write all JSON files
        for filename, content in data.items():
            filepath = self.data_dir / f"{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(content, f, indent=2)
        
        return data
    
    def get_status(self) -> dict:
        """Get complete system status."""
        return {
            "running": self.running,
            "treasury": {
                "balance": self.treasury.balance,
                "start": self.treasury.start_capital,
                **self.treasury.metrics()
            },
            "agents": {
                "total": len(self.agents),
                "active": sum(1 for a in self.agents.values() if a.status == "active"),
                "idle": sum(1 for a in self.agents.values() if a.status == "idle")
            },
            "projects": {
                "total": len(self.projects),
                "active": sum(1 for p in self.projects.values() if p.stage == "active"),
                "completed": sum(1 for p in self.projects.values() if p.stage == "completed")
            },
            "simulation": {
                "hours_elapsed": self.hours_elapsed,
                "cycles": self.cycle_count,
                "last_update": datetime.now(timezone.utc).isoformat()
            }
        }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    economy = BeCoinEconomy()
    
    print("💰 BeCoin Economy System v2.0")
    print("=" * 50)
    print(f"Initial Balance: ${economy.treasury.balance}")
    print(f"Agents: {len(economy.agents)}")
    print(f"Projects: {len(economy.projects)}")
    print()
    
    # Test one cycle
    report = economy.advance_time(hours=1)
    print(f"Hourly Report:")
    print(f"  Agent Payments: ${report['agent_payments']['total_cost']}")
    print(f"  Balance: ${report['balance_after']}")
    print()
    
    # Agent chat reports
    print("🤖 Agent Reports:")
    for report in economy.get_agent_chat_reports():
        print(f"  - {report['agent']['name']}: {report['current_task']}")
        if report['questions']:
            for q in report['questions'][:1]:
                print(f"    ❓ {q}")
    
    print("\n✅ Dashboard exported to dashboard/becoin-economy/")
