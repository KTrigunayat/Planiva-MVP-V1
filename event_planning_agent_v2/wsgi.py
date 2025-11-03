"""
WSGI entry point for deployment
Handles imports correctly regardless of how the app is run
"""
import sys
import os
from pathlib import Path

# Get the parent directory (repo root)
parent_dir = str(Path(__file__).parent.parent.absolute())

# Add parent to Python path so we can import event_planning_agent_v2 as a package
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the FastAPI app
from event_planning_agent_v2.main import app

# Export for ASGI servers
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
