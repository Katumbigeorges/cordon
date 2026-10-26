#!/usr/bin/env python3
"""Run the complete Cordon solution end-to-end and verify all components."""

import os
import sys
from pathlib import Path

print("=" * 70)
print("CORDON - Complete Solution Test")
print("=" * 70)

# Test 1: Provider selection
print("\n1️⃣  Testing Provider Selection...")
from cordon.providers import provider_from_environment

provider = provider_from_environment()
print(f"   Provider type: {type(provider).__name__}")

if type(provider).__name__ == "NvidiaOpenAIProvider":
    print("   ✅ NVIDIA provider selected")
else:
    print(f"   ⚠️  Using {type(provider).__name__} (set NVIDIA_API_KEY for live mode)")

# Test 2: Agent system
print("\n2️⃣  Testing Multi-Agent System...")
from cordon.runtime import run

result = run(
    log_path='logs/full-solution-test.jsonl',
    scenario='full-test',
)

print(f"   Run ID: {result['run_id']}")
print(f"   Mode: {result['context']['mode']}")
print(f"   Live Zetaris: {result['context']['live_zetaris']}")

# Test 3: Agent collaboration
print("\n3️⃣  Testing Agent Collaboration...")
events = result['events']
agent_types = set()
interactions = 0

for event in events:
    actor = event.get('actor', '')
    if actor:
        agent_types.add(actor)
    if event.get('details', {}).get('target_agent'):
        interactions += 1

print(f"   Agents involved: {len(agent_types)}")
print(f"   Agent types: {', '.join(sorted(agent_types))}")
print(f"   Agent interactions: {interactions}")

if interactions >= 3:
    print("   ✅ Multi-agent collaboration confirmed")
else:
    print("   ⚠️  Limited agent interaction")

# Test 4: Model usage
print("\n4️⃣  Testing Model Integration...")
model_events = [e for e in events if e.get('event') == 'model_called']
if model_events:
    details = model_events[0].get('details', {})
    print(f"   Provider: {details.get('provider')}")
    print(f"   Model: {details.get('model')}")
    if details.get('provider') == 'nvidia':
        print("   ✅ NVIDIA Nemotron active")
    else:
        print(f"   ℹ️  Using {details.get('provider')} provider")
else:
    print("   ⚠️  No model calls detected")

# Test 5: Decision quality
print("\n5️⃣  Testing Decision Gate...")
decisions = result['decisions']
lanes = {"Act now": 0, "Plan": 0, "Closed": 0}
for decision in decisions:
    lane = decision.get('lane', '')
    lanes[lane] = lanes.get(lane, 0) + 1

print(f"   Total decisions: {len(decisions)}")
print(f"   Act now: {lanes['Act now']}")
print(f"   Plan: {lanes['Plan']}")
print(f"   Closed: {lanes['Closed']}")

if lanes['Act now'] > 0:
    print("   ✅ Critical findings prioritized")

# Test 6: Evidence tracking
print("\n6️⃣  Testing Evidence Provenance...")
evidence_count = 0
for event in events:
    evidence_count += len(event.get('evidence_ids', []))

print(f"   Total evidence citations: {evidence_count}")
if evidence_count > 20:
    print("   ✅ Strong evidence tracking")

# Test 7: Critic feedback loop
print("\n7️⃣  Testing Evidence Critic Feedback...")
revision_events = [e for e in events if 'revised' in e.get('event', '')]
requery_events = [e for e in events if 'requeried' in e.get('event', '')]

print(f"   Plan revisions: {len(revision_events)}")
print(f"   Data requeries: {len(requery_events)}")

if revision_events and requery_events:
    print("   ✅ Critic feedback loop working")
else:
    print("   ⚠️  No critic feedback detected")

# Test 8: Human approval gate
print("\n8️⃣  Testing Human Approval Gate...")
actions = result.get('actions', [])
coverage_gaps = result.get('coverage_gaps', [])
all_actions = actions + coverage_gaps

pending_actions = [a for a in all_actions if a.get('approval_state') == 'pending']
print(f"   Total actions: {len(all_actions)}")
print(f"   Pending approval: {len(pending_actions)}")

if len(pending_actions) == len(all_actions) and len(all_actions) > 0:
    print("   ✅ All actions require approval")
else:
    print("   ⚠️  Some actions may bypass approval")

# Test 9: Scenario coverage
print("\n9️⃣  Testing Scenario Coverage...")
scenarios_tested = {
    "S1_reconciliation": len([f for f in result['findings'] if f.get('conflicts')]) > 0,
    "S2_kev_exposure": len([d for d in decisions if d.get('lane') == 'Act now']) > 0,
    "S3_no_route": len([d for d in decisions if 'No internet path' in d.get('rationale', '')]) > 0,
    "S4_exploitation": len(actions) > 0,
    "S5_missing_data": len(coverage_gaps) > 0,
    "S6_poisoned_logs": len(result.get('poisoned_data', [])) > 0,
    "S7_expired": len(result.get('expired_acceptances', [])) > 0,
}

covered = sum(scenarios_tested.values())
print(f"   Scenarios covered: {covered}/7")
for scenario, passed in scenarios_tested.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {scenario}")

# Test 10: Trace quality
print("\n🔟 Testing Trace Quality...")
trace_file = Path('logs/full-solution-test.jsonl')
if trace_file.exists():
    lines = trace_file.read_text().splitlines()
    print(f"   Trace events: {len(lines)}")
    print(f"   ✅ Trace file generated")
else:
    print("   ❌ No trace file found")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

strengths = []
warnings = []

if type(provider).__name__ == "NvidiaOpenAIProvider":
    strengths.append("✅ NVIDIA Nemotron integrated")
else:
    warnings.append("⚠️  NVIDIA not active (set NVIDIA_API_KEY)")

if interactions >= 3:
    strengths.append("✅ Multi-agent collaboration")

if lanes['Act now'] > 0:
    strengths.append("✅ Risk prioritization working")

if revision_events and requery_events:
    strengths.append("✅ Feedback loops active")

if len(pending_actions) == len(all_actions):
    strengths.append("✅ Human approval enforced")

if covered >= 5:
    strengths.append(f"✅ {covered}/7 scenarios covered")
elif covered >= 3:
    warnings.append(f"⚠️  Only {covered}/7 scenarios covered")

if not result['context']['live_zetaris']:
    warnings.append("⚠️  Zetaris in sample mode (needs live integration)")

print("\nStrengths:")
for s in strengths:
    print(f"  {s}")

if warnings:
    print("\nWarnings:")
    for w in warnings:
        print(f"  {w}")

print("\n📊 Results saved to:")
print(f"  - logs/full-solution-test.jsonl (trace)")
print(f"  - Findings: {len(result['findings'])}")
print(f"  - Decisions: {len(decisions)}")
print(f"  - Events: {len(events)}")

if len(strengths) >= 4 and len(warnings) <= 2:
    print("\n🎉 Solution is submission-ready!")
    sys.exit(0)
else:
    print("\n⚠️  Some areas need attention before submission")
    sys.exit(1)
