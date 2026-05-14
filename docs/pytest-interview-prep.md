# Pytest Interview Prep Guide

Focused on senior/lead-level concepts demonstrated in this project.

---

## Core Concepts

### Fixtures

**Scope hierarchy:** `function` (default) → `class` → `module` → `package` → `session`

```python
# Session-scoped: one auth call for entire test run (this project's conftest.py)
@pytest.fixture(scope="session")
def auth_token(base_url):
    client = BookingClient(base_url)
    response = client.create_token(username, password)
    return response.json()["token"]

# Function-scoped yield fixture: cleanup after each test
@pytest.fixture
def created_booking(client):
    payload = build_booking_payload()
    booking_id = client.create_booking(payload).json()["bookingid"]
    yield booking_id, payload
    client.delete_booking(booking_id)  # teardown
```

**Fixture factories** — when you need parameterized setup:
```python
@pytest.fixture
def make_booking(client):
    """Factory fixture — returns a callable that creates bookings."""
    created_ids = []
    def _make(**overrides):
        payload = build_booking_payload(**overrides)
        booking_id = client.create_booking(payload).json()["bookingid"]
        created_ids.append(booking_id)
        return booking_id, payload
    yield _make
    for bid in created_ids:
        client.delete_booking(bid)
```

**conftest.py hierarchy:** pytest discovers `conftest.py` at each directory level. Fixtures in parent directories are available to child tests. This project uses a single root `tests/conftest.py` for shared fixtures.

### Markers

```python
@pytest.mark.smoke        # test categorisation
@pytest.mark.regression
@pytest.mark.parametrize  # data-driven tests
@pytest.mark.skip(reason="known API limitation")
@pytest.mark.xfail(reason="API returns 500 for empty payload")
```

**`--strict-markers`** in `pytest.ini` catches typos in marker names at collection time.

### Parametrize

```python
# Basic
@pytest.mark.parametrize("depositpaid", [True, False], ids=["paid", "unpaid"])

# Stacked — generates cartesian product
@pytest.mark.parametrize("firstname", ["Alice", "Bob"])
@pytest.mark.parametrize("totalprice", [0, 100, 999])
# → 6 test cases

# With pytest.param for selective xfail
@pytest.mark.parametrize("payload,expected", [
    pytest.param({}, 400, id="empty"),
    pytest.param({"firstname": "Only"}, 400, id="missing_fields"),
    pytest.param(build_booking_payload(), 200, id="valid"),
])

# Indirect — pass params through fixture
@pytest.mark.parametrize("booking_type", ["standard", "premium"], indirect=True)
def test_booking(booking_type):
    ...
```

### Hooks

```python
# conftest.py
def pytest_addoption(parser):
    """Add CLI flags — this project adds --env for environment selection."""
    parser.addoption("--env", default="dev", choices=["dev", "staging", "prod"])

def pytest_collection_modifyitems(config, items):
    """Modify collected tests — e.g., auto-skip slow tests in CI."""
    if config.getoption("--quick"):
        skip_slow = pytest.mark.skip(reason="--quick mode")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
```

### Plugins Used in This Project

| Plugin | Purpose | CLI flag |
|--------|---------|----------|
| `pytest-xdist` | Parallel execution | `-n auto` |
| `pytest-rerunfailures` | Retry transient failures | `--reruns 2` |
| `pytest-timeout` | Kill hung tests | `--timeout=30` |
| `pytest-html` | HTML report generation | `--html=report.html` |

---

## Top 20 Interview Q&A

### Conceptual

**Q1: What's the difference between fixtures and setup/teardown methods?**
Fixtures are dependency-injected, composable, and scoped. `setUp`/`tearDown` are class-bound and run for every test. Fixtures can be shared across files via `conftest.py` without imports, and yield fixtures handle both setup and teardown in one function.

**Q2: When would you use session-scoped vs function-scoped fixtures?**
Session-scoped for expensive, shared resources (auth tokens, DB connections). Function-scoped for test-specific data that needs isolation. In this project, `auth_token` is session-scoped (one API call), while `created_booking` is function-scoped (isolated data per test with cleanup).

**Q3: How does conftest.py work? Can you have multiple?**
Pytest discovers `conftest.py` at each directory level during collection. Fixtures and hooks in parent `conftest.py` are available to all child directories. You can have multiple — each directory can have its own. No import needed.

**Q4: What's the difference between `parametrize` and fixture parameterization?**
`parametrize` decorates the test function with test data. Fixture parameterization (`@pytest.fixture(params=[...])`) makes the fixture itself run multiple times, which is useful when the setup varies, not just the assertion.

**Q5: Explain `pytest.mark.xfail` vs `pytest.mark.skip`.**
`skip` — never runs the test. `xfail` — runs the test but expects failure. `xfail(strict=True)` fails the build if the test unexpectedly passes (useful for tracking when bugs get fixed).

### Practical

**Q6: How do you handle test data isolation in API tests?**
Factory pattern with randomised data (`data_factory.py`). Each test generates unique data, no shared state. Yield fixtures handle cleanup. This project's `build_booking_payload()` generates random names/prices so tests never conflict, even in parallel.

**Q7: How do you deal with flaky tests?**
Three strategies: (1) identify the root cause — usually shared state, timing, or external dependency; (2) add retry logic for eventual consistency; (3) use `pytest-rerunfailures` as a safety net in CI. This project demonstrates all three in `test_booking_flaky.py`.

**Q8: How would you structure an API test suite for a large service?**
Layered approach: smoke (health + basic CRUD, gates everything) → regression (full coverage) → contract (schema validation) → non-functional (performance, security). This project uses exactly this structure with separate CI jobs.

