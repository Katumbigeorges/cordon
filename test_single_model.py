#!/usr/bin/env python3
import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

api_key = os.getenv("NVIDIA_API_KEY")
model = "nvidia/nemotron-3.5-lightning-30b-a3b"

print(f"Testing: {model}\n")

payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Return JSON with hypotheses for investigating vulnerabilities."}],
    "max_tokens": 100,
    "temperature": 0.7,
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
    
    print("Sending request...")
    with urlopen(request, timeout=45) as response:
        body = json.loads(response.read().decode("utf-8"))
        print("\n✅ SUCCESS!\n")
        print(json.dumps(body, indent=2))
        
except HTTPError as e:
    print(f"\n❌ HTTP Error: {e.code}")
    try:
        error_body = e.read().decode("utf-8")
        print(f"Error response: {error_body}")
    except:
        pass
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
