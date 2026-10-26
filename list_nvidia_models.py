#!/usr/bin/env python3
"""List available models from NVIDIA API."""

import os
import json
from urllib.request import Request, urlopen

def list_models(api_key: str) -> list:
    """Try to list available models."""
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    # Try OpenAI-compatible models endpoint
    endpoints = [
        "https://integrate.api.nvidia.com/v1/models",
        "https://api.nvidia.com/v1/models",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTrying: {endpoint}")
            request = Request(endpoint, headers=headers, method="GET")
            
            with urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
                print(f"✅ Success! Response keys: {list(body.keys())}")
                
                if "data" in body:
                    models = body["data"]
                    print(f"\n📋 Found {len(models)} models:")
                    for model in models[:20]:  # First 20
                        model_id = model.get("id", model.get("model_id", "unknown"))
                        print(f"  - {model_id}")
                    
                    if len(models) > 20:
                        print(f"  ... and {len(models) - 20} more")
                    
                    return models
                else:
                    print(f"Response: {json.dumps(body, indent=2)[:500]}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return []

if __name__ == "__main__":
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        print("❌ NVIDIA_API_KEY not set")
        exit(1)
    
    print("🔍 Listing NVIDIA API Models")
    print(f"API Key: {api_key[:20]}...\n")
    print("=" * 70)
    
    models = list_models(api_key)
    
    if not models:
        print("\n⚠️ Could not list models. Try:")
        print("  1. Visit https://build.nvidia.com/")
        print("  2. Sign in and generate a new API key")
        print("  3. Make sure to accept model terms of service")
        print("\n💡 Alternative: The key might work, but models need explicit names.")
        print("   Check NVIDIA documentation for exact model IDs.")
