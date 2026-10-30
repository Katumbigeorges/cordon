# Shared setup for the four-person team

## Coordinator checklist

1. Confirm this repository is the team's authoritative project.
2. Fetch remote branch information yourself and agree the starting commit with
   the team. At inspection, only `data-agent` and `origin/data-agent` were locally
   known; `origin/HEAD` pointed to that branch. Remote state has not been fetched.
3. Preserve or finish existing work before switching branches. This checkout has
   a pre-existing modification to `cordon/memory.py` owned by the user.
4. Establish `main` from the agreed application baseline. Do not rename or
   overwrite another contributor's branch.
5. Fill the ownership table and activate real rules in `.github/CODEOWNERS`.
6. Run local checks, push the setup yourself, and configure GitHub below.
7. Have all four contributors verify setup from separate clean clones.

The supplied Role D task describes `Makefile`, `ui/app.py`, `eval/`, and
`docs/CONTEXT.md`. Those are absent from this checkout. The current application
uses `api/`, `cordon/`, and Python scenario definitions. Reconcile task documents
against the agreed baseline before assigning file-level work. Do not promise
`make setup`, `make up`, or `make eval` until those commands actually exist.

## Confirmed ownership register

Fill this with all four people; do not infer A/B/C assignments from folder names.

| Role | Person / GitHub login | Owned paths | Backup reviewer |
| --- | --- | --- | --- |
| A | Pending task document | Pending | Pending |
| B | Pending task document | Pending | Pending |
| C | Pending task document | Pending | Pending |
| D | Task document names @ChristianByabushi; confirm | Product/UI, scenarios, eval, docs; reconcile actual paths | Pending |
| Coordinator (one of the four) | Confirm | Workflow, integration, releases | Confirm |

## Contributor setup

Use Python 3.11 or later and Git. The current offline application tests use the
Python standard library. CI covers Python 3.11 and 3.14 on Linux. In Git Bash:

```bash
git clone https://github.com/Katumbigeorges/cordon.git
cd cordon
git switch main
python --version
python tools/check_local.py
git switch -c feat/<role>-<task>
```

These instructions assume the coordinator has published `main` and this setup.
If Python is missing, arrange installation first; no installer is run here.
An optional private virtual environment is `python -m venv .venv`.

For an optional sample API check in a dedicated Git Bash terminal:

```bash
export SAMPLE_MODE=true
unset MODEL_PROVIDER_URL MODEL_PROVIDER_API_KEY
python -m api.server
```

The API listens on loopback port 8000. In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/run -H 'Content-Type: application/json' -d '{"mode":"sample"}'
# Replace RUN_ID with the returned run_id:
curl http://127.0.0.1:8000/runs/RUN_ID/board
curl http://127.0.0.1:8000/runs/RUN_ID/paths
curl http://127.0.0.1:8000/runs/RUN_ID/trace
```

Stop the server with Ctrl+C. This checkout exposes JSON routes; a browser board
at `/` and a `/health` route are not implemented. Sample runs write traces under
`logs/`; inspect `git status` and do not commit generated changes accidentally.

## GitHub settings: coordinator applies manually

- Add the other three contributors with the access they need. Confirm CODEOWNERS
  users have write access; avoid distributing administrator access unnecessarily.
- After publishing and validating `main`, make it the default branch.
- Run a pull request or manually dispatch `Cordon checks` so status checks appear.
- Protect `main` with pull requests, one approval, stale approval dismissal,
  resolved conversations, and both `Offline tests (Python 3.11)` and
  `Offline tests (Python 3.14)` checks. Require up-to-date branches.
- Enable code-owner review after actual ownership rules are filled in.
- Block force pushes and deletion; restrict bypasses. Enable squash merging.
- Configure a protected production environment when the deployment target is
  chosen. Keep deployment credentials in the platform's secret store.

GitHub plan and repository visibility can affect availability of protections;
verify the controls shown in this repository's settings. The checklist does not
claim that any remote settings have already been applied.

Reference: [GitHub branch protection documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

## Publishing this setup yourself

First preserve the existing memory change in its own appropriate commit or
working copy, with its owner's agreement. Do not use a blanket `git add .`.
Then fetch remote information, confirm the shared baseline, and check whether
`main` already exists remotely. If it exists, use it rather than creating a
competing history. If it does not, create `main` from the agreed commit and push
it yourself. Use a `codex/team-workflow` branch for these setup files and a PR
into `main`. Review the exact staged diff and run:

```bash
python tools/check_local.py
git diff --check
```

Stage only `.gitignore`, `CONTRIBUTING.md`, `.github/`, the three new documents
under `docs/`, and `tools/check_local.py`. Commit and push your setup branch,
open the PR, validate CI, then merge and enable protections. No commit, branch
creation, push, or remote settings change is performed by these instructions.
