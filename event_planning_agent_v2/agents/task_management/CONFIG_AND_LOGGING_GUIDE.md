# Task Management Agent: Configuration and Logging Guide

## Quick Start

### Using Default Configuration

```python
from event_planning_agent_v2.agents.task_management.core.task_management_agent import TaskManagementAgent

# Create agent with default configuration
agent = TaskManagementAgent()
```

### Using Environment-Specific Configuration

```python
from event_planning_agent_v2.config.task_management_config import get_config
from event_planning_agent_v2.agents.task_management.core.task_management_agent import TaskManagementAgent

# Development configuration (verbose logging)
dev_config = get_config("development")
agent = TaskManagementAgent(config=dev_config.to_dict())

# Production configuration (optimized for performance)
prod_config = get_config("production")
agent = TaskManagementAgent(config=prod_config.to_dict())

# Testing configuration (minimal logging, LLM disabled)
test_config = get_config("testing")
agent = TaskManagementAgent(config=test_config.to_dict())
```

### Using Custom Configuration

```python
from event_planning_agent_v2.agents.task_management.core.task_management_agent import TaskManagementAgent

# Create custom configuration
custom_config = {
    "enable_llm_enhancement": True,
    "llm_model": "gemma:2b",
    "max_retries": 3,
    "timeout_seconds": 30,
    "enable_conflict_detection": True,
    "enable_logistics_check": True,
    "enable_venue_lookup": True,
    "parallel_tool_execution": False,
    "log_level": "INFO",
    "enable_debug_logging": False,
    "log_sub_agent_outputs": True,
    "log_tool_results": True
}

agent = TaskManagementAgent(config=custom_config)
```

### Using Environment Variables

```bash
# Set environment variables
export TASK_MGMT_LLM_MODEL="tinyllama"
export TASK_MGMT_LOG_LEVEL="DEBUG"
export TASK_MGMT_ENABLE_LLM_ENHANCEMENT="true"
export TASK_MGMT_PARALLEL_EXECUTION="false"
export TASK_MGMT_TIMEOUT_SECONDS="60"
```

```python
from event_planning_agent_v2.config.task_management_config import load_config_from_env
from event_planning_agent_v2.agents.task_management.core.task_management_agent import TaskManagementAgent

# Load configuration from environment variables
config = load_config_from_env()
agent = TaskManagementAgent(config=config.to_dict())
```

## Configuration Reference

### LLM Enhancement Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_llm_enhancement` | bool | True | Enable/disable LLM task enhancement |
| `llm_model` | str | "gemma:2b" | LLM model to use (gemma:2b or tinyllama) |
| `max_retries` | int | 3 | Maximum retry attempts for LLM calls |
| `timeout_seconds` | int | 30 | Timeout for LLM operations in seconds |

### Tool Enablement Flags

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_conflict_detection` | bool | True | Enable conflict detection tool |
| `enable_logistics_check` | bool | True | Enable logistics verification tool |
| `enable_venue_lookup` | bool | True | Enable venue lookup tool |
| `enable_vendor_assignment` | bool | True | Enable vendor assignment tool |
| `enable_timeline_calculation` | bool | True | Enable timeline calculation tool |

### Processing Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `parallel_tool_execution` | bool | False | Execute tools in parallel (False = sequential) |

### Logging Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `log_level` | str | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `enable_debug_logging` | bool | False | Enable verbose debug logging |
| `enable_performance_logging` | bool | True | Log performance metrics |
| `log_sub_agent_outputs` | bool | True | Log sub-agent output data |
| `log_tool_results` | bool | True | Log tool result data |

### Sub-Agent Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_prioritization_agent` | bool | True | Enable prioritization sub-agent |
| `enable_granularity_agent` | bool | True | Enable granularity sub-agent |
| `enable_resource_dependency_agent` | bool | True | Enable resource dependency sub-agent |

### Error Handling

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `continue_on_sub_agent_error` | bool | True | Continue processing if sub-agent fails |
| `continue_on_tool_error` | bool | True | Continue processing if tool fails |
| `max_tool_retries` | int | 2 | Maximum retry attempts for tool operations |

