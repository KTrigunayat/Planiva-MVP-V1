# Event Planning Agent v2 - Complete Demo Instructions

This guide shows you how to run the complete Event Planning Agent v2 system with Priya & Rohit's wedding data and see all functionalities in action.

## 🎯 What You'll See

The demo showcases all Event Planning Agent v2 capabilities:

- ✅ **Multi-agent AI System**: Orchestrator, Budgeting, Sourcing, and Optimization agents
- ✅ **Real-time Progress Tracking**: Live updates as agents work on your plan
- ✅ **Intelligent Vendor Matching**: AI-powered vendor sourcing and scoring
- ✅ **Automated Combination Scoring**: Smart ranking of vendor combinations
- ✅ **Comprehensive Blueprint Generation**: Complete event plans with timelines
- ✅ **Multi-format Export**: JSON, PDF, and text format exports

## 🚀 Quick Start (Recommended)

### Option 1: Full Event Planning Agent v2 (Complete System)

1. **Double-click `run_demo.bat`** (Windows) or run:
   ```bash
   python run_complete_demo.py
   ```

2. **Wait for the demo to complete** (5-10 minutes)
   - The system will start the API server
   - Run the complete AI workflow
   - Generate Priya & Rohit's wedding plan
   - Export results to files

3. **Check the generated files**:
   - `priya_rohit_wedding_blueprint_[timestamp].json`
   - `priya_rohit_wedding_summary_[timestamp].txt`

### Option 2: Simple Workflow Demo (Faster Alternative)

If the full system has issues, use the simple workflow:

```bash
cd Event_planning_agent
python demo_priya_rohit_simple.py
```

## 📋 Detailed Setup Instructions

### Prerequisites

- **Python 3.8+** installed
- **All project dependencies** (will be installed automatically)
- **8GB+ RAM** recommended for full system
- **Internet connection** for package installation

### Manual Setup (If Needed)

1. **Install Event Planning Agent v2 dependencies**:
   ```bash
   cd event_planning_agent_v2
   pip install -r requirements.txt
   ```

2. **Install Streamlit GUI dependencies**:
   ```bash
   cd streamlit_gui
   pip install -r requirements.txt
   ```

3. **Setup database** (for simple workflow):
   ```bash
   cd Event_planning_agent
   python database_setup.py
   ```

## 🎭 Demo Scenarios

### Priya & Rohit's Wedding Details

```json
{
  "clientName": "Priya & Rohit",
  "guestCount": {"Reception": 150, "Ceremony": 100},
  "location": "Bangalore",
  "budget": 800000,
  "theme": "traditional elegant",
  "colors": ["red", "gold", "maroon"],
  "cuisine": ["South Indian", "North Indian"],
  "dietary": ["Vegetarian"],
  "photography": "Traditional with candid shots",
  "makeup": "Classic bridal makeup"
}
```

## 🔧 System Components

### 1. Event Planning Agent v2 (Full System)
- **Location**: `event_planning_agent_v2/`
- **API Server**: FastAPI with multi-agent workflow
- **Agents**: Orchestrator, Budgeting, Sourcing, Optimization
- **Database**: PostgreSQL with vendor data
- **Features**: Real-time progress, AI matching, blueprint generation

### 2. Streamlit GUI
- **Location**: `streamlit_gui/`
- **Interface**: Web-based user interface
- **Features**: Form input, progress tracking, results display
- **Export**: PDF, JSON, text formats

### 3. Simple Workflow (Fallback)
- **Location**: `Event_planning_agent/`
- **Database**: SQLite with vendor data
- **Features**: Basic vendor sourcing and matching

## 📊 Expected Output

