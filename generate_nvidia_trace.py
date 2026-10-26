#!/usr/bin/env python3
"""Generate a trace showing NVIDIA Nemotron in action."""

from cordon.runtime import run

print("🚀 Generating trace with NVIDIA Nemotron...\n")

result = run(log_path='logs/nvidia-live-test.jsonl')

print(f"✅ Run complete!")
print(f"   Run ID: {result['run_id']}\n")

# Find the model call event
for event in result['events']:
    if event.get('event') == 'model_called':
        details = event.get('details', {})
        print(f"📊 MODEL CALL:")
        print(f"   Provider: {details.get('provider')}")
        print(f"   Model: {details.get('model')}")
        break

print(f"\n📁 Trace saved to: logs/nvidia-live-test.jsonl")
print(f"   Findings: {len(result['findings'])}")
print(f"   Decisions: {len(result['decisions'])}")
print(f"   Events: {len(result['events'])}")
