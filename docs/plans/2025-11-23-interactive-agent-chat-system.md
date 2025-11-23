# Interactive Agent Chat System - Implementation Plan

**Datum:** 2025-11-23
**Status:** PLANUNG
**Ziel:** Vollständig interaktive Chat-Funktionalität mit LLM-gesteuerten Agenten, die direkte Auswirkungen auf die Firma haben

---

## 🎯 Vision

Transformation des Dashboards in ein **interaktives Command Center**, in dem der Benutzer:
- Mit spezifischen Agenten in Echtzeit kommunizieren kann
- Agenten über LLM (Ollama) orchestriert werden und kontextuell antworten
- Agenten-Interaktionen **direkte Auswirkungen auf die Firma** haben (Projekte, Treasury, etc.)
- Agenten stets im **Interesse der Firma** handeln (Treasury-Safety, ROI-Maximierung)
- Ein **großes, nutzbares Chatfenster** für angenehme Kommunikation nutzt

---

## 📋 Aktuelle Situation (Analyse)

### ✅ Vorhanden
- Dashboard mit Chat-UI (`dashboard/office-ui.html`, Zeilen 1046-1069)
- WebSocket-Infrastruktur (`/ws/chat` in `dashboard/server.py`, Zeile 474)
- REST-API für Chat (`/api/chat/send`, `/api/chat/history`)
- Agent-Selektor im UI
- Chat-Historie-Speicherung (JSON)
- Basis Broadcast-Funktionalität für alle Clients

### ❌ Fehlend
- **LLM-Integration**: Agenten-Antworten sind nur simuliert
- **Orchestrator-Integration**: Keine Verbindung zu `autonomous_agents/orchestrator.py`
- **Firmen-Auswirkungen**: Chat hat keine Auswirkung auf Economy/Treasury/Projekte
- **Agenten-Persönlichkeiten**: Keine Nutzung der 51 Personalities aus Agency_of_Agents
- **Großes Chatfenster**: Aktuell nur 400px × 600px (zu klein zum Lesen)

---

## 🏗️ Implementierungsphasen

### **Phase 1: Dashboard UI Umbau**
**Ziel:** Großes, nutzbares Chatfenster mit verbesserter UX

#### 1.1 Chatfenster-Layout überarbeiten
**Datei:** `dashboard/office-ui.html`

**Änderungen:**
- Chatfenster von **400px → 800px Breite** vergrößern
- Maximale Höhe von **600px → 900px** erhöhen
- Responsive Design für verschiedene Bildschirmgrößen
- **Neues Layout-Konzept:**
  ```
  ┌─────────────────────────────────────┐
  │  💬 AGENT CHAT                     │ ← Header (fixed)
  ├─────────────────────────────────────┤
  │                                     │
  │  [Agent Avatar] Agent-Name          │ ← Selected Agent Info
  │  Status: ACTIVE | Fokus: Backend    │
  │                                     │
  ├─────────────────────────────────────┤
  │  Chat Messages (scrollable)         │ ← 700px Höhe
  │  - User: "Fix deployment issue"     │
  │  - Agent: "Analyzing logs..."       │
  │  - Agent: "Found issue in..."       │
  │                                     │
  ├─────────────────────────────────────┤
  │  [Agent Selector ▼] [Input....] [>] │ ← Input Area
  └─────────────────────────────────────┘
  ```

**CSS-Anpassungen:**
```css
#agent-chat-section {
    width: 800px;  /* statt 400px */
    max-height: 900px;  /* statt 600px */
    min-height: 400px;
    resize: both;  /* User kann Größe anpassen */
    overflow: auto;
}

.chat-messages {
    max-height: 700px;  /* statt 400px */
    font-size: 12px;  /* statt 11px für bessere Lesbarkeit */
    line-height: 1.6;  /* mehr Zeilenabstand */
}

.chat-input {
    min-height: 60px;  /* Multi-line Input */
    resize: vertical;
}
```

**Neue Features:**
- **Resize-Handle**: User kann Chatfenster-Größe anpassen
- **Fullscreen-Modus**: Button zum Maximieren auf ganzen Bildschirm
- **Agent-Info-Panel**: Zeigt Status, Fokus, aktuelle Aufgabe des gewählten Agenten
- **Typing-Indicator**: "Agent tippt..." Animation während LLM-Antwort generiert wird

#### 1.2 Agent-Auswahl verbessern
**Neue Features:**
- **Avatar + Name** im Selector anzeigen
- **Status-Indicator** (🟢 aktiv, 🟡 idle, 🔴 blockiert)
- **Agent-Tooltip**: Beim Hover über Agent Details anzeigen (Rolle, aktuelle Aufgabe)
- **Filter-Funktion**: Nur aktive Agenten, nur verfügbare Agenten, etc.

