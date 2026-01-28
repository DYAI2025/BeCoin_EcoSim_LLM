# BeCoin Economy v3.0 - TODO

## 🎯 Ziel
Selbstständig funktionierendes Wirtschaftssystem mit Kundengewinnung, Projektarbeit und nachhaltigem Einkommen.

---

## Phase 1: Work Assignment System

### 1.1 Agent Activation
- [ ] Funktion `assign_tasks_to_agents()` erstellen
- [ ] Agent-Status: IDLE → ACTIVE bei Aufgaben-Zuweisung
- [ ] `current_task` setzen bei Aktivierung
- [ ] Tests: Agent wird aktiv bei verfügbarem Projekt

### 1.2 Work Session Tracking
- [ ] `start_work_session(agent_id, project_id)` Funktion
- [ ] `end_work_session(agent_id)` Funktion  
- [ ] Arbeitszeit pro Session tracken
- [ ] Token-Verbrauch pro Session loggen

### 1.3 Progress Updates
- [ ] Nur Fortschritt wenn Agent aktiv arbeitet
- [ ] `advance_time()` anpassen: require active_agents > 0
- [ ] Realistische Progress-Rate (nicht mehr 5%/h passiv)

### 1.4 Milestone Completion
- [ ] Subtask-Complete Events implementieren
- [ ] Project-Complete Trigger bei 100% mit echter Arbeit
- [ ] Revenue erst bei echter Fertigstellung auslösen

---

## Phase 2: Customer Acquisition

### 2.1 Lead Generation
- [ ] `generate_leads()` Funktion erstellen
- [ ] Zufällige Anfragen pro Stunde (20-30% Chance)
- [ ] Lead-Typen: Web-App, API, Dashboard, Integration
- [ ] Lead-Qualität: Budget, Timeline, Anforderungen

### 2.2 Project Pipeline Management
- [ ] `create_project_from_lead(lead)` Funktion
- [ ] Pipeline → Active Workflow wenn Agenten verfügbar
- [ ] Project-Werte basierend auf Lead-Budget
- [ ] Pipeline-Dashboard: Alle Leads anzeigen

### 2.3 Customer Interaction
- [ ] CEO-Fragen bei Lead-Generierung
- [ ] "Kunde X fragt Y an - annehmen oder ablehnen?"
- [ ] Acceptance-Rate: ~70% der Leads
- [ ] Abgelehnte Leads als "lost" tracken

### 2.4 Market Dynamics
- [ ] Lead-Volumen variiert (Saison-Effekte)
- [ ] Competition-Faktor: Manchmal verliert man Leads
- [ ] Upselling: Bestehende Projekte erweitern

---

## Phase 3: Economics Balancing

### 3.1 Burn Rate Adjustment
- [ ] Baseline Burn: $120/h → $60/h reduzieren
- [ ] Variable Kosten nur bei aktiver Arbeit
- [ ] Fixed Costs: Server, Infrastructure
- [ ] Variable Costs: Agent-Salaries, Token-Usage

### 3.2 Revenue Streams
- [ ] Project Revenue (Primary): $2,000-5,000/projekt
- [ ] Recurring Revenue: Monthly Retainers (optional)
- [ ] Consulting Fees: Schnell-Lieferungen (Bonus)

### 3.3 Profit Margins
- [ ] Ziel: 30-50% Profit-Marge
- [ ] Kosten-Kontrolle bei neuen Projekten
- [ ] ROI-Berechnung pro Projekt

### 3.4 Tax Implementation
- [ ] 15% Tax bei Profit (nicht bei Verlust)
- [ ] Quartalsweise vs. tägliche Abzüge
- [ ] Tax-Reserve bilden

---

## Phase 4: Dashboard & API Updates

