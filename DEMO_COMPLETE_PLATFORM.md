# Complete Event Management Platform Demo

## Overview

This demo showcases the **complete Event Planning Agent v2 platform** with all three major components:

1. **Event Planning** - AI-powered vendor sourcing and optimization
2. **CRM & Communications** - Client communication management and tracking
3. **Task Management** - Task coordination, timeline visualization, and conflict resolution

## Demo Features

### 🎯 Event Planning
- Client requirements processing from JSON input
- AI multi-agent workflow (Orchestrator, Budgeting, Sourcing, Optimization, Scoring)
- Intelligent vendor combination generation
- Fitness scoring and ranking
- Comprehensive blueprint generation
- Budget allocation and optimization

### 💬 CRM & Communications
- Communication preference management
- Multi-channel support (Email, SMS, WhatsApp)
- Timezone and quiet hours configuration
- Communication history tracking
- Delivery and engagement monitoring
- Analytics and performance metrics
- Channel effectiveness analysis

### 📅 Task Management
- Extended task list with dependencies
- Priority-based task organization
- Timeline visualization (Gantt chart concept)
- Conflict detection and resolution
- Vendor assignment tracking
- Workload distribution analysis
- Progress monitoring

## Input Data

The demo uses **Priya & Rohit's wedding data** from `streamlit_gui/client_data.json`:

- **Event**: Traditional Indian Wedding
- **Location**: Bangalore, Karnataka, India
- **Date**: December 15, 2025
- **Guests**: 150 (Reception), 100 (Ceremony)
- **Budget**: ₹800,000 (8 lakhs INR)
- **Theme**: Traditional Elegant
- **Colors**: Red, Gold, and Maroon
- **Cuisine**: 100% Vegetarian (South Indian & North Indian)
- **Special Requirements**: Traditional rituals, classical music, no alcohol

## Running the Demo

### Option 1: Using the Batch File (Windows)

```cmd
run_complete_demo.bat
```

### Option 2: Using Python Directly

```cmd
python demo_complete_platform.py
```

### Option 3: With Custom Client Data

```python
from demo_complete_platform import CompleteEventManagementDemo

demo = CompleteEventManagementDemo("path/to/your/client_data.json")
demo.run_complete_demo()
```

## Prerequisites

- Python 3.8 or higher
- Required packages: `requests`, `json`, `datetime`
- (Optional) Event Planning Agent v2 API running at `http://localhost:8000`

**Note**: The demo will run in **demo mode** with simulated responses if the API is not available.

## Demo Output

The demo will display:

### Part 1: Event Planning
```
📋 Creating Event Plan
   ✅ Event plan created successfully
   🆔 Plan ID: demo_plan_20251028_123456

📋 Monitoring Planning Progress
   🤖 Orchestrator Agent - Coordinating the workflow
   🤖 Budgeting Agent - Analyzing budget allocation
   🤖 Sourcing Agent - Finding matching vendors
   🤖 Optimization Agent - Creating combinations
   🤖 Scoring Agent - Ranking options
   ✅ Planning completed successfully!

📋 Retrieving Vendor Combinations
   ✅ Retrieved 2 vendor combinations
   
   🏆 Combination 1:
      💯 Fitness Score: 92.5%
      💰 Total Cost: ₹745,000
      🏢 Venue: Grand Banquet Hall Bangalore
      🍽️ Caterer: Royal South Indian Caterers
      📸 Photographer: Traditional Moments Photography
      💄 Makeup: Bridal Beauty Experts
```

### Part 2: CRM & Communications
```
📋 Setting Communication Preferences
   ✅ Communication preferences set successfully
   📧 Preferred Channels: Email, SMS, WhatsApp
   🌍 Timezone: Asia/Kolkata
   🌙 Quiet Hours: 22:00 - 08:00

📋 Communication History
   ✅ Retrieved 4 communications
   
   📨 Recent Communications:
      ✅ 📧 Welcome
         Status: Delivered
         ✓ Opened
      
      ✅ 📧 Budget Summary
         Status: Delivered
         ✓ Opened

📋 Communication Analytics
   ✅ Communication Analytics Summary
   
   📊 Overall Metrics:
      Total Sent: 4
      Total Delivered: 4 (100.0%)
      Total Opened: 2 (50.0%)
      Total Clicked: 1 (25.0%)
```