#### 1.3 Chat-Message-Formatierung
**Neue Features:**
- **Markdown-Support**: Agenten können Markdown verwenden (Code-Blocks, Listen, etc.)
- **Code-Highlighting**: Syntax-Highlighting für Code-Snippets
- **Action-Buttons**: Agenten können Buttons in Nachrichten einbetten ("Projekt starten", "Treasury prüfen", etc.)
- **Timestamps**: Relative Zeit ("vor 2 Minuten") statt absoluter Zeit

---

### **Phase 2: LLM-Integration (Ollama)**
**Ziel:** Agenten antworten über Ollama LLM mit spezialisierten Persönlichkeiten

#### 2.1 Ollama-Client in Backend integrieren
**Neue Datei:** `dashboard/llm_bridge.py`

**Funktionalität:**
```python
"""
LLM Bridge für Agent-Chat-Antworten via Ollama
"""

import httpx
from typing import Dict, Optional

class OllamaLLMBridge:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen2.5-coder:7b"

    async def generate_agent_response(
        self,
        agent_id: str,
        agent_personality: Dict,
        user_message: str,
        context: Dict
    ) -> str:
        """
        Generiert Agent-Antwort via Ollama.

        Args:
            agent_id: Agent-Identifikator (z.B. "agent-helio")
            agent_personality: Personality-Definition aus Agency_of_Agents
            user_message: User-Nachricht
            context: Firmen-Context (Treasury, aktive Projekte, etc.)

        Returns:
            Generierte Agent-Antwort als String
        """
        prompt = self._build_agent_prompt(
            agent_personality, user_message, context
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
            )
            result = response.json()
            return result["response"]

    def _build_agent_prompt(
        self,
        personality: Dict,
        user_message: str,
        context: Dict
    ) -> str:
        """
        Baut Prompt für LLM basierend auf:
        - Agent-Persönlichkeit (Rolle, Expertise, Kommunikationsstil)
        - Firmen-Context (Treasury, Projekte, Metrics)
        - User-Message
        - Guardrails (Treasury-Safety, ROI-Fokus)
        """
        return f"""Du bist {personality['name']}, {personality['role']}.

**Deine Expertise:** {', '.join(personality.get('expertise', []))}

**Dein Kommunikationsstil:** {personality.get('communication_style', 'Professionell und präzise')}

**Firmen-Context:**
- Treasury Balance: {context['treasury']['balance']} Bc
- Burn Rate: {context['treasury']['burn_rate']} Bc/h
- Aktive Projekte: {len(context['projects']['active'])}
- Pipeline: {len(context['projects']['pipeline'])}

**Guardrails (KRITISCH):**
1. NIEMALS Treasury-Balance unter 0 reduzieren
2. IMMER ROI und Profit-Maximierung im Fokus
3. NIEMALS Projekte starten ohne ausreichende Mittel
4. STETS im Interesse der Firma handeln

**User-Nachricht:** {user_message}

**Deine Antwort (max 3-4 Sätze, handlungsorientiert):**"""

    async def check_ollama_health(self) -> bool:
        """Prüft ob Ollama erreichbar ist"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
```

#### 2.2 Personality Loader erweitern
**Datei:** `autonomous_agents/personalities/loader.py` (bereits vorhanden)

**Anpassungen:**
- Personality-Definitionen für Dashboard-Chat verfügbar machen
- Mapping: `agent_id` → `personality` (z.B. "agent-helio" → "Backend_Developer")
- REST-API Endpunkt: `/api/agents/personalities`

**Neue Funktion:**
```python
def get_personality_for_agent(agent_id: str) -> Optional[Dict]:
    """
    Gibt Personality-Definition für einen Dashboard-Agent zurück.

    Mapping:
    - agent-helio → Product Manager
    - agent-nami → Backend Developer
    - agent-atlas → Financial Analyst
    - agent-circe → DevOps Engineer
    """
    personality_mapping = {
        "agent-helio": "Product_Manager",
        "agent-nami": "Backend_Developer",
        "agent-atlas": "Financial_Analyst",
        "agent-circe": "DevOps_Engineer"
    }

    personality_name = personality_mapping.get(agent_id)
    if not personality_name:
        return None

    return load_personality_by_name(personality_name)
```

#### 2.3 Chat-Endpoint mit LLM erweitern
**Datei:** `dashboard/server.py`

