"""
FastAPI REST API for event planning system
"""

from .routes import router
from .middleware import (
    ErrorHandlingMiddleware, ObservabilityMiddleware, MetricsMiddleware,
    RateLimitingMiddleware, AuthenticationMiddleware, AuthorizationMiddleware,
    RequestValidationMiddleware, HealthCheckMiddleware,
    RateLimitConfig, AuthConfig,
    add_cors_middleware, add_security_middleware, add_observability_middleware, add_all_middleware
)
from .schemas import (
    EventPlanRequest, EventPlanResponse, CombinationSelection,
    ErrorResponse, HealthResponse, PlanListResponse, AsyncTaskResponse,
    EventType, PlanStatus, VendorInfo, EventCombination, WorkflowStatus
)

__all__ = [
    # Routes
    "router",
    
    # Middleware
    "ErrorHandlingMiddleware",
    "ObservabilityMiddleware", 
    "MetricsMiddleware",
    "RateLimitingMiddleware",
    "AuthenticationMiddleware",
    "AuthorizationMiddleware",
    "RequestValidationMiddleware",
    "HealthCheckMiddleware",
    
    # Middleware configuration
    "RateLimitConfig",
    "AuthConfig",
    
    # Middleware setup functions
    "add_cors_middleware",
    "add_security_middleware",
    "add_observability_middleware",
    "add_all_middleware",
    
    # Schemas
    "EventPlanRequest",
    "EventPlanResponse",
    "CombinationSelection",
    "ErrorResponse",
    "HealthResponse",
    "PlanListResponse",
    "AsyncTaskResponse",
    "EventType",
    "PlanStatus",
    "VendorInfo",
    "EventCombination",
    "WorkflowStatus"
]