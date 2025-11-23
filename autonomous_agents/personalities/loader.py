"""
Agency_of_Agents personality loader for autonomous agents.

Loads agent personalities from the Agency_of_Agents repository and makes them
available to the orchestrator for task-specific agent creation.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentPersonality:
    """Represents a specialized agent personality from Agency_of_Agents."""

    name: str
    description: str
    color: str
    category: str
    file_path: str
    full_prompt: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "category": self.category,
            "file_path": self.file_path,
            "full_prompt": self.full_prompt,
        }


class PersonalityLoader:
    """Loads and manages agent personalities from Agency_of_Agents."""

    def __init__(self, agency_path: Optional[str] = None):
        """
        Initialize the personality loader.

        Args:
            agency_path: Path to Agency_of_Agents directory. If None, will search
                         in standard locations.
        """
        if agency_path is None:
            agency_path = self._find_agency_path()

        self.agency_path = Path(agency_path)
        self.personalities: Dict[str, AgentPersonality] = {}
        self._load_all_personalities()

    def _find_agency_path(self) -> str:
        """Find the Agency_of_Agents directory."""
        # Try common locations
        search_paths = [
            "/home/dyai/Dokumente/DYAI_home/DEV/AI_LLM/Agency_of_Agents/agency-agents",
            os.path.expanduser("~/Agency_of_Agents/agency-agents"),
            "../../../Agency_of_Agents/agency-agents",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            "Could not find Agency_of_Agents directory. "
            "Please specify the path explicitly."
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown file."""
        frontmatter = {}
        body = content

        # Check for YAML frontmatter (--- at start and end)
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                # Parse frontmatter
                frontmatter_text = parts[1]
                body = parts[2]

                for line in frontmatter_text.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def _load_personality(
        self, file_path: Path, category: str
    ) -> Optional[AgentPersonality]:
        """Load a single personality from a markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, body = self._parse_frontmatter(content)

            # Extract metadata
            name = frontmatter.get("name", file_path.stem)
            description = frontmatter.get("description", "")
            color = frontmatter.get("color", "blue")

            # Create personality object
            personality = AgentPersonality(
                name=name,
                description=description,
                color=color,
                category=category,
                file_path=str(file_path),
                full_prompt=body.strip(),
            )

            return personality

        except Exception as e:
            print(f"Warning: Failed to load personality from {file_path}: {e}")
            return None

    def _load_all_personalities(self):
        """Load all personalities from the Agency directory."""
        categories = [
            "engineering",
            "design",
            "marketing",
            "product",
            "project-management",
            "support",
            "testing",
            "specialized",
            "spatial-computing",
        ]

        for category in categories:
            category_path = self.agency_path / category
            if not category_path.exists():
                continue

            # Load all markdown files in the category
            for md_file in category_path.glob("*.md"):
                personality = self._load_personality(md_file, category)
                if personality:
                    self.personalities[personality.name] = personality

        print(f"✅ Loaded {len(self.personalities)} agent personalities")

    def get_personality(self, name: str) -> Optional[AgentPersonality]:
        """Get a specific personality by name."""
        return self.personalities.get(name)

    def list_personalities(
        self, category: Optional[str] = None
    ) -> List[AgentPersonality]:
        """
        List all available personalities.

        Args:
            category: Optional category filter

        Returns:
            List of personality objects
        """
        if category:
            return [p for p in self.personalities.values() if p.category == category]
        return list(self.personalities.values())

    def search_personalities(self, query: str) -> List[AgentPersonality]:
        """
        Search for personalities matching a query.

        Args:
            query: Search string to match against name and description

        Returns:
            List of matching personalities
        """
        query = query.lower()
        matches = []

        for personality in self.personalities.values():
            if (
                query in personality.name.lower()
                or query in personality.description.lower()
            ):
                matches.append(personality)

        return matches

    def get_best_match(self, task_description: str) -> Optional[AgentPersonality]:
        """
        Find the best personality match for a given task.

        This uses simple keyword matching. In production, you might want
        to use embeddings or LLM-based matching.

        Args:
            task_description: Description of the task

        Returns:
            Best matching personality or None
        """
        task_lower = task_description.lower()

        # Define keyword mappings
        keyword_mappings = {
            "frontend": "engineering-frontend-developer",
            "backend": "engineering-backend-architect",
            "mobile": "engineering-mobile-app-builder",
            "ai": "engineering-ai-engineer",
            "devops": "engineering-devops-automator",
            "prototype": "engineering-rapid-prototyper",
            "ui": "design-ui-designer",
            "ux": "design-ux-researcher",
            "brand": "design-brand-guardian",
            "marketing": "marketing-growth-hacker",
            "content": "marketing-content-creator",
            "test": "testing-test-automation-engineer",
            "qa": "testing-qa-analyst",
        }

        # Check for keyword matches
        for keyword, personality_name in keyword_mappings.items():
            if keyword in task_lower:
                personality = self.get_personality(personality_name)
                if personality:
                    return personality

        # If no match, return a general-purpose agent
        return self.get_personality("engineering-senior-developer")

    def save_cache(self, cache_path: str):
        """Save loaded personalities to cache file."""
        cache_data = {
            name: personality.to_dict()
            for name, personality in self.personalities.items()
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return sorted(set(p.category for p in self.personalities.values()))

    def get_personality_for_dashboard_agent(self, agent_id: str) -> Optional[Dict]:
        """
        Gibt Personality-Definition für einen Dashboard-Agent zurück.

        Dashboard-Agenten werden auf spezialisierte Personalities aus
        Agency_of_Agents gemappt.

        Args:
            agent_id: Dashboard-Agent-ID (z.B. "agent-helio")

        Returns:
            Dict mit Personality-Daten oder None falls nicht gefunden
        """
        # Mapping: Dashboard-Agent-ID → Personality Name
        personality_mapping = {
            "agent-helio": "Product Manager",
            "agent-nami": "Backend Developer",
            "agent-atlas": "Financial Analyst",
            "agent-circe": "DevOps Engineer"
        }

        # Fallback für unbekannte Agenten
        personality_name = personality_mapping.get(agent_id)

        if not personality_name:
            # Try to find a general-purpose personality
            personality = self.get_personality("Senior Developer")
            if not personality:
                # Last resort: any available personality
                personalities_list = list(self.personalities.values())
                personality = personalities_list[0] if personalities_list else None
        else:
            # Search for matching personality
            personality = None
            for p in self.personalities.values():
                if personality_name.lower() in p.name.lower():
                    personality = p
                    break

        if not personality:
            return None

        # Convert to dict with additional dashboard-specific fields
        return {
            "name": personality.name,
            "role": personality.description or personality.name,
            "expertise": self._extract_expertise(personality.full_prompt),
            "communication_style": self._extract_communication_style(personality.full_prompt),
            "category": personality.category,
            "full_prompt": personality.full_prompt
        }

    def _extract_expertise(self, prompt: str) -> List[str]:
        """
        Extrahiert Expertise-Keywords aus Personality-Prompt.

        Args:
            prompt: Personality Prompt Text

        Returns:
            Liste von Expertise-Keywords
        """
        # Simple keyword extraction (kann mit NLP verbessert werden)
        expertise_keywords = []

        # Common tech keywords
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js",
            "FastAPI", "Django", "PostgreSQL", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "CI/CD", "DevOps",
            "Machine Learning", "AI", "Data Science",
            "UI/UX", "Design", "Product Management", "Finance"
        ]

        prompt_lower = prompt.lower()
        for keyword in tech_keywords:
            if keyword.lower() in prompt_lower:
                expertise_keywords.append(keyword)

        # Limit to top 5
        return expertise_keywords[:5]

    def _extract_communication_style(self, prompt: str) -> str:
        """
        Extrahiert Kommunikationsstil aus Personality-Prompt.

        Args:
            prompt: Personality Prompt Text

        Returns:
            Beschreibung des Kommunikationsstils
        """
        # Check for style indicators in prompt
        prompt_lower = prompt.lower()

        if "friendly" in prompt_lower or "warm" in prompt_lower:
            return "Freundlich und hilfsbereit"
        elif "technical" in prompt_lower or "precise" in prompt_lower:
            return "Technisch und präzise"
        elif "creative" in prompt_lower:
            return "Kreativ und inspirierend"
        elif "analytical" in prompt_lower:
            return "Analytisch und datengetrieben"
        else:
            return "Professionell und fokussiert"


# Convenience function for quick access
def load_personalities(agency_path: Optional[str] = None) -> PersonalityLoader:
    """
    Load all agent personalities.

    Args:
        agency_path: Optional path to Agency_of_Agents directory

    Returns:
        PersonalityLoader instance with all personalities loaded
    """
    return PersonalityLoader(agency_path)


if __name__ == "__main__":
    # Test the loader
    print("🧪 Testing Personality Loader...\n")

    try:
        loader = load_personalities()

        print("\n📊 Statistics:")
        print(f"  Total personalities: {len(loader.personalities)}")
        print(f"  Categories: {', '.join(loader.get_categories())}")

        print("\n🔍 Sample personalities:")
        for i, personality in enumerate(list(loader.personalities.values())[:5]):
            print(f"  {i + 1}. {personality.name} ({personality.category})")
            print(f"     {personality.description[:80]}...")

        print("\n🎯 Testing best match:")
        test_tasks = [
            "Build a React component for the dashboard",
            "Deploy the application to AWS",
            "Write unit tests for the API",
        ]

        for task in test_tasks:
            match = loader.get_best_match(task)
            if match:
                print(f"  Task: {task}")
                print(f"  Match: {match.name}")

        # Save cache
        cache_path = "../config/personalities_cache.json"
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        loader.save_cache(cache_path)
        print(f"\n💾 Saved personality cache to {cache_path}")

        print("\n✅ Personality loader test passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