### Part 3: Task Management
```
📋 Extended Task List
   ✅ Retrieved 12 tasks
   
   📋 Task Overview:
      🔴 Critical Priority (4 tasks):
         ✅ Venue booking and contract signing
         🔄 Catering menu finalization
         ⏳ Final guest count confirmation
         ⏳ Wedding ceremony
   
   📊 Task Statistics:
      Total Tasks: 12
      ✅ Completed: 1 (8.3%)
      🔄 In Progress: 2 (16.7%)
      ⏳ Pending: 9 (75.0%)

📋 Timeline Visualization
   ✅ Timeline Gantt Chart Generated
   
   📅 Event Timeline Overview:
      📍 2025-10-16 (60 days): Venue booking deadline
      📍 2025-10-31 (45 days): Catering menu finalization
      📍 2025-11-15 (30 days): Photography session booking
      🎊 2025-12-15 (TODAY): 🎉 WEDDING DAY 🎉

📋 Conflict Detection & Resolution
   ⚠️ Found 2 potential conflicts
   
   🟡 Conflict 1: Timeline Overlap
      Issue: Photographer and makeup artist both scheduled at 10:00 AM
      💡 Suggested Fix: Start makeup at 8:00 AM, photography at 10:00 AM

📋 Vendor Assignments & Workload
   ✅ 4 vendors assigned
   
   👥 Grand Banquet Hall Bangalore
      Type: Venue
      💯 Fitness Score: 92.5%
      🟡 Workload: Medium (5 tasks)
   
   👥 Royal South Indian Caterers
      Type: Caterer
      💯 Fitness Score: 95.0%
      🟠 Workload: High (8 tasks)
```

## Generated Files

The demo generates the following files:

1. **event_blueprint_[timestamp].json** - Complete event blueprint with all details
2. **Console output** - Comprehensive demo results displayed in terminal

## Integration with Streamlit GUI

After running the demo, you can explore the platform interactively:

```cmd
cd streamlit_gui
streamlit run app.py
```

The Streamlit GUI provides:
- Interactive event planning forms
- Real-time progress monitoring
- Visual timeline (Gantt charts)
- Communication history browser
- Analytics dashboards
- Export functionality

## Demo Architecture

```
demo_complete_platform.py
├── Load Client Data (from JSON)
├── Check API Health
├── Part 1: Event Planning
│   ├── Create Event Plan
│   ├── Monitor Progress (Multi-agent workflow)
│   ├── Get Vendor Combinations
│   ├── Select Best Combination
│   ├── Generate Blueprint
│   └── Export Results
├── Part 2: CRM & Communications
│   ├── Set Communication Preferences
│   ├── View Communication History
│   └── Analyze Communication Analytics
├── Part 3: Task Management
│   ├── View Extended Task List
│   ├── View Timeline Visualization
│   ├── Check for Conflicts
│   └── View Vendor Assignments
└── Print Final Summary
```

## Customization

### Using Your Own Client Data

Create a JSON file with the following structure:

```json
{
  "form_data": {
    "client_name": "Your Client Name",
    "client_email": "client@email.com",
    "client_phone": "+1-234-567-8900",
    "event_type": "Wedding",
    "event_date": "2025-12-31",
    "location": "Your City",
    "total_guests": 100,
    "total_budget": 50000,
    "event_theme": "Your Theme",
    "client_vision": "Your vision...",
    ...
  }
}
```

Then run:

```python
demo = CompleteEventManagementDemo("path/to/your/data.json")
demo.run_complete_demo()
```

### Modifying Demo Behavior

Edit `demo_complete_platform.py` to:
- Change API endpoint: Modify `self.api_base_url`
- Add more vendors: Update `create_demo_combinations()`
- Add more tasks: Update `create_demo_tasks()`
- Customize output: Modify print statements

## Troubleshooting

### API Connection Issues

If the API is not running:
- The demo will automatically switch to **demo mode**
- All features will still be demonstrated with simulated data
- No functionality is lost

### Missing Client Data File

```
❌ Client data file not found: streamlit_gui/client_data.json
```

**Solution**: Ensure the file exists or provide a different path

### Python Import Errors

```
ModuleNotFoundError: No module named 'requests'
```

**Solution**: Install required packages:
```cmd
pip install requests
```

## Platform Capabilities Demonstrated

### AI-Powered Features
- ✅ Multi-agent workflow coordination
- ✅ Intelligent vendor matching
- ✅ Budget optimization
- ✅ Fitness scoring algorithms
- ✅ Conflict detection
- ✅ Workload balancing

### Communication Features
- ✅ Multi-channel messaging (Email, SMS, WhatsApp)
- ✅ Timezone-aware scheduling
- ✅ Quiet hours respect
- ✅ Delivery tracking
- ✅ Engagement analytics
- ✅ Channel performance comparison

### Task Management Features
- ✅ Dependency tracking
- ✅ Priority management
- ✅ Timeline visualization
- ✅ Conflict resolution
- ✅ Vendor coordination
- ✅ Progress monitoring

## Next Steps

1. **Review Demo Output**: Examine the generated blueprint and task list
2. **Explore Streamlit GUI**: Run the interactive web interface
3. **Customize for Your Needs**: Modify client data and preferences
4. **Integrate with Backend**: Connect to the full API for live data
5. **Deploy to Production**: Follow deployment guides in `streamlit_gui/docs/`

## Support

For questions or issues:
- Check `streamlit_gui/README.md` for GUI documentation
- Review `streamlit_gui/docs/` for detailed guides
- See `event_planning_agent_v2/README.md` for backend documentation

## License

This demo is part of the Event Planning Agent v2 system.

---

**🎉 Enjoy exploring the complete Event Management Platform!**
