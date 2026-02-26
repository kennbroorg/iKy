# iKy - OSINT Tool

## Project Structure

- `backend/` — Python 3.12 Flask + Celery backend
- `frontend/` — Angular frontend
- `install/docker/` — Dockerfiles and compose config

## Coding Style

All Python code MUST comply with the project's `ruff.toml` configuration:

- **Formatter**: ruff format (black-compatible), line-length 88, target py312
- **Linter rules**: E, F, W (pycodestyle/pyflakes), I (isort), B (bugbear), UP (pyupgrade), SIM (simplify), C4 (comprehensions), A (builtins), RUF (ruff-specific)
- **Ignored**: E203 (black-compatible whitespace), E501 (line length handled by formatter)
- **Tests**: S101 (assert usage) is allowed in `**/tests/**`

When writing or modifying Python code:

1. Use modern Python 3.12 idioms (f-strings, `|` union types, `match`, etc.)
2. Keep lines at 88 chars max
3. Sort imports with isort style (stdlib, third-party, local — separated by blank lines)
4. Prefer list/dict/set comprehensions over map/filter
5. Avoid shadowing Python builtins (rule A)
6. Use `pathlib.Path` over `os.path` where practical

## Dev Workflow

- `just setup` — create `.venv/` with pre-commit and ruff (pinned to match pre-commit config)
- `just lint` / `just fmt` — check or auto-fix with ruff from the venv
- `just build` / `just up` / `just down` — Docker lifecycle
- `just test` — run pytest inside the backend container
