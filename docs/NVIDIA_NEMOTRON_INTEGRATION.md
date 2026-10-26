# NVIDIA Nemotron Integration

## Overview

Cordon uses **NVIDIA Nemotron 70B Instruct** via the NVIDIA NIM (NVIDIA Inference Microservices) API to power the Planner agent's investigation hypothesis generation. This provides state-of-the-art reasoning for vulnerability prioritization in healthcare environments.

## Model Details

**Model:** `nvidia/llama-3.1-nemotron-70b-instruct`
- **Provider:** NVIDIA NIM API (OpenAI-compatible endpoint)
- **Purpose:** Generate investigation hypotheses for vulnerability scenarios
- **API Endpoint:** `https://integrate.api.nvidia.com/v1`

## Architecture

```
┌─────────────────┐
│  Planner Agent  │
└────────┬────────┘
         │ create_plan()
         ▼
┌─────────────────────────┐
│ NvidiaOpenAIProvider    │
│ (providers.py)          │
└────────┬────────────────┘
         │ OpenAI-compatible
         │ chat/completions
         ▼
┌─────────────────────────┐
│ NVIDIA NIM API          │
│ Nemotron 70B Instruct   │
└─────────────────────────┘
```

## Configuration

### Environment Variables

**Required:**
```bash
NVIDIA_API_KEY=nvapi-...  # Your NVIDIA API key
```

**Optional:**
```bash
NVIDIA_MODEL=nvidia/llama-3.1-nemotron-70b-instruct  # Default model
NVIDIA_TIMEOUT=30.0  # Request timeout in seconds
```

### Provider Priority

The system selects providers in this order:

1. **NVIDIA API** (if `NVIDIA_API_KEY` is set) ✅ **ACTIVE**
2. **Custom HTTP Provider** (if `MODEL_PROVIDER_URL` is set)
3. **Deterministic Fallback** (for sample mode / offline testing)

## How It Works

### 1. Investigation Planning

When a run starts, the Planner agent calls:

```python
from cordon.agents import Planner
from cordon.providers import provider_from_environment

planner = Planner()
provider = provider_from_environment()  # Returns NvidiaOpenAIProvider

plan, model_response = planner.create_plan(provider)
```

### 2. Nemotron Prompt

The provider sends this structured prompt:

**System Prompt:**
```
You are a hospital vulnerability investigation planner.
Given a vulnerability scenario, return JSON with an array of investigation hypotheses.
Focus on patient-safety-critical attack paths and internet-reachable exposures.

Return ONLY valid JSON in this exact format:
{"hypotheses": ["hypothesis1", "hypothesis2"]}
```

**User Prompt:**
```
Return JSON with a hypotheses array for a bounded hospital vulnerability investigation.
```

### 3. Response Processing

**Expected Response:**
```json
{
  "hypotheses": [
    "internet_reachable_patient_impact",
    "credential_chain_to_ehr",
    "exploit_in_the_wild_kev_priority"
  ]
}
```

The provider:
- Parses the OpenAI-compatible response
- Extracts the JSON content
- Validates structure
- Falls back to default if parsing fails

### 4. Trace Evidence

Each model call is logged to the trace:

```json
{
  "actor": "planner",
  "event": "model_called",
  "details": {
    "provider": "nvidia",
    "model": "nvidia/llama-3.1-nemotron-70b-instruct"
  },
  "run_id": "...",
  "step_id": "planner-model-1"
}
```

## Testing

### Quick Test

```bash
python test_nvidia_nemotron.py
```

This runs three tests:
1. **Direct Provider Test** - Calls NVIDIA API directly
2. **Environment Factory Test** - Tests provider selection
3. **Agent Integration Test** - Tests with real Planner agent

### Expected Output

```
✅ PASS: Direct Provider Test
✅ PASS: Environment Factory Test
✅ PASS: Agent Integration Test

🎉 All tests passed! NVIDIA Nemotron is integrated.
```