### Terminal Output
```
🎉 Event Planning Agent v2 - Complete Demo for Priya & Rohit
================================================================================
✅ API Health: healthy
📊 Version: 2.0.0
📤 Sending event planning request...
👰 Client: Priya & Rohit
📅 Date: 2024-03-15
📍 Location: Bangalore
👥 Guests: 150 (Reception)
💰 Budget: ₹8,00,000
✅ Event plan created successfully!
🆔 Plan ID: plan_20241008_143022_abc123
🔄 Monitoring planning progress...
🔄 Status: processing | Step: vendor_sourcing | Progress: 45%
✅ Planning completed successfully!
📊 Final Progress: 100%
✅ Retrieved 5 vendor combinations
🏆 Combination 1:
   💯 Fitness Score: 92.5%
   💰 Total Cost: ₹7,45,000
   🏢 Venue: Grand Banquet Hall
   🍽️ Caterer: Royal South Indian Caterers
   📸 Photographer: Traditional Moments Studio
   💄 Makeup Artist: Bridal Beauty Experts
✅ Successfully selected combination: combo_001
✅ Final blueprint generated successfully!
✅ Blueprint exported as JSON: priya_rohit_wedding_blueprint_20241008_143045.json
✅ Summary exported as text: priya_rohit_wedding_summary_20241008_143045.txt
🎉 Demo Completed Successfully! 🎉
```

### Generated Files

1. **JSON Blueprint** (`priya_rohit_wedding_blueprint_[timestamp].json`):
   ```json
   {
     "event_info": {
       "client_name": "Priya & Rohit",
       "event_date": "2024-03-15",
       "location": "Bangalore",
       "guest_count": 150,
       "budget": 800000
     },
     "selected_combination": {
       "fitness_score": 92.5,
       "total_cost": 745000,
       "venue": { "name": "Grand Banquet Hall", ... },
       "caterer": { "name": "Royal South Indian Caterers", ... }
     },
     "timeline": { ... }
   }
   ```

2. **Text Summary** (`priya_rohit_wedding_summary_[timestamp].txt`):
   ```
   PRIYA & ROHIT'S WEDDING PLAN
   ==================================================
   
   Client: Priya & Rohit
   Date: 2024-03-15
   Location: Bangalore
   Guests: 150
   Budget: ₹8,00,000
   
   SELECTED VENDORS
   --------------------
   Venue: Grand Banquet Hall
     Contact: +91-80-12345678
     Email: events@grandbanquet.com
   
   Caterer: Royal South Indian Caterers
     Contact: +91-98765-43210
     Email: bookings@royalcaterers.com
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **API Server Won't Start**:
   ```bash
   # Check if port 8000 is free
   netstat -an | findstr :8000
   
   # Kill any process using port 8000
   taskkill /F /PID [process_id]
   ```

2. **Database Connection Error**:
   ```bash
   cd Event_planning_agent
   python database_setup.py
   python test_system.py
   ```

3. **Missing Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Python Version Issues**:
   ```bash
   python --version  # Should be 3.8+
   ```

### Alternative Commands

If the batch file doesn't work:

```bash
# Full system demo
python event_planning_agent_v2/demo_priya_rohit.py

# Simple workflow demo  
python Event_planning_agent/demo_priya_rohit_simple.py

# Start API server manually
cd event_planning_agent_v2
python main.py

# Start Streamlit GUI
cd streamlit_gui
streamlit run app.py
```

## 📱 Web Interface (Optional)

To use the web interface:

1. **Start the API server**:
   ```bash
   cd event_planning_agent_v2
   python main.py
   ```

2. **Start the Streamlit GUI**:
   ```bash
   cd streamlit_gui
   streamlit run app.py
   ```

3. **Open browser**: http://localhost:8501

4. **Create plan** with Priya & Rohit's data through the web form

## 🎊 Success Indicators

You'll know the demo worked when you see:

- ✅ **API Health Check**: "healthy" status
- ✅ **Plan Creation**: Plan ID generated
- ✅ **Progress Tracking**: 100% completion
- ✅ **Vendor Combinations**: Multiple options found
- ✅ **Blueprint Generation**: JSON and text files created
- ✅ **Budget Compliance**: Total cost within ₹8,00,000

## 📞 Support

If you encounter issues:

1. **Check the terminal output** for specific error messages
2. **Verify Python version** is 3.8 or higher
3. **Ensure all dependencies** are installed
4. **Try the simple workflow** as a fallback
5. **Check file permissions** for writing output files

## 🌟 Next Steps

After running the demo:

1. **Explore the generated files** to see the complete wedding plan
2. **Modify the client data** in the demo scripts to test different scenarios
3. **Use the web interface** for interactive planning
4. **Integrate with your own vendor database** for production use

---

**Happy Planning! 🎉**