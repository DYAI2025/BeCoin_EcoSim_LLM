#!/usr/bin/env python3
"""
Fly.io Post-Deployment Script

This script runs after each Fly.io deployment to initialize the BeCoin economy
dashboard data. It generates the initial JSON files needed by the dashboard.

Usage:
    python scripts/fly_post_deploy.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_dashboard_data():
    """Generate initial dashboard data files."""
    try:
        from becoin_economy import (
            BecoinEconomy,
            Agent,
            Project,
            Treasury,
            build_dashboard_payload,
        )

        # Create economy instance with initial data
        treasury = Treasury(start_capital=10000, balance=8500)

        agents = [
            Agent(
                id="agent-001",
                name="Frontend Developer",
                role="Frontend",
                status="active",
                equity_share=0.25,
            ),
            Agent(
                id="agent-002",
                name="Backend Architect",
                role="Backend",
                status="active",
                equity_share=0.25,
            ),
            Agent(
                id="agent-003",
                name="AI Engineer",
                role="AI/ML",
                status="idle",
                equity_share=0.25,
            ),
            Agent(
                id="agent-004",
                name="DevOps Automator",
                role="DevOps",
                status="active",
                equity_share=0.25,
            ),
        ]

        projects = [
            Project(
                id="proj-001",
                name="Dashboard Redesign",
                stage="active",
                cost=2000,
                value=3000,
                impact_score=85,
                team=["agent-001"],
            ),
            Project(
                id="proj-002",
                name="API Integration",
                stage="completed",
                cost=1500,
                value=2500,
                impact_score=92,
                team=["agent-002"],
            ),
            Project(
                id="proj-003",
                name="CI/CD Pipeline",
                stage="active",
                cost=1800,
                value=2700,
                impact_score=78,
                team=["agent-004"],
            ),
            Project(
                id="proj-004",
                name="LLM Integration",
                stage="pipeline",
                cost=2500,
                value=4000,
                impact_score=95,
                team=[],
            ),
        ]

        economy = BecoinEconomy(
            treasury=treasury,
            agents=agents,
            projects=projects,
            baseline_hourly_burn=120.0,
        )

        # Generate dashboard payload
        payload = build_dashboard_payload(economy)

        # Save to dashboard directory
        output_dir = project_root / "dashboard" / "becoin-economy"
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, data in payload.items():
            output_path = output_dir / filename
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        print(f"Generated {len(payload)} dashboard files in {output_dir}")
        return True

    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        return False


def main():
    """Main entry point for post-deployment script."""
    print("BeCoin Post-Deployment: Initializing dashboard data...")

    success = generate_dashboard_data()

    if success:
        print("Post-deployment complete!")
        sys.exit(0)
    else:
        print("Post-deployment completed with warnings")
        sys.exit(0)  # Don't fail deployment on data generation issues


if __name__ == "__main__":
    main()
