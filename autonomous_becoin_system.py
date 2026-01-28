#!/usr/bin/env python3
"""
BeCoin Autonomous Agent System
MOLT → Agent Zero → Claude of Claude → BeCoin

This system coordinates multiple AI agents to autonomously run and improve
the BeCoin economy simulation.
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
BECoin_DIR = Path("/home/dyai/clawd/BeCoin_EcoSim_LLM")
WORKSPACE_DIR = Path("/home/dyai/clawd")
LOG_DIR = BECoin_DIR / "autonomous_agents" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class AutonomousBeCoinSystem:
    """Autonomous BeCoin operation system"""
    
    def __init__(self):
        self.status = "initializing"
        self.economy_running = False
        self.agents_active = False
        self.last_update = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Save to log file
        log_file = LOG_DIR / "autonomous_system.log"
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_economy(self) -> bool:
        """Check if economy simulation is running"""
        treasury_file = BECoin_DIR / "dashboard" / "becoin-economy" / "treasury.json"
        if treasury_file.exists():
            mtime = treasury_file.stat().st_mtime
            age_seconds = datetime.now().timestamp() - mtime
            return age_seconds < 30  # Less than 30 seconds old
        return False
    
    def get_economy_status(self) -> dict:
        """Get current economy status"""
        treasury_file = BECoin_DIR / "dashboard" / "becoin-economy" / "treasury.json"
        if treasury_file.exists():
            with open(treasury_file) as f:
                return json.load(f)
        return {"balance": 0, "error": "No data"}
    
    def start_economy(self) -> bool:
        """Start the economy simulation"""
        self.log("Starting BeCoin economy simulation...")
        
        # Check if already running
        if self.check_economy():
            self.log("Economy already running")
            return True
        
        # Start the autonomous startup script
        try:
            # Run in background
            subprocess.Popen(
                ["./autonomous_startup.sh"],
                cwd=str(BECoin_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for startup
            import time
            for i in range(10):
                time.sleep(2)
                if self.check_economy():
                    self.log("Economy simulation started successfully")
                    return True
            
            self.log("Warning: Economy may not have started properly", "WARN")
            return self.check_economy()
            
        except Exception as e:
            self.log(f"Failed to start economy: {e}", "ERROR")
            return False
    
    def run_agent_task(self, task_description: str) -> dict:
        """Run a single agent task via the orchestrator"""
        self.log(f"Running agent task: {task_description}")
        
        # Create a simple task result (in real implementation, this would use the orchestrator)
        result = {
            "task": task_description,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "output": f"Agent completed: {task_description}"
        }
        
        return result
    
    def get_status(self) -> dict:
        """Get complete system status"""
        return {
            "status": self.status,
            "timestamp": datetime.now().isoformat(),
            "ollama_running": self.check_ollama(),
            "economy_running": self.check_economy(),
            "economy": self.get_economy_status(),
            "last_update": self.last_update
        }
    
    async def autonomous_loop(self):
        """Main autonomous operation loop"""
        self.log("Starting autonomous operation loop")
        self.status = "running"
        
        while True:
            try:
                # Check Ollama
                if not self.check_ollama():
                    self.log("Ollama not running, attempting restart...", "WARN")
                    subprocess.run(["docker", "start", "ollama"], capture_output=True)
                    await asyncio.sleep(5)
                
                # Check economy
                if not self.check_economy():
                    self.log("Economy not running, starting...", "WARN")
                    self.start_economy()
                
                # Get status
                status = self.get_status()
                self.last_update = datetime.now().isoformat()
                
                # Log status periodically
                if status["economy"].get("balance", 0) > 0:
                    balance = status["economy"]["balance"]
                    self.log(f"Economy Status: Balance=${balance:.0f}")
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.log(f"Error in autonomous loop: {e}", "ERROR")
                await asyncio.sleep(10)
    
    def generate_report(self) -> str:
        """Generate a system report"""
        status = self.get_status()
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║          BeCoin Autonomous System Report                   ║
╠════════════════════════════════════════════════════════════╣
║ Status: {status['status']:<47}║
║ Last Update: {status['last_update'] or 'N/A':<41}║
╠════════════════════════════════════════════════════════════╣
║ Components:                                                ║
║   Ollama:       {'✓ Running' if status['ollama_running'] else '✗ Stopped':<41}║
║   Economy:      {'✓ Running' if status['economy_running'] else '✗ Stopped':<41}║
╠════════════════════════════════════════════════════════════╣
║ Economy:                                                    ║
║   Balance: ${status['economy'].get('balance', 0):,.0f}{' ' * (41 - len(f"${status['economy'].get('balance', 0):,.0f}"))}║
║   Runway: {status['economy'].get('metrics', {}).get('runwayHours', 0):.0f} hours{' ' * (43 - len(f"{status['economy'].get('metrics', {}).get('runwayHours', 0):.0f}"))}║
╚════════════════════════════════════════════════════════════╝
"""
        return report


async def main():
    """Main entry point"""
    system = AutonomousBeCoinSystem()
    
    print("\n" + "="*60)
    print("🚀 BeCoin Autonomous Agent System")
    print("="*60 + "\n")
    
    # Start economy if not running
    if not system.check_economy():
        system.start_economy()
    
    # Show initial status
    print(system.generate_report())
    
    # Start autonomous loop
    print("\n🔄 Starting autonomous operation loop...")
    print("   Press Ctrl+C to stop\n")
    
    await system.autonomous_loop()


if __name__ == "__main__":
    asyncio.run(main())
