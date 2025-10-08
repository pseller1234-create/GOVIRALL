# Repository Agent Guidelines

## Scope
These rules apply to the entire repository unless a subdirectory defines its own `AGENTS.md`.

## Standard Commands
- **Install / setup:** `./scripts/setup.sh`
- **Run development server:** `uvicorn main:app --reload`
- **Run tests:** `pytest`
- **Type check:** `mypy .`
- **Lint / format:** `ruff check .` and `ruff format .`
- **Security scan:** `bandit -r .`

Always execute commands from the repository root. Document any deviations in the pull request.

## Style & Code Conventions
- Python code must comply with Ruff defaults and use type hints for all public functions.
- Maintain FastAPI route handlers with descriptive docstrings.
- Keep configuration and secrets in environment variables; never hard-code secrets.
- Use data classes or typed dictionaries when returning structured JSON.

## Commit & Branch Policy
- Follow Conventional Commits (e.g., `feat: add score calibration endpoint`).
- Branches should be named `feature/<description>` or `chore/<description>`.
- Rebase on `main` before opening a pull request.
- Every pull request must include a changelog entry under `/academy/release-notes`.

## Review Gates
- CI must run tests, lint, type checks, formatting validation, and security scan before merge.
- Human review is mandatory; no auto-merges.
- Trigger automated review bots with `@codex review` in the pull request discussion.

## Test Data & Redaction
- Use anonymized synthetic data for tests and demos.
- Redact any PII or API tokens from logs, fixtures, and documentation.

## Prompt Patterns & Completion Constraints
- Prompts to Codex/LLMs should specify security posture, response schema, and word limits.
- Require deterministic JSON outputs when integrating LLM calls into the product.

