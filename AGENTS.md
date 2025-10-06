# GOVIRALL Contributor Guide

## Standard Commands
- **Setup:** `./scripts/setup.sh`
- **Format:** `ruff format .`
- **Lint:** `ruff check .`
- **Type Check:** `pyright`
- **Tests:** `pytest`
- **Security Scan:** `pip-audit`

## Style Rules
- Prefer explicit imports; avoid wildcard imports.
- Keep functions ≤ 60 lines; break complex logic into helpers.
- FastAPI route handlers should return pydantic-friendly dicts or `Response` objects.
- Tests must avoid mutating `sys.path`; rely on standard imports from project root.

## Git Workflow
- Branch names: `<type>/<short-description>` (e.g., `feat/auth-flow`).
- Commits: Conventional Commits (`type(scope): summary`).
- Every PR must trigger `@codex review` for automated analysis and include human approval before merge.

## Test Data & Redaction
- Use synthetic or anonymized fixtures only; never commit real user data or secrets.
- Remove or mask credentials in logs and documentation.

## Prompting & Completions
- Prompts should state goals, constraints, and success checks succinctly.
- Responses must be technical and cite sources when referencing repository content.
- Avoid filler text; keep focus on actionable guidance.
