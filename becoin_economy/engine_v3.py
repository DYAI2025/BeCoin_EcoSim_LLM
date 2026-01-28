#!/usr/bin/env python3
"""
BeCoin Economy System v3.0
Self-sustaining economy with work assignment, lead generation, and balanced economics.
"""

import json
import time
import asyncio
import random
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

class LeadStage(Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"

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
            "runwayHours": current / hourly_burn if hourly_burn > 0 else float('inf'),
            "profitMargin": ((current - start) / start * 100) if start > 0 else 0,
            "taxPaid": self.tax_paid(),
            "revenueGenerated": revenue,
            "netProfit": current - start,
            "totalTransactions": len(self.transactions)
        }
    
    def calculate_burn_rate(self) -> float:
        if not self.transactions:
            return 60.0  # Reduced baseline
        ops_costs = sum(
            t["amount"] * -1 for t in self.transactions 
            if t["type"] == "OPERATIONS_COST" and t["amount"] < 0
        )
        hours = max(1, self.hours_elapsed if hasattr(self, 'hours_elapsed') else 1)
        return ops_costs / hours if hours > 0 else 60.0
    
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
    current_project: str = None
    equity_share: float = 0.25
    performance: dict = field(default_factory=lambda: {
        "hours_worked": 0,
        "tokens_consumed": 0,
        "projects_completed": 0,
        "becoin_earned": 0.0,
        "becoin_spent": 0.0,
        "questions_asked": 0,
        "blockers_encountered": 0,
        "tasks_completed": 0
    })
    last_activity: str = None
    work_session_start: Optional[str] = None

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
    milestones: List[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=lambda: {
        "hours_spent": 0,
        "tokens_used": 0,
        "cost_to_date": 0.0
    })

@dataclass
class Lead:
    """Sales lead with qualification data."""
    id: str
    company: str
    project_type: str
    budget: float
    timeline: str
    requirements: List[str]
    stage: str = "new"
    created_at: str = None
    probability: float = 0.5
    questions: List[str] = field(default_factory=list)
    
# ============================================================================
# ECONOMY ENGINE
# ============================================================================

