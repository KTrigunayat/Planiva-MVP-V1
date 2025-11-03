# Event Planning Agent v2 - Streamlit GUI

A modern, responsive web interface for the Event Planning Agent v2 system built with Streamlit. This GUI provides an intuitive way to create event plans, monitor AI agent progress, and manage comprehensive event blueprints with full responsive design and performance optimizations.

## Features

### Core Planning Features
- **Intuitive Event Planning Form**: Multi-section form for capturing event requirements
- **Real-time Progress Tracking**: Monitor AI agents working on your event plan
- **Vendor Combination Display**: Compare and select from optimized vendor combinations
- **Blueprint Generation**: Download comprehensive event plans and vendor information
- **Health Monitoring**: Real-time API connection status and error handling
- **Responsive Design**: Works on desktop and mobile devices

### Task Management Features
- **Extended Task List**: View hierarchical task structure with dependencies, vendors, and logistics
- **Timeline Visualization**: Interactive Gantt chart showing task schedules and conflicts
- **Conflict Resolution**: Identify and resolve timeline, resource, and venue conflicts
- **Vendor Management**: Track vendor assignments, workload, and fitness scores
- **Progress Tracking**: Monitor task completion and identify overdue items

### CRM & Communication Features
- **Communication Preferences**: Manage client preferences for channels, timezones, and quiet hours
- **Communication History**: Track all client communications with delivery status and engagement metrics
- **Analytics Dashboard**: View communication performance metrics, channel effectiveness, and engagement trends
- **Real-time Updates**: Automatic polling for communication status changes
- **Data Export**: Export communications and analytics to CSV for detailed analysis

## Prerequisites

