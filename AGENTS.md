# GOVIRALL Agent Handbook

These standards apply to the entire repository.

## Environment & Tooling
- Bootstrap the project with `./scripts/setup.sh`. It pins Python to 3.11.9, creates `.venv`, and installs runtime plus developer dependencies.
- Always work inside the virtual environment: `source .venv/bin/activate`.
- Secrets (API keys, tokens) must be loaded from environment variables or `.env.local` files that are git-ignored. Never paste secrets into prompts, code, or logs.
- Network access is disabled by default. Only enable specific domains when explicitly approved by Legal/SecOps.

## Standard Commands
Run these from the repository root with the virtual environment activated.

| Purpose | Command |
| --- | --- |
| Setup | `./scripts/setup.sh` |
| Serve (local build) | `uvicorn main:app --reload --host 0.0.0.0 --port 8000` |
| Tests | `pytest` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Type check | `mypy --strict main.py` |
| Security scan | `bandit -r .` |
| Dependency audit | `pip-audit` |
| License compliance | `pip-licenses --format=markdown` |

## Style & Implementation Rules
- Python code must follow Ruff's default style plus `ruff format` output. Use type hints for all new functions.
- Favor small, pure functions. Avoid side effects in module scope other than FastAPI app wiring.
- Validate and sanitize all external inputs. Return structured errors via FastAPI `HTTPException`.
- Keep docstrings concise and technical.
- Do not wrap imports in `try/except` blocks.

## Testing Expectations
- Add unit tests with `pytest` for new logic paths.
- Prefer `pytest-asyncio` for async endpoints.
- Ensure mocked external services cover success and failure flows.
- Tests must not call real third-party APIs. Use fixtures or VCR-style cassettes with redacted data.

## Commit & Branching Conventions
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.).
- Branch name format: `<type>/<short-description>` (e.g., `feat/score-normalization`).
- Rebase onto `main` before opening a PR. No merge commits in feature branches.

## Review Gates
A pull request is ready for review only when all of the following succeed locally and/or in CI:
1. `pytest`
2. `ruff check .`
3. `ruff format --check .`
4. `mypy --strict main.py`
5. `bandit -r .`
6. `pip-audit`
7. `pip-licenses --format=plain` (attach output to PR if new dependencies are introduced)

After pushing, comment `@codex review` on the PR to trigger automated analysis. Human review and approval are mandatory prior to merge.

## Data & Redaction Policy
- Never commit customer, PII, or credential data. Use anonymized, synthetic fixtures.
- Truncate logs to exclude payloads containing sensitive tokens or user content beyond 2 sentences.
- Delete temporary artifacts after tests complete.

## Prompting Patterns & Completion Constraints
- Prompts to Codex/ChatGPT should include: goal, context, constraints, and validation steps.
- Responses must be succinct, technical, and include citations when referencing repo files or commands.
- Avoid speculative features without product sign-off. Mark assumptions explicitly.
- Enforce JSON-only responses when downstream automation requires machine-readable output.

