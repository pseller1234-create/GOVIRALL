# Repository Operations Guide

## Standard Commands
- **Install / Setup**: `./scripts/setup.sh`
- **Format**: `ruff format .`
- **Lint**: `ruff check .`
- **Type Check**: `mypy .`
- **Test**: `pytest`
- **Security Scan**: `bandit -r .`
- **License Compliance**: `pip-licenses`

Always run tests after making changes. Lint, type check, and security scans are required before requesting review.

## Style Rules
- Python must follow PEP 8, prefer `ruff` for enforcement.
- Keep functions small and pure when possible; avoid side effects in module scope.
- Markdown should use ATX headings, wrap at ~100 characters, and keep tables GitHub-compatible.
- Do not add try/except around imports solely to suppress errors.

## Commit & Branching Conventions
- Use Conventional Commit messages (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
- Branches should be kebab-case, prefixed with the workstream when relevant (e.g., `feature/api-auth`).
- Rebase on the default branch before opening a PR; avoid merge commits in feature branches.

## Review Gates
- Push code only after all mandatory checks (format, lint, type, test, security, license) pass locally.
- On every PR, comment `@codex review` to trigger automated analysis. Human approval is required before merge.

## Test Data & Redaction
- Use synthetic or anonymized data in fixtures and examples.
- Redact or mask any user-generated or sensitive data before committing.
- Secrets must reside in environment variables or `.env.local`; never commit secrets.

## Prompting & Completion Constraints
- Prompts should clearly state requirements, expected outputs, and validation steps.
- Responses must be succinct, technical, and cite sources when referencing repository content.
- Avoid filler language; focus on actionable guidance and reproducibility.
