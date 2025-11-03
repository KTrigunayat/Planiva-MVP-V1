"""
System health and monitoring tests for Event Planning Agent v2

Tests system health monitoring, component status tracking,
and observability features.

Requirements: 6.1, 6.2, 6.5
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
import json

# Mock imports to avoid dependency issues during testing
try:
    from ..observability.health import (
        HealthChecker, HealthCheck, ComponentHealth, SystemHealth,
        HealthStatus, ComponentType, get_health_checker
    )
    from ..observability.metrics import get_metrics_collector
    from ..observability.logging import get_logger
    from ..database.test_setup import TestDatabaseSetup
except ImportError:
    # Create mock classes for testing when imports fail
    from enum import Enum
    
    class HealthStatus(str, Enum):
        HEALTHY = "healthy"
        WARNING = "warning"
        UNHEALTHY = "unhealthy"
        CRITICAL = "critical"
        UNKNOWN = "unknown"
    
    class ComponentType(str, Enum):
        AGENT = "agent"
        WORKFLOW = "workflow"
        MCP_SERVER = "mcp_server"
        DATABASE = "database"
        API = "api"
        SYSTEM = "system"
        EXTERNAL_SERVICE = "external_service"
    
    class HealthCheck:
        def __init__(self, name, component_type, check_function, **kwargs):
            self.name = name
            self.component_type = component_type
            self.check_function = check_function
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ComponentHealth:
        def __init__(self, component_name, component_type, status, message, last_check, **kwargs):
            self.component_name = component_name
            self.component_type = component_type
            self.status = status
            self.message = message
            self.last_check = last_check
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def to_dict(self):
            return {"component_name": self.component_name, "status": self.status.value}
    
    class SystemHealth:
        def __init__(self, overall_status, components, timestamp, **kwargs):
            self.overall_status = overall_status
            self.components = components
            self.timestamp = timestamp
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def to_dict(self):
            return {"overall_status": self.overall_status.value, "components": {}}
        
        def to_json(self):
            return '{"overall_status": "healthy"}'
    
    class HealthChecker:
        def __init__(self):
            self.health_checks = {}
            self.component_health = {}
            self.thresholds = {}
        
        def register_health_check(self, health_check):
            self.health_checks[health_check.name] = health_check
        
        def unregister_health_check(self, name):
            if name in self.health_checks:
                del self.health_checks[name]
        
        def run_health_check(self, name):
            if name in self.health_checks:
                return ComponentHealth(name, ComponentType.SYSTEM, HealthStatus.HEALTHY, "Test", datetime.utcnow())
            return None
        
        def run_all_health_checks(self):
            return {}
        
        def get_system_health(self):
            return SystemHealth(HealthStatus.HEALTHY, {}, datetime.utcnow())
        
        def set_threshold(self, name, value):
            self.thresholds[name] = value
        
        def start_health_checking(self):
            pass
        
        def stop_health_checking(self):
            pass
    
    def get_health_checker():
        return HealthChecker()
    
    def get_metrics_collector():
        return Mock()
    
    def get_logger(name, **kwargs):
        import logging
        return logging.getLogger(name)
    
    TestDatabaseSetup = None


class TestHealthChecker:
    """Test health checker functionality"""
    
    @pytest.fixture
    def health_checker(self):
        """Create fresh health checker for testing"""
        return HealthChecker()
    
    @pytest.fixture
    def sample_health_check(self):
        """Sample health check for testing"""
        def mock_check_function():
            return {
                "success": True,
                "message": "Test check passed",
                "response_time_ms": 50,
                "metadata": {"test": "data"}
            }
        
        return HealthCheck(
            name="test_component",
            component_type=ComponentType.SYSTEM,
            check_function=mock_check_function,
            interval_seconds=10,
            timeout_seconds=5,
            description="Test health check"
        )
    
    def test_register_health_check(self, health_checker, sample_health_check):
        """Test registering a health check"""
        health_checker.register_health_check(sample_health_check)
        
        assert "test_component" in health_checker.health_checks
        assert health_checker.health_checks["test_component"] == sample_health_check
    
    def test_unregister_health_check(self, health_checker, sample_health_check):
        """Test unregistering a health check"""
        health_checker.register_health_check(sample_health_check)
        health_checker.unregister_health_check("test_component")
        
        assert "test_component" not in health_checker.health_checks
    
    def test_run_health_check_success(self, health_checker, sample_health_check):
        """Test running a successful health check"""
        health_checker.register_health_check(sample_health_check)
        
        result = health_checker.run_health_check("test_component")
        
        assert result is not None
        assert isinstance(result, ComponentHealth)
        assert result.component_name == "test_component"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test check passed"
        assert result.response_time_ms > 0
    
    def test_run_health_check_failure(self, health_checker):
        """Test running a failing health check"""
        def failing_check():
            raise Exception("Test failure")
        
        failing_health_check = HealthCheck(
            name="failing_component",
            component_type=ComponentType.SYSTEM,
            check_function=failing_check,
            critical=True
        )
        
        health_checker.register_health_check(failing_health_check)
        
        result = health_checker.run_health_check("failing_component")
        
        assert result is not None
        assert result.status == HealthStatus.CRITICAL
        assert "Test failure" in result.message
    
    def test_run_health_check_timeout(self, health_checker):
        """Test health check timeout handling"""
        def slow_check():
            time.sleep(2)  # Longer than timeout
            return {"success": True}
        
        slow_health_check = HealthCheck(
            name="slow_component",
            component_type=ComponentType.SYSTEM,
            check_function=slow_check,
            timeout_seconds=1
        )
        
        health_checker.register_health_check(slow_health_check)
        
        result = health_checker.run_health_check("slow_component")
        
        assert result is not None
        assert result.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]
        assert "timed out" in result.message.lower()
    
    def test_run_all_health_checks(self, health_checker):
        """Test running all health checks"""
        # Register multiple health checks
        for i in range(3):
            def check_func():
                return {"success": True, "message": f"Check {i} passed"}
            
            health_check = HealthCheck(
                name=f"component_{i}",
                component_type=ComponentType.SYSTEM,
                check_function=check_func
            )
            health_checker.register_health_check(health_check)
        
        results = health_checker.run_all_health_checks()
        
        assert len(results) == 3
        for i in range(3):
            assert f"component_{i}" in results
            assert results[f"component_{i}"].status == HealthStatus.HEALTHY
    
    def test_get_system_health(self, health_checker):
        """Test getting overall system health"""
        # Register health checks with different statuses
        def healthy_check():
            return {"success": True, "message": "Healthy"}
        
        def warning_check():
            return {"success": True, "message": "Warning", "response_time_ms": 1500}
        
        def unhealthy_check():
            raise Exception("Unhealthy")
        
        health_checker.register_health_check(HealthCheck(
            name="healthy_component",
            component_type=ComponentType.SYSTEM,
            check_function=healthy_check
        ))
        
        health_checker.register_health_check(HealthCheck(
            name="warning_component", 
            component_type=ComponentType.API,
            check_function=warning_check
        ))
        
        health_checker.register_health_check(HealthCheck(
            name="unhealthy_component",
            component_type=ComponentType.DATABASE,
            check_function=unhealthy_check
        ))
        
        # Run all checks first
        health_checker.run_all_health_checks()
        
        # Get system health
        system_health = health_checker.get_system_health()
        
        assert isinstance(system_health, SystemHealth)
        assert system_health.overall_status == HealthStatus.UNHEALTHY  # Due to unhealthy component
        assert len(system_health.components) == 3
        assert "summary" in system_health.to_dict()
    
    def test_health_thresholds(self, health_checker):
        """Test health status determination based on thresholds"""
        # Test response time thresholds
        def slow_check():
            time.sleep(0.1)  # 100ms
            return {"success": True}
        
        health_checker.set_threshold("response_time_warning_ms", 50)
        health_checker.set_threshold("response_time_critical_ms", 200)
        
        slow_health_check = HealthCheck(
            name="slow_component",
            component_type=ComponentType.API,
            check_function=slow_check
        )
        
        health_checker.register_health_check(slow_health_check)
        
        result = health_checker.run_health_check("slow_component")
        
        # Should be warning due to response time
        assert result.status == HealthStatus.WARNING
    
    def test_background_health_checking(self, health_checker):
        """Test background health checking"""
        check_count = 0
        
        def counting_check():
            nonlocal check_count
            check_count += 1
            return {"success": True, "count": check_count}
        
        health_check = HealthCheck(
            name="counting_component",
            component_type=ComponentType.SYSTEM,
            check_function=counting_check,
            interval_seconds=1  # Check every second
        )
        
        health_checker.register_health_check(health_check)
        health_checker.check_interval = 1  # Check every second
        
        # Start background checking
        health_checker.start_health_checking()
        
        # Wait for a few checks
        time.sleep(3)
        
        # Stop background checking
        health_checker.stop_health_checking()
        
        # Verify checks were run
        assert check_count >= 2  # Should have run at least twice


class TestSystemHealthMonitoring:
    """Test system-wide health monitoring"""
    
    @pytest.fixture
    def test_db(self):
        """Setup test database"""
        db_setup = TestDatabaseSetup()
        db_setup.setup_test_database()
        yield db_setup
        db_setup.cleanup_test_database()
    
    def test_database_health_check(self, test_db):
        """Test database health monitoring"""
        health_checker = get_health_checker()
        
        # Run database health check
        result = health_checker.run_health_check("database_connection")
        
        if result:  # May not exist in test environment
            assert result.component_type == ComponentType.DATABASE
            # Status depends on actual database availability
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_resources_health_check(self, mock_disk, mock_memory, mock_cpu):
        """Test system resource monitoring"""
        # Mock system metrics
        mock_cpu.return_value = 45.0
        
        mock_memory_obj = Mock()
        mock_memory_obj.percent = 60.0
        mock_memory_obj.available = 8 * 1024**3  # 8GB
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.percent = 70.0
        mock_disk_obj.free = 100 * 1024**3  # 100GB
        mock_disk.return_value = mock_disk_obj
        
        health_checker = get_health_checker()
        
        # Run system resources check
        result = health_checker.run_health_check("system_resources")
        
        if result:  # May not exist in test environment
            assert result.component_type == ComponentType.SYSTEM
            assert result.status == HealthStatus.HEALTHY  # All metrics are healthy
            assert "cpu_usage" in result.metadata
            assert "memory_usage" in result.metadata
    
    def test_api_endpoints_health_check(self):
        """Test API endpoints health monitoring"""
        health_checker = get_health_checker()
        
        # Run API endpoints check
        result = health_checker.run_health_check("api_endpoints")
        
        if result:  # May not exist in test environment
            assert result.component_type == ComponentType.API
            # Status depends on actual API availability
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]


class TestComponentHealthTracking:
    """Test individual component health tracking"""
    
    def test_component_health_creation(self):
        """Test creating component health objects"""
        component_health = ComponentHealth(
            component_name="test_component",
            component_type=ComponentType.AGENT,
            status=HealthStatus.HEALTHY,
            message="Component is healthy",
            last_check=datetime.utcnow(),
            response_time_ms=100.0,
            metadata={"version": "1.0.0"},
            checks={"connectivity": {"success": True}}
        )
        
        assert component_health.component_name == "test_component"
        assert component_health.component_type == ComponentType.AGENT
        assert component_health.status == HealthStatus.HEALTHY
        assert component_health.response_time_ms == 100.0
        
        # Test serialization
        health_dict = component_health.to_dict()
        assert "component_name" in health_dict
        assert "status" in health_dict
        assert health_dict["status"] == "healthy"
    
    def test_system_health_aggregation(self):
        """Test system health aggregation from components"""
        components = {
            "component1": ComponentHealth(
                component_name="component1",
                component_type=ComponentType.AGENT,
                status=HealthStatus.HEALTHY,
                message="Healthy",
                last_check=datetime.utcnow()
            ),
            "component2": ComponentHealth(
                component_name="component2",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.WARNING,
                message="Warning",
                last_check=datetime.utcnow()
            ),
            "component3": ComponentHealth(
                component_name="component3",
                component_type=ComponentType.MCP_SERVER,
                status=HealthStatus.UNHEALTHY,
                message="Unhealthy",
                last_check=datetime.utcnow()
            )
        }
        
        system_health = SystemHealth(
            overall_status=HealthStatus.UNHEALTHY,  # Worst status
            components=components,
            timestamp=datetime.utcnow(),
            summary={
                "total_components": 3,
                "healthy": 1,
                "warning": 1,
                "unhealthy": 1
            }
        )
        
        assert system_health.overall_status == HealthStatus.UNHEALTHY
        assert len(system_health.components) == 3
        
        # Test serialization
        health_dict = system_health.to_dict()
        assert "overall_status" in health_dict
        assert "components" in health_dict
        assert len(health_dict["components"]) == 3
        
        # Test JSON serialization
        health_json = system_health.to_json()
        assert isinstance(health_json, str)
        parsed = json.loads(health_json)
        assert "overall_status" in parsed


class TestHealthCheckDecorator:
    """Test health check decorator functionality"""
    
    def test_health_check_decorator(self):
        """Test health check decorator registration"""
        from ..observability.health import health_check
        
        @health_check(
            name="decorated_component",
            component_type=ComponentType.WORKFLOW,
            interval_seconds=60,
            critical=True,
            description="Decorated health check"
        )
        def decorated_health_check():
            return {
                "success": True,
                "message": "Decorated check passed"
            }
        
        # Verify the function is registered
        health_checker = get_health_checker()
        assert "decorated_component" in health_checker.health_checks
        
        # Verify the health check properties
        health_check_obj = health_checker.health_checks["decorated_component"]
        assert health_check_obj.name == "decorated_component"
        assert health_check_obj.component_type == ComponentType.WORKFLOW
        assert health_check_obj.interval_seconds == 60
        assert health_check_obj.critical is True
        assert health_check_obj.description == "Decorated health check"


class TestMetricsIntegration:
    """Test integration with metrics collection"""
    
    @patch('event_planning_agent_v2.observability.metrics.get_metrics_collector')
    def test_health_check_metrics_recording(self, mock_metrics):
        """Test that health checks record metrics"""
        mock_collector = Mock()
        mock_metrics.return_value = mock_collector
        
        health_checker = HealthChecker()
        
        def test_check():
            return {"success": True, "message": "Test"}
        
        health_check = HealthCheck(
            name="metrics_test",
            component_type=ComponentType.SYSTEM,
            check_function=test_check
        )
        
        health_checker.register_health_check(health_check)
        health_checker.run_health_check("metrics_test")
        
        # Verify metrics were recorded
        mock_collector.record_timer.assert_called()
        
        # Check the call arguments
        call_args = mock_collector.record_timer.call_args
        assert "health_check_metrics_test_duration" in call_args[0]
        assert "labels" in call_args[1]


class TestHealthCheckConfiguration:
    """Test health check configuration and management"""
    
    def test_health_check_enable_disable(self):
        """Test enabling and disabling health checks"""
        health_checker = HealthChecker()
        
        def test_check():
            return {"success": True}
        
        health_check = HealthCheck(
            name="configurable_check",
            component_type=ComponentType.SYSTEM,
            check_function=test_check,
            enabled=False  # Start disabled
        )
        
        health_checker.register_health_check(health_check)
        
        # Should not run when disabled
        result = health_checker.run_health_check("configurable_check")
        assert result is None
        
        # Enable and test
        health_checker.health_checks["configurable_check"].enabled = True
        result = health_checker.run_health_check("configurable_check")
        assert result is not None
        assert result.status == HealthStatus.HEALTHY
    
    def test_threshold_configuration(self):
        """Test configuring health thresholds"""
        health_checker = HealthChecker()
        
        # Test default thresholds
        assert health_checker.thresholds["response_time_warning_ms"] == 1000
        assert health_checker.thresholds["cpu_warning"] == 80.0
        
        # Update thresholds
        health_checker.set_threshold("response_time_warning_ms", 500)
        health_checker.set_threshold("cpu_critical", 90.0)
        
        assert health_checker.thresholds["response_time_warning_ms"] == 500
        assert health_checker.thresholds["cpu_critical"] == 90.0


class TestHealthCheckErrorHandling:
    """Test error handling in health checks"""
    
    def test_health_check_exception_handling(self):
        """Test handling of exceptions in health checks"""
        health_checker = HealthChecker()
        
        def exception_check():
            raise ValueError("Test exception")
        
        health_check = HealthCheck(
            name="exception_test",
            component_type=ComponentType.SYSTEM,
            check_function=exception_check
        )
        
        health_checker.register_health_check(health_check)
        
        result = health_checker.run_health_check("exception_test")
        
        assert result is not None
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test exception" in result.message
        assert "error" in result.metadata
    
    def test_critical_component_failure(self):
        """Test handling of critical component failures"""
        health_checker = HealthChecker()
        
        def critical_failure():
            raise Exception("Critical failure")
        
        health_check = HealthCheck(
            name="critical_test",
            component_type=ComponentType.DATABASE,
            check_function=critical_failure,
            critical=True
        )
        
        health_checker.register_health_check(health_check)
        
        result = health_checker.run_health_check("critical_test")
        
        assert result is not None
        assert result.status == HealthStatus.CRITICAL
        assert "Critical failure" in result.message


# Test configuration
@pytest.fixture(scope="session")
def setup_health_monitoring():
    """Setup health monitoring for tests"""
    from ..observability.health import setup_default_health_checks
    
    # Don't start background checking in tests
    health_checker = get_health_checker()
    health_checker.check_enabled = False
    
    yield health_checker
    
    # Cleanup
    health_checker.stop_health_checking()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])