### Performance Optimization

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_caching` | bool | True | Enable result caching |
| `cache_ttl_seconds` | int | 300 | Cache time-to-live in seconds |
| `batch_processing_enabled` | bool | False | Enable batch processing |

## Logging Guide

### Log Levels

The Task Management Agent uses structured logging with the following levels:

#### DEBUG
- Sub-agent invocation details
- Tool execution details
- Sub-agent output data (when `log_sub_agent_outputs` is enabled)
- Tool result data (when `log_tool_results` is enabled)

**When to use:** Development and troubleshooting

#### INFO
- Processing milestones (start, consolidation, tool processing, completion)
- Sub-agent completion status
- Tool completion status
- Final processing summary

**When to use:** Production monitoring

#### WARNING
- Sub-agent failures (with continuation)
- Tool failures (with continuation)
- Consolidation errors and warnings
- Missing data warnings

**When to use:** Identifying potential issues

#### ERROR
- Critical sub-agent failures
- Critical tool failures
- Consolidation failures
- Processing failures

**When to use:** Identifying failures requiring attention

### Log Output Examples

#### Process Start
```json
{
  "timestamp": "2025-10-21T10:30:00.000Z",
  "level": "INFO",
  "message": "Starting Task Management Agent processing",
  "operation": "process_start",
  "component": "task_management",
  "metadata": {
    "plan_id": "plan-123",
    "workflow_status": "in_progress",
    "config": {...}
  }
}
```

#### Sub-Agent Execution
```json
{
  "timestamp": "2025-10-21T10:30:01.234Z",
  "level": "INFO",
  "message": "Agent PrioritizationAgent prioritize_tasks in 1234.56ms",
  "operation": "agent_prioritize_tasks",
  "component": "task_management",
  "metadata": {
    "agent_name": "PrioritizationAgent",
    "action": "prioritize_tasks",
    "success": true,
    "output_size": 1024
  },
  "performance": {
    "duration_ms": 1234.56,
    "success": true,
    "operation": "agent_prioritize_tasks"
  }
}
```

#### Tool Execution
```json
{
  "timestamp": "2025-10-21T10:30:05.678Z",
  "level": "INFO",
  "message": "Performance: timeline_calculation_tool completed in 567.89ms",
  "operation": "timeline_calculation_tool",
  "component": "task_management",
  "performance": {
    "duration_ms": 567.89,
    "success": true,
    "operation": "timeline_calculation_tool"
  },
  "metadata": {
    "timeline_count": 15
  }
}
```

#### Process Completion
```json
{
  "timestamp": "2025-10-21T10:30:15.000Z",
  "level": "INFO",
  "message": "Task Management Agent processing completed in 15.00s",
  "operation": "process_complete",
  "component": "task_management",
  "metadata": {
    "processing_time_seconds": 15.0,
    "summary": {
      "total_tasks": 20,
      "tasks_with_errors": 0,
      "tasks_with_warnings": 2,
      "tasks_requiring_review": 1
    }
  },
  "performance": {
    "duration_ms": 15000.0,
    "success": true,
    "operation": "task_management_processing"
  }
}
```

### Viewing Logs

Logs are written to:
- **Console**: Structured JSON output to stdout
- **File**: `logs/task_management.log` (if file logging is enabled)

To view logs in real-time:
```bash
# View all logs
tail -f logs/task_management.log

# View only errors
tail -f logs/task_management.log | grep '"level":"ERROR"'

# View performance metrics
tail -f logs/task_management.log | grep '"performance"'
```

### Filtering Logs

Use `jq` to filter and format JSON logs:

```bash
# View only INFO level logs
cat logs/task_management.log | jq 'select(.level=="INFO")'

# View logs for specific operation
cat logs/task_management.log | jq 'select(.operation=="process_start")'

# View performance metrics
cat logs/task_management.log | jq 'select(.performance != null)'

