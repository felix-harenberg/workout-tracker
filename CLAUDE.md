# CLAUDE.md

Hyrox Tracker: offline Android app (Python + Flet + SQLite) to log strength training, runs and Hyrox sessions. Public repo, portfolio project. Owner: Felix, CS student at ETH, 3 hours per week budget.

## Read first

- `docs/PLAN.md` is the source of truth: phases, scope, rules. Read it at the start of every session.
- Work on the **first phase with unchecked boxes**. Do not start tasks from a later phase.
- When a task is done, tick its box in `docs/PLAN.md` in the same commit.

## Scope guard (important)

Felix tends to add features mid-project. Your job is to protect the scope:

- Anything not in the current phase, or listed under "Bewusst nicht in 1.0", is **not built**. Instead, propose a GitHub issue with label `later` (`gh issue create --label later ...`) and continue.
- No login, server, cloud sync, iOS, training plans, timers, social features, Play Store.
- If a request conflicts with the plan, say so directly before doing anything.

## Architecture rules

- `src/core/`: models, SQLite access, calculations (PRs, volume, pace). **Never imports `flet`.** Fully covered by pytest.
- `src/ui/`: Flet screens only. Calls `core/`, holds no business logic.
- `src/main.py`: entry point.
- Storage: stdlib `sqlite3`, one DB file. Units: kg, km, seconds internally; pace shown as min/km.
- Python 3.12, type hints on public functions, dataclasses for models.

## Commands

Felix develops locally on Windows in VS Code (Python 3.12 via `py -3.12`). The devcontainer stays for anyone who prefers Codespaces.

```bash
py -3.12 -m venv .venv && .venv\Scripts\activate && pip install -e ".[dev]"   # one-time setup
pytest                           # run tests
ruff check . && ruff format .    # lint + format
flet run src/main.py             # run as desktop window
flet run --web --port 8550 src/main.py   # preview UI in browser
```

APK builds run in GitHub Actions, not locally (Flutter + Android SDK are too heavy). Phase 1 sets up that workflow.

## Working style

- Small steps. Before writing code for a task, state the plan in 3 to 5 bullets and wait for OK on anything non-trivial.
- Write tests for `core/` before or together with the code.
- Every session ends with a commit (even a half feature) and a short note in the relevant issue: where to continue next time.
- Commit messages in English, imperative, e.g. `Add StrengthSet model and repository`.
- Communicate with Felix in German for planning and progress, code and comments in English.
- Be direct. If something in the plan or a request is a bad idea, say it.
