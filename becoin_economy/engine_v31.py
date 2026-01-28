#!/usr/bin/env python3
"""
BeCoin Economy v3.1 - Single Customer Model
Only one customer exists. Growth comes through repeated satisfaction.
"""

import json
import random
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

# ============================================================================
# MODELS
# ============================================================================

class AgentStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    WAITING = "waiting"  # Waiting for customer feedback

class ProjectStage(Enum):
    PIPELINE = "pipeline"
    ACTIVE = "active"
    COMPLETED = "completed"
    AWAITING_REVIEW = "awaiting_review"  # Waiting for customer approval

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
        return {
            "burnRate": hourly_burn,
            "runwayHours": self.balance / hourly_burn if hourly_burn > 0 else float('inf'),
            "revenueGenerated": revenue,
            "netProfit": self.balance - self.start_capital,
            "totalTransactions": len(self.transactions)
        }
    
    def calculate_burn_rate(self) -> float:
        ops_costs = sum(
            t["amount"] * -1 for t in self.transactions 
            if t["type"] == "OPERATIONS_COST" and t["amount"] < 0
        )
        hours = max(1, len([t for t in self.transactions if t["type"] == "OPERATIONS_COST"]))
        return ops_costs / hours if hours > 0 else 60.0
    
    def revenue_generated(self) -> float:
        return sum(t["amount"] for t in self.transactions if t["type"] == "CUSTOMER_PAYMENT")

@dataclass
class Agent:
    """Autonomous agent with performance tracking."""
    id: str
    name: str
    role: str
    hourly_rate: float = 25.0
    status: str = "idle"
    current_task: str = None
    performance: dict = field(default_factory=lambda: {
        "hours_worked": 0,
        "tasks_completed": 0,
        "becoin_earned": 0.0,
        "quality_score": 0.0
    })

@dataclass
class Customer:
    """The single customer - our lifeline."""
    id: str
    name: str
    satisfaction_score: float = 0.5  # 0.0 - 1.0
    total_orders: int = 0
    total_spent: float = 0.0
    history: List[dict] = field(default_factory=list)
    
    def can_place_order(self) -> bool:
        """Customer only orders if satisfied enough."""
        return self.satisfaction_score >= 0.3  # Minimum threshold

@dataclass
class Project:
    """Project awaiting customer feedback."""
    id: str
    name: str
    stage: str = "pipeline"
    value: float = 0.0
    team: List[str] = field(default_factory=list)
    progress: float = 0.0
    quality_score: float = 0.0
    submitted_at: str = None

# ============================================================================
# ECONOMY ENGINE
# ============================================================================