**Änderungen an `_create_agent_message()`:**
```python
async def _create_agent_message(
    target_agent: str,
    user_content: str,
    economy_context: Dict
) -> Dict:
    """
    Erstellt Agent-Antwort via Ollama LLM.

    Args:
        target_agent: Agent-ID (z.B. "agent-helio")
        user_content: User-Nachricht
        economy_context: Aktueller Firmen-Zustand (Treasury, Projekte, etc.)

    Returns:
        Agent-Nachricht als Dict
    """
    # Personality laden
    personality = get_personality_for_agent(target_agent)
    if not personality:
        personality = get_default_personality()

    # LLM-Antwort generieren
    llm_bridge = OllamaLLMBridge()

    # Health-Check
    if not await llm_bridge.check_ollama_health():
        return {
            "type": "agent_message",
            "content": "⚠️ LLM-Service nicht erreichbar. Bitte Ollama starten.",
            "sender": target_agent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Antwort generieren
    response_content = await llm_bridge.generate_agent_response(
        agent_id=target_agent,
        agent_personality=personality,
        user_message=user_content,
        context=economy_context
    )

    return {
        "type": "agent_message",
        "content": response_content,
        "sender": target_agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "personality": personality["name"],
            "model": "qwen2.5-coder:7b"
        }
    }
```

---

### **Phase 3: Orchestrator-Integration & Firmen-Auswirkungen**
**Ziel:** Chat-Interaktionen haben direkte Auswirkungen auf Economy/Treasury/Projekte

#### 3.1 Economy-Context-Provider
**Neue Datei:** `dashboard/economy_bridge.py`

**Funktionalität:**
```python
"""
Bridge zwischen Dashboard-Chat und BecoinEconomy Engine
"""

from becoin_economy import BecoinEconomy
from becoin_economy.models import Project, Transaction
from becoin_economy.exporter import build_dashboard_payload
from typing import Dict, List
import json
from pathlib import Path

class EconomyBridge:
    def __init__(self, economy: BecoinEconomy):
        self.economy = economy

    def get_context_for_chat(self) -> Dict:
        """
        Liefert aktuellen Firmen-Context für LLM-Prompts.

        Returns:
            Dict mit Treasury, Projekten, Agenten, Metrics
        """
        snapshot = self.economy.snapshot()

        return {
            "treasury": {
                "balance": snapshot.treasury.balance,
                "burn_rate": self._calculate_burn_rate(),
                "runway_hours": self._calculate_runway()
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
                    "earned": agent.metrics.becoins_earned
                }
                for agent in snapshot.agents
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
                project_name=action["project_name"],
                budget=action["budget"]
            )

        elif action_type == "check_treasury":
            return self._check_treasury()

        elif action_type == "complete_project":
            return self._complete_project(
                project_id=action["project_id"]
            )

        elif action_type == "review_pipeline":
            return self._review_pipeline()

        else:
            return {"status": "error", "message": f"Unknown action: {action_type}"}

    def _start_project(self, agent_id: str, project_name: str, budget: int) -> Dict:
        """Startet neues Projekt (mit Treasury-Safety-Check)"""
        try:
            # Treasury-Safety-Check
            if self.economy.treasury.balance < budget:
                return {
                    "status": "rejected",
                    "message": f"❌ Insufficient funds. Balance: {self.economy.treasury.balance} Bc, Required: {budget} Bc",
                    "guardrail": "TREASURY_SAFETY"
                }

            # Projekt erstellen
            project = Project(
                id=f"project-{len(self.economy.projects) + 1}",
                name=project_name,
                value=budget,
                team=[agent_id],
                status="active"
            )

            self.economy.start_project(project)

            return {
                "status": "success",
                "message": f"✅ Projekt '{project_name}' gestartet. Budget: {budget} Bc",
                "project_id": project.id,
                "changes": {
                    "treasury": -budget,
                    "active_projects": +1
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"❌ Fehler beim Projektstart: {str(e)}"
            }

    def _check_treasury(self) -> Dict:
        """Gibt Treasury-Status zurück"""
        snapshot = self.economy.snapshot()

        return {
            "status": "success",
            "data": {
                "balance": snapshot.treasury.balance,
                "burn_rate": self._calculate_burn_rate(),
                "runway_hours": self._calculate_runway(),
                "recent_transactions": [
                    {
                        "type": tx.type,
                        "amount": tx.amount,
                        "timestamp": tx.timestamp
                    }
                    for tx in snapshot.treasury.transactions[-5:]
                ]
            }
        }

    def _calculate_burn_rate(self) -> float:
        """Berechnet Burn Rate (Bc/Stunde)"""
        # Implementierung basierend auf exporter.py
        pass

    def _calculate_runway(self) -> float:
        """Berechnet Runway in Stunden"""
        burn_rate = self._calculate_burn_rate()
        if burn_rate > 0:
            return self.economy.treasury.balance / burn_rate
        return float('inf')
```

