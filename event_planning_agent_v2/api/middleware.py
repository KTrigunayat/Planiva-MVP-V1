"""
FastAPI middleware for Event Planning Agent v2 with comprehensive observability,
authentication, authorization, rate limiting, and CORS support
"""

import time
import uuid
import json
import hashlib
from typing import Callable, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import jwt
from pydantic import BaseModel

from ..observability.logging import get_logger, set_correlation_id, ensure_correlation_id
from ..observability.tracing import (
    get_tracer, trace_operation, SpanKind, inject_trace_context, extract_trace_context
)
from ..observability.metrics import get_metrics_collector
from ..error_handling.handlers import ErrorHandlerFactory, ErrorContext
from ..error_handling.exceptions import EventPlanningError
from ..error_handling.monitoring import get_error_monitor
from ..config.settings import get_settings

logger = get_logger(__name__, component="api_middleware")
security = HTTPBearer(auto_error=False)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Comprehensive observability middleware with tracing, logging, and metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.tracer = get_tracer()
        self.metrics_collector = get_metrics_collector()
        self.error_monitor = get_error_monitor()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-Id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation context
        set_correlation_id(correlation_id)
        
        # Extract trace context from headers
        trace_context = extract_trace_context(dict(request.headers))
        if trace_context:
            self.tracer.set_trace_context(trace_context)
        
        # Start request span
        operation_name = f"{request.method} {request.url.path}"
        
        with trace_operation(
            operation_name,
            kind=SpanKind.SERVER,
            component="api",
            tags={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.path": request.url.path,
                "http.user_agent": request.headers.get("user-agent", ""),
                "correlation_id": correlation_id
            }
        ) as span:
            
            start_time = time.time()
            
            try:
                # Log request start
                logger.info(
                    f"Request started: {request.method} {request.url.path}",
                    operation="request_start",
                    metadata={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params),
                        "user_agent": request.headers.get("user-agent", ""),
                        "client_ip": request.client.host if request.client else None
                    }
                )
                
                # Process request
                response = await call_next(request)
                
                # Calculate response time
                response_time_ms = (time.time() - start_time) * 1000
                
                # Add observability headers
                response.headers["X-Correlation-Id"] = correlation_id
                response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
                
                # Inject trace context into response headers
                inject_trace_context(dict(response.headers))
                
                # Set span tags
                span.set_tag("http.status_code", response.status_code)
                span.set_tag("response_time_ms", response_time_ms)
                
                # Record metrics
                self.metrics_collector.record_timer(
                    "api_request_duration",
                    response_time_ms,
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": str(response.status_code)
                    }
                )
                
                self.metrics_collector.record_counter(
                    "api_requests_total",
                    1.0,
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": str(response.status_code)
                    }
                )
                
                # Log request completion
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                    operation="request_complete",
                    performance={
                        "duration_ms": response_time_ms,
                        "success": response.status_code < 400
                    },
                    metadata={
                        "status_code": response.status_code,
                        "response_size": response.headers.get("content-length", "unknown")
                    }
                )
                
                return response
                
            except Exception as exc:
                response_time_ms = (time.time() - start_time) * 1000
                
                # Set error span tags
                span.set_error(exc)
                
                # Record error metrics
                self.metrics_collector.record_counter(
                    "api_errors_total",
                    1.0,
                    labels={
                        "method": request.method,
                        "path": request.url.path,
                        "error_type": type(exc).__name__
                    }
                )
                
                # Record error in monitoring system
                self.error_monitor.record_error(
                    error=exc,
                    component="api",
                    operation=operation_name,
                    correlation_id=correlation_id,
                    metadata={
                        "method": request.method,
                        "path": request.url.path,
                        "response_time_ms": response_time_ms
                    }
                )
                
                # Log error
                logger.error(
                    f"Request failed: {request.method} {request.url.path}",
                    operation="request_error",
                    exception=exc,
                    metadata={
                        "method": request.method,
                        "path": request.url.path,
                        "response_time_ms": response_time_ms
                    }
                )
                
                # Re-raise to be handled by error middleware
                raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware with recovery strategies"""
    
    def __init__(self, app):
        super().__init__(app)
        self.error_handler = ErrorHandlerFactory.create_default_chain()
        self.error_monitor = get_error_monitor()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Create error context
            correlation_id = getattr(request.state, 'correlation_id', None) or ensure_correlation_id()
            
            error_context = ErrorContext(
                error=exc,
                component="api",
                operation=f"{request.method} {request.url.path}",
                correlation_id=correlation_id,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers)
                }
            )
            
            # Process error through handler chain
            action = self.error_handler.process_error(error_context)
            
            # Determine response based on error type and action
            if isinstance(exc, EventPlanningError):
                status_code = self._get_status_code_for_error(exc)
                error_response = {
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": exc.message,
                        "code": exc.error_code,
                        "correlation_id": correlation_id
                    }
                }
                
                # Add retry information if available
                if exc.retry_after:
                    error_response["error"]["retry_after"] = exc.retry_after
                
            else:
                # Generic error
                status_code = 500
                error_response = {
                    "error": {
                        "type": "InternalServerError",
                        "message": "An internal server error occurred",
                        "correlation_id": correlation_id
                    }
                }
            
            # Create error response
            response = Response(
                content=json.dumps(error_response),
                status_code=status_code,
                media_type="application/json"
            )
            
            # Add observability headers
            response.headers["X-Correlation-Id"] = correlation_id
            
            return response
    
    def _get_status_code_for_error(self, error: EventPlanningError) -> int:
        """Map error types to HTTP status codes"""
        from ..error_handling.exceptions import (
            ValidationError, AuthenticationError, AuthorizationError,
            ResourceError, ExternalServiceError
        )
        
        if isinstance(error, ValidationError):
            return 400
        elif isinstance(error, AuthenticationError):
            return 401
        elif isinstance(error, AuthorizationError):
            return 403
        elif isinstance(error, ResourceError):
            return 503
        elif isinstance(error, ExternalServiceError):
            return 502
        else:
            return 500


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record request start
        self.metrics_collector.record_counter(
            "api_requests_in_progress",
            1.0,
            labels={"method": request.method, "path": request.url.path}
        )
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Record request end
            self.metrics_collector.record_counter(
                "api_requests_in_progress",
                -1.0,
                labels={"method": request.method, "path": request.url.path}
            )


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check endpoints"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle health check endpoints directly
        if request.url.path in ["/health", "/healthz", "/health/live", "/health/ready"]:
            from ..observability.health import get_health_checker
            
            health_checker = get_health_checker()
            
            if request.url.path in ["/health", "/healthz"]:
                # Full health check
                system_health = health_checker.get_system_health()
                
                status_code = 200 if system_health.overall_status.value in ["healthy", "warning"] else 503
                
                return Response(
                    content=system_health.to_json(),
                    status_code=status_code,
                    media_type="application/json"
                )
            
            elif request.url.path == "/health/live":
                # Liveness check - just return OK if service is running
                return Response(
                    content='{"status": "alive"}',
                    status_code=200,
                    media_type="application/json"
                )
            
            elif request.url.path == "/health/ready":
                # Readiness check - check if service is ready to handle requests
                system_health = health_checker.get_system_health()
                
                ready = system_health.overall_status.value != "critical"
                status_code = 200 if ready else 503
                
                return Response(
                    content=json.dumps({
                        "status": "ready" if ready else "not_ready",
                        "overall_status": system_health.overall_status.value
                    }),
                    status_code=status_code,
                    media_type="application/json"
                )
        
        # Continue with normal request processing
        return await call_next(request)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    enabled: bool = True


class AuthConfig(BaseModel):
    """Authentication configuration"""
    enabled: bool = True
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    token_expiry_hours: int = 24
    require_auth_paths: Set[str] = {"/v1/plans"}
    public_paths: Set[str] = {"/", "/health", "/healthz", "/health/live", "/health/ready", "/docs", "/openapi.json"}


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window algorithm"""
    
    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.request_times: Dict[str, list] = defaultdict(list)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.config.enabled:
            return await call_next(request)
        
        # Get client identifier (IP address or authenticated user)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if self._is_rate_limited(client_id, request):
            # Record rate limit hit
            self.metrics_collector.record_counter(
                "api_rate_limit_hits",
                1.0,
                labels={
                    "client_id": client_id,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            logger.warning(
                f"Rate limit exceeded for client {client_id}",
                operation="rate_limit_exceeded",
                metadata={
                    "client_id": client_id,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            return Response(
                content=json.dumps({
                    "error": {
                        "type": "RateLimitExceeded",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": 60
                    }
                }),
                status_code=429,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                },
                media_type="application/json"
            )
        
        # Record request
        self._record_request(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get authenticated user ID first
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                token = auth_header.replace("Bearer ", "")
                settings = get_settings()
                payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
                return f"user:{payload.get('sub', 'unknown')}"
            except:
                pass
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _is_rate_limited(self, client_id: str, request: Request) -> bool:
        """Check if client is rate limited"""
        now = datetime.utcnow()
        
        # Clean old entries
        self._cleanup_old_entries(client_id, now)
        
        # Check minute limit
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        minute_count = self.request_counts[client_id][minute_key]
        
        if minute_count >= self.config.requests_per_minute:
            return True
        
        # Check hour limit
        hour_key = now.strftime("%Y-%m-%d-%H")
        hour_count = sum(
            count for key, count in self.request_counts[client_id].items()
            if key.startswith(hour_key)
        )
        
        if hour_count >= self.config.requests_per_hour:
            return True
        
        # Check burst limit
        recent_requests = [
            t for t in self.request_times[client_id]
            if (now - t).total_seconds() < 10  # Last 10 seconds
        ]
        
        if len(recent_requests) >= self.config.burst_limit:
            return True
        
        return False
    
    def _record_request(self, client_id: str):
        """Record a request for rate limiting"""
        now = datetime.utcnow()
        
        # Record in minute bucket
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        self.request_counts[client_id][minute_key] += 1
        
        # Record timestamp for burst detection
        self.request_times[client_id].append(now)
        
        # Keep only recent timestamps
        cutoff = now - timedelta(seconds=10)
        self.request_times[client_id] = [
            t for t in self.request_times[client_id] if t > cutoff
        ]
    
    def _cleanup_old_entries(self, client_id: str, now: datetime):
        """Clean up old rate limiting entries"""
        # Remove entries older than 1 hour
        cutoff = now - timedelta(hours=1)
        cutoff_key = cutoff.strftime("%Y-%m-%d-%H-%M")
        
        keys_to_remove = [
            key for key in self.request_counts[client_id].keys()
            if key < cutoff_key
        ]
        
        for key in keys_to_remove:
            del self.request_counts[client_id][key]
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = datetime.utcnow()
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        used = self.request_counts[client_id][minute_key]
        return max(0, self.config.requests_per_minute - used)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT-based authentication middleware"""
    
    def __init__(self, app, config: Optional[AuthConfig] = None):
        super().__init__(app)
        self.config = config or AuthConfig()
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.config.enabled:
            return await call_next(request)
        
        # Check if path requires authentication
        if not self._requires_auth(request.url.path):
            return await call_next(request)
        
        # Extract and validate token
        auth_result = self._authenticate_request(request)
        
        if not auth_result["valid"]:
            self.metrics_collector.record_counter(
                "api_auth_failures",
                1.0,
                labels={
                    "reason": auth_result["reason"],
                    "path": request.url.path
                }
            )
            
            logger.warning(
                f"Authentication failed: {auth_result['reason']}",
                operation="auth_failure",
                metadata={
                    "path": request.url.path,
                    "reason": auth_result["reason"]
                }
            )
            
            return Response(
                content=json.dumps({
                    "error": {
                        "type": "AuthenticationError",
                        "message": auth_result["message"]
                    }
                }),
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Add user info to request state
        request.state.user = auth_result["user"]
        
        # Record successful authentication
        self.metrics_collector.record_counter(
            "api_auth_success",
            1.0,
            labels={"path": request.url.path}
        )
        
        return await call_next(request)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if path requires authentication"""
        # Check public paths first
        if path in self.config.public_paths:
            return False
        
        # Check if path starts with any public path
        for public_path in self.config.public_paths:
            if path.startswith(public_path):
                return False
        
        # Check if path requires auth
        for auth_path in self.config.require_auth_paths:
            if path.startswith(auth_path):
                return True
        
        # Default to requiring auth for API paths
        return path.startswith("/v1/") or path.startswith("/api/")
    
    def _authenticate_request(self, request: Request) -> Dict[str, any]:
        """Authenticate request and return result"""
        try:
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return {
                    "valid": False,
                    "reason": "missing_token",
                    "message": "Authorization header is required"
                }
            
            # Extract token
            if not auth_header.startswith("Bearer "):
                return {
                    "valid": False,
                    "reason": "invalid_format",
                    "message": "Authorization header must be in format 'Bearer <token>'"
                }
            
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Validate token
            settings = get_settings()
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret,
                    algorithms=[settings.jwt_algorithm]
                )
            except jwt.ExpiredSignatureError:
                return {
                    "valid": False,
                    "reason": "token_expired",
                    "message": "Token has expired"
                }
            except jwt.InvalidTokenError:
                return {
                    "valid": False,
                    "reason": "invalid_token",
                    "message": "Invalid token"
                }
            
            # Extract user info
            user_info = {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", [])
            }
            
            return {
                "valid": True,
                "user": user_info,
                "token_payload": payload
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                "valid": False,
                "reason": "auth_error",
                "message": "Authentication failed"
            }


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """Role-based authorization middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
        
        # Define path permissions
        self.path_permissions = {
            "/v1/plans": ["read:plans", "write:plans"],
            "/v1/plans/{plan_id}": ["read:plans"],
            "/v1/plans/{plan_id}/select-combination": ["write:plans"],
            "/v1/plans/{plan_id}/resume": ["write:plans"],
        }
        
        # Define role permissions
        self.role_permissions = {
            "admin": ["read:plans", "write:plans", "delete:plans", "admin:system"],
            "planner": ["read:plans", "write:plans"],
            "client": ["read:plans"],
            "viewer": ["read:plans"]
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authorization if no user (authentication middleware handles this)
        if not hasattr(request.state, "user"):
            return await call_next(request)
        
        user = request.state.user
        
        # Check if user has required permissions
        if not self._is_authorized(request, user):
            self.metrics_collector.record_counter(
                "api_authz_failures",
                1.0,
                labels={
                    "user_id": user.get("user_id", "unknown"),
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            logger.warning(
                f"Authorization failed for user {user.get('user_id')}",
                operation="authz_failure",
                metadata={
                    "user_id": user.get("user_id"),
                    "path": request.url.path,
                    "method": request.method,
                    "user_roles": user.get("roles", [])
                }
            )
            
            return Response(
                content=json.dumps({
                    "error": {
                        "type": "AuthorizationError",
                        "message": "Insufficient permissions to access this resource"
                    }
                }),
                status_code=403,
                media_type="application/json"
            )
        
        return await call_next(request)
    
    def _is_authorized(self, request: Request, user: Dict[str, any]) -> bool:
        """Check if user is authorized for the request"""
        # Get required permissions for path
        required_permissions = self._get_required_permissions(request.url.path, request.method)
        
        if not required_permissions:
            return True  # No specific permissions required
        
        # Get user permissions from roles
        user_permissions = set()
        for role in user.get("roles", []):
            user_permissions.update(self.role_permissions.get(role, []))
        
        # Add explicit permissions
        user_permissions.update(user.get("permissions", []))
        
        # Check if user has all required permissions
        return all(perm in user_permissions for perm in required_permissions)
    
    def _get_required_permissions(self, path: str, method: str) -> Set[str]:
        """Get required permissions for path and method"""
        # Simple path matching - in production, use more sophisticated routing
        if path.startswith("/v1/plans"):
            if method in ["GET"]:
                return {"read:plans"}
            elif method in ["POST", "PUT", "PATCH"]:
                return {"write:plans"}
            elif method in ["DELETE"]:
                return {"delete:plans"}
        
        return set()


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation middleware using Pydantic models"""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics_collector = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = 10 * 1024 * 1024  # 10MB
                if size > max_size:
                    return Response(
                        content=json.dumps({
                            "error": {
                                "type": "RequestTooLarge",
                                "message": f"Request body too large. Maximum size is {max_size} bytes."
                            }
                        }),
                        status_code=413,
                        media_type="application/json"
                    )
            except ValueError:
                pass
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return Response(
                    content=json.dumps({
                        "error": {
                            "type": "UnsupportedMediaType",
                            "message": "Content-Type must be application/json"
                        }
                    }),
                    status_code=415,
                    media_type="application/json"
                )
        
        return await call_next(request)


# Convenience functions to add middleware
def add_cors_middleware(app, allowed_origins: list = None):
    """Add CORS middleware to FastAPI app"""
    if allowed_origins is None:
        allowed_origins = ["*"]  # In production, specify exact origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-Id", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )
    
    logger.info(f"Added CORS middleware with origins: {allowed_origins}")


def add_security_middleware(app, auth_config: Optional[AuthConfig] = None, rate_limit_config: Optional[RateLimitConfig] = None):
    """Add security middleware to FastAPI app"""
    
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(AuthorizationMiddleware)
    app.add_middleware(AuthenticationMiddleware, auth_config)
    app.add_middleware(RateLimitingMiddleware, rate_limit_config)
    
    logger.info("Added security middleware to FastAPI app")


def add_observability_middleware(app):
    """Add all observability middleware to FastAPI app"""
    
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(HealthCheckMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ObservabilityMiddleware)
    
    logger.info("Added observability middleware to FastAPI app")


def add_all_middleware(
    app,
    auth_config: Optional[AuthConfig] = None,
    rate_limit_config: Optional[RateLimitConfig] = None,
    cors_origins: Optional[list] = None
):
    """Add all middleware to FastAPI app in correct order"""
    
    # Add CORS first (outermost)
    add_cors_middleware(app, cors_origins)
    
    # Add observability middleware
    add_observability_middleware(app)
    
    # Add security middleware (innermost)
    add_security_middleware(app, auth_config, rate_limit_config)
    
    logger.info("Added all middleware to FastAPI app")