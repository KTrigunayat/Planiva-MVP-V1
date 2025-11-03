"""
Main application entry point for Event Planning Agent v2
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from event_planning_agent_v2.config.settings import get_settings
from event_planning_agent_v2.api.routes import router
from event_planning_agent_v2.api.middleware import ErrorHandlingMiddleware, LoggingMiddleware

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Event Planning Agent v2",
    description="AI-powered event planning system with multi-agent collaboration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API routes
app.include_router(router, prefix="/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

# Metrics endpoint (placeholder)
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {"metrics": "placeholder"}

def main():
    """Main entry point"""
    uvicorn.run(
        "event_planning_agent_v2.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()