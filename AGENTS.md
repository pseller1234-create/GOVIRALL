# Codex Operating Guide for GOVIRALL

## Environment & Setup
- Always provision tooling via `./scripts/setup.sh`. The script creates `.venv`, pins `python3.11` (fallback to `python3`), upgrades `pip`, and installs `requirements.txt`.
- Activate the environment with `source .venv/bin/activate` before running local commands.
- Internet access is disabled by default. Do not reach out to external domains without explicit security approval.
- Secrets belong in `.env.local` (ignored) or a managed secret store. Never paste secrets in prompts or commit history.

## Standard Commands
| Purpose | Command |
| --- | --- |
| Build / serve | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Tests | `pytest` (add tests under `tests/`) |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Typecheck | `mypy .` |
| Security scan | `bandit -r .` |
| Schema snapshot | `python -m scripts.schema_check` (create module when schema logic lands) |
| Model snapshot | `python -m scripts.model_snapshot` (placeholder until modeling module exists) |

> If a command depends on a tool not yet vendored, add it to `requirements-dev.txt` (create as needed) and document the install.

## Python Style Rules
- Target Python 3.11. Keep modules import-safe and avoid side effects on import.
- Use type annotations everywhere. Prefer `pydantic` models for request/response bodies.
- Format with Ruff (PEP 8 compatible, 88 char soft limit). No unused imports or wildcard imports.
- Never wrap imports in `try/except`. Fail loudly when dependencies are missing.
- Keep functions under 50 lines. Extract helpers for complex logic.

## Commit & Branch Strategy
- Branch from `main` using `feature/<slug>` or `fix/<slug>` naming.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`...).
- Squash commits before merge if history is noisy.

## Review Gates
1. `pytest`
2. `ruff check .`
3. `ruff format --check .`
4. `mypy .`
5. `bandit -r .`
6. Update docs/ADR when architecture changes.
- Trigger Codex review by commenting `@codex review` on the PR.
- Human reviewer sign-off is mandatory even when all checks pass; no auto-merge.

## Test Data & Redaction Policy
- Use synthetic or publicly shareable data in fixtures. No production exports.
- Strip PII, access tokens, or client identifiers from examples.
- Delete transient uploads after tests complete. Document fixtures in `/tests/fixtures/README.md` when added.

## Prompt Patterns & Completion Constraints
- Prompts should outline: **Context**, **Goal**, **Constraints**, **Acceptance tests**.
- Responses must be concise, technical, and cite sources when referencing repo files or logs.
- Avoid speculation; prefer actionable TODOs. Highlight security implications explicitly.
- When uncertain, respond with clarifying questions before proceeding.

## Operational Notes
- Enable Codex code review in project settings.
- Rotate API tokens quarterly; record rotations in the security log.
- Maintain an audit trail in PR descriptions (tests, risk, rollout).
