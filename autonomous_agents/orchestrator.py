#!/usr/bin/env python3
"""
Autonomous Agent Orchestrator

This orchestrator executes implementation plans autonomously using local LLMs
(via Ollama) and specialized agent personalities from Agency_of_Agents.

Key Features:
- Reads implementation plans from markdown files
- Routes tasks to specialized agent personalities
- Executes code generation and file operations
- Runs tests and validation steps
- Provides progress monitoring and logging
"""
import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from autonomous_agents.economy_context import (  # noqa: E402
    build_default_economy,
    summarize_economy,
)
from autonomous_agents.personalities import load_personalities  # noqa: E402


@dataclass
class Task:
    """Represents a single task from an implementation plan."""

    number: int
    title: str
    description: str
    code_snippets: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    output: str = ""
    agent_personality: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of executing a task."""

    success: bool
    output: str
    files_modified: List[str]
    tests_passed: bool = False
    error_message: str = ""


class OllamaClient:
    """Client for interacting with local Ollama LLM."""

    def __init__(self, config_path: str = "autonomous_agents/config/models.json"):
        """Initialize Ollama client with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.model = self.config.get("primary_model", "qwen2.5-coder:7b")
        self.endpoint = self.config.get("endpoint", "http://localhost:11434")
        self.options = self.config.get("options", {})

    def _load_config(self) -> dict:
        """Load model configuration."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {}

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using the local LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt (e.g., agent personality)

        Returns:
            Generated text
        """
        # Build the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Call Ollama API via curl
        cmd = [
            "curl",
            "-s",
            f"{self.endpoint}/api/generate",
            "-d",
            json.dumps(
                {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": self.options,
                }
            ),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"Ollama API call failed: {result.stderr}")

            response = json.loads(result.stdout)
            return response.get("response", "")

        except subprocess.TimeoutExpired:
            raise RuntimeError("LLM generation timed out after 120 seconds")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse LLM response: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")


class PlanParser:
    """Parses implementation plans from markdown files."""

    def __init__(self, plan_path: str):
        """Initialize parser with plan file path."""
        self.plan_path = Path(plan_path)
        if not self.plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_path}")

    def parse(self) -> List[Task]:
        """
        Parse the plan file and extract tasks.

        Returns:
            List of Task objects
        """
        with open(self.plan_path, "r") as f:
            content = f.read()

        tasks = []
        current_task = None

        # Split into sections by task headers (## Task N:)
        task_pattern = r"^## Task (\d+): (.+)$"
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for task header
            match = re.match(task_pattern, line)
            if match:
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)

                # Start new task
                task_num = int(match.group(1))
                task_title = match.group(2).strip()
                current_task = Task(number=task_num, title=task_title, description="")

            elif current_task:
                # Accumulate task content
                if line.startswith("```"):
                    # Extract code snippet
                    code_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith("```"):
                        code_lines.append(lines[i])
                        i += 1
                    current_task.code_snippets.append("\n".join(code_lines))
                elif line.strip().startswith("**File:**"):
                    # Extract file path
                    file_path = line.split("**File:**")[1].strip().strip("`")
                    current_task.files_to_modify.append(file_path)
                else:
                    # Add to description
                    current_task.description += line + "\n"

            i += 1

        # Add last task
        if current_task:
            tasks.append(current_task)

        return tasks


