# Cordon - Multi-Agent Vulnerability Prioritization for Healthcare

**Track:** Solving Fragmented Intelligence  
**Hackathon:** Open Agent Hackathon 2026

> A multi-agent system that helps hospital IT teams prioritize vulnerabilities based on patient-critical attack paths, not just CVSS scores.

---

## Problem

Hospital IT teams face thousands of vulnerability alerts from multiple scanners (Trivy, Grype, etc.). Which vulnerabilities actually threaten patient safety? Current approaches:

- **CVSS alone** doesn't consider reachability or business impact
- **Scanner conflicts** create noise (Trivy and Grype matched on only 9.2% of images)
- **Manual triage** is slow and inconsistent
- **Alert fatigue** leads to missed critical issues

---

## Solution

Cordon uses **multi-agent reasoning** to:

1. **Reconcile** scanner conflicts (Trivy vs Grype disagreements)
2. **Enrich** findings with KEV/EPSS threat intelligence
3. **Analyze** attack paths from internet to patient-critical systems
4. **Prioritize** based on exploitability + reachability + clinical impact
5. **Draft** remediation actions that require human approval

### Decision Lanes

- **Act Now:** KEV + Internet-reachable path + Patient-critical impact
- **Plan:** KEV but not externally reachable, or high EPSS score
- **Closed:** Low risk, no active exploitation, isolated systems

---

## Architecture

### Multi-Agent Collaboration

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐
│ Planner  │────▶│ Data         │────▶│ Evidence Critic │
│          │     │ Executor     │     │                 │
└──────────┘     └──────────────┘     └────────┬────────┘
     ▲                                          │
     │                                          │ needs_revision
     └──────────────────────────────────────────┘
                  (feedback loop)
                         │
                         ▼
                ┌────────────────┐     ┌───────────────┐
                │ Decision Gate  │────▶│ Action Draft  │
                │                │     │               │
                └────────────────┘     └───────┬───────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Human Approval  │
                                     │   (Required)    │
                                     └─────────────────┘
```

### Key Features

✅ **Genuine Multi-Agent Interaction** - Not a linear pipeline  
✅ **Evidence-Based Decisions** - Every decision cites source evidence  
✅ **Feedback Loops** - Critic can force plan revision  
✅ **Attack Path Analysis** - Graph-based reachability computation  
✅ **Human-in-the-Loop** - All actions require approval  
✅ **Full Traceability** - JSONL audit logs for every step  

---

## Sponsor Technology Integration

### NVIDIA Nemotron 3.5 Lightning (30B)

**Role:** Powers the Planner agent's investigation hypothesis generation

**Integration:**
- Automatically selected when `NVIDIA_API_KEY` is set
- Generates dynamic hypotheses vs. hardcoded rules
- Traces include provider/model metadata

**Evidence:**
```json
{
  "actor": "planner",
  "event": "model_called",
  "details": {
    "provider": "nvidia",
    "model": "nvidia/nemotron-3.5-lightning-30b-a3b"
  }
}
```

### Zetaris Lightning SQL

**Role:** Unified data gateway for fragmented hospital data sources

**Integration:**
- Hospital data (assets, scans, firewall, credentials) via Postgres connector
- Threat intelligence (KEV, EPSS) via REST or Postgres fallback
- Source discovery through `SHOW LIGHTNING DATABASES`
- All queries through parameterized templates (no SQL injection)

**Current State:**
- ✅ KEV/EPSS enrichment active
- ⚠️ Hospital data registration in progress (see `zetaris/registration/`)
- ✅ Graceful fallback to sample mode

### Meterless H-MEM

**Role:** Hierarchical memory for risk acceptance tracking

**Integration:**
- Stores risk acceptances with expiry dates
- Retrieves expired acceptances for re-evaluation
- Provides provenance for security decisions
- Local store with HTTP client for live service

**Evidence:** Scenario S7 demonstrates expired acceptance detection

---

## Installation & Setup

### Prerequisites

- **Python 3.11+**
- **Docker** (for Zetaris & Postgres)
- **NVIDIA API Key** (from https://build.nvidia.com/)
- **Zetaris API Key** (from Zetaris GUI)

### Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd cordon
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and set:
#   NVIDIA_API_KEY=nvapi-...
#   ZETARIS_API_KEY=akmg...
#   ZETARIS_LIVE=true  (for live mode, false for sample mode)

# 3. Start services (optional - only needed for live mode)
docker-compose up -d

# 4. Register Zetaris data sources (if using live mode)
# Open http://localhost:3000
# Run SQL from: zetaris/registration/01_hospital_postgres.sql
# Then run: zetaris/registration/02_threat_rest.sql

# 5. Run the system
python run_full_solution.py
```

