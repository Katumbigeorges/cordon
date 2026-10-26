# Release and deployment process

## Current boundary

The hosting target has not been specified. This setup adds offline CI, not an
automatic production deployment. The existing `docker-compose.yml` provisions
the Zetaris platform; it is not a production package for the Cordon Python API.
The current API uses the Python development HTTP server and in-memory run state.
It requires deployment design and hardening before external production use.

## Promotion gates

1. **Local:** each contributor runs `python tools/check_local.py` and checks the
   feature manually. Coordinator repeats the check on the integrated commit.
2. **Pull request:** reviewer approves, agreed contracts remain compatible, and
   both required CI jobs pass. Merge into `main`.
3. **Staging:** coordinator deploys the exact merged commit (or immutable image
   built from it). Run live integration checks with staging credentials and
   verify board data, paths, traces, and approval behavior. Record the evidence.
4. **Production:** coordinator approves promotion of that same tested artifact.
   Record the release version, full commit SHA, configuration version, operator,
   timestamp, staging results, and previous working artifact.

Do not rebuild a different artifact for production or deploy from a developer's
uncommitted working directory. Keep sample-mode success separate from real sponsor
integration evidence. Follow `AGENTS.md` before any live Zetaris work; required
connection guides/runners are absent here and must be reconciled first.

## Before enabling production

- Choose hosting, domain, TLS, and a supported application server/runtime.
- Define authentication and authorization, particularly approval access.
- Define persistence, backups, restart behavior, and migrations for run state.
- Add and verify health/readiness checks; `/health` is currently absent.
- Define staging/production secret stores and least-privilege integration users.
- Validate real model, Zetaris, and Meterless connections without exposing keys.
- Make readiness fail clearly if required integrations are absent; the current
  model provider can fall back to deterministic sample output.
- Capture monitoring, bounded timeouts, release smoke checks, and rollback steps
  specific to the chosen platform.

## Rollback

Keep the previous immutable artifact available. On a failed smoke check, stop
promotion and redeploy the previous artifact with its compatible configuration.
Verify API functionality and integration health again. Do not assume a code
rollback reverses data migrations or already executed external actions: assess
those separately, and restore data only under an agreed recovery procedure.

## Integration rhythm

Agree a daily integration window. Contributors merge small approved PRs throughout
the day; the coordinator runs an integrated demonstration and records blockers.
Freeze features before release, accepting only fixes needed for release gates.
The dates in the task document are historical scheduling context, not evidence
that milestones or submission have been completed.
