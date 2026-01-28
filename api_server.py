#!/usr/bin/env python3
"""
BeCoin Economy API Server v3.0
FastAPI server for the autonomous economy dashboard.
"""

import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from becoin_economy.engine_v3 import BeCoinEconomy

app = FastAPI(title="BeCoin Economy API", version="3.0")

# Global economy instance
economy = BeCoinEconomy()

@app.get("/")
async def root():
    """Serve the main dashboard."""
    dashboard_path = Path("dashboard/economy-dashboard.html")
    if dashboard_path.exists():
        return HTMLResponse(dashboard_path.read_text())
    return {"message": "Dashboard not found"}

@app.get("/api/status")
async def status():
    """System status."""
    return {
        "status": "operational",
        "service": "becoin-economy-v3",
        "version": "3.0",
        "autonomous_loop": economy.running
    }

@app.get("/api/treasury")
async def get_treasury():
    """Treasury data and transactions."""
    return economy.get_api_treasury()

@app.get("/api/agents")
async def get_agents():
    """Agent status and performance."""
    return economy.get_api_agents()

@app.get("/api/projects")
async def get_projects():
    """Project status and progress."""
    return economy.get_api_projects()

@app.get("/api/pipeline")
async def get_pipeline():
    """Sales pipeline and leads."""
    return economy.get_api_pipeline()

@app.get("/api/questions")
async def get_questions():
    """CEO questions that need answers."""
    return economy.get_api_questions()

@app.post("/api/advance")
async def advance_time(hours: int = 1):
    """Advance simulation time."""
    report = economy.advance_time(hours=hours)
    return report

@app.post("/api/accept-lead/{lead_id}")
async def accept_lead(lead_id: str):
    """Accept a lead and create project."""
    result = economy.accept_lead(lead_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/reject-lead/{lead_id}")
async def reject_lead(lead_id: str, reason: str = "Not interested"):
    """Reject a lead."""
    result = economy.reject_lead(lead_id, reason)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/start-autonomous")
async def start_autonomous():
    """Start the autonomous simulation loop."""
    if not economy.running:
        economy.running = True
        # Start background task
        asyncio.create_task(autonomous_loop())
    return {"status": "started"}

@app.post("/api/stop-autonomous")
async def stop_autonomous():
    """Stop the autonomous simulation loop."""
    economy.running = False
    return {"status": "stopped"}

async def autonomous_loop():
    """Background autonomous simulation loop."""
    while economy.running:
        try:
            economy.advance_time(hours=1)
            await asyncio.sleep(5)  # 5 seconds = 1 hour simulation
        except Exception as e:
            print(f"Autonomous loop error: {e}")
            await asyncio.sleep(1)

# Mount static files
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    print("🤖 BeCoin Economy API v3.0")
    print("Dashboard: http://localhost:8000")
    print("API: http://localhost:8000/api/status")
    print("Press Ctrl+C to stop")
    print()

    # Start autonomous loop
    economy.running = True
    asyncio.create_task(autonomous_loop())

    uvicorn.run(app, host="0.0.0.0", port=8000)