---

## Usage

### Sample Mode (Offline)

Works without live credentials - good for testing and CI:

```bash
# Set in .env or:
unset NVIDIA_API_KEY
unset ZETARIS_LIVE

python run_full_solution.py
```

**Output:**
- Uses deterministic provider (no API calls)
- Uses local sample data
- All scenarios still pass
- Generates full traces

### Live Mode (Production)

Uses NVIDIA Nemotron and Zetaris:

```bash
export NVIDIA_API_KEY=nvapi-...
export ZETARIS_LIVE=true

python run_full_solution.py
```

**Output:**
- Nemotron generates dynamic hypotheses
- Zetaris queries registered data sources
- Real KEV/EPSS enrichment
- Full trace with provider metadata

### API Mode

```python
from cordon.runtime import run

result = run(
    log_path='logs/my-run.jsonl',
    scenario='production',
)

print(f"Findings: {len(result['findings'])}")
print(f"Act Now: {sum(1 for d in result['decisions'] if d['lane'] == 'Act now')}")
```

---

## Scenarios Covered

| ID | Scenario | Evidence |
|----|----------|----------|
| **S1** | Scanner Reconciliation | Trivy vs Grype conflicts typed (ID, severity, count) |
| **S2** | KEV on Internet Edge | Log4Shell on patient-portal → "Act now" |
| **S3** | Same CVE, No Route | Same CVE on lab-reporting → "Plan" (not reachable) |
| **S4** | Active Exploitation | T1190/T1059 markers → Containment action drafted |
| **S5** | Missing Telemetry | Imaging-server has no logs → Coverage gap flagged |
| **S6** | Prompt Injection Defense | "close this alert" in logs → Ignored as untrusted data |
| **S7** | Expired Risk Acceptance | Pharmacy exception expired → Reopened for review |

---

## Testing

### Run Full Test Suite

```bash
python run_full_solution.py
```

**Expected Output:**
```
✅ NVIDIA Nemotron integrated
✅ Multi-agent collaboration (5 agents, 33+ interactions)
✅ 7/7 scenarios covered
✅ All actions require approval
🎉 Solution is submission-ready!
```

### Individual Tests

```bash
# Test NVIDIA integration
python test_nvidia_nemotron.py

# Test provider selection
python -c "from cordon.providers import provider_from_environment; print(type(provider_from_environment()).__name__)"

# Generate traces
python generate_nvidia_trace.py
```

### Check Traces

```bash
# View full trace
cat logs/full-solution-test.jsonl | jq

# Check provider usage
grep '"provider"' logs/full-solution-test.jsonl

# Check agent interactions
grep '"target_agent"' logs/full-solution-test.jsonl
```

---

## Project Structure

```
cordon/
├── cordon/                    # Core agent system
│   ├── agents.py             # Planner, Executor, Critic, Gate
│   ├── contracts.py          # Data contracts (Finding, Decision, etc.)
│   ├── graph.py              # Attack path computation
│   ├── memory.py             # H-MEM implementation
│   ├── providers.py          # NVIDIA & model providers
│   ├── reconcile.py          # Scanner conflict resolution
│   ├── runtime.py            # Orchestration entry point
│   └── sample_data.py        # Offline test fixtures
├── zetaris/
│   ├── templates/            # SQL query templates
│   │   ├── assets_from_postgres.sql
│   │   ├── kev_by_cve.sql
│   │   └── ...
│   └── registration/         # Zetaris setup SQL
│       ├── 01_hospital_postgres.sql
│       └── 02_threat_rest.sql
├── tools/
│   └── zetaris.py            # Zetaris client wrapper
├── api/
│   ├── app.py                # FastAPI application
│   └── server.py             # HTTP server
├── logs/                     # Generated traces (gitignored)
├── docs/                     # Documentation
├── .env.example              # Configuration template
├── .env                      # Local config (gitignored)
├── run_full_solution.py      # Main test/demo script
└── README.md                 # This file
```