- Python 3.8 or higher
- Event Planning Agent v2 backend running (default: http://localhost:8000)

## Installation

1. **Clone or navigate to the streamlit_gui directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env file with your configuration
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

The application will be available at http://localhost:8501

## Configuration

### Environment Variables

The application can be configured using environment variables or the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Event Planning Agent v2 API URL |
| `API_TIMEOUT` | `30` | API request timeout in seconds |
| `API_RETRY_ATTEMPTS` | `3` | Number of retry attempts for failed requests |
| `APP_TITLE` | `Event Planning Agent` | Application title |
| `APP_ICON` | `🎉` | Application icon |
| `ENVIRONMENT` | `development` | Environment mode (development/production) |

### API Integration

The GUI integrates with the following Event Planning Agent v2 endpoints:

**Core Planning APIs:**
- `GET /health` - Health check
- `POST /v1/plans` - Create new event plan
- `GET /v1/plans/{id}/status` - Get plan status
- `GET /v1/plans/{id}/results` - Get plan results
- `POST /v1/plans/{id}/select` - Select vendor combination
- `GET /v1/plans/{id}/blueprint` - Get final blueprint
- `GET /v1/plans` - List all plans

**Task Management APIs:**
- `GET /api/task-management/extended-task-list` - Get extended task list with dependencies
- `GET /api/task-management/timeline` - Get timeline data for Gantt chart
- `GET /api/task-management/conflicts` - Get task conflicts
- `POST /api/task-management/update-status` - Update task status
- `POST /api/task-management/resolve-conflict` - Resolve conflicts
- `GET /api/task-management/vendor-assignments` - Get vendor assignments

**CRM APIs:**
- `GET /api/crm/preferences` - Get client communication preferences
- `POST /api/crm/preferences` - Update communication preferences
- `GET /api/crm/communications` - Get communication history
- `GET /api/crm/analytics` - Get communication analytics

## Usage

### 1. Creating an Event Plan

1. Navigate to **"➕ Create Plan"**
2. Fill out the event planning form:
   - Basic information (client, event type, date, location)
   - Guest information and budget
   - Venue, catering, and service preferences
   - Client vision and special requirements
3. Submit the form to start the planning process

### 2. Monitoring Progress

1. Go to **"📊 Plan Status"** to track progress
2. View real-time updates as AI agents work:
   - Budget allocation analysis
   - Vendor sourcing
   - Combination optimization
3. See which agent is currently active
4. Monitor estimated completion time

### 3. Reviewing Results

1. Visit **"🎯 Results"** when planning completes
2. Compare vendor combinations:
   - View fitness scores and total costs
   - See detailed vendor information
   - Use comparison tools for side-by-side analysis
3. Select your preferred combination

### 4. Getting the Blueprint

1. Access **"📋 Blueprint"** after selection
2. Review the comprehensive event plan:
   - Timeline and logistics
   - Vendor contact information
   - Budget breakdown
3. Download in multiple formats (PDF, JSON, text)

### 5. Managing Tasks

1. Navigate to **"📋 Task List"** to view all tasks
2. Features:
   - View hierarchical task structure with parent-child relationships
   - Filter by priority, status, or vendor
   - Sort by priority, start date, or duration
   - Mark tasks as complete with checkboxes
   - View dependencies, logistics, and conflicts for each task
3. Use **"📅 Timeline"** for visual task scheduling:
   - Interactive Gantt chart with zoom controls
   - Color-coded by priority level
   - Hover for task details
   - Identify overlapping tasks and conflicts
4. Check **"⚠️ Conflicts"** to resolve issues:
   - View timeline, resource, and venue conflicts
   - See suggested resolutions
   - Apply resolutions with one click
5. Monitor **"👥 Vendors"** for vendor management:
   - View all vendor assignments
   - Check workload distribution
   - See fitness scores and contact details

### 6. Managing Client Communications

1. Set up **"⚙️ Preferences"**:
   - Select preferred communication channels (Email, SMS, WhatsApp)
   - Set timezone and quiet hours
   - Configure opt-out preferences
2. View **"📨 History"** to track communications:
   - See all sent messages with delivery status
   - Filter by channel, status, or date range
   - View engagement metrics (opens, clicks)
   - Export to CSV for analysis
3. Analyze **"📊 Analytics"**:
   - View key metrics (sent, delivered, opened, clicked)
   - Compare channel performance
   - See engagement trends over time
   - Export detailed reports

## Project Structure

```
streamlit_gui/
├── app.py                          # Main application entry point
├── requirements.txt                # Python dependencies
├── .env                           # Environment configuration
├── .env.template                  # Configuration template
├── README.md                      # This file
├── components/                    # Reusable UI components
│   ├── __init__.py
│   ├── api_client.py              # API integration with all endpoints
│   ├── health_monitor.py          # Connection monitoring
│   ├── crm_components.py          # CRM UI components (badges, cards)
│   └── task_components.py         # Task UI components (priority, status, vendor badges)
├── pages/                         # Page modules
│   ├── __init__.py
│   ├── create_plan.py             # Event planning form
│   ├── plan_status.py             # Progress tracking
│   ├── results.py                 # Vendor combinations
│   ├── plan_blueprint.py          # Final blueprint
│   ├── task_list.py               # Extended task list
│   ├── timeline_view.py           # Timeline Gantt chart
│   ├── conflicts.py               # Conflict resolution
│   ├── vendors.py                 # Vendor management
│   ├── crm_preferences.py         # Communication preferences
│   ├── communication_history.py   # Communication tracking
│   └── crm_analytics.py           # Analytics dashboard
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── helpers.py                 # Helper functions
│   ├── validators.py              # Input validation
│   └── export.py                  # Data export utilities
└── tests/                         # Test suite
    ├── __init__.py
    ├── test_crm_pages.py          # CRM page tests
    └── test_task_pages.py         # Task page tests
```

## Development

### Running in Development Mode

Set `ENVIRONMENT=development` in your `.env` file to enable:
- Debug information in the sidebar
- Detailed error messages
- Exception stack traces

### Adding New Pages

1. Create a new page module in the `pages/` directory
2. Add the page to the navigation structure in `app.py`
3. Implement the page rendering method

### Customizing Styles

The application uses custom CSS defined in `app.py`. Modify the styles in the `st.markdown()` section to customize the appearance.

## Troubleshooting

### Connection Issues

If you see "API server error" or connection problems:

1. **Check if the backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify the API_BASE_URL** in your `.env` file

3. **Check network connectivity** between the GUI and backend

4. **Review backend logs** for any errors

### Performance Issues

- **Enable caching**: The application uses Streamlit's built-in caching
- **Reduce polling frequency**: Increase `HEALTH_CHECK_INTERVAL` if needed
- **Check API response times**: Monitor the response time display in the status widget

### Form Validation Errors

- **Required fields**: Ensure all required fields are filled
- **Date validation**: Event date must be in the future
- **Budget validation**: Budget must be a positive number
- **Email/phone format**: Use valid formats for contact information

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the Event Planning Agent v2 backend logs
3. Verify your configuration matches the requirements
4. Check that all dependencies are installed correctly

## License

This project is part of the Event Planning Agent v2 system.