"""
WSGI entry point for deployment
This file ensures proper module imports when deployed
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import the app
from event_planning_agent_v2.main import app

# Export for WSGI servers
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
