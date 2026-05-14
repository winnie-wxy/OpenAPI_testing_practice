# Test Data Management Strategy

How this project handles test data creation, isolation, and cleanup.

---

## Data Generation: Factory Pattern

All test data is generated via `src/utils/data_factory.py`:

```python
def build_booking_payload(
    firstname=None, lastname=None, totalprice=None,
    depositpaid=None, checkin=None, checkout=None, additionalneeds=None,
) -> dict:
    return {
        "firstname": firstname or random_string(),
        "lastname": lastname or random_string(),
        "totalprice": totalprice if totalprice is not None else random.randint(50, 500),
        ...
    }
```

**Why this approach:**
- **Parallel-safe**: random values prevent collisions between concurrent tests
- **Flexible**: override any field for specific scenarios, defaults for everything else
- **No shared state**: each call generates independent data
- **Deterministic when needed**: pass explicit values for assertions (`firstname="Winnie"`)

## Data Lifecycle: Create → Use → Teardown

```
Test starts
  └─ Fixture setup: build_booking_payload() → POST /booking → booking_id
      └─ Test runs: uses booking_id for GET/PUT/PATCH/DELETE
          └─ Fixture teardown: DELETE /booking/{booking_id}
              └─ Test ends (data cleaned up regardless of pass/fail)
```

Implementation via yield fixture in `conftest.py`:

```python
@pytest.fixture
def created_booking(client):
    payload = build_booking_payload()
    booking_id = client.create_booking(payload).json()["bookingid"]
    yield booking_id, payload
    client.delete_booking(booking_id)  # cleanup
```

## Data Isolation Principles

| Principle | Implementation |
|-----------|---------------|
| No cross-test dependencies | Each test creates its own data via factory |
| No shared mutable state | No module-level variables holding booking IDs |
| No ordering assumptions | Tests can run in any order or in parallel |
| Cleanup on failure | Yield fixtures clean up even when assertions fail |
| Unique identifiers | Random names/values prevent data collisions |

## Environment-Specific Data Seeding

| Environment | Strategy |
|-------------|----------|
| **Dev** | Factory generates data on-the-fly, cleaned up per-test |
| **Staging** | Same factory pattern, but pre-seeded reference data for read-only tests |
| **Prod** | Read-only smoke tests only, no data creation |

Configuration via `--env` flag:
```bash
pytest --env=staging -m smoke
```

## PHI/PII Considerations (Insurance Domain)

For Cover Genius XCover integration testing:

| Data Category | Approach |
|---------------|----------|
| Customer names | Random strings (no real names) |
| Policy numbers | Generated UUIDs or sequential counters |
| Financial data | Random amounts within valid ranges |
| Dates | Future dates relative to `datetime.now()` |
| Addresses | Synthetic data (faker library if needed) |
| Medical info | Never used in test data — mock or omit |

**Rule:** Never use production data in test environments. All test data is synthetic.

## Cleanup Strategy

### Per-Test Cleanup (Primary)

Yield fixtures handle individual test cleanup:
- **Pros**: immediate, guaranteed, test-isolated
- **Cons**: relies on API availability during teardown

### Fallback: Ignore 404 on Cleanup

If a test deletes the booking as part of its assertion, the teardown gracefully handles the 404:
```python
yield booking_id, payload
client.delete_booking(booking_id)  # returns 404 if already deleted — acceptable
```

### Scheduled Cleanup (Production Pattern)

For long-running environments, consider a nightly cleanup job:
```bash
# CI cron job: delete all test bookings older than 24 hours
pytest tests/cleanup/ --env=staging -m cleanup
```

This project doesn't need this for the public Restful Booker API (data is ephemeral), but it's a pattern worth demonstrating for real-world insurance APIs.