---

## Configuration

### Environment Variables

**Required for Live Mode:**
```bash
NVIDIA_API_KEY=nvapi-...              # From https://build.nvidia.com/
NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
ZETARIS_API_KEY=akmg...               # From Zetaris GUI
ZETARIS_REST_URL=http://localhost:8888/api/v1.0
ZETARIS_ORG_ID=1
ZETARIS_LIVE=true                     # Enable live queries
```

**Optional:**
```bash
NVIDIA_TIMEOUT=45.0                   # Model timeout (seconds)
ZETARIS_QUERY_LIMIT=1000             # Max rows per query
HMEM_SERVICE_URL=http://localhost:7070  # For live H-MEM service
MODEL_PROVIDER_URL=...               # Alternative model provider
```

**Sample Mode:**
```bash
# Unset or set to false
NVIDIA_API_KEY=
ZETARIS_LIVE=false
SAMPLE_MODE=true
```

---

## Limitations & Future Work

### Current Limitations

- **No Actual Remediation:** Actions are drafted, not executed
- **Synthetic Data:** Hospital data is generated, not from real systems
- **Sample Scan Images:** 5 containers with known vulnerabilities
- **Zetaris Registration:** Requires manual SQL execution
- **No UI:** Command-line and API only

### Future Enhancements

- **World Model Integration:** Full graph reasoning with Meterless
- **Markovian Engine:** Long-running investigations with bounded context
- **Real Scanner Integration:** Live Trivy/Grype output
- **Automated Remediation:** Ticket creation, patching workflows
- **Dashboard UI:** Real-time decision visualization
- **Multi-Hospital Deployment:** Tenant isolation, RBAC

---

## Scoring Criteria Alignment

| Criterion | Evidence | Location |
|-----------|----------|----------|
| **Impact (30)** | Healthcare vulnerability triage, patient safety focus | README, scenarios S2/S3 |
| **Technical (20)** | Multi-agent feedback loops, evidence provenance | `logs/*.jsonl`, agents.py |
| **Innovation (15)** | Attack-path ranking vs CVSS, conflict reconciliation | graph.py, reconcile.py |
| **Demo (15)** | 7/7 scenarios, traceable decisions | run_full_solution.py output |
| **Product & UX (10)** | API-first, programmatic access, approval gate | api/app.py |
| **Sponsor Tech (10)** | NVIDIA reasoning, Zetaris data gateway, H-MEM memory | providers.py, zetaris_live.py, memory.py |

---

## License

MIT License - See LICENSE file

---

## Attribution

- **NVIDIA NIM API:** Model inference
- **Zetaris Lightning:** Unified data access
- **Meterless:** H-MEM memory architecture
- **CISA KEV:** Exploited vulnerability catalog
- **FIRST EPSS:** Exploit prediction scores
- **Trivy/Grype:** Vulnerability scanners (scan-only test images)

---

## Development Team

Built for Open Agent Hackathon 2026

- **Track:** Solving Fragmented Intelligence
- **Approach:** Multi-agent reasoning over reconciled scanner output
- **Key Innovation:** Patient-critical attack path prioritization

---

## Quick Links

- **Run Test:** `python run_full_solution.py`
- **View Traces:** `cat logs/full-solution-test.jsonl | jq`
- **Zetaris Setup:** `zetaris/registration/README.md`
- **NVIDIA Docs:** `docs/NVIDIA_NEMOTRON_INTEGRATION.md`
- **Sponsor Tech:** See "Sponsor Technology Integration" above

---

**Status:** ✅ Submission-ready with sample mode  
**Live Mode:** ⚠️ Requires Zetaris registration (see zetaris/registration/)