### 4.1 API Endpoints
- [ ] `GET /api/treasury` - Balance, Metrics, Transactions
- [ ] `GET /api/agents` - Alle Agenten mit Status
- [ ] `GET /api/projects` - Alle Projekte mit Fortschritt
- [ ] `GET /api/pipeline` - Leads und Pipeline-Status
- [ ] `GET /api/questions` - Offene Fragen von Agenten

### 4.2 CEO Dashboard
- [ ] 💰 Treasury-Balance mit Trend-Graph
- [ ] 📊 Revenue vs. Costs Chart
- [ ] 👥 Agent-Übersicht mit aktuellen Aufgaben
- [ ] 📋 Pipeline-View: Neue Leads bewerten
- [ ] ❓ Fragen von Agenten: "Was soll ich_priorisieren?"
- [ ] 🚨 Alerts: Niedrige Balance, Blockierte Agenten

### 4.3 Agent Chat UI
- [ ] Jeder Agent mit eigenem Chat-Bereich
- [ ] "Ich brauche Input zu Feature X"
- [ ] "Projekt Y ist fertig - nächste Schritte?"
- [ ] Performance-Stats pro Agent

### 4.4 Real-time Updates
- [ ] WebSocket oder Polling (5s Intervall)
- [ ] Auto-Refresh bei Status-Änderungen
- [ ] Notification bei wichtigen Events

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests
- [ ] Test `assign_tasks_to_agents()`
- [ ] Test `generate_leads()`
- [ ] Test `advance_time()` mit aktiven Agenten
- [ ] Test Revenue-Trigger bei Project-Complete

### 5.2 Integration Tests
- [ ] End-to-End: 1 Woche Simulation
- [ ] Check: Revenue > Costs?
- [ ] Check: Alle Agenten arbeiten?
- [ ] Check: Neue Projekte entstehen?

### 5.3 Performance Tests
- [ ] 100+ Simulation-Zyklen ohne Absturz
- [ ] Memory-Leaks checken
- [ ] Dashboard-Ladezeit < 2s

### 5.4 User Acceptance
- [ ] Dashboard zeigt alles Wichtige
- [ ] CEO kann Entscheidungen treffen
- [ ] Agenten fragen sinnvolle Fragen
- [ ] Wirtschaft läuft autonom

---

## Phase 6: Deployment

### 6.1 Fly.io Deployment
- [ ] Dockerfile aktualisieren (engine_v3.py)
- [ ] Gesundheits-Check Endpoints
- [ ] Environment Variables setzen
- [ ] `fly deploy` und testen

### 6.2 Local Development
- [ ] `autonomous_startup_v3.sh` erstellen
- [ ] Demo-Modus mit beschleunigter Zeit
- [ ] Reset-Funktion für neue Simulation

### 6.3 Monitoring
- [ ] Error-Logging
- [ ] Performance-Metriken
- [ ] Balance-Alerts (bei < $1,000)

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `becoin_economy/engine_v3.py` | Create (von engine_v2.py erweitert) |
| `becoin_economy/engine_v2.py` | Backup behalten |
| `dashboard/economy-dashboard.html` | Create (CEO View) |
| `docs/API.md` | Create (API Dokumentation) |
| `autonomous_startup_v3.sh` | Create |
| `SPEX.md` | Finalisieren |
| `beCoinCycle.md` | Referenz behalten |

---

## 🎯 Definition of Done

**Wirtschaft läuft autonom wenn:**
- [ ] Treasury Balance > $5,000 (Start: $10,000)
- [ ] Mindestens 3 Projekte in 7 Tagen abgeschlossen
- [ ] Alle 4 Agenten arbeiten regelmäßig
- [ ] Revenue > Costs im Durchschnitt
- [ ] Dashboard zeigt Echtzeit-Daten
- [ ] CEO kann Fragen beantworten über Dashboard
- [ ] Keine menschliche Intervention nötig für Standard-Betrieb

---

*Erstellt: 2026-01-28*
*Basierend auf: Agent Zero Analyse + SPEX*
