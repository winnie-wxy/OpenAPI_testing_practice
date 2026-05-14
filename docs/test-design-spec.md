# Open-Spec Test Design Simulation

Demonstrates the full requirements → test spec → implementation workflow using Cover Genius XCover domain as context.

---

## 1. Requirement Spec

**Feature:** XCover API — Booking Protection Lifecycle

**Context:** Cover Genius XCover provides embedded insurance at the point of sale. When a customer books a flight/hotel, the partner's checkout calls XCover to bind a protection policy. The policy has a lifecycle: quote → bind → view → modify → cancel → refund.

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-001 | System shall provide a health check endpoint returning status 201 | P1 |
| REQ-002 | System shall authenticate partners via username/password and return a session token | P1 |
| REQ-003 | System shall reject authentication with invalid credentials | P1 |
| REQ-004 | System shall allow authenticated partners to create a booking (bind policy) | P1 |
| REQ-005 | System shall return the created booking with a unique booking ID | P1 |
| REQ-006 | System shall allow retrieval of a booking by ID | P1 |
| REQ-007 | System shall allow full update (PUT) of a booking by authenticated partner | P2 |
| REQ-008 | System shall allow partial update (PATCH) of a booking by authenticated partner | P2 |
| REQ-009 | System shall allow deletion (cancellation) of a booking by authenticated partner | P1 |
| REQ-010 | System shall return 404 for non-existent booking IDs | P2 |
| REQ-011 | System shall reject update/delete from unauthenticated requests (403) | P1 |
| REQ-012 | System shall handle concurrent booking creation without data corruption | P2 |
| REQ-013 | System shall respond within 2000ms (P95) for all endpoints | P2 |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | API response time P95 < 2000ms under normal load | P2 |
| NFR-002 | API shall handle 10 concurrent requests without 5xx errors | P2 |
| NFR-003 | API shall not crash on SQL injection payloads | P1 |
| NFR-004 | API shall not crash on XSS payloads | P2 |
| NFR-005 | API shall handle oversized payloads gracefully (no 500) | P3 |

---

## 2. Test Spec — Derived Test Scenarios

Each test scenario traces back to one or more requirements.

### Smoke Tests

| ID | Test Scenario | Traces To | Priority |
|----|--------------|-----------|----------|
| TS-001 | Health check returns 201 | REQ-001 | P1 |
| TS-002 | Valid credentials return token | REQ-002 | P1 |
| TS-003 | Invalid credentials return error reason | REQ-003 | P1 |
| TS-004 | Create booking returns booking ID | REQ-004, REQ-005 | P1 |
| TS-005 | Created booking data matches payload | REQ-004 | P1 |
| TS-006 | GET booking returns created data | REQ-006 | P1 |

### Regression Tests

| ID | Test Scenario | Traces To | Priority |
|----|--------------|-----------|----------|
| TS-007 | Full CRUD lifecycle (create → read → update → patch → delete → verify deleted) | REQ-004 to REQ-010 | P1 |
| TS-008 | PUT without auth returns 403 | REQ-011 | P1 |
| TS-009 | DELETE without auth returns 403 | REQ-011 | P1 |
| TS-010 | GET non-existent booking returns 404 | REQ-010 | P2 |
| TS-011 | Create with empty payload — document behavior | REQ-004 | P3 |
| TS-012 | Create with missing required fields — document behavior | REQ-004 | P3 |
| TS-013 | Create with wrong type for totalprice | REQ-004 | P3 |
| TS-014 | Create with invalid date format | REQ-004 | P3 |
| TS-015 | Create with varied name data (unicode, apostrophe, min length) | REQ-004 | P2 |
| TS-016 | Create with deposit paid true/false | REQ-004 | P2 |

### Contract Tests

| ID | Test Scenario | Traces To | Priority |
|----|--------------|-----------|----------|
| TS-017 | Create booking response matches Pydantic schema | REQ-005 | P1 |
| TS-018 | GET booking response matches Pydantic schema | REQ-006 | P1 |
| TS-019 | Invalid response shape is detected by schema validation | REQ-005 | P2 |

### Non-Functional Tests

| ID | Test Scenario | Traces To | Priority |
|----|--------------|-----------|----------|
| TS-020 | Health check P95 response time < 2000ms | NFR-001 | P2 |
| TS-021 | GET booking P95 response time < 2000ms | NFR-001 | P2 |
| TS-022 | POST booking P95 response time < 2000ms | NFR-001 | P2 |
| TS-023 | 10 concurrent POST requests — no 5xx | NFR-002 | P2 |
| TS-024 | 10 concurrent GET requests — all 200 | NFR-002 | P2 |
| TS-025 | SQL injection payloads — no 500 | NFR-003 | P1 |
| TS-026 | XSS payloads — no 500 | NFR-004 | P2 |
| TS-027 | Oversized payload — no 500 | NFR-005 | P3 |

---

