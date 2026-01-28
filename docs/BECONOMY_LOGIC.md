# 💰 BeCoin Economy System - Payment & Finance Logic

## 🎯 System Overview

Das BeCoin Economy System ist eine vollständige autonome Unternehmenssimulation mit:

- **Treasury Management** - $10.000 Startkapital
- **Agent Payment System** - Stündliche Gehälter basierend auf Performance
- **Tax & Compliance** - Regelmäßige Abzüge (Finanzamt, Betriebskosten)
- **Token Tracking** - LLM Token-Verbrauch pro Agent
- **Revenue Generation** - Projekte verdienen echtes Geld
- **Autonomous Agents** - 4 Agenten die selbstständig arbeiten

---

## 📊 Economy Parameters

```python
START_CAPITAL = 10_000          # Initial Treasury
BASELINE_BURNS_PER_HOUR = 120    # $120/h operative Kosten
AGENT_COST_PER_HOUR = 25         # $25 Agent/Stunde (Base Salary)
TAX_RATE = 0.15                  # 15% Finanzamt Abzug
TOKEN_COST_PER_1K = 0.01         # $0.01 pro 1K Token (Ollama local)
BONUS_PER_PROJECT = 0.1          # 10% Project Value als Bonus
```

---

## 💸 Payment Flow

### 1. Hourly Agent Costs (Jede Stunde)
```
Treasury → -$25/Agent/Stunde
         → Agent Performance Tracking
         → Agent Equity Update
```

### 2. Token Consumption (Pro Request)
```
Token Usage = Request Tokens + Response Tokens
Cost = (Tokens / 1000) × $0.01
Treasury → -Token Cost
```

### 3. Tax Deductions (Täglich)
```
Daily Tax = SUM(Hourly Burn × 24) × 15%
Finanzamt Abzug = -$432/Tag (bei $120/h)
```

### 4. Project Revenue (Bei Fertigstellung)
```
Project Value → +$ zu Treasury
Bonus Pool = 10% × Project Value
Agent Boni = Bonus Pool / Team Size
```

---

## 🤖 Agent Types & Costs

| Agent | Role | Cost/Hour | Specialization |
|-------|------|-----------|----------------|
| Frontend Developer | Frontend | $25 | UI/UX, React |
| Backend Architect | Backend | $30 | API, Database |
| AI Engineer | AI/ML | $35 | LLM, Agents |
| DevOps Automator | DevOps | $25 | CI/CD, Docker |

---

## 📈 Metrics Tracked

### Per Agent
```python
agent.performance = {
    "hours_worked": 0,
    "tokens_consumed": 0,
    "projects_completed": 0,
    "becoin_earned": 0.0,
    "becoin_spent": 0.0,
    "active_project": None,
    "last_activity": timestamp
}
```

### Per Project
```python
project.metrics = {
    "cost_to_date": 0.0,
    "hours_spent": 0,
    "tokens_used": 0,
    "progress_percent": 0.0,
    "roi": 0.0  # value / cost
}
```

### Global Economy
```python
economy.metrics = {
    "burnRate": 120.0,          # $/Stunde
    "runwayHours": 778.0,        # Stunden bis $0
    "profitMargin": -100.0,      # %
    "agentEfficiency": 0.0,      # Token/$ Value
    "taxPaid": 0.0,              # Total Tax
    "revenueGenerated": 0.0      # Total Revenue
}
```

---

## 🔄 Autonomous Operation Loop

```python
while economy.running:
    # Every 1 hour (5 seconds real time)
    1. Deduct agent salaries (Treasury → Agent)
    2. Track token usage (Agent Activity)
    3. Calculate tax exposure (Daily)
    
    # Every 1 simulated day
    4. Pay taxes (Treasury → Finanzamt)
    5. Generate financial report
    6. Check for insolvency
    
    # Every project completion
    7. Add revenue to Treasury
    8. Distribute bonuses
    9. Update agent equity
    
    # Continuous
    10. Agents work on projects
    11. Progress increments
    12. Dashboard updates
```

---

## 🚨 Failure Modes & Safeguards

### Insolvency Protection
```python
if treasury.balance < 100:
    trigger_alert("CRITICAL: Low runway!")
    pause_non_essential_operations()
```

### Agent Burnout
```python
if agent.hours_worked > 160:  # 4 weeks × 40h
    agent.status = "EXHAUSTED"
    require_cooldown(hours=24)
```

### Token Limit
```python
if daily_tokens > 100_000:
    rate_limit_requests()
```

---

## 📊 Dashboard Data Structure

```json
{
  "treasury": {
    "balance": 7780.0,
    "startCapital": 10000,
    "taxPaid": 4320.0,
    "revenueGenerated": 2500.0
  },
  "agents": [
    {
      "id": "agent-001",
      "name": "Frontend Developer",
      "role": "Frontend",
      "hourly_rate": 25.0,
      "hours_worked": 48,
      "tokens_consumed": 45000,
      "becoin_earned": 1200.0,
      "status": "active"
    }
  ],
  "projects": [
    {
      "id": "proj-001",
      "name": "Dashboard Redesign",
      "cost": 2000,
      "value": 3000,
      "progress": 65,
      "team": ["agent-001"]
    }
  ],
  "autonomous_loop": {
    "status": "running",
    "cycles_completed": 48,
    "last_update": "2026-01-28T07:14:00Z"
  }
}
```

---

## 🎯 Success Criteria

Das System ist "Autonom" wenn:

1. ✅ Treasury balance > $1000
2. ✅ Mindestens 1 Projekt pro Tag abgeschlossen
3. ✅ Agenten arbeiten ohne menschliches Eingreifen
4. ✅ Token-Verbrauch wird korrekt getrackt
5. ✅ Steuern werden automatisch abgezogen
6. ✅ Dashboard zeigt Echtzeit-Daten

---

## 📝 Agent Chat Integration

Agents reportieren autonom:

```python
def agent_report(agent_id: str) -> dict:
    return {
        "agent": agent.name,
        "current_task": agent.current_task,
        "progress_percent": calculate_progress(agent),
        "needs_input": check_for_blockers(agent),
        "questions": [
            "Soll ich Feature X oder Y priorisieren?",
            "Budget für API-Rate-Limits?"
        ],
        "recommendations": agent_suggestions(agent)
    }
```

---

*Letzte Aktualisierung: 2026-01-28*
*Version: 2.0*
