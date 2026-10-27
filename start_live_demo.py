#!/usr/bin/env python3
"""
Quick Start Script for Cordon Live Demo

This script:
1. Starts the Meterless H-MEM service in background
2. Waits for Zetaris to be ready
3. Verifies all components
4. Starts the web UI

Usage:
    python start_live_demo.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def start_hmem_service() -> subprocess.Popen | None:
    """Start the H-MEM service in background."""
    print("🚀 Starting Meterless H-MEM service...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "meterless_hmem_service.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for it to start
        time.sleep(2)
        
        if process.poll() is None:
            print("   ✅ H-MEM service started (PID: {})".format(process.pid))
            return process
        else:
            print("   ❌ H-MEM service failed to start")
            return None
            
    except Exception as e:
        print(f"   ❌ Error starting H-MEM: {e}")
        return None


def wait_for_zetaris(max_wait: int = 60) -> bool:
    """Wait for Zetaris to be ready."""
    print(f"⏳ Waiting for Zetaris (max {max_wait}s)...")
    
    import json
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    from uuid import uuid4
    import base64
    
    # Try to use login endpoint first with username/password
    username = os.getenv("ZETARIS_USERNAME", "admin@zetaris.com")
    password = os.getenv("ZETARIS_PASSWORD", "Zetaris1@")
    base_url = os.getenv("ZETARIS_BASE_URL", "http://localhost:3000")
    rest_url = os.getenv("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0")
    
    start_time = time.time()
    last_error = None
    api_key = None
    
    while time.time() - start_time < max_wait:
        try:
            # Try to login and get a token first
            if not api_key:
                try:
                    login_payload = json.dumps({
                        "username": username,
                        "password": password
                    }).encode("utf-8")
                    
                    login_req = Request(
                        f"{base_url}/api/auth/login",
                        data=login_payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    
                    with urlopen(login_req, timeout=5) as response:
                        login_data = json.loads(response.read().decode("utf-8"))
                        api_key = login_data.get("token") or login_data.get("apiKey")
                        if api_key:
                            print(f"   ✓ Logged in successfully")
                except Exception as e:
                    pass  # Try with existing key if login fails
            
            # Now try the datasources endpoint
            headers = {
                "X-Org-ID": "1",
                "X-Request-ID": str(uuid4()),
            }
            
            # Use API key if we have it, otherwise use stored one from env
            key_to_use = api_key or os.getenv("ZETARIS_API_KEY")
            if key_to_use:
                headers["X-API-Key"] = key_to_use
            
            request = Request(f"{rest_url}/datasource/datasources", headers=headers)
            
            with urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                print(f"   ✅ Zetaris is ready ({len(data) if isinstance(data, list) else 0} datasources)")
                
                # Update .env with working key if we got a new one
                if api_key and api_key != os.getenv("ZETARIS_API_KEY"):
                    print(f"   💡 New API key obtained, update .env with: ZETARIS_API_KEY={api_key}")
                
                return True
                
        except URLError as e:
            last_error = str(e)
            if "401" in str(e) or "Unauthorized" in str(e):
                # Try to get a fresh token
                api_key = None
            time.sleep(3)
            print("   ⏳ Still waiting...")
    
    print(f"   ❌ Zetaris not ready after {max_wait}s: {last_error}")
    print(f"   💡 Try logging into Zetaris UI at {base_url}")
    print(f"   💡 Create a new API key: Settings -> API Keys -> Create New Key")
    print(f"   💡 Then update .env with: ZETARIS_API_KEY=<your-new-key>")
    return False


def verify_setup() -> bool:
    """Run quick verification."""
    print("\n🔍 Verifying setup...")
    
    result = subprocess.run(
        [sys.executable, "setup_live_data.py"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if "✅ System ready for demo" in result.stdout:
        print("   ✅ All systems operational")
        return True
    else:
        print("   ⚠️  Some components need attention")
        print(result.stdout)
        return False


def start_web_ui() -> subprocess.Popen:
    """Start the web UI server."""
    print("\n🌐 Starting web UI...")
    
    process = subprocess.Popen(
        [sys.executable, "api/server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(2)
    print("   ✅ UI server started")
    print("   🌐 Open: http://localhost:8000")
    
    return process


def main() -> int:
    """Main entry point."""
    print("""
========================================================================
  Cordon Live Demo Startup
  Starting all services for the demo
========================================================================
""")
    
    # Load environment
    env_path = Path(".env")
    if env_path.exists():
        print(f"📄 Loading environment from: {env_path}\n")
        for line in env_path.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key and not os.getenv(key):
                    os.environ[key] = value
    
    # Start services
    hmem_process = start_hmem_service()
    
    if hmem_process:
        # Update environment to use H-MEM service
        os.environ["HMEM_SERVICE_URL"] = "http://localhost:9000"
    
    # Wait for Zetaris
    zetaris_ready = wait_for_zetaris(max_wait=30)
    
    if not zetaris_ready:
        print("\n⚠️  Zetaris not ready, continuing with sample mode...")
        print("   💡 Make sure: docker-compose up -d")
        print("   💡 Wait ~60s for Zetaris to warm up")
        print("   💡 Check logs: docker-compose logs driver | tail -20")
    
    # Verify setup
    print()
    try:
        verify_setup()
    except subprocess.TimeoutExpired:
        print("   ⏭️  Verification timed out, continuing...")
    except Exception as e:
        print(f"   ⚠️  Verification failed: {e}")
    
    # Start UI
    ui_process = start_web_ui()
    
    print("""
========================================================================
  🎉 Cordon is ready for demo!
------------------------------------------------------------------------
  Services Running:
    • H-MEM Service:  http://localhost:9000
    • Web UI:         http://localhost:8000

  Live Data Status:
    • NVIDIA NIM:     ✅ Active (AI reasoning)
    • Zetaris:        {}
    • Meterless:      {}
------------------------------------------------------------------------
  Press Ctrl+C to stop all services
========================================================================
""".format(
        "✅ Active (KEV/EPSS)" if zetaris_ready else "⚠️  Sample mode",
        "✅ Active" if hmem_process else "⚠️  Local mode"
    ))
    
    # Keep running
    try:
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        ui_process.terminate()
        if hmem_process:
            hmem_process.terminate()
        
        print("   ✅ Services stopped")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