#### 3.2 Action-Detection im LLM-Response
**Neue Funktion in `llm_bridge.py`:**

```python
def parse_agent_actions(agent_response: str) -> List[Dict]:
    """
    Parst Agent-Antwort nach Action-Intents.

    Beispiel:
    "Ich starte das Deployment-Projekt mit 500 Bc Budget."
    → [{"type": "start_project", "project_name": "Deployment", "budget": 500}]

    Returns:
        Liste von Action-Dicts
    """
    actions = []

    # Regex-Pattern für häufige Aktionen
    patterns = {
        "start_project": r"starte.*projekt\s+['\"]?(\w+)['\"]?.*?(\d+)\s*bc",
        "check_treasury": r"treasury|kasse|balance|guthaben",
        "complete_project": r"schließe.*projekt|fertigstellen.*(\w+)",
    }

    # Pattern-Matching
    for action_type, pattern in patterns.items():
        match = re.search(pattern, agent_response.lower())
        if match:
            # Action-Parameter extrahieren
            # ...
            actions.append({...})

    return actions
```

#### 3.3 WebSocket-Flow mit Actions
**Neuer Flow:**

```
User sendet Nachricht → WebSocket /ws/chat
    ↓
Backend empfängt Nachricht
    ↓
Economy-Context laden (Treasury, Projekte)
    ↓
LLM generiert Antwort (mit Personality + Context + Guardrails)
    ↓
Action-Detection: Antwort nach Aktionen parsen
    ↓
IF Aktionen gefunden:
    → Economy-Bridge: Aktionen ausführen
    → Treasury-Safety-Check
    → Economy-State ändern (Projekt starten, etc.)
    → Ergebnis an User senden
    ↓
Antwort an alle Chat-Clients broadcasten
    ↓
Dashboard-Update triggern (Projekte, Treasury, etc.)
```

**Code-Anpassung in `server.py`:**
```python
@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    chat_connections.append(websocket)

    try:
        while True:
            # User-Nachricht empfangen
            data = await websocket.receive_json()

            if data["type"] == "user_message":
                # 1. Speichern
                chat_messages.append(data)
                save_chat_history()

                # 2. Economy-Context laden
                economy_context = economy_bridge.get_context_for_chat()

                # 3. LLM-Antwort generieren
                agent_response = await _create_agent_message(
                    target_agent=data["target_agent"],
                    user_content=data["content"],
                    economy_context=economy_context
                )

                # 4. Actions parsen
                actions = parse_agent_actions(agent_response["content"])

                # 5. Actions ausführen
                action_results = []
                for action in actions:
                    result = economy_bridge.execute_agent_action(
                        agent_id=data["target_agent"],
                        action=action
                    )
                    action_results.append(result)

                # 6. Ergebnis-Nachricht erstellen
                if action_results:
                    result_message = "\n\n".join([
                        r["message"] for r in action_results
                    ])
                    agent_response["content"] += f"\n\n{result_message}"
                    agent_response["actions"] = action_results

                # 7. Broadcasten
                chat_messages.append(agent_response)
                save_chat_history()
                await broadcast_to_chat_clients(agent_response)

                # 8. Dashboard-Update triggern
                await trigger_dashboard_update()

    except WebSocketDisconnect:
        chat_connections.remove(websocket)
```

---

### **Phase 4: Agenten-Persönlichkeiten & Multi-Agent-Routing**
**Ziel:** 51 spezialisierte Agenten aus Agency_of_Agents nutzen

#### 4.1 Agent-Roster erweitern
**Neue Agenten-Typen im Dashboard:**

Aktuell: 4 Agenten (Helio, Nami, Atlas, Circe)

**Neu:** Bis zu 51 Agenten aus Agency_of_Agents:
- **Development:** Backend, Frontend, Full-Stack, DevOps, QA
- **Product:** Product Manager, Designer, UX Researcher
- **Business:** CEO, CFO, Sales, Marketing
- **Data:** Data Scientist, ML Engineer, Analytics
- **Operations:** HR, Legal, Security, etc.

