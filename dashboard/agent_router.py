"""
Agent Router für Smart Routing von User-Nachrichten

Wählt automatisch den besten Agenten basierend auf:
- Intent-Detection aus User-Nachricht
- Agent-Expertise und Rolle
- Agent-Verfügbarkeit und Status
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Smart Router für automatische Agent-Auswahl basierend auf User-Intent.
    """

    def __init__(self):
        """Initialisiert Agent Router."""
        # Intent-Keywords für verschiedene Kategorien
        self.intent_keywords = {
            "deployment": ["deploy", "deployment", "ci/cd", "docker", "kubernetes", "pipeline", "release"],
            "finance": ["treasury", "burn rate", "budget", "roi", "revenue", "cost", "financial", "kasse", "geld"],
            "backend": ["api", "endpoint", "database", "backend", "server", "rest", "graphql", "fastapi"],
            "frontend": ["ui", "ux", "react", "design", "interface", "component", "frontend"],
            "product": ["feature", "requirements", "roadmap", "priority", "product", "user story"],
            "testing": ["test", "qa", "quality", "bug", "testing", "coverage"],
            "data": ["data", "analytics", "metrics", "analysis", "statistics"],
            "general": ["help", "question", "info", "status"]
        }

        # Mapping: Intent → Agent-ID
        self.intent_to_agent = {
            "deployment": "agent-circe",  # DevOps Engineer
            "finance": "agent-atlas",     # Financial Analyst
            "backend": "agent-nami",      # Backend Developer
            "frontend": "agent-nami",     # Backend Developer (fallback)
            "product": "agent-helio",     # Product Manager
            "testing": "agent-nami",      # Backend Developer (fallback)
            "data": "agent-atlas",        # Financial Analyst (fallback)
            "general": "agent-helio"      # Product Manager (general queries)
        }

    def route_message_to_agent(
        self,
        user_message: str,
        available_agents: List[Dict],
        default_agent: str = "agent-helio"
    ) -> str:
        """
        Wählt besten Agenten für User-Message basierend auf Intent.

        Beispiele:
        - "Deploy the application" → DevOps Engineer (agent-circe)
        - "Check our burn rate" → Financial Analyst (agent-atlas)
        - "Build new API endpoint" → Backend Developer (agent-nami)
        - "Add new feature" → Product Manager (agent-helio)

        Args:
            user_message: User-Nachricht
            available_agents: Liste verfügbarer Agenten
            default_agent: Fallback-Agent wenn kein Match

        Returns:
            Agent-ID des am besten geeigneten Agenten
        """
        # Detect intent from message
        detected_intent = self._detect_intent(user_message)

        if detected_intent:
            # Get target agent for intent
            target_agent_id = self.intent_to_agent.get(detected_intent)

            # Check if agent is available
            if target_agent_id and self._is_agent_available(target_agent_id, available_agents):
                logger.info(f"Routed message to {target_agent_id} (Intent: {detected_intent})")
                return target_agent_id

            logger.warning(f"Preferred agent {target_agent_id} not available for intent {detected_intent}")

        # Fallback: Check if default agent is available
        if self._is_agent_available(default_agent, available_agents):
            logger.info(f"Routed message to default agent {default_agent}")
            return default_agent

        # Last resort: Return first available agent
        if available_agents:
            fallback = available_agents[0]["id"]
            logger.warning(f"Using fallback agent {fallback}")
            return fallback

        # No agents available
        logger.error("No agents available for routing")
        return default_agent

    def detect_multiple_intents(self, user_message: str) -> List[str]:
        """
        Detektiert mehrere Intents in einer Nachricht.

        Beispiel:
        "Check our burn rate and deploy the new feature"
        → ["finance", "deployment", "product"]

        Args:
            user_message: User-Nachricht

        Returns:
            Liste von erkannten Intents
        """
        intents = []
        message_lower = user_message.lower()

        for intent, keywords in self.intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if intent not in intents:
                    intents.append(intent)

        return intents

    def route_to_multiple_agents(
        self,
        user_message: str,
        available_agents: List[Dict]
    ) -> List[str]:
        """
        Routet Nachricht an mehrere Agenten (bei mehreren Intents).

        Args:
            user_message: User-Nachricht
            available_agents: Liste verfügbarer Agenten

        Returns:
            Liste von Agent-IDs
        """
        intents = self.detect_multiple_intents(user_message)

        if not intents:
            # No specific intent detected, use default
            return [self.route_message_to_agent(user_message, available_agents)]

        # Get unique agents for all intents
        agent_ids = []
        for intent in intents:
            agent_id = self.intent_to_agent.get(intent)
            if agent_id and agent_id not in agent_ids:
                if self._is_agent_available(agent_id, available_agents):
                    agent_ids.append(agent_id)

        return agent_ids if agent_ids else [self.route_message_to_agent(user_message, available_agents)]

    def get_routing_explanation(self, user_message: str, selected_agent_id: str) -> str:
        """
        Gibt Erklärung für Routing-Entscheidung zurück.

        Args:
            user_message: User-Nachricht
            selected_agent_id: Gewählter Agent

        Returns:
            Erklärung als String
        """
        intent = self._detect_intent(user_message)

        if not intent:
            return f"Nachricht an {selected_agent_id} (Standard-Agent)"

        intent_explanation = {
            "deployment": "Deployment/CI-CD Keywords erkannt",
            "finance": "Finanz/Treasury Keywords erkannt",
            "backend": "Backend/API Keywords erkannt",
            "frontend": "Frontend/UI Keywords erkannt",
            "product": "Product/Feature Keywords erkannt",
            "testing": "Test/QA Keywords erkannt",
            "data": "Data/Analytics Keywords erkannt",
            "general": "Allgemeine Anfrage"
        }

        explanation = intent_explanation.get(intent, "Intent erkannt")
        return f"Nachricht an {selected_agent_id} ({explanation})"

    def _detect_intent(self, message: str) -> Optional[str]:
        """
        Detektiert primären Intent aus Nachricht.

        Args:
            message: User-Nachricht

        Returns:
            Intent-String oder None
        """
        message_lower = message.lower()

        # Count matches for each intent
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score

        # Return intent with highest score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            return best_intent

        return None

    def _is_agent_available(self, agent_id: str, available_agents: List[Dict]) -> bool:
        """
        Prüft ob Agent verfügbar ist.

        Args:
            agent_id: Agent-ID
            available_agents: Liste verfügbarer Agenten

        Returns:
            True wenn verfügbar, False sonst
        """
        return any(agent["id"] == agent_id for agent in available_agents)

    def add_custom_intent_mapping(self, intent: str, keywords: List[str], agent_id: str):
        """
        Fügt custom Intent-Mapping hinzu.

        Args:
            intent: Intent-Name
            keywords: Liste von Keywords
            agent_id: Ziel-Agent-ID
        """
        self.intent_keywords[intent] = keywords
        self.intent_to_agent[intent] = agent_id
        logger.info(f"Added custom intent mapping: {intent} → {agent_id}")


# Singleton instance
_agent_router = None


def get_agent_router() -> AgentRouter:
    """
    Gibt Singleton-Instanz des Agent Router zurück.

    Returns:
        AgentRouter Instanz
    """
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter()
    return _agent_router


# Convenience function for quick routing
def route_to_best_agent(
    user_message: str,
    available_agents: List[Dict],
    default_agent: str = "agent-helio"
) -> str:
    """
    Convenience function für schnelles Routing.

    Args:
        user_message: User-Nachricht
        available_agents: Liste verfügbarer Agenten
        default_agent: Fallback-Agent

    Returns:
        Agent-ID
    """
    router = get_agent_router()
    return router.route_message_to_agent(user_message, available_agents, default_agent)