class BeCoinEconomy:
    """Complete self-sustaining economy system."""
    
    # Economy Parameters - BALANCED FOR SUSTAINABILITY
    START_CAPITAL = 10_000
    BASELINE_BURN_PER_HOUR = 60.0  # Reduced from $120 to $60
    AGENT_COSTS = {
        "frontend": 25.0,
        "backend": 30.0,
        "ai": 35.0,
        "devops": 25.0
    }
    TAX_RATE = 0.15
    TOKEN_COST_PER_1K = 0.01  # Local Ollama is cheap!
    BONUS_POOL = 0.10  # 10% of project value
    
    # Lead Generation Parameters
    LEAD_GENERATION_CHANCE = 0.25  # 25% chance per hour (20-30% range)
    LEAD_TYPES = [
        {"type": "Web Application", "budget_range": (2000, 4000), "timeline": "2-4 weeks"},
        {"type": "API Integration", "budget_range": (1500, 3000), "timeline": "1-3 weeks"},
        {"type": "Dashboard", "budget_range": (2500, 4500), "timeline": "3-5 weeks"},
        {"type": "Mobile App", "budget_range": (3000, 6000), "timeline": "4-8 weeks"},
        {"type": "AI Solution", "budget_range": (4000, 8000), "timeline": "4-6 weeks"},
        {"type": "Database Migration", "budget_range": (2000, 3500), "timeline": "2-4 weeks"},
        {"type": "E-commerce Platform", "budget_range": (3500, 7000), "timeline": "4-8 weeks"},
        {"type": "Chatbot Integration", "budget_range": (1500, 2500), "timeline": "1-2 weeks"},
    ]
    
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
                team=["agent-001", "agent-004"],
                milestones=[
                    {"name": "UI Design", "progress": 25, "completed": False},
                    {"name": "Frontend Dev", "progress": 50, "completed": False},
                    {"name": "Integration", "progress": 75, "completed": False},
                    {"name": "Testing", "progress": 100, "completed": False}
                ]
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
                team=["agent-004"],
                milestones=[
                    {"name": "Setup Pipeline", "progress": 33, "completed": False},
                    {"name": "Add Tests", "progress": 66, "completed": False},
                    {"name": "Deploy", "progress": 100, "completed": False}
                ]
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
        
        # Initialize Leads Pipeline
        self.leads = {}
        self.pending_questions = []  # Questions CEO needs to answer
        
        self.cycle_count = 0
        self.hours_elapsed = 0
        self.running = False
        
        # Save initial state
        self.export_dashboard()
    
    # =========================================================================
    # PHASE 1: WORK ASSIGNMENT SYSTEM
    # =========================================================================
    
    def assign_tasks_to_agents(self) -> dict:
        """
        Assign available projects to idle agents.
        Agenten: IDLE → ACTIVE bei Aufgaben-Zuweisung
        """
        report = {
            "assignments": [],
            "agents_activated": 0,
            "projects_updated": []
        }
        
        # Find projects in pipeline that need team members
        pipeline_projects = [
            (pid, p) for pid, p in self.projects.items() 
            if p.stage == "pipeline"
        ]
        
        # Find idle agents
        idle_agents = [
            (aid, a) for aid, a in self.agents.items() 
            if a.status == "idle"
        ]
        
        # Assign pipeline projects to idle agents
        for proj_id, project in pipeline_projects:
            if not idle_agents:
                break
            
            # Determine required roles for project
            required_roles = self._determine_project_roles(project)
            
            # Find matching idle agent
            for agent_id, agent in idle_agents[:]:
                if agent.role in required_roles:
                    # Activate agent and assign to project
                    agent.status = "active"
                    agent.current_task = f"Working on {project.name}"
                    agent.current_project = proj_id
                    agent.work_session_start = datetime.now(timezone.utc).isoformat()
                    
                    # Add to project team
                    if agent_id not in project.team:
                        project.team.append(agent_id)
                    
                    # Move project to active if team is complete
                    if len(project.team) >= 2:  # Need at least 2 agents
                        project.stage = "active"
                        report["projects_updated"].append(proj_id)
                    
                    report["assignments"].append({
                        "agent_id": agent_id,
                        "agent_name": agent.name,
                        "project_id": proj_id,
                        "project_name": project.name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    report["agents_activated"] += 1
                    
                    # Remove from idle list
                    idle_agents.remove((agent_id, agent_id))
        
        return report
    
    def _determine_project_roles(self, project: Project) -> List[str]:
        """Determine required roles for a project based on name."""
        name_lower = project.name.lower()
        roles = []
        
        if "frontend" in name_lower or "dashboard" in name_lower or "ui" in name_lower:
            roles.append("frontend")
        if "backend" in name_lower or "api" in name_lower or "database" in name_lower:
            roles.append("backend")
        if "ai" in name_lower or "llm" in name_lower or "chatbot" in name_lower:
            roles.append("ai")
        if "devops" in name_lower or "pipeline" in name_lower or "deploy" in name_lower:
            roles.append("devops")
        
        # Default roles if none detected
        if not roles:
            roles = ["frontend", "backend", "devops"]
        
        return roles
    
    def start_work_session(self, agent_id: str, task_description: str) -> dict:
        """Start a work session for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        agent.status = "active"
        agent.current_task = task_description
        agent.work_session_start = datetime.now(timezone.utc).isoformat()
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "task": task_description,
            "started_at": agent.work_session_start
        }
    
    def end_work_session(self, agent_id: str, subtask_completed: str = None) -> dict:
        """End a work session and update progress."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        report = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "task_completed": agent.current_task,
            "project": agent.current_project,
            "duration_hours": 1.0  # Simplified
        }
        
        # Update agent stats
        agent.performance["hours_worked"] += 1
        agent.performance["tasks_completed"] += 1
        
        # Update project progress
        if agent.current_project:
            project = self.projects.get(agent.current_project)
            if project and project.stage == "active":
                # Progress based on team size and active work
                progress_per_agent = 10.0 / max(len(project.team), 1)
                project.progress = min(100.0, project.progress + progress_per_agent)
                project.metrics["hours_spent"] += 1
                
                report["project_progress"] = round(project.progress, 1)
                
                # Check for milestone completion
                self._check_milestones(project)
                
                # Check if project is done
                if project.progress >= 100:
                    self.complete_project(agent.current_project)
        
        # Reset agent
        agent.status = "idle"
        agent.current_task = None
        agent.current_project = None
        agent.work_session_start = None
        agent.last_activity = datetime.now(timezone.utc).isoformat()
        
        return report
    
    def _check_milestones(self, project: Project):
        """Check and update project milestones."""
        for milestone in project.milestones:
            if not milestone["completed"] and project.progress >= milestone["progress"]:
                milestone["completed"] = True
                milestone["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    # =========================================================================
    # PHASE 2: CUSTOMER ACQUISITION
    # =========================================================================
    
    def generate_leads(self) -> dict:
        """
        Generate new leads with 20-30% chance per hour.
        Returns lead data or empty dict if no lead generated.
        """
        # Random chance based on configured rate
        if random.random() > self.LEAD_GENERATION_CHANCE:
            return {"generated": False, "reason": "Random check failed"}
        
        # Generate lead data
        lead_type = random.choice(self.LEAD_TYPES)
        lead_id = f"lead-{len(self.leads) + 1:03d}"
        
        budget = random.randint(*lead_type["budget_range"])
        
        lead = Lead(
            id=lead_id,
            company=f"Company {random.randint(100, 999)}",
            project_type=lead_type["type"],
            budget=budget,
            timeline=lead_type["timeline"],
            requirements=[
                f"Requirement {i+1}" for i in range(random.randint(2, 5))
            ],
            stage="new",
            created_at=datetime.now(timezone.utc).isoformat(),
            probability=random.uniform(0.4, 0.7),
            questions=self._generate_lead_questions(lead_type["type"])
        )
        
        self.leads[lead_id] = lead
        
        # Generate CEO question
        question = {
            "id": f"q-{len(self.pending_questions) + 1}",
            "lead_id": lead_id,
            "company": lead.company,
            "project_type": lead.project_type,
            "budget": budget,
            "question": f"New lead from {lead.company}: {lead.project_type} project, budget ${budget}. Accept?",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "answered": False
        }
        self.pending_questions.append(question)
        
        return {
            "generated": True,
            "lead_id": lead_id,
            "company": lead.company,
            "project_type": lead.project_type,
            "budget": budget,
            "timeline": lead.timeline,
            "question_id": question["id"]
        }
    
    def _generate_lead_questions(self, project_type: str) -> List[str]:
        """Generate questions CEO needs to answer for a lead."""
        questions = {
            "Web Application": [
                "Do we have capacity for this project?",
                "Should we propose a higher budget tier?"
            ],
            "API Integration": [
                "Is the integration scope clear?",
                "Do we need to hire additional help?"
            ],
            "Dashboard": [
                "What are the key metrics to display?",
                "Should we use real-time data?"
            ],
            "Mobile App": [
                "iOS, Android, or both?",
                "What is the target user base?"
            ],
            "AI Solution": [
                "What model should we use?",
                "Is training data available?"
            ],
            "Database Migration": [
                "What is the current database system?",
                "Any data compatibility concerns?"
            ],
            "E-commerce Platform": [
                "What payment gateways needed?",
                "How many products initially?"
            ],
            "Chatbot Integration": [
                "What platforms (web, slack, discord)?",
                "What is the knowledge base?"
            ]
        }
        return questions.get(project_type, ["What are the priorities?"])
    
    def accept_lead(self, lead_id: str) -> dict:
        """Accept a lead and create a new project."""
        lead = self.leads.get(lead_id)
        if not lead:
            return {"error": "Lead not found"}
        
        if lead.stage != "new":
            return {"error": "Lead already processed"}
        
        # Calculate project values
        cost = lead.budget * 0.8  # 80% of budget for cost
        value = lead.budget  # Revenue equals budget
        
        # Create project
        project_id = f"proj-{len(self.projects) + 1:03d}"
        project = Project(
            id=project_id,
            name=f"{lead.company} - {lead.project_type}",
            stage="pipeline",
            cost=cost,
            value=value,
            impact_score=lead.probability * 100,
            team=[],
            milestones=[
                {"name": "Discovery", "progress": 25, "completed": False},
                {"name": "Development", "progress": 50, "completed": False},
                {"name": "Testing", "progress": 75, "completed": False},
                {"name": "Delivery", "progress": 100, "completed": False}
            ]
        )
        
        self.projects[project_id] = project
        lead.stage = "won"
        lead.project_id = project_id
        
        # Mark question as answered
        for q in self.pending_questions:
            if q["lead_id"] == lead_id:
                q["answered"] = True
                q["answer"] = "accepted"
                q["project_id"] = project_id
        
        return {
            "lead_id": lead_id,
            "project_id": project_id,
            "project_name": project.name,
            "budget": lead.budget,
            "timeline": lead.timeline
        }
    
    def reject_lead(self, lead_id: str, reason: str = None) -> dict:
        """Reject a lead."""
        lead = self.leads.get(lead_id)
        if not lead:
            return {"error": "Lead not found"}
        
        lead.stage = "lost"
        lead.rejection_reason = reason
        
        # Mark question as answered
        for q in self.pending_questions:
            if q["lead_id"] == lead_id:
                q["answered"] = True
                q["answer"] = "rejected"
                q["reason"] = reason
        
        return {
            "lead_id": lead_id,
            "status": "rejected",
            "reason": reason
        }
    
    # =========================================================================
    # PHASE 3 & 4: CORE OPERATIONS & BALANCED ECONOMICS
    # =========================================================================
    
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
                
                # Performance tracking
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
        # Calculate daily burn (24 hours × reduced baseline)
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
        """
        Advance simulation time by hours.
        Includes: Work assignment, lead generation, progress updates, payments.
        """
        report = {
            "hours_advanced": hours,
            "assignments": {"agents_activated": 0, "projects_updated": []},
            "leads_generated": [],
            "agent_payments": {"agent_payments": [], "total_cost": 0.0},
            "tax_deducted": None,
            "balance_before": self.treasury.balance,
            "balance_after": 0,
            "agents_status": {},
            "projects_progress": {},
            "hours_elapsed": self.hours_elapsed
        }
        
        self.hours_elapsed += hours
        self.cycle_count += 1
        
        # PHASE 1: Assign tasks to idle agents
        assignment_report = self.assign_tasks_to_agents()
        report["assignments"] = assignment_report
        
        # PHASE 2: Generate leads (20-30% chance per hour)
        for _ in range(hours):
            lead_result = self.generate_leads()
            if lead_result.get("generated"):
                report["leads_generated"].append(lead_result)
        
        # Deduct baseline operations cost (reduced from $120 to $60)
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
        
        # Process work sessions for active agents
        for agent_id, agent in self.agents.items():
            report["agents_status"][agent_id] = {
                "name": agent.name,
                "status": agent.status,
                "hours_worked": agent.performance["hours_worked"],
                "current_task": agent.current_task
            }
            
            if agent.status == "active":
                # End work session and update progress
                session_report = self.end_work_session(agent_id)
                
                proj_id = session_report.get("project")
                if proj_id:
                    report["projects_progress"][proj_id] = {
                        "name": self.projects.get(proj_id, {}).name,
                        "progress": session_report.get("project_progress", 0)
                    }
        
        # Pay agent salaries
        payment_report = self.pay_hourly_agent_costs()
        report["agent_payments"] = payment_report
        
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
        project.progress = 100.0
        
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
            "project_id": project_id,
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
                agent.status = "idle"
                agent.current_task = None
                agent.current_project = None
                
                report["agent_bonuses"].append({
                    "agent": agent.name,
                    "bonus": round(per_agent, 2)
                })
        
        return report
    
    # =========================================================================
    # PHASE 3: DASHBOARD API
    # =========================================================================
    
    def get_api_treasury(self) -> dict:
        """API endpoint: /api/treasury"""
        return {
            "balance": self.treasury.balance,
            "startCapital": self.treasury.start_capital,
            "metrics": self.treasury.metrics(),
            "transactions": self.treasury.transactions[-50:]  # Last 50
        }
    
    def get_api_agents(self) -> dict:
        """API endpoint: /api/agents"""
        return {
            "agents": {
                aid: {
                    "id": aid,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "hourly_rate": a.hourly_rate,
                    "current_task": a.current_task,
                    "current_project": a.current_project,
                    "equity_share": a.equity_share,
                    "performance": a.performance,
                    "last_activity": a.last_activity
                }
                for aid, a in self.agents.items()
            },
            "summary": {
                "total": len(self.agents),
                "active": sum(1 for a in self.agents.values() if a.status == "active"),
                "idle": sum(1 for a in self.agents.values() if a.status == "idle")
            }
        }
    
    def get_api_projects(self) -> dict:
        """API endpoint: /api/projects"""
        return {
            "projects": {
                pid: {
                    "id": pid,
                    "name": p.name,
                    "stage": p.stage,
                    "cost": p.cost,
                    "value": p.value,
                    "progress": round(p.progress, 1),
                    "team": p.team,
                    "milestones": p.milestones,
                    "metrics": p.metrics
                }
                for pid, p in self.projects.items()
            },
            "summary": {
                "total": len(self.projects),
                "active": sum(1 for p in self.projects.values() if p.stage == "active"),
                "pipeline": sum(1 for p in self.projects.values() if p.stage == "pipeline"),
                "completed": sum(1 for p in self.projects.values() if p.stage == "completed")
            }
        }
    
    def get_api_pipeline(self) -> dict:
        """API endpoint: /api/pipeline - Sales pipeline"""
        return {
            "leads": {
                lid: {
                    "id": lid,
                    "company": l.company,
                    "project_type": l.project_type,
                    "budget": l.budget,
                    "timeline": l.timeline,
                    "stage": l.stage,
                    "probability": l.probability,
                    "requirements": l.requirements
                }
                for lid, l in self.leads.items()
            },
            "pending_questions": [q for q in self.pending_questions if not q["answered"]],
            "summary": {
                "total_leads": len(self.leads),
                "new": sum(1 for l in self.leads.values() if l.stage == "new"),
                "won": sum(1 for l in self.leads.values() if l.stage == "won"),
                "lost": sum(1 for l in self.leads.values() if l.stage == "lost")
            }
        }
    
    def get_api_questions(self) -> dict:
        """API endpoint: /api/questions - Questions CEO needs to answer"""
        return {
            "questions": self.pending_questions,
            "unanswered_count": sum(1 for q in self.pending_questions if not q["answered"])
        }
    
    def get_agent_chat_reports(self) -> List[dict]:
        """Generate autonomous agent reports for chat."""
        reports = []
        
        for agent_id, agent in self.agents.items():
            # Determine if agent needs input
            blockers = []
            questions = []
            recommendations = []
            
            # Check current project
            if agent.current_project:
                proj = self.projects.get(agent.current_project)
                if proj:
                    # Generate contextual questions based on progress
                    if proj.progress < 25:
                        blockers.append("Still in discovery phase - need requirements clarification")
                        agent.performance["blockers_encountered"] += 1
                    elif proj.progress < 50:
                        questions.append(f"Should I prioritize performance or features for {proj.name}?")
                        agent.performance["questions_asked"] += 1
                    elif proj.progress < 75:
                        questions.append(f"{proj.name}: Ready for code review or continue development?")
                        agent.performance["questions_asked"] += 1
                    else:
                        recommendations.append(f"{proj.name}: Final testing and deployment planning needed")
            
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
                "current_project": agent.current_project,
                "performance": {
                    "hours_worked": hours,
                    "tokens_consumed": agent.performance["tokens_consumed"],
                    "projects_completed": agent.performance["projects_completed"],
                    "tasks_completed": agent.performance["tasks_completed"],
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
                    "current_project": a.current_project,
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
                    "milestones": p.milestones,
                    "metrics": p.metrics
                }
                for pid, p in self.projects.items()
            },
            "pipeline": {
                "leads": {
                    lid: {
                        "id": lid,
                        "company": l.company,
                        "project_type": l.project_type,
                        "budget": l.budget,
                        "timeline": l.timeline,
                        "stage": l.stage,
                        "probability": l.probability
                    }
                    for lid, l in self.leads.items()
                },
                "pending_questions": [q for q in self.pending_questions if not q["answered"]]
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
                    "bonus_pool_percent": self.BONUS_POOL * 100,
                    "lead_generation_chance": self.LEAD_GENERATION_CHANCE
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
                "pipeline": sum(1 for p in self.projects.values() if p.stage == "pipeline"),
                "completed": sum(1 for p in self.projects.values() if p.stage == "completed")
            },
            "pipeline": {
                "total_leads": len(self.leads),
                "pending_questions": sum(1 for q in self.pending_questions if not q["answered"])
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
    
    print("💰 BeCoin Economy System v3.0")
    print("=" * 50)
    print(f"Initial Balance: ${economy.treasury.balance}")
    print(f"Agents: {len(economy.agents)}")
    print(f"Projects: {len(economy.projects)}")
    print()
    
    # Test one cycle
    report = economy.advance_time(hours=1)
    print(f"Hourly Report:")
    print(f"  Assignments: {report['assignments']['agents_activated']} agents activated")
    print(f"  Leads Generated: {len(report['leads_generated'])}")
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