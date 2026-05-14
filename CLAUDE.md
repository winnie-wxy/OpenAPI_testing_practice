# CoverG — Project Instructions

## Purpose

Interview preparation project demonstrating senior/lead QA engineering capabilities. Targets the [Restful Booker API](https://restful-booker.herokuapp.com) as a stand-in for Cover Genius XCover insurance API.

## Architecture

```
src/
  api/booking_client.py    — HTTP client wrapping requests.Session (auth via cookie token)
  models/booking.py        — Pydantic models for response schema validation
  utils/data_factory.py    — Randomised test data factory (parallel-safe, no shared state)

tests/
  conftest.py              — Session-scoped fixtures (auth_token, client, unauth_client, created_booking)
  smoke/                   — Health check, auth, basic create (gate for regression)
  regression/              — Full CRUD lifecycle, negative tests, parametrized variations
  contract/                — Pydantic-based response schema validation
  nonfunctional/           — Response time, concurrency, resilience, security smoke

docs/                      — Interview prep docs, test strategy, AI-driven QA approach
postman/                   — Postman collection + environment mirroring pytest tests
```

## Test Categories and Markers

| Marker | Purpose | Run command |
|--------|---------|-------------|
| `smoke` | Quick health + basic CRUD | `pytest -m smoke` |
| `regression` | Full coverage + edge cases | `pytest -m regression` |
| `contract` | Response schema validation | `pytest -m contract` |
| `nonfunctional` | Performance, security, resilience | `pytest -m nonfunctional` |

## Running Tests

```bash
# All tests
pytest

# By marker
pytest -m smoke
pytest -m "regression or contract"
pytest -m nonfunctional

# With parallel execution
pytest -n auto

# Last failed only
pytest --lf

# With reruns for flaky tests
pytest --reruns 2
```

## Environment Configuration

- Config loaded from `.env` via `python-dotenv`
- Override with `--env` flag: `pytest --env=staging`
- Credentials: public test API (`admin` / `password123`)

## CI Pipeline

`.github/workflows/tests.yml` — Three-stage pipeline:
1. **Smoke** — gates everything, runs first
2. **Regression** — runs after smoke passes (includes contract tests)
3. **Non-functional** — runs after regression passes

Features: pip caching, parallel execution (`pytest-xdist`), flake management (`pytest-rerunfailures`), JUnit XML reports, test result PR comments.

## Coding Conventions

- **Class-based tests** — group related tests in classes with descriptive docstrings
- **Fixture injection** — no hardcoded URLs or credentials in test files
- **Data factory** — all test data via `build_booking_payload()`, never hardcoded
- **Yield fixtures** — created resources are cleaned up via teardown
- **Parametrize** — use `pytest.mark.parametrize` with `ids` for data-driven tests
- **Assertions** — one logical assertion per test, descriptive failure messages where needed

## Commit Conventions

- Imperative mood: "Add X", "Fix Y", "Update Z"
- Reference task context in commit body when relevant
- Separate concerns: one logical change per commit
