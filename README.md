# REST API Test Suite — Restful Booker

![API Tests](https://github.com/yourusername/CoverG/actions/workflows/tests.yml/badge.svg)

Pytest-based API test suite for the [Restful Booker API](https://restful-booker.herokuapp.com), demonstrating production-grade REST API testing patterns including non-functional testing, CI/CD with parallel execution and flake management, and AI-driven QA workflows.

## Architecture

```
├── src/
│   ├── api/
│   │   └── booking_client.py       # API client — tests never call requests directly
│   ├── models/
│   │   └── booking.py              # Pydantic response models (schema contracts)
│   └── utils/
│       └── data_factory.py         # Randomised test data — parallel-safe, no shared state
├── tests/
│   ├── conftest.py                 # Session fixtures, yield cleanup, env config
│   ├── smoke/                      # Health check, auth, basic CRUD
│   ├── regression/                 # Lifecycle, negative tests, parametrize, flaky fix demos
│   ├── contract/                   # Pydantic schema validation
│   └── nonfunctional/              # Performance, concurrency, resilience, security
├── postman/                        # Postman collection + environment
├── docs/                           # Interview prep, test strategy, AI-driven QA
├── .github/workflows/tests.yml     # 3-stage CI: smoke → regression → nonfunctional
├── .env.example                    # Environment configuration template
└── pytest.ini                      # Markers, strict-markers, timeout
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| API client class (`BookingClient`) | Single point of change if endpoints move. Tests read as business intent. |
| Pydantic schema validation | Catches field additions/removals/renames. Stronger than `assert key in dict`. |
| Session-scoped auth fixture | Authenticates once, reuses token across all tests. |
| Data factory with randomisation | Each test gets unique data — safe for parallel execution. |
| Yield fixtures with cleanup | Created resources are deleted in teardown, regardless of test outcome. |
| Marker-based test categories | `pytest -m smoke` for quick checks, staged CI gates on smoke first. |
| Environment configuration | `.env` files with `--env` flag for multi-environment support. |
| Statistical performance assertions | P95 over multiple samples instead of single-request thresholds. |

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Running Tests

```bash
# All tests
pytest

# By category
pytest -m smoke
pytest -m regression
pytest -m contract
pytest -m nonfunctional

# Parallel execution
pytest -n auto

# With reruns for flaky tests
pytest --reruns 2

# Last failed only (fast debugging)
pytest --lf

# Target specific environment
pytest --env=staging -m smoke

# With HTML report
pytest --html=reports/report.html --self-contained-html

# JUnit XML for CI
pytest --junitxml=reports/results.xml
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/tests.yml`) runs on push/PR to `main`:

```
Smoke (gate) → Regression + Contract → Non-Functional → Test Results Summary
```

**Features:**
- Parallel execution via `pytest-xdist` (`-n auto`)
- Flake management via `pytest-rerunfailures` (`--reruns 2`)
- Test timeout enforcement (`--timeout=30`)
- Strict marker validation (`--strict-markers`)
- Pip caching for faster builds
- JUnit XML + HTML report artifacts
- PR comments with test result summaries (`dorny/test-reporter`, `EnricoMi/publish-unit-test-result-action`)

## Test Coverage

| Category | Tests | What It Covers |
|----------|-------|----------------|
| Smoke | 6 | API health, auth (valid/invalid), basic create/read |
| Regression | 15 | CRUD lifecycle, auth enforcement, negative validation, parametrised variations, flaky fix demos |
| Contract | 3 | Response shapes match Pydantic models |
| Non-Functional | 14 | Response time P95, concurrent requests, resilience, security smoke |
| **Total** | **41** | |

## Postman Collection

`postman/` contains a collection and environment file mirroring the pytest tests:

1. Import both files into Postman
2. Select the "Restful Booker - Dev" environment
3. Run "Auth - Create Token" first (populates `{{token}}` variable)
4. Run the collection or individual requests

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/pytest-interview-prep.md`](docs/pytest-interview-prep.md) | Core concepts, top 20 Q&A, senior patterns |
| [`docs/test-design-spec.md`](docs/test-design-spec.md) | Requirements → test spec → traceability matrix |
| [`docs/ai-driven-qa-strategy.md`](docs/ai-driven-qa-strategy.md) | AI across QA lifecycle, tool evaluation, prompt playbook |
| [`docs/test-data-strategy.md`](docs/test-data-strategy.md) | Factory pattern, data lifecycle, cleanup strategies |
| [`docs/test-records-management.md`](docs/test-records-management.md) | JUnit XML records, flake tracking, exit criteria |

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `requests` | HTTP client |
| `pydantic` | Response schema validation |
| `python-dotenv` | Environment configuration |
| `pytest-xdist` | Parallel execution |
| `pytest-rerunfailures` | Transient failure retry |
| `pytest-timeout` | Hung test prevention |
| `pytest-html` | HTML report generation |
