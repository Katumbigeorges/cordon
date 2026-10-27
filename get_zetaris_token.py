#!/usr/bin/env python3
"""
Get a fresh Zetaris API token using username/password

This script logs into Zetaris and gets a valid API token.
Update your .env file with the returned token.
"""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def load_env():
    """Load environment variables from .env"""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                if key and not os.getenv(key):
                    os.environ[key] = value


def get_token():
    """Get API token from Zetaris"""
    load_env()
    
    username = os.getenv("ZETARIS_USERNAME", "admin@zetaris.com")
    password = os.getenv("ZETARIS_PASSWORD", "Zetaris1@")
    base_url = os.getenv("ZETARIS_BASE_URL", "http://localhost:3000")
    
    print(f"🔐 Logging into Zetaris at {base_url}...")
    print(f"   Username: {username}")
    
    try:
        # Try the login endpoint
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
        
        with urlopen(login_req, timeout=10) as response:
            login_data = json.loads(response.read().decode("utf-8"))
            
            # Try different possible token field names
            token = (login_data.get("token") or 
                    login_data.get("apiKey") or 
                    login_data.get("access_token") or
                    login_data.get("key"))
            
            if token:
                print(f"\n✅ Login successful!")
                print(f"\n📋 Your API token:")
                print(f"   {token}")
                print(f"\n💡 Update .env file:")
                print(f"   ZETARIS_API_KEY={token}")
                
                # Offer to update .env automatically
                response = input("\n❓ Update .env automatically? (y/n): ")
                if response.lower() == 'y':
                    update_env(token)
                
                return token
            else:
                print(f"\n❌ Login response doesn't contain token")
                print(f"   Response: {json.dumps(login_data, indent=2)}")
                return None
                
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"\n❌ Login failed: {e}")
        print(f"   Response: {error_body}")
        
        if e.code == 404:
            print(f"\n💡 The /api/auth/login endpoint doesn't exist.")
            print(f"   You need to create an API key manually:")
            print(f"   1. Open: {base_url}")
            print(f"   2. Login with: {username}")
            print(f"   3. Go to: Settings → API Keys")
            print(f"   4. Click: Create New Key")
            print(f"   5. Copy the key and update .env:")
            print(f"      ZETARIS_API_KEY=<your-key>")
        
        return None
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Make sure Zetaris is running:")
        print(f"   docker-compose up -d")
        print(f"   docker-compose logs -f")
        return None


def update_env(token):
    """Update .env file with new token"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("   ❌ .env file not found")
        return
    
    # Read current content
    content = env_path.read_text()
    lines = content.splitlines()
    
    # Find and replace ZETARIS_API_KEY line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("ZETARIS_API_KEY="):
            lines[i] = f"ZETARIS_API_KEY={token}"
            updated = True
            break
    
    if not updated:
        # Add it if it doesn't exist
        lines.append(f"ZETARIS_API_KEY={token}")
    
    # Write back
    env_path.write_text('\n'.join(lines) + '\n')
    print(f"   ✅ Updated .env file")


if __name__ == "__main__":
    print("""
========================================================================
  Zetaris API Token Generator
  Get a fresh token for the REST API
========================================================================
""")
    
    get_token()
    
    print("\n✅ Done!")
    print()
