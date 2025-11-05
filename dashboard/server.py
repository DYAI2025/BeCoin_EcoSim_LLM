"""
CEO Discovery Dashboard - FastAPI Server

This server provides REST and WebSocket APIs for the CEO Discovery Dashboard.
It integrates with the Becoin Economy system and supports autonomous agent operations.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from dashboard import __version__
except ModuleNotFoundError:
    # When running directly, dashboard module not in path
    __version__ = "1.0.0"


# Initialize FastAPI app
app = FastAPI(
    title="CEO Discovery Dashboard",
    description="Real-time monitoring and control for autonomous AI agent firm",
    version=__version__
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - provides service information."""
    return {
        "message": "CEO Discovery Dashboard API",
        "version": __version__,
        "service": "ceo-discovery-dashboard",
        "status": "operational"
    }


@app.get("/api/status")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "operational",
        "service": "ceo-discovery-dashboard",
        "version": __version__
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
