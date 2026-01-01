# Fly.io LLM Integration - Lösungsstrategien

**Status**: Planning
**Erstellt**: 2025-12-20
**Ziel**: Echte AI-Agent-Funktionalität auf Fly.io ermöglichen

---

## Problemstellung

Das BeCoin EcoSim System nutzt derzeit **Ollama** für LLM-Inferenz, was lokal gut funktioniert, aber auf Fly.io nicht läuft, weil:
- Ollama benötigt ~8-16GB RAM für 7B Modelle
- Aktuelle Fly.io Konfiguration: 2GB RAM, 4 vCPUs
- Docker-Image enthält kein Ollama
- Keine GPU-Unterstützung in der aktuellen Config

**Betroffene Features:**
- `autonomous_agents/chat_session.py` - Interaktiver Chat mit AI
- `autonomous_agents/orchestrator.py` - Autonome Code-Generierung
- Alle 51 spezialisierten Agent-Persönlichkeiten

---

## Lösungsoptionen

### ⭐ Option 1: Anthropic Claude API (EMPFOHLEN)

**Vorteile:**
- ✅ Bereits in `requirements.txt` (`anthropic==0.18.1`)
- ✅ Schnelle Integration (~2-4 Stunden Entwicklung)
- ✅ Keine Infrastruktur-Verwaltung
- ✅ Claude Sonnet 4.5 für beste Code-Qualität
- ✅ Pay-per-use, keine Fixkosten

**Nachteile:**
- ❌ API-Kosten pro Request (~$3-15 pro 1M Tokens)
- ❌ Abhängigkeit von externem Service
- ❌ Latenz durch Netzwerk-Calls

**Geschätzte Kosten:**
- 1000 Chat-Messages/Monat: ~$2-5
- 100 autonome Executions/Monat: ~$10-20
- **Total: $15-25/Monat** bei moderater Nutzung

**Implementierung:**

```python
# autonomous_agents/llm_client.py
import os
from anthropic import Anthropic

class LLMClient:
    """Abstraction layer for LLM providers."""

    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "ollama")

        if self.provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        elif self.provider == "ollama":
            # Existing Ollama implementation
            self.endpoint = "http://localhost:11434"
            self.model = "qwen2.5-coder:7b"

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if self.provider == "anthropic":
            messages = [{"role": "user", "content": prompt}]
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt or "",
                messages=messages
            )
            return response.content[0].text

        elif self.provider == "ollama":
            # Existing curl-based Ollama call
            return self._call_ollama(prompt, system_prompt)

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider!r}")
```

**Deployment:**
```bash
# Fly.io secrets setzen
fly secrets set LLM_PROVIDER="anthropic"
fly secrets set ANTHROPIC_API_KEY="sk-ant-..."
fly secrets set ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"

# Deploy
fly deploy
```

**Zeitaufwand:**
- Implementation: 2-3 Stunden
- Testing: 1 Stunde
- Deployment: 30 Minuten
- **Total: ~4 Stunden**

---

### Option 2: OpenAI API

**Vorteile:**
- ✅ Sehr gut dokumentiert
- ✅ Breite Modellauswahl (GPT-4o, o1)
- ✅ Schnelle Integration
- ✅ Gute Code-Generation mit o1-mini

**Nachteile:**
- ❌ Zusätzliche Dependency (`openai` Package)
- ❌ API-Kosten ähnlich wie Claude
- ❌ Teilweise höhere Latenz

**Geschätzte Kosten:**
- GPT-4o: ~$2.50-10/1M Tokens
- o1-mini (Code): ~$3-12/1M Tokens
- **Total: $15-30/Monat**

**Implementation:**
```python
from openai import OpenAI

class LLMClient:
    def __init__(self, provider: str = None):
        if provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if self.provider == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
```

**Zeitaufwand:** ~4-5 Stunden

---

### Option 3: Ollama auf größeren Fly.io Maschinen

