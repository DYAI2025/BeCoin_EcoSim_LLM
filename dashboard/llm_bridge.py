"""
LLM Bridge für Agent-Chat-Antworten via Ollama

Dieser Bridge verbindet das Dashboard mit Ollama (lokaler LLM-Server) und generiert
kontextuelle Agent-Antworten basierend auf:
- Agent-Persönlichkeiten (aus Agency_of_Agents)
- Firmen-Context (Treasury, Projekte, Metriken)
- Guardrails (Treasury-Safety, ROI-Fokus)
"""

import httpx
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OllamaLLMBridge:
    """
    Bridge für Ollama LLM Integration im Dashboard-Chat.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        """
        Initialisiert den Ollama LLM Bridge.

        Args:
            base_url: Ollama Server URL (default: http://localhost:11434)
            model: LLM Model zu verwenden (default: qwen2.5-coder:7b)
        """
        self.base_url = base_url
        self.model = model
        self.timeout = 30.0

    async def generate_agent_response(
        self,
        agent_id: str,
        agent_personality: Dict,
        user_message: str,
        context: Dict
    ) -> str:
        """
        Generiert Agent-Antwort via Ollama LLM.

        Args:
            agent_id: Agent-Identifikator (z.B. "agent-helio")
            agent_personality: Personality-Definition aus Agency_of_Agents
            user_message: User-Nachricht
            context: Firmen-Context (Treasury, aktive Projekte, etc.)

        Returns:
            Generierte Agent-Antwort als String

        Raises:
            httpx.HTTPError: Bei Ollama-Verbindungsproblemen
            ValueError: Bei ungültigen Parametern
        """
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty")

        prompt = self._build_agent_prompt(
            agent_personality, user_message, context
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Generating response for {agent_id} via Ollama ({self.model})")

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 500,
                            "stop": ["\n\n\n", "User:", "Assistant:"]
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                agent_response = result.get("response", "").strip()
                logger.info(f"Generated {len(agent_response)} chars for {agent_id}")

                return agent_response

        except httpx.TimeoutException as e:
            logger.error(f"Ollama timeout for {agent_id}: {e}")
            return "⚠️ LLM-Timeout. Bitte erneut versuchen."
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error for {agent_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating response for {agent_id}: {e}")
            return f"⚠️ Fehler bei der Antwort-Generierung: {str(e)}"

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

        Args:
            personality: Agent-Persönlichkeit (Name, Rolle, Expertise, etc.)
            user_message: User-Nachricht
            context: Firmen-Context

        Returns:
            Vollständiger Prompt für LLM
        """
        treasury = context.get('treasury', {})
        projects = context.get('projects', {})

        # Agent-Persönlichkeit
        name = personality.get('name', 'Agent')
        role = personality.get('role', 'AI Assistant')
        expertise = personality.get('expertise', [])
        communication_style = personality.get('communication_style', 'Professionell und präzise')

        # Expertise formatieren
        expertise_text = ', '.join(expertise) if expertise else 'Allgemeine Expertise'

        # Treasury-Metriken
        balance = treasury.get('balance', 0)
        burn_rate = treasury.get('burn_rate', 0)
        runway_hours = treasury.get('runway_hours', 0)

        # Projekt-Counts
        active_count = len(projects.get('active', []))
        pipeline_count = len(projects.get('pipeline', []))

        # Guardrails
        guardrails = """
**KRITISCHE GUARDRAILS (NIEMALS IGNORIEREN):**
1. Treasury-Balance darf NIEMALS unter 0 fallen
2. Projekte NUR starten wenn ausreichend Budget verfügbar
3. IMMER ROI und Profit-Maximierung im Fokus behalten
4. STETS im Interesse der Firma handeln
5. Bei Unsicherheit: VORSICHTIG und KONSERVATIV agieren
        """.strip()

        prompt = f"""Du bist {name}, {role} in der BeCoin Economy Firma.

**Deine Expertise:** {expertise_text}

**Dein Kommunikationsstil:** {communication_style}

**AKTUELLER FIRMEN-CONTEXT:**
- Treasury Balance: {balance:,} Bc
- Burn Rate: {burn_rate:.1f} Bc/h
- Runway: {runway_hours:.1f} Stunden
- Aktive Projekte: {active_count}
- Pipeline Projekte: {pipeline_count}

{guardrails}

**USER-NACHRICHT:**
{user_message}

**DEINE AUFGABE:**
Beantworte die User-Nachricht als {name}. Sei:
- Konkret und handlungsorientiert
- Kurz (max 3-4 Sätze, außer bei komplexen Analysen)
- Professionell aber freundlich
- Fokussiert auf praktische Lösungen

Wenn die Nachricht eine Aktion impliziert (z.B. "Starte Projekt X"), dann:
1. Prüfe Treasury-Safety
2. Berechne Auswirkungen
3. Gib klare Empfehlung oder führe Aktion aus

**DEINE ANTWORT:**"""

        return prompt

    async def check_ollama_health(self) -> bool:
        """
        Prüft ob Ollama erreichbar ist und das Model verfügbar ist.

        Returns:
            True wenn Ollama erreichbar und Model verfügbar, sonst False
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Prüfe Ollama Server
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()

                # Prüfe ob Model verfügbar
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "") for m in models]

                if self.model in model_names:
                    logger.info(f"Ollama health check passed. Model '{self.model}' available.")
                    return True
                else:
                    logger.warning(f"Ollama health check: Model '{self.model}' not found. Available: {model_names}")
                    return False

        except httpx.TimeoutException:
            logger.warning("Ollama health check: Timeout")
            return False
        except httpx.HTTPError as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Ollama health check: {e}")
            return False

    def parse_agent_actions(self, agent_response: str) -> List[Dict]:
        """
        Parst Agent-Antwort nach Action-Intents.

        Beispiele:
        - "Ich starte das Deployment-Projekt mit 500 Bc Budget."
          → [{"type": "start_project", "project_name": "Deployment", "budget": 500}]

        - "Ich prüfe den Treasury-Status."
          → [{"type": "check_treasury"}]

        Args:
            agent_response: Agent-Antwort Text

        Returns:
            Liste von Action-Dicts
        """
        actions = []
        response_lower = agent_response.lower()

        # Pattern für häufige Aktionen
        patterns = {
            "start_project": r"starte?\s+(?:das\s+)?(?:projekt\s+)?['\"]?(\w+(?:\s+\w+)?)['\"]?.*?(\d+)\s*bc",
            "check_treasury": r"pr[üu]fe?.*?(?:treasury|kasse|balance|guthaben)",
            "complete_project": r"(?:schlie[sß]e?|beende?|fertig).*?(?:projekt\s+)?['\"]?(\w+)",
            "analyze_burn_rate": r"analys(?:iere?|e).*?(?:burn\s*rate|verbrennung)",
        }

        # Start Project Action
        match = re.search(patterns["start_project"], response_lower)
        if match:
            project_name = match.group(1).strip()
            budget = int(match.group(2))
            actions.append({
                "type": "start_project",
                "project_name": project_name.title(),
                "budget": budget
            })

        # Check Treasury Action
        if re.search(patterns["check_treasury"], response_lower):
            actions.append({
                "type": "check_treasury"
            })

        # Complete Project Action
        match = re.search(patterns["complete_project"], response_lower)
        if match:
            project_name = match.group(1).strip()
            actions.append({
                "type": "complete_project",
                "project_id": project_name.lower().replace(" ", "-")
            })

        # Analyze Burn Rate Action
        if re.search(patterns["analyze_burn_rate"], response_lower):
            actions.append({
                "type": "analyze_burn_rate"
            })

        if actions:
            logger.info(f"Detected {len(actions)} actions in agent response: {[a['type'] for a in actions]}")

        return actions


# Singleton instance
_llm_bridge = None


def get_llm_bridge() -> OllamaLLMBridge:
    """
    Gibt Singleton-Instanz des LLM Bridge zurück.

    Returns:
        OllamaLLMBridge Instanz
    """
    global _llm_bridge
    if _llm_bridge is None:
        _llm_bridge = OllamaLLMBridge()
    return _llm_bridge