class Orchestrator:
    """Main orchestrator for autonomous execution."""

    def __init__(self, plan_path: str, dry_run: bool = False):
        """
        Initialize orchestrator.

        Args:
            plan_path: Path to implementation plan
            dry_run: If True, don't execute commands, just show what would happen
        """
        self.plan_path = plan_path
        self.dry_run = dry_run
        self.llm = OllamaClient()
        self.personality_loader = load_personalities()
        self.tasks: List[Task] = []
        self.current_task_index = 0
        self.economy = build_default_economy()
        self.economy_context = summarize_economy(self.economy)
        self.activation_context = {
            "prototype_focus": "",
            "relationship_goals": "",
            "data_permissions": {
                "local_files": False,
                "google_drive": False,
                "email": False,
            },
        }

        # Create logs directory
        self.logs_dir = Path("autonomous_agents/logs")
        self.logs_dir.mkdir(exist_ok=True, parents=True)

        # Initialize log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"execution_{timestamp}.log"

    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def load_plan(self):
        """Load and parse the implementation plan."""
        self.log(f"📖 Loading plan from {self.plan_path}")
        parser = PlanParser(self.plan_path)
        self.tasks = parser.parse()
        self.log(f"✅ Loaded {len(self.tasks)} tasks")

    def assign_personalities(self):
        """Assign agent personalities to tasks based on content."""
        self.log("🎭 Assigning agent personalities to tasks...")

        for task in self.tasks:
            # Use task title and description to find best match
            task_description = f"{task.title}: {task.description[:200]}"
            personality = self.personality_loader.get_best_match(task_description)

            if personality:
                task.agent_personality = personality.name
                self.log(f"  Task {task.number}: {personality.name}")

    def run_activation_briefing(self):
        """Establish first-contact rituals before autonomous execution."""
        self.log("\n🤝 Activation briefing started")
        self.log(
            "✨ Agents will reach out for a rapid prototype interview to keep the user "
            "energized about the idea."
        )
        self.log(
            "🔐 We also need explicit permission before touching local files, Google "
            "Drive artifacts, or email threads."
        )

        if sys.stdin.isatty():
            try:
                focus = input(
                    "Describe the first prototype vision or interview focus you want the "
                    "agents to pitch: "
                ).strip()
                relationship = input(
                    "How should the agents excite the user about next steps? "
                ).strip()

                def ask_permission(label: str) -> bool:
                    answer = input(
                        f"May the agents review {label}? (yes/no): "
                    ).strip().lower()
                    return answer in {"y", "yes"}

                self.activation_context["prototype_focus"] = focus
                self.activation_context["relationship_goals"] = relationship
                self.activation_context["data_permissions"]["local_files"] = ask_permission(
                    "local project files"
                )
                self.activation_context["data_permissions"]["google_drive"] = ask_permission(
                    "Google Drive"
                )
                self.activation_context["data_permissions"]["email"] = ask_permission(
                    "email threads"
                )
            except EOFError:
                self.log(
                    "⚠️ Interactive input not available; assuming permissions are pending.",
                    "WARNING",
                )
        else:
            self.log(
                "📝 Non-interactive session detected. Document prototype focus and "
                "permissions manually before continuing.",
            )

        self.log(
            "💡 Prototype focus: "
            f"{self.activation_context['prototype_focus'] or 'not captured'}"
        )
        self.log(
            "🎯 Enthusiasm plan: "
            f"{self.activation_context['relationship_goals'] or 'share a compelling teaser'}"
        )
        permissions = self.activation_context["data_permissions"]
        self.log(
            "🔎 Data permissions → local files: {local}, Google Drive: {drive}, email: {email}".format(
                local="granted" if permissions["local_files"] else "pending",
                drive="granted" if permissions["google_drive"] else "pending",
                email="granted" if permissions["email"] else "pending",
            )
        )

    def execute_task(self, task: Task) -> ExecutionResult:
        """
        Execute a single task.

        Args:
            task: Task to execute

        Returns:
            ExecutionResult with execution details
        """
        self.log(f"\n{'=' * 60}")
        self.log(f"🚀 Executing Task {task.number}: {task.title}")
        self.log(f"{'=' * 60}")

        task.status = "in_progress"

        try:
            # Get agent personality
            personality = None
            if task.agent_personality:
                personality = self.personality_loader.get_personality(
                    task.agent_personality
                )

            # Build the prompt
            prompt = self._build_task_prompt(task)

            # Get system prompt from personality
            system_prompt = personality.full_prompt if personality else None

            if self.dry_run:
                self.log("🔍 DRY RUN - Would execute:")
                self.log(f"  Personality: {task.agent_personality}")
                self.log(f"  Prompt length: {len(prompt)} chars")
                self.log(f"  Files to modify: {', '.join(task.files_to_modify)}")
                return ExecutionResult(
                    success=True,
                    output="Dry run - no execution",
                    files_modified=[],
                    tests_passed=False,
                )

            # Generate code/solution using LLM
            self.log("🤖 Generating solution...")
            response = self.llm.generate(prompt, system_prompt)

            self.log(f"📝 Generated {len(response)} characters of output")

            # Extract and apply file modifications
            files_modified = self._apply_file_changes(response, task)

            # Run tests if this is a testing task
            tests_passed = False
            if "test" in task.title.lower():
                tests_passed = self._run_tests()

            task.status = "completed"
            task.output = response

            self.log(f"✅ Task {task.number} completed successfully")

            return ExecutionResult(
                success=True,
                output=response,
                files_modified=files_modified,
                tests_passed=tests_passed,
            )

        except Exception as e:
            task.status = "failed"
            error_msg = f"Task {task.number} failed: {str(e)}"
            self.log(error_msg, "ERROR")

            return ExecutionResult(
                success=False,
                output="",
                files_modified=[],
                tests_passed=False,
                error_message=str(e),
            )

    def _build_task_prompt(self, task: Task) -> str:
        """Build the prompt for task execution."""
        prompt = f"""# Task: {task.title}

## Description
{task.description}

## Context
- Project: BeCoin Economic Simulation
- Working Directory: {os.getcwd()}
- Previous Tasks: {task.number - 1} completed
- Economy Snapshot:
{self.economy_context.describe()}

## Your Task
{task.description}

## Code Examples Provided
"""
        for i, snippet in enumerate(task.code_snippets, 1):
            prompt += f"\n### Example {i}\n```\n{snippet}\n```\n"

        prompt += """

## Files to Modify
"""
        for file_path in task.files_to_modify:
            prompt += f"- {file_path}\n"

        prompt += """

## Instructions
1. Analyze the task requirements
2. Generate clean, production-ready code
3. Follow Python best practices and type hints
4. Include error handling and logging
5. Write clear comments
6. Return code wrapped in markdown code blocks with file paths

## Output Format
For each file, use this format:

**File: path/to/file.py**
```python
# Your code here
```

Now execute this task.
"""
        return prompt

    def _apply_file_changes(self, response: str, task: Task) -> List[str]:
        """
        Extract file changes from LLM response and apply them.

        Args:
            response: LLM output containing code blocks
            task: Current task

        Returns:
            List of modified file paths
        """
        modified_files = []

        # Extract file blocks using pattern: **File: path** followed by code block
        file_pattern = r"\*\*File:\s*([^\*]+)\*\*\s*```(?:\w+)?\n(.*?)```"
        matches = re.findall(file_pattern, response, re.DOTALL)

        for file_path, code in matches:
            file_path = file_path.strip()

            if self.dry_run:
                self.log(f"  Would modify: {file_path}")
                continue

            try:
                # Create directories if needed
                full_path = Path(file_path)
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                with open(full_path, "w") as f:
                    f.write(code)

                modified_files.append(file_path)
                self.log(f"  ✍️  Modified: {file_path}")

            except Exception as e:
                self.log(f"  ⚠️  Failed to modify {file_path}: {e}", "WARNING")

        return modified_files

    def _run_tests(self) -> bool:
        """Run tests to verify changes."""
        self.log("🧪 Running tests...")

        if self.dry_run:
            return True

        try:
            # Try to run pytest
            result = subprocess.run(
                ["pytest", "-v"], capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                self.log("  ✅ All tests passed")
                return True
            else:
                self.log("  ❌ Some tests failed", "WARNING")
                self.log(result.stdout)
                return False

        except FileNotFoundError:
            self.log("  ⚠️  pytest not found, skipping tests", "WARNING")
            return False
        except Exception as e:
            self.log(f"  ⚠️  Test execution failed: {e}", "WARNING")
            return False

    def execute_all(self):
        """Execute all tasks in sequence."""
        self.log("\n" + "=" * 60)
        self.log("🎬 Starting Autonomous Execution")
        self.log("=" * 60 + "\n")
        if self.activation_context["prototype_focus"]:
            self.log(
                "📣 Anchoring work around the user's prototype vision: "
                f"{self.activation_context['prototype_focus']}"
            )
        if self.activation_context["relationship_goals"]:
            self.log(
                "💬 Agents will emphasize: "
                f"{self.activation_context['relationship_goals']}"
            )
        permissions = self.activation_context["data_permissions"]
        if granted_sources := [
            name for name, allowed in permissions.items() if allowed
        ]:
            self.log(
                "📁 Approved research surfaces: " + ", ".join(granted_sources)
            )
        else:
            self.log(
                "📁 No research repositories approved yet; agents will rely on public "
                "context until permission arrives."
            )

        start_time = datetime.now()

        for i, task in enumerate(self.tasks):
            self.current_task_index = i

            result = self.execute_task(task)

            if not result.success:
                self.log(f"\n❌ Execution stopped at task {task.number}", "ERROR")
                self.log(f"Error: {result.error_message}", "ERROR")
                break

            # Small delay between tasks
            if i < len(self.tasks) - 1:
                self.log("\n⏸️  Pausing 2 seconds before next task...")
                import time

                time.sleep(2)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        self.print_summary(duration)

    def print_summary(self, duration: float):
        """Print execution summary."""
        self.log("\n" + "=" * 60)
        self.log("📊 Execution Summary")
        self.log("=" * 60)

        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        pending = sum(1 for t in self.tasks if t.status == "pending")

        self.log(f"Total Tasks: {len(self.tasks)}")
        self.log(f"✅ Completed: {completed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"⏳ Pending: {pending}")
        self.log(f"⏱️  Duration: {duration:.1f} seconds")
        self.log(f"📝 Log file: {self.log_file}")

        if completed == len(self.tasks):
            self.log("\n🎉 All tasks completed successfully!")
        elif failed > 0:
            self.log("\n⚠️  Some tasks failed. Check the log for details.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("plan", help="Path to implementation plan (markdown file)")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without actually running",
    )

    args = parser.parse_args()

    try:
        orchestrator = Orchestrator(args.plan, dry_run=args.dry_run)
        orchestrator.load_plan()
        orchestrator.assign_personalities()
        orchestrator.run_activation_briefing()
        orchestrator.execute_all()

    except KeyboardInterrupt:
        print("\n\n⚠️  Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
