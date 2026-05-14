# Test Records Management & CI Results

How test execution records are captured, stored, and used for decision-making.

---

## JUnit XML as Machine-Readable Records

Every CI run generates JUnit XML reports:

```bash
pytest --junitxml=reports/smoke-results.xml -m smoke
pytest --junitxml=reports/regression-results.xml -m "regression or contract"
pytest --junitxml=reports/nonfunctional-results.xml -m nonfunctional
```

**What JUnit XML captures:**
- Test name and class
- Pass/fail/skip/error status
- Execution time per test
- Failure message and traceback
- Rerun attempts (with `pytest-rerunfailures`)

## Test Execution History

CI artifacts preserve test records per build:

```
Build #42
  ├── reports/smoke-results.xml
  ├── reports/regression-results.xml
  ├── reports/nonfunctional-results.xml
  ├── reports/smoke.html          (human-readable)
  ├── reports/regression.html
  └── reports/nonfunctional.html
```

**Artifact retention:** GitHub Actions default is 90 days. Extend for compliance if needed.

## Mapping Results to Requirements

Using the traceability matrix from `test-design-spec.md`:

```
REQ-001 (Health check)
  └── TS-001 (test_ping_returns_201)
      └── smoke-results.xml → PASSED (0.45s)

REQ-011 (Auth enforcement)
  └── TS-008 (test_update_without_auth_returns_403)
      └── regression-results.xml → PASSED (1.2s)
  └── TS-009 (test_delete_without_auth_returns_403)
      └── regression-results.xml → PASSED (0.9s)
```

**For Jira integration:** Parse JUnit XML and post results as comments on requirement tickets. Pattern:
```
Jira Ticket → Test Card (Verifies link) → CI Job → JUnit XML → Pass/Fail
```

## Pass/Fail Trend Tracking

### Manual Approach (Small Teams)

Track per-release results in a simple table:

| Release | Smoke | Regression | Contract | Non-Functional | Total | Pass Rate |
|---------|-------|------------|----------|----------------|-------|-----------|
| v1.0.0 | 6/6 | 15/15 | 3/3 | 14/14 | 38/38 | 100% |
| v1.1.0 | 6/6 | 15/15 | 3/3 | 13/14 | 37/38 | 97.4% |

### Automated Approach (Scale)

Use `dorny/test-reporter` or `EnricoMi/publish-unit-test-result-action` in CI to:
- Generate test result summaries in GitHub Actions job summaries
- Post test result comments on PRs
- Track trends via GitHub Actions dashboard

## Flake Rate Tracking

With `pytest-rerunfailures`, track which tests need reruns:

```
# JUnit XML shows rerun information:
<testcase name="test_concurrent_booking_creation" time="3.2">
  <rerun message="ConnectionError">...</rerun>  <!-- first attempt failed -->
</testcase>
```

**Metrics to track:**
- **Rerun rate**: % of tests that needed at least one rerun per build
- **Chronic flakeys**: tests that rerun in >10% of builds → needs fixing
- **Rerun success rate**: % of rerun attempts that eventually pass

**Decision threshold:** If a test reruns in >20% of builds, it's not a transient failure — it's a bug in the test or the system.

## CI Pipeline Structure

```
┌─────────┐     ┌────────────┐     ┌───────────────┐
│  Smoke  │────▶│ Regression │────▶│ Non-Functional│
│  (gate) │     │ + Contract │     │               │
└─────────┘     └────────────┘     └───────────────┘
     │                │                    │
     ▼                ▼                    ▼
  smoke-          regression-         nonfunctional-
  results.xml     results.xml         results.xml
     │                │                    │
     └────────────────┴────────────────────┘
                      │
                      ▼
              Test Reporter Action
              (PR comment + badge)
```

## Exit Criteria for Releases

| Criterion | Threshold | Measured By |
|-----------|-----------|-------------|
| Smoke pass rate | 100% | smoke-results.xml |
| Regression pass rate | 100% | regression-results.xml |
| Non-functional pass rate | 95% (allow P95 timing variance) | nonfunctional-results.xml |
| Flake rate | < 5% rerun rate | Rerun counts in XML |
| No new P1 failures | 0 new failures vs previous release | Diff of XML reports |
