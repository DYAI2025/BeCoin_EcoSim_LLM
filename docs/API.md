# BeCoin Economy API v3.0

## Overview

The BeCoin Economy API provides endpoints for the autonomous economy simulation. The system includes:

- **Treasury Management** - Balance, transactions, metrics
- **Agent Management** - Status, performance, assignments
- **Project Management** - Progress, teams, milestones
- **Sales Pipeline** - Leads, opportunities
- **CEO Decision Making** - Questions requiring answers

## Base URL

```
http://localhost:8000
```

## Endpoints

### System Status

#### GET `/api/status`
Get system health and version info.

**Response:**
```json
{
  "status": "operational",
  "service": "becoin-economy-v3",
  "version": "3.0",
  "autonomous_loop": true
}
```

### Treasury

#### GET `/api/treasury`
Get treasury balance, metrics, and recent transactions.

**Response:**
```json
{
  "balance": 9940.0,
  "startCapital": 10000,
  "metrics": {
    "burnRate": 60.0,
    "runwayHours": 165.67,
    "profitMargin": -0.6,
    "taxPaid": 0,
    "revenueGenerated": 0,
    "netProfit": -60,
    "totalTransactions": 1
  },
  "transactions": [
    {
      "timestamp": "2026-01-28T08:16:00Z",
      "type": "OPERATIONS_COST",
      "amount": -60.0,
      "description": "Operations burn for 1h",
      "metadata": {"hours": 1, "rate": 60.0}
    }
  ]
}
```

### Agents

#### GET `/api/agents`
Get all agents with status and performance data.

**Response:**
```json
{
  "agents": {
    "agent-001": {
      "id": "agent-001",
      "name": "Frontend Developer",
      "role": "frontend",
      "status": "active",
      "hourly_rate": 25.0,
      "current_task": "Working on Dashboard Redesign",
      "current_project": "proj-001",
      "equity_share": 0.25,
      "performance": {
        "hours_worked": 1,
        "tokens_consumed": 0,
        "projects_completed": 0,
        "becoin_earned": 25.0,
        "becoin_spent": 25.0,
        "questions_asked": 0,
        "blockers_encountered": 0,
        "tasks_completed": 1
      }
    }
  },
  "summary": {
    "total": 4,
    "active": 1,
    "idle": 3
  }
}
```

### Projects

#### GET `/api/projects`
Get all projects with progress and team information.

**Response:**
```json
{
  "projects": {
    "proj-001": {
      "id": "proj-001",
      "name": "Dashboard Redesign",
      "stage": "active",
      "cost": 2000,
      "value": 3000,
      "progress": 5.0,
      "team": ["agent-001"],
      "milestones": [
        {"name": "UI Design", "progress": 25, "completed": false},
        {"name": "Frontend Dev", "progress": 50, "completed": false}
      ],
      "metrics": {
        "hours_spent": 1,
        "tokens_used": 0,
        "cost_to_date": 25
      }
    }
  },
  "summary": {
    "total": 4,
    "active": 2,
    "pipeline": 1,
    "completed": 1
  }
}
```

### Sales Pipeline

#### GET `/api/pipeline`
Get sales leads and pipeline status.

**Response:**
```json
{
  "leads": {
    "lead-001": {
      "id": "lead-001",
      "company": "Company 952",
      "project_type": "E-commerce Platform",
      "budget": 3718,
      "timeline": "4-8 weeks",
      "stage": "new",
      "probability": 0.65
    }
  },
  "pending_questions": [
    {
      "id": "q-1",
      "lead_id": "lead-001",
      "company": "Company 952",
      "question": "New lead from Company 952: E-commerce Platform project, budget $3718. Accept?",
      "created_at": "2026-01-28T08:16:00Z",
      "answered": false
    }
  ],
  "summary": {
    "total_leads": 1,
    "new": 1,
    "won": 0,
    "lost": 0
  }
}
```

### CEO Questions

#### GET `/api/questions`
Get questions that need CEO answers.

**Response:**
```json
{
  "questions": [
    {
      "id": "q-1",
      "lead_id": "lead-001",
      "company": "Company 952",
      "question": "New lead from Company 952: E-commerce Platform project, budget $3718. Accept?",
      "created_at": "2026-01-28T08:16:00Z",
      "answered": false
    }
  ],
  "unanswered_count": 1
}
```

### Control Endpoints

#### POST `/api/advance?hours=1`
Advance simulation time by specified hours.

**Response:** Full advance report with assignments, payments, etc.

#### POST `/api/accept-lead/{lead_id}`
Accept a sales lead and create a project.

**Response:**
```json
{
  "lead_id": "lead-001",
  "project_id": "proj-005",
  "project_name": "Company 952 - E-commerce Platform",
  "budget": 3718,
  "timeline": "4-8 weeks"
}
```

#### POST `/api/reject-lead/{lead_id}?reason=Not interested`
Reject a sales lead.

**Response:**
```json
{
  "lead_id": "lead-001",
  "status": "rejected",
  "reason": "Not interested"
}
```

#### POST `/api/start-autonomous`
Start the autonomous simulation loop.

#### POST `/api/stop-autonomous`
Stop the autonomous simulation loop.

## Dashboard

The main dashboard is served at the root URL `/` and provides a real-time interface for:

- Treasury balance and metrics
- Agent status and performance
- Project progress
- Sales pipeline
- CEO decision-making (accept/reject leads)
- Recent transactions

## Data Flow

1. **Initialization** - Economy loads with 4 agents, 4 projects, $10,000 treasury
2. **Lead Generation** - 25% chance per hour for new sales opportunities
3. **Work Assignment** - Idle agents assigned to pipeline projects
4. **Progress Updates** - Active agents advance project progress
5. **Revenue Generation** - Projects complete and generate income
6. **CEO Decisions** - Accept/reject leads, make strategic choices

## Metrics

Key metrics tracked:
- **Treasury Balance** - Current capital
- **Runway Hours** - Hours until $0 (based on burn rate)
- **Agent Utilization** - Active vs idle agents
- **Project Velocity** - Projects completed per period
- **Lead Conversion** - Won leads vs total leads
- **Revenue Growth** - Income vs expenses

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid lead ID, etc.)
- `404` - Not found
- `500` - Server error

---

*API Version: 3.0*
*Last Updated: 2026-01-28*