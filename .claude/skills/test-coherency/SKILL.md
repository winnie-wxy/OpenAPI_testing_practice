---
name: test-coherency
description: Run structural and semantic coherency checks on the test coverage matrix
---

# Test Coherency Check

Run a full coherency analysis of the test suite against the coverage matrix.

## Phase 1 — Structural Check (Automated)

Run the structural checker:

```bash
python tools/coherency_check.py
```

Report the output to the user. If there are errors, these must be fixed before proceeding.

## Phase 2 — Semantic Review (AI-Assisted)

Read the coverage matrix (`coverage/matrix.yaml`) and the actual test files. Check for:

### 2a. Assertion Quality
For each requirement marked "covered", read the test function and verify:
- The test actually validates the requirement intent (not just calling the endpoint)
- Assertions are specific enough that a broken feature would fail the test
- Flag tests where `assert response.status_code == 200` is the only assertion for a data requirement

### 2b. Negative Case Coverage
For each P1 requirement, check whether negative/failure scenarios exist:
- Auth requirements: test both valid AND invalid credentials
- CRUD operations: test both success AND missing/invalid resource
- Input validation: test both valid AND malformed input
- Flag P1 requirements with only happy-path coverage

### 2c. Non-Functional Alignment
For performance/security requirements, verify:
- Response time tests use statistical approach (P95 over multiple samples), not single-sample
- Concurrency tests assert on error rates, not just "no exception"
- Security tests check for specific failure modes (not just "didn't crash")

### 2d. Contract Drift Detection
Compare `src/models/booking.py` (Pydantic models) against what the tests assert:
- Are there fields in the Pydantic model that no test checks?
- Are there fields tests assert on that aren't in the model?
- Does the live API return fields not in the model? (run a quick GET to check)

### 2e. Fixture and Data Isolation
Check test files for anti-patterns:
- Module-level mutable state (global variables holding IDs)
- Tests that depend on execution order
- Hardcoded booking IDs or URLs (should use fixtures/factory)
- Missing cleanup (create without delete in teardown)

## Phase 3 — Report

Present findings as a structured report:

```
COHERENCY REPORT
================

Structural: X errors, Y warnings
Semantic:   A issues found

--- STRUCTURAL ---
[list from Phase 1]

--- SEMANTIC ISSUES ---
[severity] [check] file:line — description

--- COVERAGE SUMMARY ---
Total requirements: N
  Covered: X (Y%)
  Gaps: Z
  P1 gaps: W (list them)

--- RECOMMENDATIONS ---
1. [highest priority action]
2. [next action]
...
```

## Phase 4 — Fix (If Requested)

If the user asks to fix issues:
1. Fix structural issues first (missing files, wrong markers)
2. Update `coverage/matrix.yaml` to reflect current state
3. Add missing negative test cases for P1 requirements
4. Re-run `python tools/coherency_check.py` to verify fixes

IMPORTANT: Always re-run the structural check after any fix to confirm no regressions.
