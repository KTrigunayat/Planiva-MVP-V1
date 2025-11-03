# Progress Tracking Implementation

This document describes the real-time progress tracking and workflow monitoring implementation for the Event Planning Agent v2 GUI.

## Overview

The progress tracking system provides real-time monitoring of the event planning workflow, including:

- **Progress visualization** with step-by-step indicators
- **Agent activity monitoring** showing which agents are currently working
- **Real-time status updates** using API polling
- **Error handling and recovery** with retry mechanisms
- **Workflow control** for cancellation and restart functionality

## Components

### 1. WorkflowSteps

Defines the workflow steps and their metadata:

```python
from components.progress import WorkflowSteps

# Get step information
step_info = WorkflowSteps.get_step_info('budget_allocation')
print(step_info['title'])  # "💰 Analyzing Budget Requirements"

# Calculate progress percentage
progress = WorkflowSteps.calculate_progress_percentage('vendor_sourcing', 50.0)
```

**Available Steps:**
- `initialization` - 🚀 Initializing Planning Process
- `budget_allocation` - 💰 Analyzing Budget Requirements  
- `vendor_sourcing` - 🔍 Sourcing Vendors
- `beam_search` - 🎯 Optimizing Combinations
- `client_selection` - 👤 Awaiting Selection
- `blueprint_generation` - 📋 Generating Blueprint

### 2. ProgressBar

Enhanced progress bar with step indicators:

```python
from components.progress import ProgressBar

ProgressBar.render(
    progress=75.0,
    current_step='vendor_sourcing',
    step_progress=50.0,
    show_percentage=True,
    show_steps=True
)
```

**Features:**
- Overall progress percentage
- Current step highlighting
- Step completion indicators
- Visual step timeline

### 3. AgentActivityDisplay

Shows current agent activity:

```python
from components.progress import AgentActivityDisplay

AgentActivityDisplay.render(
    current_step='budget_allocation',
    active_agents=['Budgeting Agent'],
    last_activity='Analyzing venue budget allocation...'
)
```

**Features:**
- Agent icons and names
- Current activity description
- Estimated duration display
- Multi-agent support

### 4. ErrorDisplay

Error handling with recovery options:

```python
from components.progress import ErrorDisplay

ErrorDisplay.render(
    error_message="Connection timeout",
    error_type="error",
    show_retry=True,
    show_restart=True,
    retry_callback=retry_function,
    restart_callback=restart_function
)
```

**Features:**
- Error categorization (error, warning, info)
- Retry mechanisms
- Restart functionality
- Custom recovery callbacks

### 5. WorkflowController

Workflow control functionality:

```python
from components.progress import WorkflowController

WorkflowController.render_controls(plan_id, current_status)
```

**Features:**
- Workflow cancellation
- Workflow restart
- Confirmation dialogs
- Status-based control availability

### 6. RealTimeStatusUpdater

Handles real-time API polling:

```python
from components.progress import RealTimeStatusUpdater

updater = RealTimeStatusUpdater('plan-123', update_interval=2)
updater.start_monitoring()
status_data = updater.update_status()
```

**Features:**
- Configurable polling interval
- Error handling and retry logic
- Automatic monitoring control
- Session state integration

## Usage

### Basic Progress Page

```python
from components.progress import render_progress_page

def my_status_page():
    plan_id = st.session_state.get('current_plan_id')
    if plan_id:
        render_progress_page(plan_id)
    else:
        st.warning("No active plan")
```

### Custom Implementation

```python
import streamlit as st
from components.progress import (
    RealTimeStatusUpdater,
    ProgressBar,
    AgentActivityDisplay,
    WorkflowSteps
)

def custom_progress_display(plan_id: str):
    # Initialize updater
    updater = RealTimeStatusUpdater(plan_id)
    
    # Get status
    status_data = updater.update_status()
    
    if status_data:
        current_step = status_data.get('current_step', 'initialization')
        step_progress = status_data.get('step_progress', 0.0)
        
        # Calculate overall progress
        overall_progress = WorkflowSteps.calculate_progress_percentage(
            current_step, step_progress
        )
        
        # Render components
        ProgressBar.render(overall_progress, current_step, step_progress)
        
        AgentActivityDisplay.render(
            current_step=current_step,
            active_agents=status_data.get('active_agents', []),
            last_activity=status_data.get('last_activity')
        )
```

## API Integration

The progress tracking system expects the following API endpoints:

### GET /v1/plans/{plan_id}/status

Returns current plan status:

```json
{
    "status": "in_progress",
    "current_step": "vendor_sourcing",
    "step_progress": 75.0,
    "active_agents": ["Sourcing Agent"],
    "last_activity": "Found 15 potential venues",
    "workflow_data": {
        "start_time": "2024-01-01T10:00:00Z",
        "sourcing_progress": {
            "venues": 15,
            "caterers": 8,
            "photographers": 12
        }
    },
    "error": null
}
```

### POST /v1/plans/{plan_id}/cancel (Optional)

Cancel workflow execution:

```json
{
    "message": "Workflow cancelled successfully"
}
```

### POST /v1/plans/{plan_id}/restart (Optional)

Restart failed workflow:

```json
{
    "message": "Workflow restarted successfully"
}
```

## Configuration

### Environment Variables

```bash
# API polling configuration
API_POLLING_INTERVAL=2          # Default polling interval (seconds)
API_MAX_RETRIES=5              # Maximum retry attempts
API_RETRY_DELAY=1              # Delay between retries (seconds)

# UI configuration
PROGRESS_AUTO_REFRESH=true     # Enable auto-refresh by default
PROGRESS_SHOW_DETAILS=true     # Show detailed workflow information
```

### Session State Variables

The progress tracking system uses these session state variables:

```python
# Monitoring state
st.session_state.monitoring_active = True/False
st.session_state.monitoring_initialized = True/False
st.session_state.last_status_check = datetime
st.session_state.status_check_count = int
st.session_state.monitoring_errors = []

# Plan state
st.session_state.current_plan_id = "plan-123"
st.session_state.plan_status = "in_progress"
st.session_state.plan_data = {...}

# UI state
st.session_state.confirm_cancel = True/False
st.session_state.confirm_restart = True/False
```

## Error Handling

The system handles various error scenarios:

### Connection Errors
- API server unavailable
- Network timeouts
- Authentication failures

**Recovery:** Automatic retry with exponential backoff

### API Errors
- Invalid plan ID (404)
- Server errors (5xx)
- Rate limiting (429)

**Recovery:** Error display with manual retry option

### Workflow Errors
- Agent failures
- Processing timeouts
- Invalid state transitions

**Recovery:** Restart workflow or return to previous step

## Performance Considerations

### Polling Optimization
- Configurable polling intervals (1-30 seconds)
- Automatic pause when tab is inactive
- Throttling for high-frequency updates

### Memory Management
- Limited error history (last 5 errors)
- Session state cleanup on navigation
- Efficient status data caching

### User Experience
- Loading indicators during API calls
- Smooth progress animations
- Responsive design for mobile devices

## Testing

Run the component tests:

```bash
cd streamlit_gui
python test_progress_components.py
```

Test coverage includes:
- Component initialization
- Progress calculations
- Error handling
- API integration
- Session state management

## Future Enhancements

Potential improvements:

1. **WebSocket Integration** - Real-time updates without polling
2. **Progress Persistence** - Save progress across browser sessions
3. **Notification System** - Browser notifications for completion
4. **Analytics Dashboard** - Historical workflow performance
5. **Custom Themes** - Configurable progress bar styles
6. **Mobile Optimization** - Enhanced mobile experience
7. **Accessibility** - Screen reader support and keyboard navigation