**Implementierung:**
```python
# dashboard/agent_roster_generator.py

def generate_dashboard_agents(personalities_path: str) -> List[Dict]:
    """
    Generiert Dashboard-Agenten aus Agency_of_Agents Personalities.

    Returns:
        Liste von Agent-Dicts für Dashboard
    """
    personalities = load_all_personalities(personalities_path)

    agents = []
    for idx, personality in enumerate(personalities[:51]):  # Max 51
        agent = {
            "id": f"agent-{personality['name'].lower().replace(' ', '-')}",
            "name": personality["name"],
            "role": personality["role"],
            "avatar": personality.get("avatar", "👤"),
            "status": "idle",
            "expertise": personality.get("expertise", []),
            "communication_style": personality.get("communication_style", "Professional"),
            "equity_share": 0.0,
            "metrics": {
                "becoins_earned": 0,
                "projects_completed": 0
            }
        }
        agents.append(agent)

    return agents
```

#### 4.2 Smart Agent-Routing
**Automatische Agent-Auswahl basierend auf User-Intent:**

```python
# dashboard/agent_router.py

def route_message_to_agent(user_message: str, available_agents: List[Dict]) -> str:
    """
    Wählt besten Agenten für User-Message basierend auf Intent.

    Beispiele:
    - "Fix the deployment pipeline" → DevOps Engineer
    - "Analyze our burn rate" → Financial Analyst
    - "Design new feature UI" → UX Designer
    - "Write API endpoint" → Backend Developer

    Returns:
        Agent-ID des am besten geeigneten Agenten
    """
    # Intent-Detection via Keywords
    intent_keywords = {
        "deployment": ["deploy", "pipeline", "ci/cd", "docker"],
        "finance": ["treasury", "burn rate", "budget", "roi"],
        "design": ["ui", "ux", "design", "interface"],
        "backend": ["api", "endpoint", "database", "backend"],
        # ... weitere Intents
    }

    # Agent-Expertise-Mapping
    expertise_to_role = {
        "deployment": "DevOps_Engineer",
        "finance": "Financial_Analyst",
        "design": "UX_Designer",
        "backend": "Backend_Developer",
    }

    # Intent erkennen
    detected_intent = detect_intent(user_message, intent_keywords)

    # Passenden Agenten finden
    target_role = expertise_to_role.get(detected_intent)
    for agent in available_agents:
        if target_role in agent.get("role", ""):
            return agent["id"]

    # Fallback: Erster verfügbarer Agent
    return available_agents[0]["id"] if available_agents else "agent-helio"
```

**UI-Integration:**
- **Auto-Routing-Button:** "🎯 Best Agent" statt manueller Selektion
- **Routing-Explanation:** "Nachricht wird an DevOps Engineer geleitet (Grund: Deployment-Keywords erkannt)"

#### 4.3 Multi-Agent-Conversations
**Feature:** Mehrere Agenten können in einem Thread antworten

**Beispiel:**
```
User: "We need to optimize our burn rate and deploy faster"
    ↓
System: [Auto-Routing]
    → Financial Analyst: "Ich analysiere die Burn Rate..."
    → DevOps Engineer: "Ich optimiere das Deployment..."
    ↓
User erhält 2 Antworten im selben Thread
```

**Implementierung:**
```python
async def handle_multi_agent_message(user_message: str) -> List[Dict]:
    """
    Sendet Nachricht an mehrere Agenten gleichzeitig.

    Returns:
        Liste von Agent-Antworten
    """
    # Intent-Detection (mehrere Intents möglich)
    intents = detect_multiple_intents(user_message)

    # Für jeden Intent einen Agenten finden
    agents = [route_to_agent_by_intent(intent) for intent in intents]

    # Parallel Antworten generieren
    responses = await asyncio.gather(*[
        generate_agent_response(agent, user_message)
        for agent in agents
    ])

    return responses
```

---

## 🎨 UI/UX Verbesserungen

### 4.4 Chat-Features
- **Markdown-Rendering:** Agent-Antworten mit Code, Listen, Tabellen
- **Action-Buttons:** "Projekt starten", "Treasury prüfen" als klickbare Buttons
- **Typing-Indicator:** "Agent tippt..." während LLM-Generierung
- **Agent-Status:** Echtzeit-Status-Updates (🟢 verfügbar, 🟡 beschäftigt, 🔴 offline)
- **Thread-View:** Conversations nach Thema gruppieren
- **Search:** Chat-Historie durchsuchen
- **Export:** Chat-Verlauf als Markdown exportieren

### 4.5 Agent-Info-Panel
**Neues Sidebar-Panel beim Chat:**
```
┌─────────────────────────┐
│ 💼 Agent: Nami          │
│ Backend Developer       │
├─────────────────────────┤
│ Status: 🟢 Verfügbar    │
│ Fokus: API Development  │
│ Expertise:              │
│  • Python, FastAPI      │
│  • PostgreSQL           │
│  • REST APIs            │
├─────────────────────────┤
│ Performance:            │
│  Earned: 2,450 Bc       │
│  Completed: 8 Projects  │
│  Equity: 12.5%          │
├─────────────────────────┤
│ Guardrails:             │
│  ✓ Treasury Safety      │
│  ✓ ROI Maximierung      │
└─────────────────────────┘
```