## Sample Mode vs. Live Mode

### Sample Mode (Offline)
```bash
unset NVIDIA_API_KEY
python run.py
```
- Uses `DeterministicProvider`
- Returns hardcoded `["internet_reachable_patient_impact"]`
- No external API calls
- Good for CI/testing

### Live Mode (NVIDIA)
```bash
export NVIDIA_API_KEY=nvapi-...
python run.py
```
- Uses `NvidiaOpenAIProvider`
- Calls NVIDIA NIM API
- Dynamic hypothesis generation
- Required for demo/submission

## Error Handling

The provider has graceful fallbacks:

```python
try:
    # Call NVIDIA API
    response = make_request()
    content = parse_json(response)
except Exception as error:
    # Fall back to deterministic
    return ModelResponse(
        content={"hypotheses": ["internet_reachable_patient_impact"]},
        provider="nvidia-fallback",
        model=f"{self.model}-error:{str(error)[:50]}"
    )
```

**Failure Modes:**
1. **Network error** → Logs error, uses fallback
2. **Invalid JSON** → Uses default hypothesis
3. **API timeout** → Uses default hypothesis
4. **Missing API key** → Uses DeterministicProvider

## Trace Verification

To verify NVIDIA is being used:

```bash
# Run a scenario
python run.py

# Check the trace
grep '"provider"' logs/sample-run.jsonl
```

**Expected:**
```json
{"actor":"planner","details":{"provider":"nvidia","model":"nvidia/llama-3.1-nemotron-70b-instruct"}}
```

**If seeing "sample":**
```json
{"actor":"planner","details":{"provider":"sample","model":"deterministic"}}
```
→ Check that `NVIDIA_API_KEY` is set correctly

## Submission Requirements

According to the weak submission examples, you must:

✅ **Integration:** NVIDIA technology has a real role (hypothesis generation)
✅ **Traceability:** Provider and model logged in every trace
✅ **Load-bearing:** Removing NVIDIA changes agent behavior
✅ **Documented:** This file + sponsor explanation

### For the Slide Deck

**NVIDIA Contribution:**
> "NVIDIA Nemotron 70B Instruct powers our Planner agent, generating investigation hypotheses that guide the multi-agent vulnerability analysis. The model's healthcare-domain reasoning helps prioritize patient-critical attack paths over generic CVSS scores."

### For the Demo Video

Show:
1. The trace with `"provider": "nvidia"`
2. The hypotheses changing between runs (if using temperature > 0)
3. Contrast with deterministic mode

## API Costs & Limits

**NVIDIA NIM API Limits:**
- Check your quota at: https://build.nvidia.com/
- Free tier may have rate limits
- Production use may require paid tier

**Current Usage:**
- 1 API call per run (Planner only)
- ~50-200 tokens per request
- Low cost, high impact

## Alternative Models

The provider can be switched to other NVIDIA models:

```bash
# Use different Nemotron variant
export NVIDIA_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b

# Or another reasoning model
export NVIDIA_MODEL=nvidia/llama-3.1-405b-instruct
```

## Troubleshooting

### Problem: "NVIDIA_API_KEY not set"
**Solution:** Check your `.env` file has the key without spaces

### Problem: Provider says "sample" not "nvidia"
**Solution:** 
```bash
# Check environment
echo $NVIDIA_API_KEY

# Reload .env
source .env
python run.py
```

### Problem: "Invalid JSON response"
**Solution:** Model may return text; fallback activates automatically

### Problem: API timeout
**Solution:** 
```bash
export NVIDIA_TIMEOUT=60.0  # Increase timeout
```

## References

- **NVIDIA NIM API Docs:** https://docs.api.nvidia.com/nim/
- **Nemotron Model Card:** https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct
- **OpenAI Compatibility:** https://platform.openai.com/docs/api-reference/chat

---

**Status:** ✅ Integrated and tested
**Last Updated:** October 26, 2026
