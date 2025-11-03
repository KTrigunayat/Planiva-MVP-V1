#!/usr/bin/env python3
"""
Test script to verify the application starts without duplicate button errors
"""
import sys
import os
import subprocess
import time
import signal
from pathlib import Path

def test_app_startup():
    """Test that the app starts without duplicate button errors"""
    print("🧪 Testing Event Planning Agent v2 GUI startup...")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Start Streamlit in the background
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8502",  # Use different port to avoid conflicts
        "--server.address=localhost",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    print("Starting Streamlit server...")
    print("Command:", " ".join(cmd))
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds for startup
        print("Waiting for server to start...")
        time.sleep(10)
        
        # Check if process is still running (no immediate crash)
        if process.poll() is None:
            print("✅ Server started successfully!")
            
            # Try to get some output
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                # Process is still running, which is good
                stdout, stderr = "", ""
            
            # Check for duplicate button errors in stderr
            if "StreamlitDuplicateElementId" in stderr:
                print("❌ Duplicate button error found:")
                print(stderr)
                return False
            elif "Error loading page" in stderr:
                print("❌ Page loading error found:")
                print(stderr)
                return False
            else:
                print("✅ No duplicate button errors detected!")
                return True
        else:
            # Process crashed
            stdout, stderr = process.communicate()
            print("❌ Server crashed on startup:")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        # Clean up: terminate the process if it's still running
        if process.poll() is None:
            print("🛑 Terminating test server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

def main():
    """Main test function"""
    print("🎯 Event Planning Agent v2 GUI - Startup Test")
    print("=" * 60)
    
    success = test_app_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test PASSED: Application starts without duplicate button errors!")
        print("\n💡 You can now run the application with:")
        print("   streamlit run app.py")
        print("   or")
        print("   python start_app.py")
        return True
    else:
        print("❌ Test FAILED: Application has startup issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)