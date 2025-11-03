# API and System Tests for Event Planning Agent v2

This directory contains comprehensive API endpoint tests, system health monitoring tests, and load testing for concurrent workflow execution as specified in task 9.3.

## Test Coverage

### 1. API Endpoint Tests (`test_api_endpoints.py`)
- **Purpose**: Maintain compatibility with existing integrations
- **Coverage**:
  - Root endpoint functionality
  - Health check endpoint
  - Event plan creation (sync/async)
  - Event plan retrieval with workflow details
  - Combination selection
  - Plan listing with pagination and filters
  - Workflow management (resume/cancel)
  - API compatibility validation
  - Error response format consistency

### 2. System Health Tests (`test_system_health.py`)
- **Purpose**: Validate system health monitoring and observability
- **Coverage**:
  - Health checker registration and execution
  - Component health tracking
  - System resource monitoring
  - Database connectivity checks
  - API endpoint availability
  - Health status aggregation
  - Background health checking
  - Metrics integration
  - Error handling and recovery

### 3. Load Testing (`test_load_testing.py`)
- **Purpose**: Test concurrent workflow execution and system scalability
- **Coverage**:
  - Concurrent API request handling
  - Workflow execution under load
  - Resource contention testing
  - Throughput scaling analysis
  - Memory usage monitoring
  - Error handling under load
  - Performance benchmarking

## Requirements Addressed

- **Requirement 5.1**: API compatibility with existing integrations
- **Requirement 6.4**: System performance under concurrent load
- **Requirement 6.5**: Monitoring and observability functionality

## Running the Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

2. Ensure the Event Planning Agent v2 is properly set up:
```bash
cd event_planning_agent_v2
pip install -r requirements.txt
```

### Running Individual Test Suites

#### API Endpoint Tests
```bash
# Run all API tests
pytest tests/test_api_endpoints.py -v

# Run specific test class
pytest tests/test_api_endpoints.py::TestEventPlanCreation -v

# Run with coverage
pytest tests/test_api_endpoints.py --cov=api --cov-report=html
```

#### System Health Tests
```bash
# Run all health monitoring tests
pytest tests/test_system_health.py -v

# Run specific health check tests
pytest tests/test_system_health.py::TestHealthChecker -v
```

#### Load Testing
```bash
# Run load tests (may take longer)
pytest tests/test_load_testing.py -v -s

# Run specific load test
pytest tests/test_load_testing.py::TestConcurrentAPIRequests::test_concurrent_plan_creation -v
```

### Running All API and System Tests

#### Using the Test Runner Script
```bash
# Run all API and system tests
python tests/run_api_system_tests.py

# Run specific test suite
python tests/run_api_system_tests.py --suite api
python tests/run_api_system_tests.py --suite health
python tests/run_api_system_tests.py --suite load

# Verbose output
python tests/run_api_system_tests.py --verbose

# Quiet output
python tests/run_api_system_tests.py --quiet
```

#### Using Pytest Directly
```bash
# Run all tests with markers
pytest -m "api or health or load" -v

# Run only API tests
pytest -m api -v

# Run only health tests
pytest -m health -v

# Run only load tests (slow)
pytest -m load -v -s
```

### Test Configuration

The tests use the following configuration files:
- `pytest.ini`: Pytest configuration and markers
- `conftest.py`: Shared fixtures and test setup
- Test-specific environment variables are set automatically

### Test Reports

The test runner generates comprehensive reports:
- JSON reports for each test suite
- Combined summary report with recommendations
- Performance metrics and benchmarks
- Error analysis and troubleshooting guidance

Example report location:
```
tests/api_system_test_report_20241201_143022.json
```

## Test Structure

### API Endpoint Tests Structure
```
TestAPIEndpoints/
├── TestRootEndpoint
├── TestHealthEndpoint
├── TestEventPlanCreation
├── TestEventPlanRetrieval
├── TestCombinationSelection
├── TestPlanListing
├── TestWorkflowManagement
└── TestAPICompatibility
```

### System Health Tests Structure
```
TestSystemHealth/
├── TestHealthChecker
├── TestSystemHealthMonitoring
├── TestComponentHealthTracking
├── TestHealthCheckDecorator
├── TestMetricsIntegration
├── TestHealthCheckConfiguration
└── TestHealthCheckErrorHandling
```

### Load Testing Structure
```
TestLoadTesting/
├── TestConcurrentAPIRequests
├── TestWorkflowConcurrency
├── TestSystemScalability
├── TestErrorHandlingUnderLoad
└── TestPerformanceBenchmarks
```

## Mocking Strategy

The tests use comprehensive mocking to:
- Isolate API logic from external dependencies
- Simulate various system conditions
- Control test execution timing
- Ensure consistent test results

Key mocked components:
- Database connections and state management
- CrewAI workflow execution
- External API calls
- System resource monitoring
- Health check functions

## Performance Expectations

### API Response Times
- Health endpoint: < 100ms average
- Plan creation: < 5000ms average
- Plan retrieval: < 1000ms average
- List operations: < 2000ms average

### Load Testing Thresholds
- Success rate: ≥ 90% under normal load
- Success rate: ≥ 80% under high load
- Concurrent requests: Up to 20 simultaneous
- Memory usage: < 500MB increase during load

### System Health
- Health check response: < 10 seconds
- Component status updates: < 30 seconds
- Background monitoring: Continuous operation

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure project root is in Python path
   - Check all dependencies are installed
   - Verify virtual environment activation

2. **Database Connection Errors**
   - Tests use mocked database by default
   - Check test database setup if using real DB
   - Verify connection strings in test configuration

3. **Timeout Issues**
   - Load tests may take longer on slower systems
   - Adjust timeout values in pytest.ini if needed
   - Use `-s` flag to see real-time output

4. **Mock Failures**
   - Verify mock patches match actual import paths
   - Check for changes in mocked module interfaces
   - Update mock return values as needed

### Debug Mode

Run tests with debug information:
```bash
# Verbose output with debug info
pytest tests/test_api_endpoints.py -v -s --tb=long

# Run single test with debugging
pytest tests/test_api_endpoints.py::TestEventPlanCreation::test_create_plan_synchronous_success -v -s --pdb
```

### Log Analysis

Tests generate structured logs:
```bash
# View test logs
tail -f logs/test_execution.log

# Filter specific component logs
grep "api_endpoints" logs/test_execution.log
```

## Integration with CI/CD

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run API and System Tests
  run: |
    python tests/run_api_system_tests.py --quiet
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: tests/*_results.json
```

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use appropriate pytest markers (`@pytest.mark.api`, etc.)
3. Include comprehensive docstrings
4. Mock external dependencies appropriately
5. Add performance assertions for load tests
6. Update this README with new test coverage

## Requirements Validation

This test suite validates the following task 9.3 requirements:

✅ **Create API endpoint tests maintaining compatibility with existing integrations**
- Comprehensive API endpoint coverage
- Request/response format validation
- Error handling consistency
- Backward compatibility verification

✅ **Implement system health and monitoring tests**
- Health checker functionality
- Component status tracking
- System resource monitoring
- Observability feature validation

✅ **Add load testing for concurrent workflow execution**
- Concurrent request handling
- Workflow scalability testing
- Performance benchmarking
- Resource utilization monitoring

The test suite provides confidence that the modernized Event Planning Agent v2 maintains API compatibility while delivering robust performance and monitoring capabilities.