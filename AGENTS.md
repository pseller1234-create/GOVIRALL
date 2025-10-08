# GOVIRALL Agent Guidelines

## Standard Commands
- **Setup**: `./scripts/setup.sh`
- **Build**: `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Test**: `pytest`
- **Lint**: `ruff check .`
- **Type Check**: `mypy .`
- **Security Scan**: `bandit -r .`
- **Format**: `ruff format .`

## Style Rules
- Prefer FastAPI dependency injection and pydantic models for request/response schemas.
- Keep functions pure when possible; isolate I/O at the API layer.
- Enforce type hints on all public functions and pydantic models.
- Document new endpoints with docstrings and OpenAPI metadata.

## Commit Conventions
- Use Conventional Commits (e.g., `feat: add viral probability endpoint`).
- Reference related issues in the footer when applicable.

## Branching Strategy
- Create feature branches from `main` using the pattern `<type>/<short-description>`.
- Rebase on the latest `main` before opening a pull request.

## Review Gates
- Every pull request must run lint, format, tests, type checks, and security scans.
- Trigger automated review by commenting `@codex review` on the pull request.
- Human approval is required before merge; disable auto-merge.

## Test Data & Redaction Policy
- Do not commit real user data, API keys, or PII. Use synthetic or anonymized samples capped at 100 rows.
- Store secrets in `.env.local` or platform secret managers; never in source control.
- Redact sensitive output in logs and documentation.

## Prompt & Completion Constraints
- Use succinct, technical language in prompts and completions.
- Include citations to sources when referencing repository files or command output.
- Avoid filler phrases; focus on actionable guidance.
- Internet access remains disabled unless explicitly allowlisted by reviewers.