**Q9: How do you run tests in parallel? What are the gotchas?**
`pytest-xdist` with `-n auto`. Gotchas: shared state (global variables, DB records), test ordering dependencies, fixture scope (session fixtures run once per worker, not once total). Solution: isolated data, factory pattern, no global mutable state.

**Q10: How do you integrate pytest with CI/CD?**
JUnit XML for machine-readable results (`--junitxml`), HTML reports as artifacts, test categorisation with markers for staged execution, `--reruns` for transient failures, `--strict-markers` to catch misconfigurations. This project's GHA workflow demonstrates all of these.

### Architecture

**Q11: How do you decide what to test at which level (unit/integration/E2E)?**
Test pyramid: most tests at unit level (fast, isolated), fewer integration tests (real HTTP calls), fewest E2E tests (full flows). For API testing, "integration" is the sweet spot — real HTTP calls but isolated test data. This project is primarily integration-level.

**Q12: How would you implement contract testing?**
This project uses Pydantic models as consumer contracts. The response body is validated against a strict schema. If the API adds/removes/renames a field, the Pydantic model raises `ValidationError`. For multi-service systems, consider Pact for provider verification.

**Q13: How do you handle auth in test suites?**
Session-scoped fixture that authenticates once and shares the token. Separate `unauth_client` fixture for testing unauthorized access. Never hardcode credentials in test files — load from env vars or secrets manager.

**Q14: What's your approach to test data management?**
Factory pattern (randomised, isolated), yield fixtures for lifecycle management (create → use → cleanup), no cross-test data dependencies. For stateful APIs, each test creates and cleans up its own data.

**Q15: How do you handle non-deterministic APIs in tests?**
Retry/poll for eventual consistency, statistical assertions (P95 over multiple samples instead of single-request thresholds), `pytest.approx()` for floating-point comparisons, `xfail` for known unstable behaviours.

### CI/CD & Debugging

**Q16: A test passes locally but fails in CI. How do you debug?**
Check: (1) environment differences (Python version, OS, network latency); (2) test ordering — run with `--randomly-seed` or `-p no:randomly`; (3) timing — CI runners are slower; (4) parallel interference — run with `-n auto` locally; (5) check `--junitxml` output for patterns.

**Q17: How do you track flake rate?**
JUnit XML artifacts + `--reruns` statistics. Compare rerun counts across builds. If a test consistently needs reruns, it's flaky and needs fixing, not more reruns.

**Q18: How do you run only failed tests from the last run?**
`pytest --lf` (last failed) or `pytest --ff` (failed first). Pytest stores results in `.pytest_cache/`. Extremely useful for iterating on fixes.

**Q19: How do you prevent test suite degradation over time?**
`--strict-markers` (no unregistered markers), `--timeout` (no hung tests), code review for test quality, flake tracking, periodic test audit, enforced cleanup in fixtures.

**Q20: How would you implement performance testing in pytest?**
This project demonstrates the approach: multiple samples per endpoint, statistical aggregation (P95), threshold assertions. For load testing at scale, use a dedicated tool (Locust, k6) and keep pytest for functional performance validation.

---

## Junior vs Senior Patterns

| Area | Junior | Senior |
|------|--------|--------|
| Test data | Hardcoded values | Factory pattern with randomisation |
| Auth | Credentials in test files | Environment variables, session fixture |
| Cleanup | None / manual | Yield fixtures with teardown |
| Assertions | Multiple unrelated asserts | One logical assertion per test |
| Flaky tests | `@pytest.mark.skip` + TODO | Root cause analysis, retry logic |
| CI | Run all tests, hope for the best | Staged pipeline, markers, reruns |
| Response time | `assert elapsed < 500` | Multi-sample P95 with tolerance |
| Shared state | Module-level globals | Per-test fixture isolation |
| Test structure | Flat file, no organisation | Layered: smoke → regression → contract |
| Reporting | Print statements | JUnit XML, HTML reports, CI artifacts |

---

## Advanced Patterns

### Custom Plugin

```python
# conftest.py or standalone plugin
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary to test output."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    print(f"\n=== Custom Summary: {passed} passed, {failed} failed ===")
```

### Dynamic Test Generation

```python
def pytest_generate_tests(metafunc):
    """Generate test cases from external data source."""
    if "api_endpoint" in metafunc.fixturenames:
        endpoints = load_endpoints_from_openapi_spec()
        metafunc.parametrize("api_endpoint", endpoints)
```

### Fixture Parameterization

```python
@pytest.fixture(params=["dev", "staging"], ids=["dev-env", "staging-env"])
def target_env(request):
    """Run the same tests against multiple environments."""
    return ENV_CONFIGS[request.param]
```

---

## "What to Say" — Anchored to This Project

| Topic | What to say |
|-------|-------------|
| Test architecture | "I use a layered approach — smoke gates regression gates non-functional. Each layer has its own CI job and marker." |
| Data management | "Factory pattern with randomised data. Each test is self-contained with yield fixture cleanup. No shared state across tests." |
| Flaky tests | "I identify root cause — usually shared state, timing, or external dependency. I demonstrated this in the project by intentionally introducing flaky patterns, then fixing each one." |
| CI/CD | "Staged pipeline with parallel execution, flake management via reruns, JUnit XML for tracking, and pip caching for speed." |
| Contract testing | "Pydantic models as response contracts. If the API shape changes, tests catch it at collection time." |
| Non-functional | "Performance: multi-sample P95. Security: injection payloads, auth bypass. Concurrency: ThreadPoolExecutor with 5xx detection." |
| AI in QA | "I use Claude Code for test generation, test plan authoring from requirements, and custom skills for Jira integration. The key is human review — AI accelerates, humans validate." |
