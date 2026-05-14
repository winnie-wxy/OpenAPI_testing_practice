# Test Coherency Check System

A two-layer verification system that ensures test coverage stays aligned with requirements — catching gaps, drift, and anti-patterns before they reach production.

## Problem It Solves

Test suites drift from requirements silently:
- A new requirement gets added to Jira → nobody writes a test → ships untested
- An API field gets renamed → test still passes (asserts on status code only) → false confidence
- A test file gets orphaned → runs in CI but covers nothing meaningful → wasted CI time
- A P1 security requirement has only happy-path testing → risk gap invisible

Without a central traceability matrix and automated checking, these gaps accumulate until a production incident reveals them.

## Architecture

```
coverage/matrix.yaml          ← single source of truth (requirement → test → CI job)
        │
        ▼
tools/coherency_check.py      ← Layer 1: structural checks (automated, fast, deterministic)
        │
        ▼
.claude/skills/test-coherency  ← Layer 2: semantic checks (AI-assisted, deeper, contextual)
        │
        ▼
.github/workflows/tests.yml   ← CI gate: runs on every PR, blocks on errors
```

## Layer 1: Structural Checks

Automated Python script that parses the coverage matrix and validates against the filesystem.

```bash
python tools/coherency_check.py              # human-readable report
python tools/coherency_check.py --format json # machine-readable for CI
python tools/coherency_check.py --strict      # exit 1 on any violation
```

### Checks Performed

| Check | What It Catches | Severity |
|-------|----------------|----------|
| `covered_without_tests` | Requirement marked "covered" but no tests listed | Error |
| `missing_test_file` | Matrix references a file that doesn't exist on disk | Error |
| `missing_test_function` | Matrix references a function not found in the file | Error |
| `orphaned_test` | Test file exists but isn't tracked in the matrix | Warning |
| `marker_mismatch` | Test's `@pytest.mark` doesn't match its CI job | Warning |
| `p1_gap` | P1 requirement with no test coverage | Warning |

### Example Output

```
============================================================
TEST COHERENCY CHECK
============================================================

Requirements: 30 total, 25 covered, 5 gaps
Test mappings: 39
Violations: 0 errors, 3 warnings

--- WARNINGS (3) ---
  [p1_gap] P1 requirement 'GAP-001' has no test coverage: Webhook delivery
  [p1_gap] P1 requirement 'GAP-002' has no test coverage: Idempotency
  [p1_gap] P1 requirement 'GAP-004' has no test coverage: Multi-tenant isolation

--- KNOWN GAPS (5) ---
  [P1] GAP-001: Webhook delivery for booking status changes
       Note: API does not support webhooks — future feature
  [P2] GAP-003: Rate limiting for excessive API requests
       Note: No rate limiting headers observed
============================================================
```

## Layer 2: Semantic Checks (AI-Assisted)

Invoked via `/test-coherency` Claude Code skill. Reads actual test code and validates:

### Assertion Quality
- Does the test actually validate the requirement intent?
- Would a broken feature still pass this test?
- Flag tests where `assert response.status_code == 200` is the only assertion

### Negative Case Coverage
- P1 auth requirements: both valid AND invalid credentials tested?
- CRUD operations: both success AND missing resource?
- Input validation: both valid AND malformed input?

### Contract Drift Detection
- Compare Pydantic models against live API response shape
- Flag fields in the model that no test checks
- Flag fields tests assert on that aren't in the model

### Data Isolation Anti-Patterns
- Module-level mutable state
- Tests depending on execution order
- Hardcoded booking IDs
- Missing cleanup in teardown

## Coverage Matrix Format

```yaml
# coverage/matrix.yaml
requirements:
  REQ-001:
    description: "Health check endpoint returns status 201"
    priority: P1
    tests:
      - file: tests/smoke/test_health.py
        function: TestHealthCheck::test_ping_returns_201
        ci_job: smoke
    status: covered  # covered | gap | partial | stale

  GAP-001:
    description: "Webhook delivery for booking status changes"
    priority: P1
    tests: []
    status: gap
    notes: "API does not support webhooks — future feature"
```

**Status values:**
- `covered` — requirement has passing tests
- `gap` — requirement exists but no test covers it
- `partial` — some scenarios tested, others missing
- `stale` — test exists but may not reflect current API behavior

## CI Integration

The coherency check runs as a parallel job in the CI pipeline:

```yaml
coherency:
  name: Coherency Check
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - run: pip install pyyaml
    - run: python tools/coherency_check.py
    - run: python tools/coherency_check.py --format json > reports/coherency.json
```

Runs on every PR. Errors block merge. Warnings are visible in the artifact.

## Workflow: When to Update the Matrix

| Event | Action |
|-------|--------|
| New test file added | Add entries to `coverage/matrix.yaml` |
| Test file deleted | Remove entries from matrix |
| New requirement identified | Add requirement with `status: gap` |
| Requirement implemented | Update status to `covered`, add test references |
| API contract changes | Run `/test-coherency` to detect drift |
| Before release | Run full coherency check, review all gaps |

## Scaling This Pattern

For a multi-repo platform, the coverage matrix becomes the central coordination point:

```
test-hub/
  coverage/
    matrix.yaml                 # cross-repo requirements
    backend-api.yaml            # backend-specific requirements
    frontend-viewer.yaml        # frontend-specific requirements
  tools/
    coherency_check.py          # checks all matrices
    staleness_check.py          # detects API changes that affect tests
    gap_report.py               # aggregates gaps across repos
```

Each component repo can have its own matrix, while the hub tracks cross-cutting requirements. The coherency checker validates both local and cross-repo traceability.
