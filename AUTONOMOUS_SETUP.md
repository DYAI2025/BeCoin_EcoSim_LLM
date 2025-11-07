# 🤖 BeCoin Autonomous System - Setup Guide

## Übersicht

Das BeCoin System kann in 3 Modi betrieben werden:

1. **Manual Mode** - Manuelle Ausführung von Plänen mit dem Orchestrator
2. **Continuous Simulation** - Kontinuierliche Wirtschaftssimulation mit Live-Updates
3. **Background Service** - Dauerhafter Betrieb als Systemdienst

## ⚡ Quick Start

### Option 1: Manuelle Ausführung (One-Shot)

```bash
# 1. Setup ausführen (einmalig)
./autonomous_agents/setup_autonomous_agents.sh

# 2. Plan ausführen
python3 autonomous_agents/orchestrator.py docs/plans/example-plan.md
```

### Option 2: Kontinuierliche Simulation

```bash
# System starten (läuft im Vordergrund)
./autonomous_startup.sh
```

**Was passiert:**
- ✅ Ollama wird geprüft und ggf. gestartet
- ✅ AI-Model wird geprüft und ggf. heruntergeladen
- ✅ Wirtschaftsdaten werden generiert
- ✅ Simulation läuft in 5-Sekunden-Zyklen (1 simulierte Stunde pro Zyklus)
- ✅ Dashboard-Daten werden alle 5 Sekunden aktualisiert
- ✅ Live-Updates auf https://becoin-ecosim-llm.fly.dev/

**Beenden:** `Ctrl+C`

### Option 3: Als Hintergrunddienst (Empfohlen)

```bash
# Service installieren und starten
sudo ./install_service.sh
```

**Service-Befehle:**

```bash
# Status prüfen
sudo systemctl status becoin-autonomous

# Logs anzeigen (live)
sudo journalctl -u becoin-autonomous -f

# Service stoppen
sudo systemctl stop becoin-autonomous

# Service starten
sudo systemctl start becoin-autonomous

# Service neustarten
sudo systemctl restart becoin-autonomous

# Service deaktivieren (bei Boot nicht mehr starten)
sudo systemctl disable becoin-autonomous
```

## 🏗️ Systemarchitektur

```
┌─────────────────────────────────────────────────────────┐
│                  Autonomes System                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Ollama     │◄────►│ Qwen2.5-7B   │               │
│  │  (LLM Server)│      │   (Model)    │               │
│  └──────┬───────┘      └──────────────┘               │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────┐              │
│  │      BeCoin Economy Engine           │              │
│  │  • Treasury Management               │              │
│  │  • Agent Orchestration               │              │
│  │  • Project Lifecycle                 │              │
│  │  • Burn Rate Simulation              │              │
│  └──────┬───────────────────────────────┘              │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────┐              │
│  │      Dashboard Exporter              │              │
│  │  • treasury.json                     │              │
│  │  • agent-roster.json                 │              │
│  │  • projects.json                     │              │
│  │  • impact-ledger.json                │              │
│  │  • orchestrator-status.json          │              │
│  └──────┬───────────────────────────────┘              │
│         │                                               │
└─────────┼───────────────────────────────────────────────┘
          │
          ▼
  ┌───────────────────┐
  │   Fly.io Deploy   │
  │   Dashboard UI    │
  └───────────────────┘
```

## 📊 Simulation-Zyklus

```
Cycle 1 (t=0h)    → Balance: $8500, Projects: 2 active
   ↓ (5 sec / 1h simulated)
Cycle 2 (t=1h)    → Burn $120, Progress +5%, Balance: $8380
   ↓
Cycle 3 (t=2h)    → Burn $120, Progress +10%, Balance: $8260
   ↓
... kontinuierlich ...
```

**Simulation-Events:**
- 30% Chance pro Zyklus: Projekt-Fortschritt (+5-15%)
- Projekte bei 100% → Status: completed
- Treasury Burn: -$120/h (konfigurierbar)
- JSON-Export: Alle 5 Sekunden
- Dashboard-Update: Real-time via Live-Reload

## 🔧 Konfiguration

### Economy Parameter

Editiere `autonomous_startup.sh` (Zeile 105+):

```python
# Treasury
treasury = Treasury(start_capital=10000, balance=8500)  # Anpassen

# Burn Rate
baseline_hourly_burn=120.0  # Stündliche Kosten

# Simulation Speed
time.sleep(5)  # Sekunden pro Zyklus (5 = 1 simulierte Stunde)
```

### Ollama Model

Andere Modelle verwenden:

