#!/usr/bin/env python3
"""Test which NVIDIA models are available."""

import os
import json
from urllib.request import Request, urlopen

# Working NVIDIA models based on API listing
MODELS_TO_TEST = [
    # Nemotron models (from API list)
    "nvidia/llama-3.1-nemotron-70b-instruct",      # Main target
    "nvidia/llama-3.1-nemotron-51b-instruct",      # Alternative
    "nvidia/nemotron-4-340b-instruct",              # Largest
    "nvidia/nemotron-3.5-lightning-30b-a3b",       # Lightning variant
    "nvidia/nemotron-3-ultra-550b-a55b",           # Ultra variant
    
    # Llama alternatives
    "meta/llama-3.2-90b-vision-instruct",
    "meta/llama2-70b",
    "nvidia/llama3-chatqa-1.5-70b",
]

def test_model(api_key: str, model: str) -> tuple[bool, str]:
    """Test if a model is available."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        request = Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        
        with urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, f"✅ Works: {content[:50]}"
            
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return False, "❌ 404: Model not found"
        elif "401" in error_msg:
            return False, "❌ 401: Invalid API key"
        elif "403" in error_msg:
            return False, "❌ 403: Access denied"
        else:
            return False, f"❌ Error: {error_msg[:50]}"

if __name__ == "__main__":
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        print("❌ NVIDIA_API_KEY not set")
        exit(1)
    
    print("🔍 Testing NVIDIA Models\n")
    print(f"API Key: {api_key[:20]}...\n")
    print("=" * 70)
    
    working_models = []
    
    for model in MODELS_TO_TEST:
        print(f"\nTesting: {model}")
        success, message = test_model(api_key, model)
        print(f"  {message}")
        
        if success:
            working_models.append(model)
    
    print("\n" + "=" * 70)
    print(f"\n✅ Working Models ({len(working_models)}):")
    for model in working_models:
        print(f"  - {model}")
    
    if working_models:
        print(f"\n💡 Recommend using: {working_models[0]}")
    else:
        print("\n⚠️ No models working. Check:")
        print("  1. API key is valid")
        print("  2. You have access to NVIDIA NIM API")
        print("  3. Visit: https://build.nvidia.com/")