# View logs with errors
cat logs/task_management.log | jq 'select(.level=="ERROR" or .exception != null)'
```

## Environment-Specific Configurations

### Development Configuration

**Use case:** Local development and debugging

**Settings:**
- Log Level: DEBUG
- Debug Logging: Enabled
- Performance Logging: Enabled
- Sub-Agent Output Logging: Enabled
- Tool Result Logging: Enabled
- All tools and agents: Enabled

**Benefits:**
- Maximum visibility into agent operations
- Detailed debugging information
- Performance metrics for optimization

### Production Configuration

**Use case:** Production deployment

**Settings:**
- Log Level: INFO
- Debug Logging: Disabled
- Performance Logging: Enabled
- Sub-Agent Output Logging: Disabled
- Tool Result Logging: Disabled
- All tools and agents: Enabled
- Longer timeout: 60s

**Benefits:**
- Optimized for performance
- Minimal logging overhead
- Essential monitoring information
- Production-ready error handling

### Testing Configuration

**Use case:** Automated testing

**Settings:**
- Log Level: WARNING
- LLM Enhancement: Disabled
- Debug Logging: Disabled
- Performance Logging: Disabled
- Sub-Agent Output Logging: Disabled
- Tool Result Logging: Disabled
- Caching: Disabled
- Short timeout: 10s

**Benefits:**
- Fast test execution
- Minimal logging noise
- Deterministic behavior (no LLM)
- Quick failure detection

## Best Practices

### 1. Use Environment-Specific Configurations

```python
import os

# Determine environment
env = os.getenv("ENVIRONMENT", "development")

# Load appropriate configuration
config = get_config(env)
agent = TaskManagementAgent(config=config.to_dict())
```

### 2. Enable Debug Logging for Troubleshooting

```python
# Temporarily enable debug logging
config = get_config("production")
config.log_level = "DEBUG"
config.enable_debug_logging = True
config.log_sub_agent_outputs = True
config.log_tool_results = True

agent = TaskManagementAgent(config=config.to_dict())
```

### 3. Disable Expensive Operations in Testing

```python
# Use testing configuration for fast tests
config = get_config("testing")
# LLM is already disabled in testing config
agent = TaskManagementAgent(config=config.to_dict())
```

### 4. Monitor Performance in Production

```python
# Ensure performance logging is enabled
config = get_config("production")
config.enable_performance_logging = True

agent = TaskManagementAgent(config=config.to_dict())
```

### 5. Use Environment Variables for Deployment

```bash
# In your deployment configuration
export TASK_MGMT_LLM_MODEL="gemma:2b"
export TASK_MGMT_LOG_LEVEL="INFO"
export TASK_MGMT_TIMEOUT_SECONDS="60"
export TASK_MGMT_ENABLE_CACHING="true"
```

```python
# In your application
config = load_config_from_env()
agent = TaskManagementAgent(config=config.to_dict())
```

## Troubleshooting

### Issue: Too much logging output

**Solution:** Reduce log level or disable debug logging

```python
config = get_config("production")
config.log_level = "WARNING"
config.enable_debug_logging = False
config.log_sub_agent_outputs = False
config.log_tool_results = False
```

### Issue: Missing performance metrics

**Solution:** Enable performance logging

```python
config.enable_performance_logging = True
```

### Issue: Agent timing out

**Solution:** Increase timeout

```python
config.timeout_seconds = 120  # Increase to 2 minutes
```

### Issue: LLM calls failing

**Solution:** Increase retries or disable LLM enhancement

```python
config.max_retries = 5  # Increase retries
# OR
config.enable_llm_enhancement = False  # Disable LLM
```

### Issue: Need to debug specific tool

**Solution:** Enable tool result logging

```python
config.log_level = "DEBUG"
config.log_tool_results = True
```

## Summary

The Task Management Agent configuration and logging system provides:

✅ **Flexible Configuration**
- Environment-specific presets
- Custom configuration support
- Environment variable overrides

✅ **Comprehensive Logging**
- Structured JSON logging
- Multiple log levels
- Performance metrics
- Agent interaction tracking

✅ **Production Ready**
- Optimized production configuration
- Error handling and recovery
- Performance monitoring

✅ **Developer Friendly**
- Verbose development configuration
- Easy debugging
- Clear documentation

For more information, see:
- `TASK_19_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `TASK_19_VERIFICATION_CHECKLIST.md` - Verification checklist
- `config/task_management_config.py` - Configuration source code
