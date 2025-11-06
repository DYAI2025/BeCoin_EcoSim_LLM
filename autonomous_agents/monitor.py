#!/usr/bin/env python3
"""
Autonomous Agent Monitor

Monitors orchestrator execution logs in real-time and provides status updates.
Can be run in parallel with the orchestrator to see live progress.
"""
import os
import sys
import time
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import argparse


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: str
    message: str


@dataclass
class TaskStatus:
    """Represents the status of a task."""
    number: int
    title: str
    status: str  # pending, in_progress, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class LogMonitor:
    """Monitors orchestrator logs and displays progress."""

    def __init__(self, log_file: Optional[str] = None, follow: bool = False):
        """
        Initialize monitor.

        Args:
            log_file: Path to log file. If None, finds the latest log.
            follow: If True, continuously follow the log file (like tail -f)
        """
        self.logs_dir = Path("autonomous_agents/logs")
        self.follow = follow

        if log_file:
            self.log_file = Path(log_file)
        else:
            self.log_file = self._find_latest_log()

        if not self.log_file or not self.log_file.exists():
            raise FileNotFoundError("No log file found")

        self.tasks: List[TaskStatus] = []
        self.current_position = 0

    def _find_latest_log(self) -> Optional[Path]:
        """Find the most recent log file."""
        if not self.logs_dir.exists():
            return None

        log_files = sorted(
            self.logs_dir.glob("execution_*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return log_files[0] if log_files else None

    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line."""
        # Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] Message
        pattern = r'\[([^\]]+)\] \[([^\]]+)\] (.+)'
        match = re.match(pattern, line)

        if match:
            timestamp_str = match.group(1)
            level = match.group(2)
            message = match.group(3)

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                return LogEntry(timestamp, level, message)
            except ValueError:
                pass

        return None

    def _extract_task_info(self, message: str) -> Optional[tuple]:
        """Extract task number and title from message."""
        # Pattern: 🚀 Executing Task N: Title
        pattern = r'🚀 Executing Task (\d+): (.+)'
        match = re.match(pattern, message)

        if match:
            return int(match.group(1)), match.group(2)

        return None

    def _update_tasks(self, entry: LogEntry):
        """Update task status based on log entry."""
        # Check for task start
        task_info = self._extract_task_info(entry.message)
        if task_info:
            task_num, task_title = task_info

            # Add or update task
            existing = next((t for t in self.tasks if t.number == task_num), None)
            if existing:
                existing.status = "in_progress"
                existing.start_time = entry.timestamp
            else:
                self.tasks.append(TaskStatus(
                    number=task_num,
                    title=task_title,
                    status="in_progress",
                    start_time=entry.timestamp
                ))

        # Check for task completion
        if "completed successfully" in entry.message.lower():
            match = re.search(r'Task (\d+)', entry.message)
            if match:
                task_num = int(match.group(1))
                task = next((t for t in self.tasks if t.number == task_num), None)
                if task:
                    task.status = "completed"
                    task.end_time = entry.timestamp

        # Check for task failure
        if "failed" in entry.message.lower() and entry.level == "ERROR":
            match = re.search(r'Task (\d+)', entry.message)
            if match:
                task_num = int(match.group(1))
                task = next((t for t in self.tasks if t.number == task_num), None)
                if task:
                    task.status = "failed"
                    task.end_time = entry.timestamp

    def read_new_lines(self) -> List[LogEntry]:
        """Read new lines from the log file since last read."""
        entries = []

        with open(self.log_file, 'r') as f:
            f.seek(self.current_position)
            new_lines = f.readlines()
            self.current_position = f.tell()

            for line in new_lines:
                entry = self._parse_log_line(line.strip())
                if entry:
                    entries.append(entry)
                    self._update_tasks(entry)

        return entries

    def display_status(self):
        """Display current status of all tasks."""
        # Clear screen (optional)
        if self.follow:
            os.system('clear' if os.name != 'nt' else 'cls')

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🤖 Autonomous Agent Monitor")
        print(f"📝 Log: {self.log_file.name}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

        if not self.tasks:
            print("⏳ Waiting for tasks...")
            return

        # Display task status
        print("📊 Task Status:")
        print()

        for task in self.tasks:
            # Status icon
            if task.status == "completed":
                icon = "✅"
            elif task.status == "in_progress":
                icon = "⚙️"
            elif task.status == "failed":
                icon = "❌"
            else:
                icon = "⏳"

            # Duration
            duration = ""
            if task.start_time and task.end_time:
                delta = (task.end_time - task.start_time).total_seconds()
                duration = f" ({delta:.1f}s)"

            print(f"{icon} Task {task.number}: {task.title}")
            print(f"   Status: {task.status.upper()}{duration}")
            print()

        # Summary
        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        in_progress = sum(1 for t in self.tasks if t.status == "in_progress")
        total = len(self.tasks)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Summary: {completed}/{total} completed, {failed} failed, {in_progress} in progress")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def monitor(self):
        """Run the monitor."""
        try:
            if self.follow:
                print(f"📡 Following {self.log_file}... (Press Ctrl+C to stop)")
                print()

                while True:
                    entries = self.read_new_lines()

                    if entries:
                        self.display_status()

                    time.sleep(1)
            else:
                # Read entire log once
                entries = self.read_new_lines()
                self.display_status()

        except KeyboardInterrupt:
            print("\n\n⚠️  Monitor stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor autonomous agent execution",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-f', '--follow',
        action='store_true',
        help='Follow log file in real-time (like tail -f)'
    )

    parser.add_argument(
        '--log-file',
        help='Path to specific log file (default: latest)'
    )

    args = parser.parse_args()

    try:
        monitor = LogMonitor(log_file=args.log_file, follow=args.follow)
        monitor.monitor()

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nNo execution logs found. Run the orchestrator first:")
        print("  python3 autonomous_agents/orchestrator.py <plan.md>")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
