#!/usr/bin/env python3
"""
AURELIA Financial Chatbot Launcher
Starts both FastAPI backend and Streamlit frontend
"""

import subprocess
import time
import sys
import os
import requests
from threading import Thread

def check_port(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def wait_for_api(max_wait=30):
    """Wait for API to be ready"""
    print("⏳ Waiting for API to be ready...")

    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass

        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i}/{max_wait}s)")

    return False

def start_backend():
    """Start FastAPI backend"""
    print("🚀 Starting FastAPI backend...")

    # Check if port 8000 is available
    if not check_port(8000):
        print("⚠️  Port 8000 is already in use. Backend may already be running.")
        return None

    try:
        # Start backend process
        process = subprocess.Popen(
            [sys.executable, "backend.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"✅ Backend started (PID: {process.pid})")
        return process

    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")

    try:
        # Start frontend process
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "frontend.py", "--server.port", "8501"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"✅ Frontend started (PID: {process.pid})")
        print("🌐 Frontend will be available at: http://localhost:8501")
        return process

    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main launcher function"""
    print("🤖 AURELIA FINANCIAL CHATBOT LAUNCHER")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("backend.py") or not os.path.exists("frontend.py"):
        print("❌ Backend or frontend files not found!")
        print("Please run this script from the AURELIA directory.")
        return

    # Check if API keys are configured
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ Environment file found")
    else:
        print("⚠️  .env file not found - make sure API keys are configured")

    backend_process = None
    frontend_process = None

    try:
        # Start backend
        backend_process = start_backend()

        if backend_process:
            # Wait for API to be ready
            if wait_for_api():
                # Start frontend
                frontend_process = start_frontend()

                if frontend_process:
                    print("\n🎉 CHATBOT SYSTEM READY!")
                    print("=" * 30)
                    print("🔗 Backend API: http://localhost:8000")
                    print("🌐 Frontend App: http://localhost:8501")
                    print("📖 API Docs: http://localhost:8000/docs")
                    print("\n💡 Open your browser and go to: http://localhost:8501")
                    print("\nPress Ctrl+C to stop both services")

                    # Keep processes running
                    try:
                        while True:
                            # Check if processes are still running
                            if backend_process and backend_process.poll() is not None:
                                print("❌ Backend process stopped unexpectedly")
                                break

                            if frontend_process and frontend_process.poll() is not None:
                                print("❌ Frontend process stopped unexpectedly")
                                break

                            time.sleep(1)

                    except KeyboardInterrupt:
                        print("\n🛑 Shutting down chatbot system...")

                else:
                    print("❌ Failed to start frontend")
            else:
                print("❌ API failed to become ready")
        else:
            print("❌ Failed to start backend")

    finally:
        # Cleanup processes
        if frontend_process:
            print("🔄 Stopping frontend...")
            frontend_process.terminate()
            frontend_process.wait()

        if backend_process:
            print("🔄 Stopping backend...")
            backend_process.terminate()
            backend_process.wait()

        print("✅ Cleanup complete")

if __name__ == "__main__":
    main()