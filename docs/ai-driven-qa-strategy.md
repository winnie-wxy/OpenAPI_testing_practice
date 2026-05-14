# AI-Driven QA Strategy

How AI tools accelerate each phase of the QA lifecycle, with practical examples from this project.

---

## AI Across the QA Lifecycle

### 1. Requirements Analysis

**What AI does:** Parse Jira Epics, Confluence HLD/LLD, and design docs. Extract testable requirements, identify gaps, and flag ambiguities.

**Example workflow:**
```
Input:  Jira Epic "XCover Booking Protection Lifecycle"
Prompt: "Analyse this epic and extract all testable requirements.
         Flag any requirements that are ambiguous or missing acceptance criteria."
Output: Structured requirement table with REQ-IDs, priorities, and gap flags
```

**This project demonstrates:** The `test-design-spec.md` was generated from a fictional requirement set, showing how AI derives test scenarios from requirements with traceability IDs.

### 2. Test Design & Spec Generation

**What AI does:** Generate test scenarios from requirements, ensuring coverage of positive/negative/edge cases. Apply risk-based prioritisation.

**Example prompt:**
```
Given these requirements for a booking API:
- REQ-004: Authenticated partners can create bookings
- REQ-011: Unauthenticated requests return 403

Generate test scenarios covering:
1. Happy path (valid create)
2. Auth enforcement (no token, expired token, invalid token)
3. Edge cases (unicode names, zero price, max-length strings)
4. Negative (empty payload, missing fields, wrong types)
```

**What the human does:** Validate coverage completeness, adjust risk priorities, add domain-specific edge cases the AI might miss.

### 3. Test Code Generation

**What AI does:** Generate test implementations following existing project patterns (fixture injection, class structure, data factory usage).

**Example prompt:**
```
Using the project's patterns (class-based tests, @pytest.mark.regression,
build_booking_payload() factory, client fixture), implement test scenarios
TS-008 and TS-009 for auth enforcement testing.
```

**Quality gate:** Human reviews generated code for:
- Correct fixture usage
- Proper assertions (not just `assert response.status_code == 200`)
- Data isolation (no shared state)
- Cleanup in teardown

### 4. Test Data Generation

**What AI does:** Generate realistic but safe test data. Randomise to avoid collisions. Handle domain-specific formats (dates, currency, policy numbers).

**This project demonstrates:** `data_factory.py` generates randomised booking data with sensible defaults. Each call produces unique data safe for parallel execution.

### 5. Code Review

**What AI does:** Review test PRs for flaky patterns, missing assertions, improper fixture scoping, data isolation issues.

**Prompt playbook for review:**
```
Review this test file for:
1. Flaky patterns (shared state, timing assertions, order dependency)
2. Missing cleanup/teardown
3. Hardcoded data that should use the factory
4. Assertions that would pass even if the feature is broken
5. CI safety (parallel execution, idempotent setup)
```

### 6. Defect Triage

**What AI does:** Analyse failure logs, correlate with recent code changes, suggest root cause hypotheses.

**Example:**
```
Test test_concurrent_booking_creation failed with:
  AssertionError: 2/10 requests returned 5xx: [500, 500]

Recent changes: Added rate limiting middleware (PR #142)

AI analysis: "The concurrent test sends 10 simultaneous requests.
The new rate limiter may be rejecting requests above the threshold.
Check rate limit config and consider adjusting test concurrency or
adding retry logic for 429 responses."
```

---

## Tool Evaluation Matrix

| Capability | Claude Code | GitHub Copilot | Gemini | ChatGPT |
|-----------|-------------|---------------|--------|---------|
| **Codebase context** | Full repo access, reads any file | IDE context (open files) | Full repo (Gemini Code Assist) | Paste-based |
| **Test generation** | Pattern-aware, uses existing fixtures | Autocomplete-based | Pattern-aware | Prompt-based |
| **Custom workflows** | Skills (reusable prompts) | Limited | Extensions | GPTs |
| **Jira/Confluence** | API integration via skills | No | No | No |
| **CI integration** | Direct (runs in terminal) | GitHub Actions Copilot | No | No |
| **Test plan from requirements** | Yes (with custom skill) | No | Limited | Yes (manual) |
| **Code review** | Yes (understands full context) | PR suggestions | Yes | Manual paste |
| **Best for** | End-to-end QA automation | In-IDE test writing | Large codebase navigation | Ad-hoc analysis |

### When to Use What

- **Claude Code**: Test strategy, test plans, multi-file generation, CI pipeline design, Jira integration
- **Copilot**: In-IDE test completion, quick fixture suggestions, autocomplete during coding
- **ChatGPT/Gemini**: Ad-hoc questions, explaining concepts, generating test data patterns

---

## Prompt Playbook

### Generate Test Plan from Jira Epic

```
Analyse the following Jira Epic and generate a test plan:

Epic: [EPIC-123] Booking Protection Lifecycle
Requirements: [paste or link]

Generate:
1. Test scope and objectives
2. Test scenarios with IDs (TS-XXX) traced to requirements
3. Risk-based priority (P1/P2/P3)
4. Test categories (smoke/regression/contract/nonfunctional)
5. Data requirements
6. Exit criteria
```

### Generate Test Code from Scenario

```
Using the project's existing patterns:
- Class-based tests with @pytest.mark.<category>
- Fixture injection (client, unauth_client, created_booking)
- Data factory: build_booking_payload(**overrides)
- Assertions with descriptive failure messages

Implement test scenario TS-XXX:
"[scenario description]"

Requirements:
- Follow existing code style in tests/regression/
- Use parametrize if multiple data variations
- Include cleanup via yield fixture if test creates data
```

### Review Test PR

```
Review this test code for production readiness:

Check for:
1. Flaky patterns (shared state, timing, order dependency)
2. Data isolation (factory usage, no hardcoded IDs)
3. Cleanup (yield fixtures for created resources)
4. CI safety (parallel execution, deterministic assertions)
5. Coverage gaps (missing negative cases, edge cases)
6. Assertion quality (would a broken feature still pass?)

Flag issues as:
- 🚨 Critical: breaks CI reliability
- ⚠️ Risk: potential instability
- 💡 Suggestion: improvement opportunity
```

### Debug Flaky Test

```
This test is flaky in CI (passes ~80% of the time):

[paste test code and recent failure output]

Analyse:
1. What is the likely root cause?
2. Is this a test problem or a product bug?
3. What's the fix?
4. How do we prevent similar flakiness?
```

---

## Integration with Test Management

The JD mentions Jira but no dedicated test management tool (TestRail, Zephyr, Xray). Likely approach:

- **Jira issue types**: Use "Test" issue type with custom fields (Test Category, Requirement Link)
- **Traceability**: Link test tickets to requirement tickets via "Verifies" relationship
- **Execution tracking**: CI artifacts (JUnit XML) + Jira comments with pass/fail summaries
- **Postman**: API collection for manual exploration and debugging, complementing automated pytest suite

This is pragmatic — separate test management tools add overhead without proportional value for smaller teams. Jira + CI artifacts + Postman covers the essentials.

---

## Key Principles

1. **AI accelerates, humans validate** — AI generates the first draft; engineers review for completeness and correctness
2. **Pattern consistency** — AI should follow existing project patterns, not introduce new frameworks
3. **Traceability** — every AI-generated test must trace back to a requirement
4. **Human-in-the-loop** — critical decisions (risk priority, coverage scope, test strategy) remain with the engineer
5. **Measurable impact** — track AI's contribution via velocity metrics (tests generated/hour, coverage delta)
