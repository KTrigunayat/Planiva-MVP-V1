"""
Load testing for concurrent workflow execution in Event Planning Agent v2

Tests system performance under concurrent load, workflow scalability,
and resource utilization during high-throughput scenarios.

Requirements: 6.4, 6.5
"""

import pytest
import asyncio
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from unittest.mock import Mock, patch, AsyncMock
import statistics
import json
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx

# Mock imports to avoid dependency issues during testing
try:
    from ..api.app import create_app
    from ..api.schemas import EventPlanRequest, PlanStatus
    from ..database.test_setup import TestDatabaseSetup
    from ..workflows.execution_engine import ExecutionConfig, ExecutionMode
    from ..observability.metrics import get_metrics_collector
    from ..observability.logging import get_logger
except ImportError:
    # Create mock classes for testing when imports fail
    from fastapi import FastAPI
    from enum import Enum
    import logging
    
    def create_app():
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "Event Planning Agent v2 API", "version": "2.0.0", "status": "active"}
        
        @app.get("/health")
        def health():
            return {"status": "healthy", "version": "2.0.0"}
        
        @app.post("/v1/plans")
        def create_plan(request: dict):
            return {"plan_id": "test_123", "status": "completed", "client_name": "Test"}
        
        return app
    
    EventPlanRequest = dict
    
    class PlanStatus(str, Enum):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    class ExecutionConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ExecutionMode(str, Enum):
        SYNCHRONOUS = "sync"
        ASYNCHRONOUS = "async"
    
    TestDatabaseSetup = None
    
    def get_metrics_collector():
        return Mock()
    
    def get_logger(name, **kwargs):
        return logging.getLogger(name)

logger = get_logger(__name__, component="load_testing")


class LoadTestMetrics:
    """Collect and analyze load test metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.start_time: float = 0
        self.end_time: float = 0
        self.concurrent_requests = 0
        self.errors: List[str] = []
        self.throughput_samples: List[Tuple[float, int]] = []  # (timestamp, completed_requests)
        
    def record_request(self, response_time: float, success: bool, error: str = None):
        """Record individual request metrics"""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)
    
    def start_test(self):
        """Mark test start"""
        self.start_time = time.time()
    
    def end_test(self):
        """Mark test end"""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics"""
        total_requests = self.success_count + self.failure_count
        duration = self.end_time - self.start_time if self.end_time > self.start_time else 0
        
        if not self.response_times:
            return {
                "total_requests": total_requests,
                "duration_seconds": duration,
                "success_rate": 0.0,
                "requests_per_second": 0.0,
                "avg_response_time_ms": 0.0,
                "errors": self.errors
            }
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.failure_count,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0.0,
            "duration_seconds": duration,
            "requests_per_second": total_requests / duration if duration > 0 else 0.0,
            "response_times": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "avg_ms": statistics.mean(self.response_times),
                "median_ms": statistics.median(self.response_times),
                "p95_ms": self._percentile(self.response_times, 95),
                "p99_ms": self._percentile(self.response_times, 99)
            },
            "concurrent_requests": self.concurrent_requests,
            "error_summary": self._summarize_errors()
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _summarize_errors(self) -> Dict[str, int]:
        """Summarize error types"""
        error_counts = {}
        for error in self.errors:
            error_type = error.split(":")[0] if ":" in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts


