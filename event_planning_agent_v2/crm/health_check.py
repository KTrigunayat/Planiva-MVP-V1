"""
Health check functionality for CRM Communication Engine.

Provides health check endpoints and monitoring for load balancers
and orchestration systems.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRMHealthStatus:
    """Overall CRM health status."""
    status: HealthStatus
    version: str
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    uptime_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "components": {
                name: {
                    "status": comp.status.value,
                    "message": comp.message,
                    "last_check": comp.last_check.isoformat(),
                    "metadata": comp.metadata
                }
                for name, comp in self.components.items()
            }
        }


class CRMHealthChecker:
    """
    Health checker for CRM Communication Engine.
    
    Monitors the health of all CRM components and provides
    status information for load balancers and monitoring systems.
    """
    
    def __init__(
        self,
        version: str = "2.0.0",
        email_agent=None,
        messaging_agent=None,
        repository=None,
        cache_manager=None
    ):
        """
        Initialize health checker.
        
        Args:
            version: CRM engine version
            email_agent: Email sub-agent instance
            messaging_agent: Messaging sub-agent instance
            repository: Communication repository instance
            cache_manager: Cache manager instance
        """
        self.version = version
        self.email_agent = email_agent
        self.messaging_agent = messaging_agent
        self.repository = repository
        self.cache_manager = cache_manager
        self.start_time = datetime.now(timezone.utc)
        
        logger.info("CRM Health Checker initialized")
    
    async def check_health(
        self,
        include_details: bool = True
    ) -> CRMHealthStatus:
        """
        Perform comprehensive health check.
        
        Args:
            include_details: Include detailed component checks
            
        Returns:
            CRMHealthStatus with overall and component health
        """
        components = {}
        
        if include_details:
            # Check email sub-agent
            components["email_agent"] = await self._check_email_agent()
            
            # Check messaging sub-agent
            components["messaging_agent"] = await self._check_messaging_agent()
            
            # Check database repository
            components["database"] = await self._check_database()
            
            # Check cache
            components["cache"] = await self._check_cache()
        
        # Determine overall status
        overall_status = self._determine_overall_status(components)
        
        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return CRMHealthStatus(
            status=overall_status,
            version=self.version,
            timestamp=datetime.now(timezone.utc),
            components=components,
            uptime_seconds=uptime
        )
    
    async def _check_email_agent(self) -> ComponentHealth:
        """Check email sub-agent health."""
        try:
            if self.email_agent is None:
                return ComponentHealth(
                    name="email_agent",
                    status=HealthStatus.DEGRADED,
                    message="Email agent not initialized"
                )
            
            # Check SMTP connectivity
            if hasattr(self.email_agent, 'check_smtp_connection'):
                smtp_ok = await self.email_agent.check_smtp_connection()
                if not smtp_ok:
                    return ComponentHealth(
                        name="email_agent",
                        status=HealthStatus.DEGRADED,
                        message="SMTP connection failed"
                    )
            
            return ComponentHealth(
                name="email_agent",
                status=HealthStatus.HEALTHY,
                message="Email agent operational"
            )
            
        except Exception as e:
            logger.error(f"Email agent health check failed: {e}")
            return ComponentHealth(
                name="email_agent",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}"
            )
    
    async def _check_messaging_agent(self) -> ComponentHealth:
        """Check messaging sub-agent health."""
        try:
            if self.messaging_agent is None:
                return ComponentHealth(
                    name="messaging_agent",
                    status=HealthStatus.DEGRADED,
                    message="Messaging agent not initialized"
                )
            
            # Check API connectivity
            if hasattr(self.messaging_agent, 'check_api_connectivity'):
                api_ok = await self.messaging_agent.check_api_connectivity()
                if not api_ok:
                    return ComponentHealth(
                        name="messaging_agent",
                        status=HealthStatus.DEGRADED,
                        message="API connectivity issues"
                    )
            
            return ComponentHealth(
                name="messaging_agent",
                status=HealthStatus.HEALTHY,
                message="Messaging agent operational"
            )
            
        except Exception as e:
            logger.error(f"Messaging agent health check failed: {e}")
            return ComponentHealth(
                name="messaging_agent",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}"
            )
    
    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity and health."""
        try:
            if self.repository is None:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Repository not initialized"
                )
            
            # Perform simple query to check connectivity
            if hasattr(self.repository, 'health_check'):
                db_ok = await self.repository.health_check()
                if not db_ok:
                    return ComponentHealth(
                        name="database",
                        status=HealthStatus.UNHEALTHY,
                        message="Database connectivity failed"
                    )
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database operational"
            )
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}"
            )
    
    async def _check_cache(self) -> ComponentHealth:
        """Check cache connectivity and health."""
        try:
            if self.cache_manager is None:
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    message="Cache manager not initialized"
                )
            
            # Check Redis connectivity
            if hasattr(self.cache_manager, 'health_check'):
                cache_ok = await self.cache_manager.health_check()
                if not cache_ok:
                    return ComponentHealth(
                        name="cache",
                        status=HealthStatus.DEGRADED,
                        message="Cache connectivity issues"
                    )
            
            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="Cache operational"
            )
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,
                message=f"Health check error: {str(e)}"
            )
    
    def _determine_overall_status(
        self,
        components: Dict[str, ComponentHealth]
    ) -> HealthStatus:
        """
        Determine overall health status from component statuses.
        
        Args:
            components: Dictionary of component health statuses
            
        Returns:
            Overall health status
        """
        if not components:
            return HealthStatus.HEALTHY
        
        # If any component is unhealthy, overall is unhealthy
        if any(comp.status == HealthStatus.UNHEALTHY for comp in components.values()):
            return HealthStatus.UNHEALTHY
        
        # If any component is degraded, overall is degraded
        if any(comp.status == HealthStatus.DEGRADED for comp in components.values()):
            return HealthStatus.DEGRADED
        
        # All components healthy
        return HealthStatus.HEALTHY
    
    def get_readiness(self) -> bool:
        """
        Check if CRM is ready to accept requests.
        
        Returns:
            True if ready, False otherwise
        """
        # Simple readiness check - can be enhanced
        return (
            self.email_agent is not None or
            self.messaging_agent is not None
        )
    
    def get_liveness(self) -> bool:
        """
        Check if CRM process is alive.
        
        Returns:
            True if alive, False otherwise
        """
        # Simple liveness check - always returns True if process is running
        return True


# Global health checker instance
_health_checker: Optional[CRMHealthChecker] = None


def initialize_health_checker(
    version: str = "2.0.0",
    email_agent=None,
    messaging_agent=None,
    repository=None,
    cache_manager=None
) -> CRMHealthChecker:
    """
    Initialize global health checker.
    
    Args:
        version: CRM engine version
        email_agent: Email sub-agent instance
        messaging_agent: Messaging sub-agent instance
        repository: Communication repository instance
        cache_manager: Cache manager instance
        
    Returns:
        CRMHealthChecker instance
    """
    global _health_checker
    _health_checker = CRMHealthChecker(
        version=version,
        email_agent=email_agent,
        messaging_agent=messaging_agent,
        repository=repository,
        cache_manager=cache_manager
    )
    return _health_checker


def get_health_checker() -> Optional[CRMHealthChecker]:
    """
    Get global health checker instance.
    
    Returns:
        CRMHealthChecker instance or None if not initialized
    """
    return _health_checker
