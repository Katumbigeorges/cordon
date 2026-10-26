#!/usr/bin/env python3
import os, json
from urllib.request import Request, urlopen

api_key = os.getenv("NVIDIA_API_KEY")
r = Request('https://integrate.api.nvidia.com/v1/models', 
            headers={'Authorization': f'Bearer {api_key}'}, 
            method='GET')
body = json.loads(urlopen(r).read())

print("\n🔍 Searching for working models...\n")

# Find Nemotron models
nemotron = [m['id'] for m in body['data'] if 'nemotron' in m['id'].lower()]
print("=" * 70)
print(f"Nemotron models ({len(nemotron)}):")
print("=" * 70)
if nemotron:
    for m in nemotron:
        print(f"  ✓ {m}")
else:
    print("  (none found)")

# Find Llama models
llama = [m['id'] for m in body['data'] if 'llama' in m['id'].lower()]
print("\n" + "=" * 70)
print(f"Llama models ({len(llama)}):")
print("=" * 70)
for m in llama[:10]:
    print(f"  ✓ {m}")
if len(llama) > 10:
    print(f"  ... and {len(llama) - 10} more")

# Find any high-performing instruct models
good_models = [m['id'] for m in body['data'] if any(keyword in m['id'].lower() 
               for keyword in ['instruct', 'chat']) and 
               any(size in m['id'].lower() for size in ['70b', '34b', '27b'])]
print("\n" + "=" * 70)
print(f"Large instruct/chat models ({len(good_models)}):")
print("=" * 70)
for m in good_models[:10]:
    print(f"  ✓ {m}")

print("\n💡 Recommendation: Use any model from above lists")