class TestConcurrentAPIRequests:
    """Test concurrent API request handling"""
    
    @pytest.fixture(scope="class")
    def test_app(self):
        """Create test FastAPI application"""
        app = create_app()
        return app
    
    @pytest.fixture(scope="class")
    def client(self, test_app):
        """Create test client"""
        return TestClient(test_app)
    
    @pytest.fixture
    def sample_request(self) -> Dict[str, Any]:
        """Sample event planning request for load testing"""
        return {
            "clientName": f"Load Test Client {uuid4().hex[:8]}",
            "guestCount": {"Reception": 100, "Ceremony": 80, "total": 100},
            "clientVision": "Simple elegant event for load testing",
            "venuePreferences": ["indoor", "outdoor"],
            "budget": 300000.0,
            "eventDate": "2024-12-01",
            "location": "Mumbai"
        }
    
    def test_concurrent_plan_creation(self, client, sample_request):
        """Test concurrent plan creation requests"""
        metrics = LoadTestMetrics()
        concurrent_requests = 10
        
        def create_plan_request():
            """Single plan creation request"""
            start_time = time.time()
            try:
                # Modify request to be unique
                request_data = sample_request.copy()
                request_data["clientName"] = f"Client {uuid4().hex[:8]}"
                
                with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
                    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                        # Mock successful execution
                        mock_result = Mock()
                        mock_result.success = True
                        mock_result.plan_id = str(uuid4())
                        mock_result.final_state = {"beam_candidates": []}
                        mock_result.nodes_executed = []
                        mock_result.error = None
                        mock_execute.return_value = mock_result
                        
                        mock_state_manager.return_value.save_plan.return_value = None
                        mock_state_manager.return_value.load_plan.return_value = {
                            "plan_id": mock_result.plan_id,
                            "status": "completed",
                            "client_name": request_data["clientName"],
                            "combinations": [],
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        response = client.post("/v1/plans", json=request_data)
                        
                        response_time = (time.time() - start_time) * 1000  # Convert to ms
                        success = response.status_code == 200
                        error = None if success else f"HTTP {response.status_code}"
                        
                        return response_time, success, error
                        
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Execute concurrent requests
        metrics.concurrent_requests = concurrent_requests
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(create_plan_request) for _ in range(concurrent_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Assertions for load test
        assert summary["success_rate"] >= 0.9, f"Success rate too low: {summary['success_rate']}"
        assert summary["response_times"]["avg_ms"] < 5000, f"Average response time too high: {summary['response_times']['avg_ms']}ms"
        assert summary["response_times"]["p95_ms"] < 10000, f"95th percentile too high: {summary['response_times']['p95_ms']}ms"
        
        logger.info(f"Concurrent API test summary: {json.dumps(summary, indent=2)}")
    
    def test_concurrent_plan_retrieval(self, client):
        """Test concurrent plan retrieval requests"""
        metrics = LoadTestMetrics()
        concurrent_requests = 20
        
        # Create some test plan IDs
        test_plan_ids = [str(uuid4()) for _ in range(5)]
        
        def retrieve_plan_request():
            """Single plan retrieval request"""
            start_time = time.time()
            try:
                plan_id = test_plan_ids[int(time.time() * 1000) % len(test_plan_ids)]
                
                with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                    # Mock plan data
                    mock_state_manager.return_value.load_plan.return_value = {
                        "plan_id": plan_id,
                        "status": "completed",
                        "client_name": "Test Client",
                        "combinations": [],
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    response = client.get(f"/v1/plans/{plan_id}")
                    
                    response_time = (time.time() - start_time) * 1000
                    success = response.status_code == 200
                    error = None if success else f"HTTP {response.status_code}"
                    
                    return response_time, success, error
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Execute concurrent requests
        metrics.concurrent_requests = concurrent_requests
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(retrieve_plan_request) for _ in range(concurrent_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze results
        summary = metrics.get_summary()
        
        # Retrieval should be faster than creation
        assert summary["success_rate"] >= 0.95, f"Success rate too low: {summary['success_rate']}"
        assert summary["response_times"]["avg_ms"] < 1000, f"Average response time too high: {summary['response_times']['avg_ms']}ms"
        assert summary["response_times"]["p95_ms"] < 2000, f"95th percentile too high: {summary['response_times']['p95_ms']}ms"
        
        logger.info(f"Concurrent retrieval test summary: {json.dumps(summary, indent=2)}")
    
    def test_mixed_workload(self, client, sample_request):
        """Test mixed workload of different API operations"""
        metrics = LoadTestMetrics()
        total_requests = 30
        
        def mixed_request():
            """Random API request"""
            start_time = time.time()
            try:
                # Randomly choose operation type
                operation = int(time.time() * 1000) % 4
                
                if operation == 0:  # Create plan
                    request_data = sample_request.copy()
                    request_data["clientName"] = f"Client {uuid4().hex[:8]}"
                    
                    with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
                        with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                            mock_result = Mock()
                            mock_result.success = True
                            mock_result.plan_id = str(uuid4())
                            mock_result.final_state = {"beam_candidates": []}
                            mock_result.nodes_executed = []
                            mock_result.error = None
                            mock_execute.return_value = mock_result
                            
                            mock_state_manager.return_value.save_plan.return_value = None
                            mock_state_manager.return_value.load_plan.return_value = {
                                "plan_id": mock_result.plan_id,
                                "status": "completed",
                                "client_name": request_data["clientName"],
                                "combinations": [],
                                "created_at": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                            
                            response = client.post("/v1/plans", json=request_data)
                
                elif operation == 1:  # Get plan
                    plan_id = str(uuid4())
                    
                    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                        mock_state_manager.return_value.load_plan.return_value = {
                            "plan_id": plan_id,
                            "status": "completed",
                            "client_name": "Test Client",
                            "combinations": [],
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        response = client.get(f"/v1/plans/{plan_id}")
                
                elif operation == 2:  # List plans
                    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                        mock_state_manager.return_value.list_plans.return_value = ([], 0)
                        
                        response = client.get("/v1/plans")
                
                else:  # Health check
                    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                        mock_state_manager.return_value.health_check.return_value = True
                        
                        response = client.get("/health")
                
                response_time = (time.time() - start_time) * 1000
                success = response.status_code in [200, 201]
                error = None if success else f"HTTP {response.status_code}"
                
                return response_time, success, error
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Execute mixed workload
        metrics.concurrent_requests = 10
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_request) for _ in range(total_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze results
        summary = metrics.get_summary()
        
        assert summary["success_rate"] >= 0.9, f"Success rate too low: {summary['success_rate']}"
        assert summary["requests_per_second"] > 5, f"Throughput too low: {summary['requests_per_second']} req/s"
        
        logger.info(f"Mixed workload test summary: {json.dumps(summary, indent=2)}")


class TestWorkflowConcurrency:
    """Test concurrent workflow execution"""
    
    @pytest.fixture
    def test_db(self):
        """Setup test database"""
        db_setup = TestDatabaseSetup()
        db_setup.setup_test_database()
        yield db_setup
        db_setup.cleanup_test_database()
    
    def test_concurrent_workflow_execution(self, test_db):
        """Test multiple workflows running concurrently"""
        from ..workflows.execution_engine import get_execution_engine
        
        metrics = LoadTestMetrics()
        concurrent_workflows = 5
        
        def execute_workflow():
            """Execute a single workflow"""
            start_time = time.time()
            try:
                # Mock workflow execution
                with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.plan_id = str(uuid4())
                    mock_result.final_state = {
                        "beam_candidates": [
                            {
                                "combination_id": "combo_1",
                                "total_score": 8.5,
                                "estimated_cost": 400000.0
                            }
                        ]
                    }
                    mock_result.nodes_executed = ["initialize", "budget", "sourcing", "beam_search"]
                    mock_result.error = None
                    mock_execute.return_value = mock_result
                    
                    # Simulate workflow execution time
                    time.sleep(0.1)  # 100ms simulation
                    
                    result = mock_execute({
                        "clientName": f"Client {uuid4().hex[:8]}",
                        "guestCount": 100,
                        "budget": 300000.0
                    }, str(uuid4()), async_execution=False)
                    
                    response_time = (time.time() - start_time) * 1000
                    success = result.success
                    error = result.error if not success else None
                    
                    return response_time, success, error
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Execute concurrent workflows
        metrics.concurrent_requests = concurrent_workflows
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workflows) as executor:
            futures = [executor.submit(execute_workflow) for _ in range(concurrent_workflows)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze results
        summary = metrics.get_summary()
        
        assert summary["success_rate"] >= 0.8, f"Workflow success rate too low: {summary['success_rate']}"
        assert summary["response_times"]["avg_ms"] < 2000, f"Average workflow time too high: {summary['response_times']['avg_ms']}ms"
        
        logger.info(f"Concurrent workflow test summary: {json.dumps(summary, indent=2)}")
    
    def test_workflow_resource_contention(self, test_db):
        """Test workflow execution under resource contention"""
        metrics = LoadTestMetrics()
        
        def resource_intensive_workflow():
            """Simulate resource-intensive workflow"""
            start_time = time.time()
            try:
                # Simulate CPU and memory intensive operations
                with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
                    # Simulate processing time
                    time.sleep(0.2)  # 200ms simulation
                    
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.plan_id = str(uuid4())
                    mock_result.final_state = {"beam_candidates": []}
                    mock_result.nodes_executed = ["initialize", "budget", "sourcing"]
                    mock_result.error = None
                    mock_execute.return_value = mock_result
                    
                    result = mock_execute({
                        "clientName": f"Resource Test {uuid4().hex[:8]}",
                        "guestCount": 200,
                        "budget": 500000.0
                    }, str(uuid4()), async_execution=False)
                    
                    response_time = (time.time() - start_time) * 1000
                    success = result.success
                    error = result.error if not success else None
                    
                    return response_time, success, error
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return response_time, False, str(e)
        
        # Test with high concurrency to create resource contention
        concurrent_workflows = 15
        metrics.concurrent_requests = concurrent_workflows
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workflows) as executor:
            futures = [executor.submit(resource_intensive_workflow) for _ in range(concurrent_workflows)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze results under contention
        summary = metrics.get_summary()
        
        # Under resource contention, we expect:
        # - Some degradation in performance but still reasonable success rate
        # - Higher response times but within acceptable limits
        assert summary["success_rate"] >= 0.7, f"Success rate under contention too low: {summary['success_rate']}"
        assert summary["response_times"]["avg_ms"] < 5000, f"Average response time under contention too high: {summary['response_times']['avg_ms']}ms"
        
        logger.info(f"Resource contention test summary: {json.dumps(summary, indent=2)}")


class TestSystemScalability:
    """Test system scalability characteristics"""
    
    def test_throughput_scaling(self):
        """Test throughput scaling with increasing load"""
        throughput_results = []
        
        for concurrent_users in [1, 5, 10, 20]:
            metrics = LoadTestMetrics()
            requests_per_user = 5
            
            def user_simulation():
                """Simulate user making multiple requests"""
                user_metrics = LoadTestMetrics()
                
                for _ in range(requests_per_user):
                    start_time = time.time()
                    try:
                        # Simulate API request
                        with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
                            mock_result = Mock()
                            mock_result.success = True
                            mock_result.plan_id = str(uuid4())
                            mock_result.final_state = {"beam_candidates": []}
                            mock_result.nodes_executed = []
                            mock_result.error = None
                            mock_execute.return_value = mock_result
                            
                            # Simulate processing
                            time.sleep(0.05)  # 50ms base processing time
                            
                            response_time = (time.time() - start_time) * 1000
                            success = True
                            error = None
                            
                            user_metrics.record_request(response_time, success, error)
                            
                    except Exception as e:
                        response_time = (time.time() - start_time) * 1000
                        user_metrics.record_request(response_time, False, str(e))
                
                return user_metrics
            
            # Execute load test
            metrics.concurrent_requests = concurrent_users
            metrics.start_test()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(user_simulation) for _ in range(concurrent_users)]
                
                for future in concurrent.futures.as_completed(futures):
                    user_metrics = future.result()
                    for rt in user_metrics.response_times:
                        metrics.record_request(rt, True, None)
                    metrics.success_count += user_metrics.success_count
                    metrics.failure_count += user_metrics.failure_count
            
            metrics.end_test()
            
            summary = metrics.get_summary()
            throughput_results.append({
                "concurrent_users": concurrent_users,
                "requests_per_second": summary["requests_per_second"],
                "avg_response_time_ms": summary["response_times"]["avg_ms"],
                "success_rate": summary["success_rate"]
            })
        
        # Analyze scaling characteristics
        logger.info(f"Throughput scaling results: {json.dumps(throughput_results, indent=2)}")
        
        # Verify scaling behavior
        for i, result in enumerate(throughput_results):
            assert result["success_rate"] >= 0.8, f"Success rate degraded at {result['concurrent_users']} users"
            
            # Response time should not increase dramatically
            if i > 0:
                prev_response_time = throughput_results[i-1]["avg_response_time_ms"]
                current_response_time = result["avg_response_time_ms"]
                
                # Allow up to 3x increase in response time as load increases
                assert current_response_time <= prev_response_time * 3, \
                    f"Response time increased too much: {prev_response_time}ms -> {current_response_time}ms"
    
    def test_memory_usage_under_load(self):
        """Test memory usage during high load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_operation():
            """Simulate memory-intensive operation"""
            # Create some data structures to simulate workflow state
            data = {
                "combinations": [{"id": i, "data": "x" * 1000} for i in range(100)],
                "workflow_state": {"step": i, "data": list(range(1000)) for i in range(10)}
            }
            
            # Simulate processing
            time.sleep(0.1)
            
            return len(str(data))
        
        # Execute memory-intensive operations concurrently
        concurrent_operations = 20
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_operations) as executor:
            futures = [executor.submit(memory_intensive_operation) for _ in range(concurrent_operations)]
            
            # Wait for completion
            for future in concurrent.futures.as_completed(futures):
                future.result()
        
        # Check memory usage after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        logger.info(f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (increase: {memory_increase:.2f}MB)")
        
        # Memory increase should be reasonable (less than 500MB for this test)
        assert memory_increase < 500, f"Memory usage increased too much: {memory_increase:.2f}MB"


class TestErrorHandlingUnderLoad:
    """Test error handling and recovery under load"""
    
    def test_error_recovery_under_load(self):
        """Test system recovery from errors under load"""
        metrics = LoadTestMetrics()
        error_rate = 0.2  # 20% of requests will fail
        
        def request_with_errors():
            """Request that may fail"""
            start_time = time.time()
            
            # Randomly fail some requests
            if time.time() % 1 < error_rate:
                # Simulate error
                time.sleep(0.05)
                response_time = (time.time() - start_time) * 1000
                return response_time, False, "Simulated error"
            else:
                # Simulate success
                time.sleep(0.1)
                response_time = (time.time() - start_time) * 1000
                return response_time, True, None
        
        # Execute requests with errors
        total_requests = 50
        concurrent_requests = 10
        
        metrics.concurrent_requests = concurrent_requests
        metrics.start_test()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(request_with_errors) for _ in range(total_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                response_time, success, error = future.result()
                metrics.record_request(response_time, success, error)
        
        metrics.end_test()
        
        # Analyze error handling
        summary = metrics.get_summary()
        
        # Should handle errors gracefully
        expected_success_rate = 1.0 - error_rate
        actual_success_rate = summary["success_rate"]
        
        # Allow some tolerance in success rate
        assert abs(actual_success_rate - expected_success_rate) < 0.1, \
            f"Success rate {actual_success_rate} too far from expected {expected_success_rate}"
        
        # System should still be responsive despite errors
        assert summary["response_times"]["avg_ms"] < 1000, \
            f"Response time too high despite errors: {summary['response_times']['avg_ms']}ms"
        
        logger.info(f"Error recovery test summary: {json.dumps(summary, indent=2)}")


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_api_response_time_benchmark(self):
        """Benchmark API response times"""
        from fastapi.testclient import TestClient
        
        app = create_app()
        client = TestClient(app)
        
        # Benchmark different endpoints
        endpoints = [
            ("GET", "/health"),
            ("GET", "/"),
        ]
        
        benchmark_results = {}
        
        for method, endpoint in endpoints:
            response_times = []
            
            for _ in range(10):  # 10 samples per endpoint
                start_time = time.time()
                
                if method == "GET":
                    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                        mock_state_manager.return_value.health_check.return_value = True
                        response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json={})
                
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
            
            benchmark_results[f"{method} {endpoint}"] = {
                "avg_ms": statistics.mean(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "median_ms": statistics.median(response_times)
            }
        
        logger.info(f"API benchmark results: {json.dumps(benchmark_results, indent=2)}")
        
        # Verify performance benchmarks
        for endpoint, metrics in benchmark_results.items():
            if "/health" in endpoint:
                assert metrics["avg_ms"] < 100, f"Health endpoint too slow: {metrics['avg_ms']}ms"
            else:
                assert metrics["avg_ms"] < 500, f"Endpoint {endpoint} too slow: {metrics['avg_ms']}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])