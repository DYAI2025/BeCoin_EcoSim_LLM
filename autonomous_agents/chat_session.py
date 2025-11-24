"""Interactive chat entrypoint for agency-grade LLM workflows.

This module opens a chat session with one of the specialized agent
personalities while injecting the BeCoin EcoSim economy snapshot so the
conversation stays grounded in treasury health and project priorities.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from autonomous_agents.economy_context import (
    build_default_economy,
    summarize_economy,
)
from autonomous_agents.orchestrator import OllamaClient
from autonomous_agents.personalities import load_personalities


class AgentChatSession:
    """Economy-aware interactive chat with an autonomous agent."""

    def __init__(
        self,
        personality_name: Optional[str] = None,
        plan_path: Optional[Path] = None,
    ) -> None:
        self.llm = OllamaClient()
        self.personality_loader = load_personalities()
        self.personality = (
            self.personality_loader.get_personality(personality_name)
            if personality_name
            else None
        )

        self.history: List[Tuple[str, str]] = []
        self.plan_context = Path(plan_path) if plan_path else None
        self.economy = build_default_economy()
        self.economy_context = summarize_economy(self.economy)

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Compose the system prompt with economy and plan context."""

        segments = [
            "You are the autonomous company decision maker for BeCoin EcoSim.",
            "You run feature discovery, design, and delivery without waiting for user approval.",
            "Use the economy snapshot to select projects, unblock teams, and protect the treasury.",
            "If you need to take an action, describe it crisply and continue without asking permission.",
            "\nEconomy snapshot:\n" + self.economy_context.describe(),
        ]

        if self.plan_context and self.plan_context.exists():
            plan_text = self.plan_context.read_text()
            segments.append(
                "\nImplementation plan provided to bootstrap momentum:\n" + plan_text
            )

        if self.personality:
            segments.append(
                "\nYou must also embody this specialized agent persona:\n"
                + self.personality.full_prompt
            )

        return "\n\n".join(segments)

    def _render_conversation(self) -> str:
        """Combine history into a single prompt for the LLM."""

        transcript = []
        for role, message in self.history:
            transcript.append(f"{role.upper()}: {message}")
        transcript.append("AGENT:")
        return "\n".join(transcript)

    def send(self, user_message: str) -> str:
        """Send a message and receive an agent response."""

        self.history.append(("user", user_message))
        prompt = self._render_conversation()
        response = self.llm.generate(prompt, system_prompt=self.system_prompt)
        cleaned_response = response.strip()
        self.history.append(("agent", cleaned_response))
        return cleaned_response

    def interact(self) -> None:
        """Start a CLI chat loop."""

        persona_label = (
            f"{self.personality.name} ({self.personality.category})"
            if self.personality
            else "senior autonomous operator"
        )
        print(
            "\n🤖 Starting chat with",
            persona_label,
            "— type 'exit' or 'quit' to stop.\n",
        )

        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if user_input.lower() in {"exit", "quit"}:
                break

            if not user_input:
                continue

            reply = self.send(user_input)
            print(f"\nAgent: {reply}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat with BeCoin agents")
    parser.add_argument(
        "--personality",
        help="Name of the agent personality (defaults to senior autonomous operator)",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        help="Optional plan markdown to inject as context for the agent",
    )
    parser.add_argument(
        "--message",
        help="Send a single message and print the response instead of opening an interactive loop",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session = AgentChatSession(args.personality, args.plan)

    if args.message:
        reply = session.send(args.message)
        print(reply)
        return

    if not sys.stdin.isatty():
        print("Interactive chat requires a TTY. Use --message for one-off prompts.")
        sys.exit(1)

    session.interact()


if __name__ == "__main__":
    main()