**Vorteile:**
- ✅ Keine API-Kosten
- ✅ Volle Kontrolle über Modelle
- ✅ Keine externen Dependencies
- ✅ Privacy (Code bleibt intern)

**Nachteile:**
- ❌ Hohe Infrastruktur-Kosten
- ❌ Komplexere Deployment-Pipeline
- ❌ Längere Cold-Start-Zeiten
- ❌ Modell-Download bei jedem Deploy

**Ressourcenanforderungen:**
- **Minimum**: 8GB RAM, 4 CPUs (~$100-150/Monat)
- **Empfohlen**: 16GB RAM, 8 CPUs (~$200-300/Monat)

**Fly.io Konfiguration:**

```toml
# fly.toml
[[vm]]
  cpu_kind = 'performance'  # oder 'shared'
  cpus = 8
  memory_mb = 16384  # 16GB

[build]
  dockerfile = "Dockerfile.ollama"
```

**Dockerfile.ollama:**
```dockerfile
FROM python:3.11-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Download model during build (increases image size massively!)
RUN ollama serve & sleep 5 && ollama pull qwen2.5-coder:7b

# Rest of setup...
COPY . /app
WORKDIR /app

# Start both Ollama and FastAPI
CMD ollama serve & sleep 5 && uvicorn dashboard.server:app --host 0.0.0.0 --port 3000
```

**Geschätzte Kosten:** $150-300/Monat

**Zeitaufwand:** ~8-12 Stunden (komplexes Setup)

---

### Option 4: Together.ai / Replicate (Serverless LLM)

**Vorteile:**
- ✅ Günstigere Preise als OpenAI/Claude
- ✅ Open-Source Modelle (Llama, Qwen, etc.)
- ✅ Serverless, keine Infrastruktur
- ✅ GPU-beschleunigte Inferenz

**Nachteile:**
- ❌ Weniger Mainstream als OpenAI/Claude
- ❌ potenziell variable Verfügbarkeit

**Together.ai Kosten:**
- Qwen 2.5 Coder 32B: ~$0.60/1M Tokens (Input), ~$0.60/1M (Output)
- **Total: ~$5-10/Monat** bei moderater Nutzung

**Implementation (Together.ai):**
```python
import requests

class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = provider
        if provider == "together":
            self.api_key = os.getenv("TOGETHER_API_KEY")
            self.model = "Qwen/Qwen2.5-Coder-32B-Instruct"

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if self.provider == "together":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 4096
                }
            )
            try:
                response.raise_for_status()
            except requests.RequestException as exc:
                raise RuntimeError(f"Together.ai request failed") from exc

            try:
                data = response.json()
            except ValueError as exc:
                raise RuntimeError("Together.ai response was not valid JSON") from exc

            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError("Unexpected Together.ai response format") from exc
```

**Zeitaufwand:** ~3-4 Stunden

---

### Option 5: Hybrid-Ansatz (Dashboard + Separate LLM-Service)

**Architektur:**
- **Fly.io App 1**: Dashboard (existierend, 2GB RAM)
- **Fly.io App 2**: Ollama-Service (8-16GB RAM, separate Maschine)
- Kommunikation über internes Fly.io Netzwerk (6PN)

**Vorteile:**
- ✅ Skalierbarkeit (LLM-Service kann unabhängig skalieren)
- ✅ Dashboard bleibt kostengünstig
- ✅ Keine API-Kosten
- ✅ Privacy

**Nachteile:**
- ❌ Komplexere Architektur
- ❌ Zwei Apps zu verwalten
- ❌ Höhere Gesamt-Kosten (~$100-150/Monat nur für LLM-Service)

**Geschätzte Kosten:**
- Dashboard: $5-10/Monat
- LLM-Service: $100-150/Monat
- **Total: $105-160/Monat**

**Zeitaufwand:** ~12-16 Stunden (komplexes Multi-App-Setup)

---

## Vergleichstabelle

