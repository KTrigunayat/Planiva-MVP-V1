#!/usr/bin/env python3
"""
Startup script for Event Planning Agent v2 Streamlit GUI
This script provides an easy way to start the application with proper configuration
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import streamlit
        import requests
        import pandas
        import plotly
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment is properly configured"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found, creating from template...")
        template_file = Path(".env.template")
        if template_file.exists():
            import shutil
            shutil.copy(template_file, env_file)
            print("✅ Created .env file from template")
        else:
            print("❌ No .env.template found")
            return False
    
    print("✅ Environment configuration found")
    return True

def start_streamlit():
    """Start the Streamlit application"""
    print("\n🚀 Starting Event Planning Agent v2 GUI...")
    print("=" * 60)
    
    # Set environment variables for better Streamlit experience
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    
    try:
        # Start Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        print("Starting Streamlit server...")
        print("Command:", " ".join(cmd))
        print("\n📱 The application will be available at:")
        print("   Local:    http://localhost:8501")
        print("   Network:  http://0.0.0.0:8501")
        print("\n💡 Tips:")
        print("   - Press Ctrl+C to stop the server")
        print("   - The app will auto-reload when you make changes")
        print("   - Check the terminal for any error messages")
        print("\n" + "=" * 60)
        
        # Wait a moment then try to open browser
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8501")
                print("🌐 Opened browser automatically")
            except:
                print("🌐 Please open http://localhost:8501 in your browser")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start Streamlit
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🎉 Event Planning Agent v2 - Streamlit GUI Startup")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 To install dependencies, run:")
        print("   pip install -r requirements.txt")
        return False
    
    # Check environment
    if not check_environment():
        return False
    
    # Start the application
    return start_streamlit()

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)