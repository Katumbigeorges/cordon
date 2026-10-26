#!/usr/bin/env python3
"""Test script to verify NVIDIA Nemotron integration."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from cordon.providers import NvidiaOpenAIProvider, provider_from_environment


def test_nvidia_direct():
    """Test NVIDIA provider directly."""
    print("=" * 60)
    print("Testing NVIDIA Nemotron Provider (Direct)")
    print("=" * 60)
    
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("❌ NVIDIA_API_KEY not set in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:20]}...")
    
    provider = NvidiaOpenAIProvider(
        api_key=api_key,
        model="nvidia/llama-3.1-nemotron-70b-instruct",
    )
    
    print(f"✓ Provider created: {provider.model}")
    print("\nSending test prompt...")
    
    prompt = "Return JSON with investigation hypotheses for a hospital vulnerability scenario."
    
    try:
        response = provider.complete(prompt)
        
        print("\n" + "=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Content: {response.content}")
        
        if response.provider == "nvidia" and "hypotheses" in response.content:
            print("\n✅ SUCCESS: NVIDIA Nemotron is working!")
            return True
        elif response.provider == "nvidia-fallback":
            print("\n⚠️ FALLBACK: Used deterministic response")
            print(f"Error: {response.model}")
            return False
        else:
            print("\n❌ UNEXPECTED: Response format incorrect")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_from_env():
    """Test provider factory with environment variables."""
    print("\n" + "=" * 60)
    print("Testing Provider Factory (from environment)")
    print("=" * 60)
    
    provider = provider_from_environment()
    
    print(f"Provider type: {type(provider).__name__}")
    
    if type(provider).__name__ == "NvidiaOpenAIProvider":
        print("✅ Correctly selected NVIDIA provider")
        
        prompt = "Return JSON with hypotheses for investigating vulnerabilities."
        response = provider.complete(prompt)
        
        print(f"\nProvider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Hypotheses: {response.content.get('hypotheses', [])}")
        
        return response.provider.startswith("nvidia")
    else:
        print(f"⚠️ Using {type(provider).__name__} instead of NVIDIA")
        return False


def test_agent_integration():
    """Test with actual agent code."""
    print("\n" + "=" * 60)
    print("Testing Agent Integration")
    print("=" * 60)
    
    from cordon.agents import Planner
    
    planner = Planner()
    provider = provider_from_environment()
    
    print(f"Provider: {type(provider).__name__}")
    
    plan, model_response = planner.create_plan(provider)
    
    print("\n" + "-" * 60)
    print("PLAN CREATED:")
    print("-" * 60)
    print(f"Queries: {plan['queries']}")
    print(f"Hypotheses: {plan['hypotheses']}")
    print(f"Max Requeries: {plan['max_requeries']}")
    
    print("\n" + "-" * 60)
    print("MODEL RESPONSE:")
    print("-" * 60)
    print(f"Provider: {model_response.provider}")
    print(f"Model: {model_response.model}")
    
    if model_response.provider.startswith("nvidia"):
        print("\n✅ Agent successfully using NVIDIA Nemotron!")
        return True
    else:
        print("\n⚠️ Agent not using NVIDIA provider")
        return False


if __name__ == "__main__":
    print("\n🚀 NVIDIA Nemotron Integration Test\n")
    
    results = {
        "Direct Provider Test": test_nvidia_direct(),
        "Environment Factory Test": test_provider_from_env(),
        "Agent Integration Test": test_agent_integration(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! NVIDIA Nemotron is integrated.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        sys.exit(1)
