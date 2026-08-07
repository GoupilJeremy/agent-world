# Repository Guidelines

## Project Structure & Module Organization

The working application is a Flask backend. `backend/app.py` creates the app; `backend/routes/` defines HTTP endpoints, `backend/services/` contains business and AI-provider logic, `backend/models/` holds SQLAlchemy entities, and `backend/config/` manages settings. Put unit and integration tests under `tests/unit/` and `tests/integration/`. `frontend/src/` currently contains placeholder directories for components, hooks, pages, and utilities; add a package manifest before introducing frontend build commands. Documentation belongs in `docs/`, runnable samples in `examples/`, and repository automation in `scripts/` and `.github/`.

## Build, Test, and Development Commands

- `python -m venv .venv` creates an isolated environment; activate it before installing packages.
- `pip install -r requirements.txt -r requirements-dev.txt` installs runtime and quality-tool dependencies.
- `Copy-Item .env.example .env` creates local configuration on PowerShell. Never commit the resulting `.env`.
- `python run.py` starts the development API at `http://127.0.0.1:5000`; use `--port 8080` to override the port.
- `docker compose -f docker-compose.dev.yml up --build` starts the development stack and its services.
- `pytest` runs all tests and produces terminal plus `htmlcov/` coverage reports.
- `black --check backend tests; isort --check-only backend tests; flake8 backend tests --max-line-length=88 --extend-ignore=E203; mypy backend tests --ignore-missing-imports` mirrors CI quality checks.
- `python setup.py sdist bdist_wheel` builds release archives in `dist/`.

## Coding Style & Naming Conventions

Use four-space indentation, Black's 88-character line limit, and isort's Black profile. Add type hints to public Python APIs and keep route handlers thin by moving domain logic into services. Name modules, functions, and variables `snake_case`, classes `PascalCase`, and constants `UPPER_SNAKE_CASE`. Prefer small modules grouped by responsibility rather than adding logic to `backend/app.py`.

## Testing Guidelines

Pytest discovers `test_*.py`, `Test*` classes, and `test_*` functions. Mark tests with `unit`, `integration`, `api`, or `slow` where useful. Every behavior change should include a focused regression test; run `pytest tests/unit/` during iteration and the complete suite before opening a PR. CI requires at least 90% backend coverage.

## Commit & Pull Request Guidelines

History follows Conventional Commits (`feat:`, `fix:`, `style:`, `docs:`, `test:`, `refactor:`, `chore:`). Keep commits atomic and include the user-story ID when applicable: `fix: handle missing agent name (US-019)`. Use branches such as `feature/US-011`, `fix/US-004`, or `docs/README`. Target `main`; PRs should summarize the change, link the issue/user story, list verification commands, and include screenshots for visible UI changes. Confirm formatting, typing, tests, and coverage locally before requesting review.