---

## 🔒 Guardrails & Safety

### 5.1 Treasury-Safety
**KRITISCH:** Agenten dürfen NIEMALS Treasury-Balance unter 0 reduzieren

**Implementierung:**
```python
def validate_agent_action(action: Dict, economy: BecoinEconomy) -> Tuple[bool, str]:
    """
    Validiert Agent-Aktion vor Ausführung.

    Returns:
        (valid: bool, message: str)
    """
    if action["type"] == "start_project":
        budget = action["budget"]
        balance = economy.treasury.balance

        if balance < budget:
            return False, f"❌ TREASURY SAFETY: Balance ({balance} Bc) < Budget ({budget} Bc)"

        # Runway-Check: Mind. 24h Runway nach Projekt-Start
        burn_rate = calculate_burn_rate(economy)
        new_balance = balance - budget
        runway_hours = new_balance / burn_rate if burn_rate > 0 else float('inf')

        if runway_hours < 24:
            return False, f"❌ RUNWAY SAFETY: Nur {runway_hours:.1f}h Runway nach Projekt"

        return True, "✅ Action validated"

    return True, "✅ No validation required"
```

### 5.2 Action-Approval-Flow
**Optional:** User muss bestimmte Aktionen bestätigen

**Beispiel:**
```
Agent: "Ich starte das Refactoring-Projekt mit 1000 Bc Budget."
System: [Action detected: start_project]
    ↓
User erhält Approval-Nachricht:
    "🔔 Agent Nami möchte Projekt starten:
     - Name: Refactoring
     - Budget: 1000 Bc
     - Verbleibende Balance: 4000 Bc

     [✅ Genehmigen] [❌ Ablehnen]"
```

**Konfigurierbare Approval-Schwellen:**
```python
APPROVAL_THRESHOLDS = {
    "start_project": 500,  # Projekte >500 Bc benötigen Approval
    "complete_project": None,  # Kein Approval nötig
    "treasury_withdraw": 100,  # Withdrawals >100 Bc benötigen Approval
}
```

---

## 📊 Monitoring & Analytics

### 6.1 Chat-Analytics
**Neue Metriken im Dashboard:**
- **Total Messages:** Gesamt-Nachrichten seit Start
- **Agent Response Time:** Durchschnittliche Antwortzeit (LLM)
- **Actions Executed:** Anzahl ausgeführter Aktionen
- **Action Success Rate:** % erfolgreicher Aktionen
- **Most Active Agent:** Agent mit meisten Interaktionen
- **Top Actions:** Häufigste Action-Typen

**Visualisierung:**
```
Chat Analytics (Last 7 Days)
────────────────────────────────
Messages:        432
Avg Response:    2.3s
Actions:         89 (95% success)
Most Active:     Agent Nami (Backend Developer)
Top Action:      check_treasury (42%)
```

### 6.2 Agent-Performance-Tracking
**Neue Metriken pro Agent:**
- **Chat-Aktivität:** Anzahl Antworten, Durchschnittliche Länge
- **Aktionen:** Anzahl ausgeführter Aktionen, Erfolgsrate
- **Firmen-Impact:** Treasury-Änderungen durch Agent-Aktionen, ROI
- **User-Satisfaction:** implizit (Anzahl Follow-up-Fragen)
- **User-Satisfaction:** Implicit (Anzahl Follow-up-Fragen)

---

## 🔧 Technische Implementierung

### 7.1 Dependencies
**Neue Packages:**
```txt
# requirements.txt (Dashboard)
httpx>=0.27.0          # Ollama API Client
markdown>=3.5.0        # Markdown-Rendering
pygments>=2.17.0       # Code-Highlighting
python-multipart>=0.0.6  # File-Uploads (optional)
```

### 7.2 Umgebungsvariablen
```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
CHAT_AUTO_ROUTING=true
CHAT_MULTI_AGENT=true
CHAT_ACTION_APPROVAL=true
CHAT_ACTION_APPROVAL_THRESHOLD=500
AGENCY_PERSONALITIES_PATH=~/Dokumente/DYAI_Home/DEV/AI_LLM/Agency_of_Agents/
```

