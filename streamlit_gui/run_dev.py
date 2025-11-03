#!/usr/bin/env python3
"""
Development runner for Event Planning Agent v2 Streamlit GUI
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the Streamlit application in development mode"""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Set development environment
    os.environ['ENVIRONMENT'] = 'development'
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  .env file not found. Creating from template...")
        if Path('.env.template').exists():
            import shutil
            shutil.copy('.env.template', '.env')
            print("✅ Created .env file from template")
        else:
            print("❌ .env.template not found. Please create .env file manually.")
            return 1
    
    # Check if requirements are installed
    try:
        import streamlit
        import requests
        import aiohttp
        from asyncio_throttle import Throttler
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing requirements...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Run Streamlit
    print("🚀 Starting Event Planning Agent v2 GUI...")
    print("📱 The application will be available at: http://localhost:8501")
    print("🔧 Development mode enabled")
    
    try:
        subprocess.run([
            'streamlit', 'run', 'app.py',
            '--server.port=8501',
            '--server.address=localhost',
            '--server.headless=false',
            '--browser.gatherUsageStats=false'
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        return 0
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())