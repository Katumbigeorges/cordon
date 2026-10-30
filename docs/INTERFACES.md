# Shared interface agreement

Before parallel implementation, owners confirm this document against the chosen
baseline. Current interfaces are observations, not a substitute for the missing
role task documents.

| Interface | Current implementation | Change rule |
| --- | --- | --- |
| Domain structures | `cordon/contracts.py` | Producer and consumers review field/type changes together |
| Orchestration | `cordon.runtime.run(...)` | Preserve expected decisions, actions, paths, and trace/event consumers |
| Create run | `POST /run` | Document payload, response, and error changes in PR |
| Board | `GET /runs/{run_id}/board` | Coordinate API and UI updates |
| Paths | `GET /runs/{run_id}/paths` | Preserve explicit assumptions and evidence |
| Trace | `GET /runs/{run_id}/trace` | Coordinate event names and trace viewer |
| Approval | `POST /runs/{run_id}/actions/{action_id}/approve` | Review execution and authorization implications |
| Scenarios | `scenarios/definitions.py`, `scenarios/runner.py` | Keep unimplemented scenarios explicit; no invented passing results |

Record approved interface changes here when they merge. Prefer additive optional
fields; coordinate any required-field or route removal in a single reviewed PR.