| Option | Kosten/Monat | Setup-Zeit | Wartung | Code-Qualität | Privacy |
|--------|--------------|------------|---------|---------------|---------|
| **Claude API** | $15-25 | 4h | Niedrig | ⭐⭐⭐⭐⭐ | Extern |
| **OpenAI API** | $15-30 | 4-5h | Niedrig | ⭐⭐⭐⭐ | Extern |
| **Ollama (Fly)** | $150-300 | 8-12h | Mittel | ⭐⭐⭐ | Intern |
| **Together.ai** | $5-10 | 3-4h | Niedrig | ⭐⭐⭐⭐ | Extern |
| **Hybrid** | $105-160 | 12-16h | Hoch | ⭐⭐⭐ | Intern |

---

## 🎯 Empfehlung

**Für Prototyping/MVP:**
→ **Option 1: Anthropic Claude API**
- Schnellste Implementation
- Beste Code-Qualität
- Moderate Kosten
- Einfach zu deployen

**Für Budget-bewusste Projekte:**
→ **Option 4: Together.ai**
- Niedrigste Kosten
- Gute Code-Modelle verfügbar
- Serverless

**Für Production mit hohem Volumen:**
→ **Option 5: Hybrid-Ansatz**
- Langfristig günstiger bei hohem Volumen
- Volle Kontrolle
- Privacy-freundlich

---

## Implementierungsplan (Option 1: Claude API)

### Phase 1: LLM Client Abstraktion (2h)
```bash
# Neue Datei erstellen
touch autonomous_agents/llm_client.py

# Tests erstellen
touch autonomous_agents/tests/test_llm_client.py
```

**Implementierung:**
1. `LLMClient` Klasse mit Provider-Abstraktion
2. Anthropic Integration
3. Fallback auf Ollama für lokale Entwicklung
4. Environment-basierte Konfiguration

### Phase 2: Integration in bestehenden Code (1.5h)
1. `orchestrator.py` updaten → LLMClient verwenden
2. `chat_session.py` updaten → LLMClient verwenden
3. `economy_context.py` bleibt unverändert

### Phase 3: Testing (1h)
1. Unit Tests für LLMClient
2. Integration Tests mit Mock-Responses
3. Manuelles Testing gegen echte Claude API

### Phase 4: Deployment (30min)
```bash
# Secrets setzen
fly secrets set LLM_PROVIDER="anthropic"
fly secrets set ANTHROPIC_API_KEY="sk-ant-..."

# requirements.txt updaten (bereits vorhanden)
# anthropic==0.18.1 ✓

# Deploy
fly deploy
```

---

## Environment Variables (alle Optionen)

```bash
# Option 1: Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Option 2: OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Option 3/5: Ollama (local/Fly.io)
LLM_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Option 4: Together.ai
LLM_PROVIDER=together
TOGETHER_API_KEY=...
TOGETHER_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
```

---

## Migration Strategy

**Für reibungslose Migration:**

1. **Backwards-Compatible Implementation**
   - LLMClient erkennt automatisch verfügbare Provider
   - Fallback: Anthropic → Together → Ollama

2. **Environment-basierte Steuerung**
   - Lokal: Ollama (kostenlos)
   - Fly.io: Claude API (production)
   - CI/CD: Mock-Provider (testing)

3. **Graceful Degradation**
   - Falls API nicht verfügbar: Statische Antworten
   - Error-Handling mit Retry-Logic
   - Rate-Limiting awareness

---

## Nächste Schritte

**Soll ich die Implementation starten?**

1. **Welche Option bevorzugen Sie?**
   - Option 1 (Claude) - schnell & qualitativ
   - Option 4 (Together.ai) - günstig
   - Andere?

2. **Was ist Ihr Budget?**
   - <$20/Monat → Together.ai
   - $20-50/Monat → Claude/OpenAI
   - >$100/Monat → Ollama auf Fly.io

3. **Priorität?**
   - Schnelligkeit → Claude API (4h)
   - Kosten → Together.ai (3-4h)
   - Privacy → Ollama Hybrid (12-16h)

**Ich kann sofort mit der Implementation beginnen!**