### 7.3 Dateistruktur
```
dashboard/
├── server.py                    # FastAPI Server (erweitert)
├── llm_bridge.py               # NEU: Ollama LLM Integration
├── economy_bridge.py           # NEU: Economy-Integration
├── agent_router.py             # NEU: Smart Agent-Routing
├── agent_roster_generator.py   # NEU: Agent-Roster aus Personalities
├── chat_analytics.py           # NEU: Chat-Analytics
├── office-ui.html              # Dashboard UI (erweitert)
├── chat_history.json           # Chat-Historie
└── becoin-economy/
    └── ...                     # Existing payload JSONs

autonomous_agents/
├── personalities/
│   ├── loader.py              # ERWEITERT: Dashboard-Integration
│   └── ...                    # 51 Personality-Definitionen
└── orchestrator.py            # Evtl. erweitert für Chat-Integration
```

---

## 🚀 Rollout-Plan

### Phase 1: UI Umbau (3-4 Stunden)
1. ✅ Chatfenster vergrößern (800px × 900px)
2. ✅ Resize-Funktion hinzufügen
3. ✅ Agent-Info-Panel implementieren
4. ✅ Markdown-Rendering hinzufügen
5. ✅ Typing-Indicator implementieren

### Phase 2: LLM-Integration (4-5 Stunden)
1. ✅ `llm_bridge.py` erstellen
2. ✅ Ollama-Client implementieren
3. ✅ Prompt-Engineering (mit Personalities + Context)
4. ✅ `server.py` erweitern für LLM-Antworten
5. ✅ Health-Check für Ollama
6. ✅ Error-Handling (Ollama offline, etc.)

### Phase 3: Orchestrator-Integration (5-6 Stunden)
1. ✅ `economy_bridge.py` erstellen
2. ✅ Economy-Context-Provider implementieren
3. ✅ Action-Detection implementieren
4. ✅ Action-Execution (mit Treasury-Safety)
5. ✅ Dashboard-Update triggern nach Aktionen
6. ✅ Approval-Flow implementieren (optional)

### Phase 4: Agenten-Persönlichkeiten (3-4 Stunden)
1. ✅ Agent-Roster erweitern (51 Agenten)
2. ✅ `agent_router.py` implementieren
3. ✅ Multi-Agent-Conversations
4. ✅ Agent-Info-Panel mit Details
5. ✅ UI-Tests mit verschiedenen Agenten

### Phase 5: Testing & Polish (2-3 Stunden)
1. ✅ End-to-End Tests
2. ✅ Guardrail-Tests (Treasury-Safety)
3. ✅ Performance-Tests (LLM-Antwortzeit)
4. ✅ UI/UX Polish
5. ✅ Dokumentation aktualisieren

**Gesamt:** ~17-22 Stunden

---

## 🧪 Test-Szenarien

### Szenario 1: Projekt starten via Chat
```
User: "Start a new API optimization project with 800 Bc budget"
    ↓
Agent (Backend Developer): "Ich analysiere die Anforderung...
    Aktueller Treasury: 5000 Bc
    Burn Rate: 50 Bc/h

    Projekt 'API Optimization' wird gestartet:
    - Budget: 800 Bc
    - Verbleibende Balance: 4200 Bc
    - Runway: 84h

    ✅ Projekt gestartet. Ich beginne mit der Implementierung."

System: [Action executed: start_project]
    → Treasury: 5000 → 4200 Bc
    → Active Projects: +1

Dashboard-Update: Projekt erscheint in "ACTIVE" Lane
```

### Szenario 2: Treasury-Safety Guardrail
```
User: "Launch the new feature with 6000 Bc budget"
    ↓
Agent (Product Manager): "Ich prüfe die Anforderung...
    Aktueller Treasury: 5000 Bc
    Budget: 6000 Bc

    ❌ TREASURY SAFETY: Insufficient funds.
    Balance (5000 Bc) < Required (6000 Bc)

    Ich empfehle:
    1. Budget auf 4000 Bc reduzieren
    2. Projekt in 2 Phasen aufteilen
    3. Zusätzliche Revenue generieren

    Was möchten Sie tun?"

System: [Action rejected: TREASURY_SAFETY]
    → Keine Änderung am Economy-State
```