## 3. Test Tasks — Implementation Breakdown

| Task | Description | Acceptance Criteria | Traces To |
|------|-------------|---------------------|-----------|
| T-001 | Implement smoke test suite | Health, auth, basic create tests pass | TS-001 to TS-006 |
| T-002 | Implement CRUD lifecycle test | Full create→read→update→patch→delete flow passes | TS-007 |
| T-003 | Implement auth enforcement tests | 403 returned for unauth PUT/DELETE | TS-008, TS-009 |
| T-004 | Implement negative/validation tests | Document API behavior for invalid input | TS-010 to TS-014 |
| T-005 | Implement data variation tests | Parametrized tests for name/price/deposit variations | TS-015, TS-016 |
| T-006 | Implement contract validation | Pydantic schema validation passes for all endpoints | TS-017 to TS-019 |
| T-007 | Implement response time tests | P95 assertions pass for all endpoints | TS-020 to TS-022 |
| T-008 | Implement concurrency tests | 10 concurrent requests with no 5xx | TS-023, TS-024 |
| T-009 | Implement security smoke tests | SQL injection, XSS, oversized payloads handled | TS-025 to TS-027 |

---

## 4. Implementation Mapping

| Task | Test File | Test Class |
|------|-----------|------------|
| T-001 | `tests/smoke/test_health.py` | `TestHealthCheck` |
| T-001 | `tests/smoke/test_auth.py` | `TestAuth` |
| T-001 | `tests/smoke/test_create_booking.py` | `TestCreateBooking` |
| T-002 | `tests/regression/test_booking_lifecycle.py` | `TestBookingLifecycle` |
| T-003 | `tests/regression/test_booking_negative.py` | `TestUnauthorizedAccess` |
| T-004 | `tests/regression/test_booking_negative.py` | `TestNotFound`, `TestCreateBookingValidation` |
| T-005 | `tests/regression/test_booking_parametrize.py` | `TestCreateBookingVariations` |
| T-006 | `tests/contract/test_booking_schema.py` | `TestBookingResponseSchema` |
| T-007 | `tests/nonfunctional/test_response_time.py` | `TestResponseTime` |
| T-008 | `tests/nonfunctional/test_concurrent_requests.py` | `TestConcurrentRequests` |
| T-009 | `tests/nonfunctional/test_security_smoke.py` | `TestSecuritySmoke` |

---

## 5. Traceability Matrix

| Requirement | Test Spec | Test File | CI Job |
|-------------|-----------|-----------|--------|
| REQ-001 | TS-001 | `test_health.py` | smoke |
| REQ-002 | TS-002 | `test_auth.py` | smoke |
| REQ-003 | TS-003 | `test_auth.py` | smoke |
| REQ-004 | TS-004, TS-005, TS-011–016 | `test_create_booking.py`, `test_booking_negative.py`, `test_booking_parametrize.py` | smoke, regression |
| REQ-005 | TS-004, TS-017 | `test_create_booking.py`, `test_booking_schema.py` | smoke, regression |
| REQ-006 | TS-006, TS-018 | `test_create_booking.py`, `test_booking_schema.py` | smoke, regression |
| REQ-007 | TS-007 | `test_booking_lifecycle.py` | regression |
| REQ-008 | TS-007 | `test_booking_lifecycle.py` | regression |
| REQ-009 | TS-007 | `test_booking_lifecycle.py` | regression |
| REQ-010 | TS-010 | `test_booking_negative.py` | regression |
| REQ-011 | TS-008, TS-009 | `test_booking_negative.py` | regression |
| REQ-012 | TS-023, TS-024 | `test_concurrent_requests.py` | nonfunctional |
| REQ-013 | TS-020–022 | `test_response_time.py` | nonfunctional |
| NFR-001 | TS-020–022 | `test_response_time.py` | nonfunctional |
| NFR-002 | TS-023, TS-024 | `test_concurrent_requests.py` | nonfunctional |
| NFR-003 | TS-025 | `test_security_smoke.py` | nonfunctional |
| NFR-004 | TS-026 | `test_security_smoke.py` | nonfunctional |
| NFR-005 | TS-027 | `test_security_smoke.py` | nonfunctional |

---

## AI-Agentic Workflow Demonstrated

This document was produced using the following AI-assisted workflow:

1. **Requirements analysis** — Claude Code analyses the feature requirements and identifies testable scenarios
2. **Test spec generation** — Derives test scenarios with traceability IDs from requirements
3. **Task breakdown** — Creates implementable tasks with acceptance criteria
4. **Implementation** — Generates test code following the project's patterns (class-based, fixture injection, data factory)
5. **Traceability** — Maps every requirement → test spec → test file → CI job

This mirrors how AI-driven QA works in practice: the AI accelerates the systematic work (requirements analysis, scenario derivation, boilerplate generation), while the engineer validates coverage completeness, edge case selection, and risk prioritisation.
