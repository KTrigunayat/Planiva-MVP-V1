"""
FastAPI application setup with comprehensive middleware integration
"""

import logging
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from .routes import router
from .middleware import (
    add_all_middleware, AuthConfig, RateLimitConfig
)
from ..config.settings import get_settings
from ..database.setup import initialize_database, setup_observability

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Event Planning Agent v2 API")
    
    try:
        # Initialize database
        await initialize_database()
        logger.info("Database initialized successfully")
        
        # Setup observability
        setup_observability()
        logger.info("Observability setup completed")
        
        logger.info("Event Planning Agent v2 API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Event Planning Agent v2 API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Event Planning Agent v2 API",
        description="Modernized event planning system using CrewAI, LangGraph, and MCP servers",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Configure middleware
    auth_config = AuthConfig(
        enabled=getattr(settings, 'auth_enabled', True),
        jwt_secret=getattr(settings, 'jwt_secret', 'your-secret-key'),
        jwt_algorithm=getattr(settings, 'jwt_algorithm', 'HS256'),
        token_expiry_hours=getattr(settings, 'token_expiry_hours', 24)
    )
    
    rate_limit_config = RateLimitConfig(
        enabled=getattr(settings, 'rate_limiting_enabled', True),
        requests_per_minute=getattr(settings, 'rate_limit_per_minute', 60),
        requests_per_hour=getattr(settings, 'rate_limit_per_hour', 1000),
        burst_limit=getattr(settings, 'rate_limit_burst', 10)
    )
    
    cors_origins = getattr(settings, 'cors_origins', ["*"])
    
    # Add all middleware
    add_all_middleware(
        app=app,
        auth_config=auth_config,
        rate_limit_config=rate_limit_config,
        cors_origins=cors_origins
    )
    
    # Include routers
    app.include_router(router, prefix="/api")
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Event Planning Agent v2 API",
            version="2.0.0",
            description="""
            Modernized event planning system using CrewAI, LangGraph, and MCP servers.
            
            ## Features
            
            - **Multi-Agent Workflow**: CrewAI-powered agents for orchestration, budgeting, sourcing, timeline, and blueprint generation
            - **Advanced Orchestration**: LangGraph workflow engine with beam search optimization
            - **Enhanced Capabilities**: MCP servers for vendor data, calculations, and monitoring
            - **Comprehensive Observability**: Structured logging, distributed tracing, and metrics collection
            - **Security**: JWT authentication, role-based authorization, and rate limiting
            - **Scalability**: Asynchronous processing and horizontal scaling support
            
            ## Authentication
            
            Most endpoints require JWT authentication. Include the token in the Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            
            ## Rate Limiting
            
            API requests are rate limited to prevent abuse:
            - 60 requests per minute per client
            - 1000 requests per hour per client
            - Burst limit of 10 requests per 10 seconds
            
            Rate limit headers are included in responses:
            - `X-RateLimit-Limit`: Request limit per minute
            - `X-RateLimit-Remaining`: Remaining requests in current window
            - `Retry-After`: Seconds to wait when rate limited (429 response)
            
            ## Error Handling
            
            All errors follow a consistent format:
            ```json
            {
                "error": {
                    "type": "ErrorType",
                    "message": "Human readable error message",
                    "correlation_id": "unique-request-id"
                }
            }
            ```
            
            ## Workflow Status
            
            Event planning workflows provide real-time status updates:
            - `pending`: Workflow not yet started
            - `processing`: Workflow actively running
            - `completed`: Workflow finished successfully
            - `failed`: Workflow encountered an error
            - `cancelled`: Workflow was cancelled by user
            """,
            routes=app.routes,
        )
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        
        # Add security to all protected endpoints
        for path, path_item in openapi_schema["paths"].items():
            if path.startswith("/api/v1/"):
                for method, operation in path_item.items():
                    if method.lower() != "options":
                        operation["security"] = [{"BearerAuth": []}]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    logger.info("FastAPI application created and configured")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "event_planning_agent_v2.api.app:app",
        host=getattr(settings, 'api_host', '0.0.0.0'),
        port=getattr(settings, 'api_port', 8000),
        reload=getattr(settings, 'debug', False),
        log_level="info"
    )