```bash
# Alternatives Model herunterladen
ollama pull llama3.1:8b

# In autonomous_startup.sh ändern (Zeile 30)
if ollama list | grep -q "llama3.1:8b"; then
```

## 📁 Wichtige Dateien

```
.
├── autonomous_startup.sh          # Haupt-Startup-Script
├── install_service.sh             # Service-Installation
├── becoin-autonomous.service      # systemd Service-Definition
├── autonomous_agents/
│   ├── orchestrator.py            # Plan-basierte Ausführung
│   ├── monitor.py                 # Log-Monitoring
│   ├── logs/                      # Execution Logs
│   └── personalities/             # 51 Agenten-Persönlichkeiten
├── dashboard/
│   ├── becoin-economy/            # Live Dashboard-Daten
│   │   ├── treasury.json
│   │   ├── agent-roster.json
│   │   ├── projects.json
│   │   ├── impact-ledger.json
│   │   └── orchestrator-status.json
│   └── office-ui.html             # Frontend
└── docs/plans/                    # Implementation Plans
```

## 🔍 Monitoring

### Live Dashboard

https://becoin-ecosim-llm.fly.dev/

### Logs Anzeigen

```bash
# Service Logs (live)
sudo journalctl -u becoin-autonomous -f

# Letzte 100 Zeilen
sudo journalctl -u becoin-autonomous -n 100

# Logs seit gestern
sudo journalctl -u becoin-autonomous --since yesterday

# Nur Fehler
sudo journalctl -u becoin-autonomous -p err
```

### Status Prüfen

```bash
# Ollama Status
curl http://localhost:11434/api/tags

# Models auflisten
ollama list

# Economy Status (API)
curl http://localhost:3000/api/status

# Dashboard JSON
ls -lh dashboard/becoin-economy/
```

## 🐛 Troubleshooting

### Ollama startet nicht

```bash
# Manuell starten
ollama serve

# Oder als user service
systemctl --user start ollama
```

### Model nicht gefunden

```bash
# Model neu herunterladen
ollama pull qwen2.5-coder:7b

# Verfügbare Models prüfen
ollama list
```

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u becoin-autonomous -n 50

# Manuell testen
./autonomous_startup.sh

# Permissions prüfen
ls -la autonomous_startup.sh
# Sollte -rwxr-xr-x sein
```

### Dashboard zeigt keine Updates

```bash
# JSON-Dateien prüfen
ls -lht dashboard/becoin-economy/

# Letzte Änderung sollte < 10 Sekunden sein
stat dashboard/becoin-economy/treasury.json

# File-Content prüfen
cat dashboard/becoin-economy/treasury.json | jq .balance
```

## 🚀 Deployment

Das System läuft lokal und exportiert Daten für das Fly.io Dashboard.

**Workflow:**
1. Lokale Simulation läuft: `./autonomous_startup.sh`
2. Generiert JSON-Daten: `dashboard/becoin-economy/*.json`
3. Fly.io Dashboard liest Daten: Via Static Files Mount
4. Live-Updates: JSON wird alle 5 Sekunden aktualisiert

**Für echte Live-Synchronisation:**

```bash
# Dashboard neu deployen mit aktuellen Daten
fly deploy

# Oder: Rsync/SCP Setup für automatisches Upload
# (Advanced - benötigt zusätzliche Konfiguration)
```

## 💡 Tipps

1. **Performance**: Auf einem Server mit GPU läuft Ollama schneller
2. **Memory**: Qwen2.5-Coder 7B benötigt ~8GB RAM
3. **Disk**: ~5GB für Model + Dependencies
4. **Logs**: Logs rotieren automatisch (systemd journal)
5. **Backup**: Dashboard-Daten sind reproduzierbar (keine Backups nötig)

## 📚 Weitere Dokumentation

- [Autonomous Agents README](autonomous_agents/README.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Main README](README.md)
- [Claude.md](CLAUDE.md)

## 🎯 Use Cases

### 1. Entwicklung & Testing
```bash
# Vordergrund-Modus mit Live-Output
./autonomous_startup.sh
```

### 2. Demo & Präsentation
```bash
# Service-Modus (läuft im Hintergrund)
sudo ./install_service.sh
# Dashboard: https://becoin-ecosim-llm.fly.dev/
```

### 3. Production (24/7)
```bash
# Service installieren
sudo ./install_service.sh

# Monitoring einrichten
sudo journalctl -u becoin-autonomous -f | tee -a monitoring.log
```

---

**Built with ❤️ for autonomous AI development**