### Szenario 3: Multi-Agent-Conversation
```
User: "We need to fix the deployment and analyze our financials"
    ↓
System: [Auto-Routing: 2 Intents erkannt]
    → DevOps Engineer
    → Financial Analyst

Agent (DevOps): "Ich analysiere das Deployment-System...
    Aktuelle Pipeline: 12min Build-Zeit
    Optimierungspotential: 50%

    Vorschlag: Docker-Layer-Caching aktivieren
    Zeitersparnis: 6min/Build
    Kosten: 100 Bc

    Soll ich implementieren?"

Agent (Financial Analyst): "Ich analysiere die Finanzen...
    Treasury: 5000 Bc
    Burn Rate: 50 Bc/h
    Revenue: 1200 Bc/Woche

    ⚠️ Burn Rate ist höher als Revenue!
    Handlungsempfehlung:
    1. Kosten reduzieren (30% möglich)
    2. Revenue steigern (2 neue Kunden)

    ROI-Prognose: Positiv in 3 Wochen"
```

---

## 📚 Dokumentation

### API-Dokumentation
**Neue Endpunkte:**
- `GET /api/agents/personalities` - Alle verfügbaren Agent-Personalities
- `GET /api/agents/{agent_id}/status` - Agent-Status
- `POST /api/chat/action` - Agent-Aktion ausführen (mit Approval)
- `GET /api/chat/analytics` - Chat-Analytics
- `GET /api/ollama/health` - Ollama-Health-Check

### User-Dokumentation
**Neue Sektion in CLAUDE.md:**
```markdown
## Interactive Agent Chat

Das Dashboard bietet einen vollständig interaktiven Chat mit 51 spezialisierten Agenten:

### Quick Start
1. Öffne Dashboard: http://localhost:3000
2. Chatfenster rechts unten öffnen
3. Agent auswählen oder Auto-Routing nutzen
4. Nachricht eingeben und Enter drücken

### Verfügbare Aktionen
Agenten können folgende Aktionen ausführen:
- ✅ Projekte starten/abschließen
- ✅ Treasury prüfen
- ✅ Pipeline reviewen
- ✅ Burn Rate analysieren
- ✅ ROI berechnen

### Guardrails
Alle Agenten unterliegen strikten Guardrails:
- 🔒 Treasury-Balance darf niemals <0 werden
- 🔒 Mindestens 24h Runway nach Projekt-Start
- 🔒 ROI-Maximierung im Fokus
- 🔒 Stets im Firmen-Interesse handeln

### Beispiele
\`\`\`
"Start API refactoring with 500 Bc budget"
"Check our treasury status"
"Analyze burn rate and suggest optimizations"
\`\`\`
```

---

## 🎯 Success Metrics

### KPIs
- **User Engagement:** Durchschnittliche Nachrichten pro Session
- **Action Success Rate:** % erfolgreicher Agent-Aktionen
- **Response Quality:** User-Feedback (Implicit: Follow-up-Fragen)
- **Economy Impact:** Treasury-Änderungen durch Chat-Aktionen
- **Agent Performance:** Durchschnittliche Antwortzeit

### Ziele
- ✅ 95%+ Action Success Rate
- ✅ <3s durchschnittliche Antwortzeit
- ✅ 100% Treasury-Safety (keine negativen Balances)
- ✅ 10+ Nachrichten pro User-Session
- ✅ 50%+ der Projekte via Chat gestartet

---

## 🔮 Future Enhancements

### V2.0 Features
- **Voice-Chat:** Spracheingabe/ausgabe für Agenten
- **Agent-Avatars:** Generierte Avatars für jeden Agenten
- **Multi-Language:** Deutsch, Englisch, weitere Sprachen
- **Agent-Learning:** Agenten lernen aus vergangenen Interaktionen
- **Advanced-Routing:** ML-basiertes Agent-Routing
- **Integration:** Slack, Discord, MS Teams
- **Mobile-App:** Native Mobile-Chat-App

### V3.0 Features
- **Autonomous-Mode:** Agenten können proaktiv Vorschläge machen
- **Inter-Agent-Chat:** Agenten kommunizieren untereinander
- **Simulation-Mode:** "What-If"-Szenarien durchspielen
- **Advanced-Analytics:** Predictive Analytics, Forecasting

---

## 🙏 Credits

- **Ollama:** LLM-Inference (qwen2.5-coder:7b)
- **Agency_of_Agents:** 51 Personality-Definitionen
- **BeCoin Economy:** Treasury & Project Management
- **FastAPI:** Backend-Framework
- **WebSockets:** Real-time Communication

---

## 📝 Changelog

### 2025-11-23 - Initial Plan
- ✅ Dashboard UI Analyse
- ✅ LLM-Integration Design
- ✅ Orchestrator-Integration Design
- ✅ Agenten-Persönlichkeiten Konzept
- ✅ Guardrails & Safety Konzept
- ✅ Rollout-Plan erstellt

---

**Status:** BEREIT FÜR IMPLEMENTIERUNG
**Nächster Schritt:** Phase 1 - Dashboard UI Umbau beginnen
