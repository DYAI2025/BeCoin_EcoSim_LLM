# BeCoin Economy - SPEX (Solution Proposal EXchange)

## Problem Statement
**Das Wirtschaftssystem kollabiert:** $120-200/h Burn bei $0 Revenue. Agenten arbeiten nicht, keine Kundengewinnung, passive "Simulation".

## Analyse-Grundlage
- Agent Zero Report: `beCoinCycle.md`
- Engine: `becoin_economy/engine_v2.py`
- Dashboard: `dashboard/office-ui.html`

## Lösungsvorschlag

### Phase 1: Work Assignment System
```
Tasks:
1. `assign_work_to_agents()` - Agenten aktivieren, Aufgaben zuweisen
2. `work_session_tracking()` - Arbeitssitzungen tracken
3. Nur Fortschritt wenn Agenten wirklich arbeiten
```

### Phase 2: Customer Acquisition
```
Tasks:
1. `generate_leads()` - Zufällige Anfragen generieren
2. `create_new_projects()` - Neue Projekte aus Leads erstellen
3. Pipeline-Management: Pipeline → Active → Completed
```

### Phase 3: Economics Balancing
```
Tasks:
1. Baseline Burn auf $50-80/h reduzieren
2. Project Values erhöhen oder häufiger abschließen
3. Passive Revenue Streams hinzufügen
```

### Phase 4: Dashboard/API Updates
```
Tasks:
1. `/api/treasury` Endpoint erstellen
2. `/api/projects` Pipeline View
3. CEO/Management Dashboard mit Fragen
```

## Requirements
- [ ] Agenten arbeiten autonom an Projekten
- [ ] Neue Projekte kommen durch Lead-Generation
- [ ] Revenue > Costs (im Durchschnitt)
- [ ] Dashboard zeigt Echtzeit-Daten + Fragen von Agenten
- [ ] CEO-Rolle definiert (wer fragt Kunden?)

## Technical Approach
```python
# Work Assignment
def assign_work_to_agents():
    for agent in idle_agents:
        project = get_available_project()
        if project:
            agent.status = "active"
            agent.current_task = project.name
            project.team.append(agent.id)

# Customer Acquisition  
def generate_leads():
    if random_chance(0.2):  # 20% chance per hour
        leads.append(create_lead())
```

## Deliverables
1. `engine_v3.py` - Mit Work Assignment & Lead Generation
2. `dashboard-v3.html` - CEO View + Agent Questions
3. `docs/API.md` - API Endpoints dokumentiert
4. `autonomous_startup_v3.sh` - Startup Script aktualisiert
5. `TODO.md` - Alle Tasks aufgelistet

## Timeline
- Phase 1: 2-3 Stunden
- Phase 2: 2-3 Stunden  
- Phase 3: 1 Stunde
- Phase 4: 2 Stunden

## Success Criteria
- ✅ Treasury Balance stabil oder wachsend
- ✅ Mindestens 1 Projekt/Tag abgeschlossen
- ✅ Agenten melden autonom Fragen
- ✅ Dashboard zeigt Revenue > Costs
- ✅ Neue Projekte erscheinen regelmäßig

---

*SPEX erstellt: 2026-01-28*
*Autoren: Agent Zero (Analyse), MOLT (Synthese)*
