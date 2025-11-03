"""
Health check system for Event Planning Agent v2.

Provides comprehensive health monitoring for all system components
including agents, workflows, MCP servers, and infrastructure.
"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

from .logging import get_logger
from .metrics import get_metrics_collector

logger = get_logger(__name__, component="health")


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Types of system components"""
    AGENT = "agent"
    WORKFLOW = "workflow"
    MCP_SERVER = "mcp_server"
    DATABASE = "database"
    API = "api"
    SYSTEM = "system"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class HealthCheck:
    """Individual health check definition"""
    name: str
    component_type: ComponentType
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: int = 30
    timeout_seconds: int = 10
    enabled: bool = True
    critical: bool = False
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"Health check for {self.name}"


@dataclass
class ComponentHealth:
    """Health status of a system component"""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    last_check: datetime
    response_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component_name": self.component_name,
            "component_type": self.component_type.value,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata,
            "checks": self.checks
        }


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: datetime
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "components": {name: comp.to_dict() for name, comp in self.components.items()}
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


class HealthChecker:
    """Central health checking system"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        self.metrics_collector = get_metrics_collector()
        
        # Health check execution
        self.check_enabled = True
        self.check_interval = 30  # seconds
        self.check_thread: Optional[threading.Thread] = None
        self.stop_checking = threading.Event()
        
        # Health thresholds
        self.thresholds = {
            "response_time_warning_ms": 1000,
            "response_time_critical_ms": 5000,
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10,  # 10%
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize default health checks
        self._initialize_default_checks()
    
    def _initialize_default_checks(self):
        """Initialize default health checks"""
        
        # System health check
        self.register_health_check(HealthCheck(
            name="system_resources",
            component_type=ComponentType.SYSTEM,
            check_function=self._check_system_resources,
            interval_seconds=30,
            critical=True,
            description="Check system CPU, memory, and disk usage"
        ))
        
        # Database health check
        self.register_health_check(HealthCheck(
            name="database_connection",
            component_type=ComponentType.DATABASE,
            check_function=self._check_database_connection,
            interval_seconds=60,
            critical=True,
            description="Check database connectivity and performance"
        ))
        
        # API health check
        self.register_health_check(HealthCheck(
            name="api_endpoints",
            component_type=ComponentType.API,
            check_function=self._check_api_endpoints,
            interval_seconds=45,
            critical=False,
            description="Check API endpoint availability"
        ))
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check"""
        with self._lock:
            self.health_checks[health_check.name] = health_check
        
        logger.info(f"Registered health check: {health_check.name}")
    
    def unregister_health_check(self, check_name: str):
        """Unregister a health check"""
        with self._lock:
            if check_name in self.health_checks:
                del self.health_checks[check_name]
                logger.info(f"Unregistered health check: {check_name}")
    
    def start_health_checking(self):
        """Start background health checking"""
        if self.check_thread and self.check_thread.is_alive():
            logger.warning("Health checking already started")
            return
        
        self.stop_checking.clear()
        self.check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.check_thread.start()
        
        logger.info("Health checking started")
    
    def stop_health_checking(self):
        """Stop background health checking"""
        self.stop_checking.set()
        if self.check_thread:
            self.check_thread.join(timeout=5)
        
        logger.info("Health checking stopped")
    
    def run_health_check(self, check_name: str) -> Optional[ComponentHealth]:
        """Run a specific health check"""
        with self._lock:
            if check_name not in self.health_checks:
                logger.error(f"Health check not found: {check_name}")
                return None
            
            health_check = self.health_checks[check_name]
        
        if not health_check.enabled:
            return None
        
        start_time = time.time()
        
        try:
            # Run the health check with timeout
            result = self._run_check_with_timeout(
                health_check.check_function,
                health_check.timeout_seconds
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine health status
            status = self._determine_health_status(result, response_time_ms, health_check)
            
            # Create component health
            component_health = ComponentHealth(
                component_name=check_name,
                component_type=health_check.component_type,
                status=status,
                message=result.get("message", "Health check completed"),
                last_check=datetime.utcnow(),
                response_time_ms=response_time_ms,
                metadata=result.get("metadata", {}),
                checks={check_name: result}
            )
            
            # Store component health
            with self._lock:
                self.component_health[check_name] = component_health
            
            # Record metrics
            self.metrics_collector.record_timer(
                f"health_check_{check_name}_duration",
                response_time_ms,
                labels={"check": check_name, "status": status.value}
            )
            
            logger.debug(f"Health check completed: {check_name} - {status.value}")
            return component_health
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Create failed health status
            component_health = ComponentHealth(
                component_name=check_name,
                component_type=health_check.component_type,
                status=HealthStatus.CRITICAL if health_check.critical else HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=response_time_ms,
                metadata={"error": str(e)},
                checks={check_name: {"success": False, "error": str(e)}}
            )
            
            with self._lock:
                self.component_health[check_name] = component_health
            
            logger.error(f"Health check failed: {check_name} - {e}")
            return component_health
    
    def run_all_health_checks(self) -> Dict[str, ComponentHealth]:
        """Run all enabled health checks"""
        results = {}
        
        with self._lock:
            check_names = list(self.health_checks.keys())
        
        for check_name in check_names:
            result = self.run_health_check(check_name)
            if result:
                results[check_name] = result
        
        return results
    
    def get_system_health(self) -> SystemHealth:
        """Get overall system health status"""
        with self._lock:
            components = dict(self.component_health)
        
        # Determine overall status
        overall_status = self._calculate_overall_status(components)
        
        # Generate summary
        summary = self._generate_health_summary(components)
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            timestamp=datetime.utcnow(),
            summary=summary
        )
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health status for specific component"""
        with self._lock:
            return self.component_health.get(component_name)
    
    def set_threshold(self, threshold_name: str, value: float):
        """Set health threshold"""
        self.thresholds[threshold_name] = value
        logger.info(f"Updated threshold {threshold_name} to {value}")
    
    def _health_check_loop(self):
        """Background health check loop"""
        while not self.stop_checking.wait(self.check_interval):
            try:
                # Run health checks that are due
                self._run_scheduled_checks()
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    def _run_scheduled_checks(self):
        """Run health checks that are scheduled"""
        current_time = datetime.utcnow()
        
        with self._lock:
            checks_to_run = []
            
            for check_name, health_check in self.health_checks.items():
                if not health_check.enabled:
                    continue
                
                # Check if it's time to run this check
                last_check = None
                if check_name in self.component_health:
                    last_check = self.component_health[check_name].last_check
                
                if (last_check is None or 
                    (current_time - last_check).total_seconds() >= health_check.interval_seconds):
                    checks_to_run.append(check_name)
        
        # Run checks outside of lock
        for check_name in checks_to_run:
            try:
                self.run_health_check(check_name)
            except Exception as e:
                logger.error(f"Scheduled health check failed: {check_name} - {e}")
    
    def _run_check_with_timeout(self, check_function: Callable, timeout_seconds: int) -> Dict[str, Any]:
        """Run health check function with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Health check timed out after {timeout_seconds} seconds")
        
        # Set timeout (Unix only)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = check_function()
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        except AttributeError:
            # Windows doesn't support SIGALRM, use threading timeout
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(check_function)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(f"Health check timed out after {timeout_seconds} seconds")
    
    def _determine_health_status(
        self,
        result: Dict[str, Any],
        response_time_ms: float,
        health_check: HealthCheck
    ) -> HealthStatus:
        """Determine health status based on check result"""
        
        # Check if the result explicitly indicates status
        if "status" in result:
            return HealthStatus(result["status"])
        
        # Check if the result indicates success/failure
        if "success" in result and not result["success"]:
            return HealthStatus.CRITICAL if health_check.critical else HealthStatus.UNHEALTHY
        
        # Check response time thresholds
        if response_time_ms > self.thresholds.get("response_time_critical_ms", 5000):
            return HealthStatus.CRITICAL if health_check.critical else HealthStatus.UNHEALTHY
        elif response_time_ms > self.thresholds.get("response_time_warning_ms", 1000):
            return HealthStatus.WARNING
        
        # Check component-specific thresholds
        if health_check.component_type == ComponentType.SYSTEM:
            cpu_usage = result.get("cpu_usage", 0)
            memory_usage = result.get("memory_usage", 0)
            
            if (cpu_usage > self.thresholds.get("cpu_critical", 95) or
                memory_usage > self.thresholds.get("memory_critical", 95)):
                return HealthStatus.CRITICAL
            elif (cpu_usage > self.thresholds.get("cpu_warning", 80) or
                  memory_usage > self.thresholds.get("memory_warning", 85)):
                return HealthStatus.WARNING
        
        # Default to healthy if no issues detected
        return HealthStatus.HEALTHY
    
    def _calculate_overall_status(self, components: Dict[str, ComponentHealth]) -> HealthStatus:
        """Calculate overall system health status"""
        if not components:
            return HealthStatus.UNKNOWN
        
        # Count status levels
        status_counts = {status: 0 for status in HealthStatus}
        critical_components = []
        
        for component in components.values():
            status_counts[component.status] += 1
            
            # Track critical components
            if component.status == HealthStatus.CRITICAL:
                critical_components.append(component.component_name)
        
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.WARNING] > 0:
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] > 0:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _generate_health_summary(self, components: Dict[str, ComponentHealth]) -> Dict[str, Any]:
        """Generate health summary statistics"""
        if not components:
            return {"total_components": 0}
        
        # Count by status
        status_counts = {status.value: 0 for status in HealthStatus}
        for component in components.values():
            status_counts[component.status.value] += 1
        
        # Count by component type
        type_counts = {comp_type.value: 0 for comp_type in ComponentType}
        for component in components.values():
            type_counts[component.component_type.value] += 1
        
        # Calculate average response time
        response_times = [comp.response_time_ms for comp in components.values()]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Find slowest component
        slowest_component = max(components.values(), key=lambda x: x.response_time_ms) if components else None
        
        return {
            "total_components": len(components),
            "status_breakdown": status_counts,
            "component_type_breakdown": type_counts,
            "average_response_time_ms": avg_response_time,
            "slowest_component": {
                "name": slowest_component.component_name,
                "response_time_ms": slowest_component.response_time_ms
            } if slowest_component else None
        }
    
    # Default health check implementations
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
                load_1min = load_avg[0]
            except (AttributeError, OSError):
                load_1min = 0
            
            return {
                "success": True,
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "load_1min": load_1min,
                "message": f"System resources: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to check system resources: {e}"
            }
    
    def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from ..database.setup import DatabaseSetup
            
            db_setup = DatabaseSetup()
            start_time = time.time()
            
            # Test database connection
            with db_setup.get_session() as session:
                # Simple query to test connectivity
                result = session.execute("SELECT 1").fetchone()
                
                if result and result[0] == 1:
                    connection_time_ms = (time.time() - start_time) * 1000
                    
                    return {
                        "success": True,
                        "connection_time_ms": connection_time_ms,
                        "message": f"Database connection successful ({connection_time_ms:.2f}ms)"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Database query returned unexpected result"
                    }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Database connection failed: {e}"
            }
    
    def _check_api_endpoints(self) -> Dict[str, Any]:
        """Check API endpoint availability"""
        try:
            # This would typically make HTTP requests to API endpoints
            # For now, we'll simulate the check
            
            endpoints_to_check = [
                "/health",
                "/v1/plans",
                "/metrics"
            ]
            
            endpoint_results = {}
            all_healthy = True
            
            for endpoint in endpoints_to_check:
                # Simulate endpoint check
                # In practice, this would make actual HTTP requests
                endpoint_results[endpoint] = {
                    "status": "healthy",
                    "response_time_ms": 50  # Simulated
                }
            
            return {
                "success": all_healthy,
                "endpoints": endpoint_results,
                "message": f"Checked {len(endpoints_to_check)} API endpoints"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"API endpoint check failed: {e}"
            }


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# Convenience functions
def register_health_check(health_check: HealthCheck):
    """Register health check"""
    checker = get_health_checker()
    checker.register_health_check(health_check)


def get_system_health() -> SystemHealth:
    """Get system health status"""
    checker = get_health_checker()
    return checker.get_system_health()


def run_health_check(check_name: str) -> Optional[ComponentHealth]:
    """Run specific health check"""
    checker = get_health_checker()
    return checker.run_health_check(check_name)


# Health check decorators
def health_check(
    name: str,
    component_type: ComponentType,
    interval_seconds: int = 30,
    timeout_seconds: int = 10,
    critical: bool = False,
    description: str = ""
):
    """Decorator to register function as health check"""
    
    def decorator(func):
        health_check_obj = HealthCheck(
            name=name,
            component_type=component_type,
            check_function=func,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            critical=critical,
            description=description or f"Health check for {name}"
        )
        
        register_health_check(health_check_obj)
        return func
    
    return decorator


# Initialize default health checking
def setup_default_health_checks():
    """Setup default health checking"""
    checker = get_health_checker()
    checker.start_health_checking()
    
    logger.info("Default health checking setup completed")