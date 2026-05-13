# REST API Test Suite — Restful Booker

Pytest-based API test suite for the [Restful Booker API](https://restful-booker.herokuapp.com), demonstrating production-grade REST API testing patterns.

## Architecture

```
├── src/
│   ├── api/
│   │   └── booking_client.py    # API client — tests never call requests directly
│   ├── models/
│   │   └── booking.py           # Pydantic response models (schema contracts)
│   └── utils/
│       └── data_factory.py      # Randomised test data — parallel-safe, no shared state
├── tests/
│   ├── conftest.py              # Session-scoped fixtures (auth token, clients)
│   ├── smoke/                   # Is the API alive? Basic CRUD works?
│   ├── regression/              # Full coverage: parametrize, negative, lifecycle
│   └── contract/                # Response schema validation via Pydantic
├── .github/workflows/tests.yml  # CI: smoke gates regression
└── pytest.ini                   # Markers, default options
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| API client class (`BookingClient`) | Single point of change if endpoints move. Tests read as business intent, not HTTP plumbing. |
| Pydantic schema validation | Catches field additions/removals/renames. Stronger than `assert key in dict`. |
| Session-scoped auth fixture | Authenticates once, reuses token across all tests. Avoids redundant `/auth` calls. |
| Data factory with randomisation | Each test gets unique data — no shared state, safe for parallel execution. |
| Marker-based test categories | `pytest -m smoke` for quick checks, full suite for regression. CI gates on smoke first. |
| Parametrize over copy-paste | One test function covers many input variations — easier to maintain and extend. |

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
# All tests
pytest

# By category
pytest -m smoke
pytest -m regression
pytest -m contract

# With HTML report
pytest --html=reports/report.html --self-contained-html
```

## CI/CD

GitHub Actions workflow runs on push/PR to `main`:
1. **Smoke** — health check + basic CRUD (fast feedback gate)
2. **Regression** — full suite including contracts (runs only if smoke passes)

Both jobs upload HTML reports as artifacts.

## Test Coverage

| Category | Tests | What It Proves |
|----------|-------|----------------|
| Smoke | 6 | API is alive, auth works, basic create/read |
| Regression | 11 | CRUD lifecycle, negative cases (no auth, bad data, 404), parametrised data variations |
| Contract | 3 | Response shapes match Pydantic models |
| **Total** | **23** | |