class BeCoinEconomy:
    """
    Economy with ONE customer. Growth comes through repeated satisfaction.
    
    Flow:
    1. Customer places order (if satisfied)
    2. Agents work on project
    3. Project delivered
    4. Customer reviews (satisfaction changes)
    5. If satisfied → new orders (growth)
       If not → no more orders (death spiral)
    """

    START_CAPITAL = 10_000
    BASELINE_BURN_PER_HOUR = 50.0  # Lower fixed costs
    
    # Agent configuration
    AGENT_COSTS = {
        "frontend": 25.0,
        "backend": 30.0,
        "ai": 35.0,
        "devops": 25.0
    }
    
    def __init__(self):
        # Treasury
        self.treasury = Treasury(start_capital=self.START_CAPITAL, balance=self.START_CAPITAL)
        
        # Agents
        self.agents = {
            "agent-001": Agent(id="agent-001", name="Frontend Developer", role="frontend"),
            "agent-002": Agent(id="agent-002", name="Backend Architect", role="backend"),
            "agent-003": Agent(id="agent-003", name="AI Engineer", role="ai"),
            "agent-004": Agent(id="agent-004", name="DevOps Automator", role="devops"),
        }
        
        # THE SINGLE CUSTOMER
        self.customer = Customer(id="customer-001", name="Enterprise Corp")
        
        # Projects (only from our one customer)
        self.projects = {}
        
        # Simulation state
        self.cycle_count = 0
        self.hours_elapsed = 0
        self.running = False
        
        print(f"🏢 Economy initialized with 1 customer: {self.customer.name}")
        print(f"   Start capital: ${self.START_CAPITAL}")
    
    # =========================================================================
    # CUSTOMER INTERACTION - THE HEART OF THE ECONOMY
    # =========================================================================
    
    def customer_place_order(self) -> dict:
        """
        Customer decides to place a new order.
        Only happens if customer is satisfied enough.
        """
        if not self.customer.can_place_order():
            return {"ordered": False, "reason": "Customer not satisfied enough"}
        
        # Customer places order
        project_value = random.randint(2000, 5000)
        project_types = [
            "Website Redesign", "API Integration", "Dashboard Analytics",
            "Mobile App", "Database Migration", "Automation System"
        ]
        project_name = f"{self.customer.name}: {random.choice(project_types)}"
        
        project_id = f"proj-{len(self.projects) + 1:03d}"
        project = Project(
            id=project_id,
            name=project_name,
            stage="active",
            value=project_value,
            team=[],
            submitted_at=datetime.now(timezone.utc).isoformat()
        )
        self.projects[project_id] = project
        
        # Payment comes FIRST (money before work!)
        self.treasury.apply_transaction(
            tx_type="CUSTOMER_PAYMENT",
            amount=project_value,
            description=f"Payment from {self.customer.name}: {project_name}",
            metadata={"project_id": project_id, "customer_id": self.customer.id}
        )
        
        self.customer.total_orders += 1
        self.customer.total_spent += project_value
        
        return {
            "ordered": True,
            "project_id": project_id,
            "project_name": project_name,
            "payment": project_value,
            "customer_satisfaction": self.customer.satisfaction_score
        }
    
    def customer_review_project(self, project_id: str, satisfaction: float) -> dict:
        """
        Customer reviews completed project.
        satisfaction: 0.0 (terrible) to 1.0 (amazing)
        
        This is the KEY feedback loop!
        """
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        project.stage = "completed"
        
        # Update customer satisfaction (weighted average)
        old_score = self.customer.satisfaction_score
        self.customer.satisfaction_score = (old_score * 0.7) + (satisfaction * 0.3)
        
        # Record in history
        self.customer.history.append({
            "project_id": project_id,
            "satisfaction": satisfaction,
            "new_score": self.customer.satisfaction_score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "project_id": project_id,
            "satisfaction_given": satisfaction,
            "new_customer_score": self.customer.satisfaction_score,
            "will_order_again": self.customer.can_place_order()
        }
    
    # =========================================================================
    # AGENT WORK SYSTEM
    # =========================================================================
    
    def assign_work(self) -> dict:
        """Assign idle agents to active projects."""
        report = {"assignments": [], "agents_activated": 0}
        
        # Find active projects without team
        active_projects = [p for p in self.projects.values() if p.stage == "active" and not p.team]
        
        # Find idle agents
        idle_agents = [a for a in self.agents.values() if a.status == "idle"]
        
        # Assign agents to projects
        for project in active_projects:
            if not idle_agents:
                break
            
            agent = idle_agents.pop(0)
            agent.status = "active"
            agent.current_task = f"Working on {project.name}"
            project.team.append(agent.id)
            
            report["assignments"].append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "project_id": project.id,
                "project_name": project.name
            })
            report["agents_activated"] += 1
        
        return report
    
    def advance_time(self, hours: int = 1) -> dict:
        """Advance simulation by hours."""
        report = {
            "hours": hours,
            "customer_order": None,
            "assignments": {"agents_activated": 0},
            "payments": 0,
            "costs": 0,
            "balance_before": self.treasury.balance,
            "balance_after": 0,
            "customer_satisfaction": self.customer.satisfaction_score
        }
        
        self.hours_elapsed += hours
        self.cycle_count += 1
        
        # Phase 1: Check if customer wants to order
        # Chance based on satisfaction (higher satisfaction = higher chance)
        order_chance = self.customer.satisfaction_score * 0.3  # 0-30% per hour
        if random.random() < order_chance:
            order_result = self.customer_place_order()
            if order_result.get("ordered"):
                report["customer_order"] = order_result
                report["payments"] = order_result["payment"]
        
        # Phase 2: Assign agents to work
        assignment = self.assign_work()
        report["assignments"] = assignment
        
        # Phase 3: Agents work and project progress
        for agent_id, agent in self.agents.items():
            if agent.status == "active":
                # Work happens
                agent.performance["hours_worked"] += 1
                agent.performance["tasks_completed"] += 1
                
                # Pay agent
                self.treasury.apply_transaction(
                    tx_type="AGENT_SALARY",
                    amount=-agent.hourly_rate,
                    description=f"Salary for {agent.name}",
                    metadata={"agent_id": agent_id, "hours": 1}
                )
                report["costs"] += agent.hourly_rate
                
                # Update project progress
                for project in self.projects.values():
                    if agent.id in project.team and project.stage == "active":
                        project.progress += 10  # 10% per agent per hour
                        
                        # Project complete?
                        if project.progress >= 100:
                            project.progress = 100
                            project.stage = "AWAITING_REVIEW"
                            
                            # Give agent bonus from project value
                            bonus = project.value * 0.1
                            agent.performance["becoin_earned"] += bonus
                            
                            # Transfer bonus
                            self.treasury.apply_transaction(
                                tx_type="AGENT_BONUS",
                                amount=-bonus,
                                description=f"Bonus for {project.name}",
                                metadata={"agent_id": agent_id}
                            )
                            report["costs"] += bonus
                
                # Reset agent
                agent.status = "idle"
                agent.current_task = None
        
        # Phase 4: Operations cost
        ops_cost = self.BASELINE_BURN_PER_HOUR * hours
        self.treasury.apply_transaction(
            tx_type="OPERATIONS_COST",
            amount=-ops_cost,
            description=f"Operations for {hours}h"
        )
        report["costs"] += ops_cost
        
        report["balance_after"] = self.treasury.balance
        
        return report
    
    # =========================================================================
    # DASHBOARD API
    # =========================================================================
    
    def get_api_status(self) -> dict:
        return {
            "status": "operational",
            "service": "becoin-economy-v3.1",
            "version": "3.1-single-customer"
        }
    
    def get_api_treasury(self) -> dict:
        return {
            "balance": self.treasury.balance,
            "startCapital": self.treasury.start_capital,
            "metrics": self.treasury.metrics()
        }
    
    def get_api_agents(self) -> dict:
        return {
            "agents": {
                aid: {
                    "id": aid,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "hourly_rate": a.hourly_rate,
                    "current_task": a.current_task,
                    "performance": a.performance
                }
                for aid, a in self.agents.items()
            },
            "summary": {
                "total": len(self.agents),
                "active": sum(1 for a in self.agents.values() if a.status == "active"),
                "idle": sum(1 for a in self.agents.values() if a.status == "idle")
            }
        }
    
    def get_api_customer(self) -> dict:
        return {
            "customer": {
                "id": self.customer.id,
                "name": self.customer.name,
                "satisfaction_score": self.customer.satisfaction_score,
                "total_orders": self.customer.total_orders,
                "total_spent": self.customer.total_spent,
                "can_order": self.customer.can_place_order(),
                "order_probability": self.customer.satisfaction_score * 0.3
            },
            "history": self.customer.history[-10:]
        }
    
    def get_api_projects(self) -> dict:
        return {
            "projects": {
                pid: {
                    "id": pid,
                    "name": p.name,
                    "stage": p.stage,
                    "value": p.value,
                    "progress": p.progress,
                    "team": p.team
                }
                for pid, p in self.projects.items()
            },
            "summary": {
                "total": len(self.projects),
                "active": sum(1 for p in self.projects.values() if p.stage == "active"),
                "awaiting_review": sum(1 for p in self.projects.values() if p.stage == "AWAITING_REVIEW"),
                "completed": sum(1 for p in self.projects.values() if p.stage == "completed")
            }
        }
    
    def get_full_status(self) -> dict:
        """Complete status for dashboard."""
        return {
            "treasury": self.get_api_treasury(),
            "agents": self.get_api_agents(),
            "customer": self.get_api_customer(),
            "projects": self.get_api_projects()
        }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏢3.1 - BeCoin Economy v Single Customer Model")
    print("=" * 60)
    print()
    print("Rules:")
    print("  1. ONE customer - our lifeline")
    print("  2. Customer only orders if satisfied (score >= 0.3)")
    print("  3. Payment comes FIRST (before work)")
    print("  4. Customer reviews after completion (satisfaction affects future orders)")
    print("  5. Growth comes through repeated satisfaction")
    print()
    
    e = BeCoinEconomy()
    
    print("\n📊 Initial State:")
    print(f"   Customer Satisfaction: {e.customer.satisfaction_score:.0%}")
    print(f"   Can Order: {e.customer.can_place_order()}")
    
    print("\n🚀 Starting 48-hour simulation...")
    for i in range(48):
        report = e.advance_time(hours=1)
        if report["customer_order"] and i % 6 == 0:
            print(f"   Hour {i+1}: Customer ordered ${report['customer_order']['payment']}!")
    
    print("\n📈 Final State:")
    status = e.get_full_status()
    print(f"   Balance: ${status['treasury']['balance']:,.2f}")
    print(f"   Revenue: ${status['treasury']['metrics']['revenueGenerated']:,.2f}")
    print(f"   Customer Satisfaction: {status['customer']['satisfaction_score']:.0%}")
    print(f"   Orders: {status['customer']['total_orders']}")
    print(f"   Projects: {status['projects']['summary']['active']} active, {status['projects']['summary']['completed']} done")
    
    print("\n" + "=" * 60)
