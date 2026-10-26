# Team development workflow

This is one shared project for four contributors. The coordinator establishes the
baseline, ownership, integration rules, and release process. Each contributor owns
implementation and local verification of their tasks.

## Branches and review

- `main` is the intended stable integration branch. It must be established by the
  coordinator; its existence is not assumed in the current checkout.
- Start each small task from current `main`; use `feat/<role>-<task>` or
  `fix/<role>-<task>`. Automation-created branches use `codex/`.
- Open one pull request per coherent change. Avoid long-lived branches per person.
- Require one approving reviewer other than the author and passing CI. Squash merge.
- Do not force-push shared branches. Never resolve conflicts by blindly accepting
  all changes from one side. Consult the affected owner and rerun the checks.

With a clean working tree, in Git Bash:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/d-board
# Implement, then:
python tools/check_local.py
git diff
git add <explicit-paths>
git diff --cached
git commit -m "Add three-lane review board"
# The contributor performs this push:
git push -u origin feat/d-board
```

To update a published task branch without rewriting its history:

```bash
git fetch origin
git merge origin/main
python tools/check_local.py
```

If conflicts occur, resolve each file with its owner, stage only resolved paths,
and complete the merge with `git commit`. Use `git merge --abort` to return to the
pre-merge state when needed. Start merges with a clean working tree.

## Ownership and shared contracts

Confirm the four task documents and GitHub logins before activating CODEOWNERS.
Role D's supplied document assigns product/UI, scenarios, evaluation, and most
documentation. The A/B/C assignments have not been supplied here.

Record confirmed ownership in `docs/TEAM_SETUP.md`. Folder ownership routes review;
it does not prevent necessary cross-team changes. Agree changes to
`cordon/contracts.py`, runtime output fields, API routes, environment settings,
dependencies, and deployment files before implementation. Include affected owners
in review. Keep consumers compatible or update producer and consumer together.

## Local checks and truthful evaluation

Run `python tools/check_local.py` before pushing. It runs the existing tests in
sample mode with outbound connections blocked and writes traces in a temporary
directory. No package installation or credentials are required for this suite.
It does not prove live Zetaris/model/Meterless integration or production readiness.

Do not hardcode scenario outcomes to make evaluation pass. Record unimplemented
scenarios as such. Distinguish sample, synthetic evaluation, and live results.

Keep `.env.local`, passwords, API keys, local environments, and machine-specific
paths out of commits. Stage explicit files. Existing tracked logs are not made
untracked by `.gitignore`; agree any removal separately and inspect them before
publishing. Put new local outputs in ignored `local-results/`.

## Zetaris source contributions

Follow `AGENTS.md` for live connection preflight, SQL syntax, dry runs, explicit
approval before instance writes, and source verification. For new data packages,
use `_create.sql` / `_select.sql` pairs, document source licenses and HOWTOs, and
register create scripts in the source manifest when that runner/manifest is
available. Do not invent missing scripts or bypass approval for live changes.

See `docs/TEAM_SETUP.md` for first-time setup and `docs/DEPLOYMENT.md` for releases.
