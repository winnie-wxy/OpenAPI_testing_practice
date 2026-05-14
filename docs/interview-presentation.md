# Interview Presentation — Talking Points & Demo Script

**Interview:** Cover Genius — Sr QA Engineer / QA Lead
**Interviewer:** Maxim Rosca (Sr Engineering Manager, QA)
**Total time:** 45 minutes
**Suggested split:** ~15 min presentation/demo, ~30 min conversation/questions

---

## Opening (2 min)

> "I built this project to demonstrate how I approach API test automation at scale. It's a pytest suite against a REST booking API — think of it as a simplified version of XCover's policy lifecycle. But the interesting part isn't the tests themselves — it's the engineering around them."

**Key point:** You're not showing 51 tests. You're showing a **system** — test architecture, CI pipeline, data management, coherency checking, and AI-driven workflows.

---

## Slide 1: Architecture Overview (2 min)

**Show:** Project structure diagram

**Talk through:**
- Layered test architecture: smoke → regression → contract → non-functional
- Each layer gates the next in CI — smoke fails, nothing else runs
- Separation of concerns: API client, data factory, Pydantic models, test files
- "This is the same pattern I use in production — at my current role I manage a test platform across 20+ repos"

**Transition:** "Let me show what happens when you run this..."

---

## Slide 2: CI Pipeline (2 min)

**Show:** CI workflow diagram

**Talk through:**
- Three-stage pipeline with parallel execution (`pytest-xdist`)
- Flake management (`--reruns 2`) — not ignoring flakes, managing them
- JUnit XML for machine-readable metrics, HTML for human review
- PR comments with test result summaries
- Coherency check runs in parallel — catches coverage drift

**Key quote:**
> "Reruns are a safety net, not a solution. If a test reruns in more than 20% of builds, it needs fixing, not more reruns. I track rerun rates as a quality signal."

---

## Slide 3: Flaky Test Debugging Story (3 min)

**Show:** Git history showing the intentional → fix commits

**Talk through the three anti-patterns:**

1. **Race condition** — create booking then immediately GET
   - Fix: polling with retry/backoff
   - "In a real system with eventual consistency, this is the #1 source of flakiness"

2. **Shared state** — module-level variable coupling tests
   - Fix: per-test fixture isolation
   - "This breaks instantly with `pytest-xdist` parallel execution"

3. **Single-sample timing** — `assert elapsed < 500ms`
   - Fix: multi-sample P95 statistical approach
   - "Network jitter makes single-sample assertions useless in CI"

**Key quote:**
> "I deliberately introduced these anti-patterns, then fixed them, so the git history tells the debugging story. This is how I'd onboard a junior engineer — show them the pattern, show them why it breaks, show them the fix."

---

## Slide 4: Coherency Check System (3 min)

**Demo:** Run `python tools/coherency_check.py` live

**Talk through:**
- Coverage matrix as single source of truth (requirement → test → CI job)
- Structural checks: automated, fast, runs in CI
- Semantic checks: AI-assisted, deeper analysis via Claude Code skill
- "This catches the silent gap — a requirement gets added to Jira, nobody writes a test, and it ships untested. The coherency check makes that visible."

**Show the gap report:**
> "See these P1 gaps? Webhooks, idempotency, multi-tenancy — the API doesn't support them, so I've documented them as known gaps with rationale. That's better than pretending they don't exist."

**Key quote:**
> "The most dangerous test suite is one that passes 100% and gives you false confidence. Coherency checks tell you what you're NOT testing."

---

## Slide 5: AI-Driven QA (2 min)

**Talk through (no demo needed — the project IS the demo):**

- This entire project was built with Claude Code
- But the value isn't code generation — it's the workflows:
  - Requirements → test specs → implementation (with traceability)
  - Custom skills for test plan generation, Jira card creation, coherency checking
  - CLAUDE.md as configurable engineering context (not a personality file)
- "AI accelerates the systematic work. The engineer makes the judgment calls — risk prioritisation, coverage scope, what NOT to test."

**Key quote:**
> "I've built 20+ custom Claude Code skills for test engineering — test plan generation from Jira Epics, Jira card creation with smart linking, coherency checking. The AI does the boilerplate, I do the strategy."

---

## Slide 6: What I'd Build at Cover Genius (1 min)

**Quick list — don't over-explain, let Maxim ask:**

- XCover policy lifecycle E2E tests (quote → bind → claim → settle)
- Multi-currency / multi-locale test matrix
- Contract testing between partner integrations and XCover API
- Webhook delivery verification (idempotency, retry, dead-letter)
- Performance baselines per partner integration
- Coherency checking across the test platform

**Close:**
> "This project shows the patterns. At Cover Genius, the complexity is the domain — 60+ countries, 50+ currencies, partner-specific integrations. The test architecture scales the same way."

---

## Conversation Prep — Likely Questions (30 min)

### "How do you decide what to automate vs test manually?"

> "Automate the regression safety net — the things that must pass every release. Manual test for exploratory, new feature validation, and anything involving subjective judgment. The split shifts over time — what starts manual gets automated once the feature stabilises."

### "How do you handle test data in a multi-tenant system?"

> "Factory pattern with randomised data — each test creates its own tenant, its own policies, its own claims. Yield fixtures handle cleanup. No shared state between tests, no ordering dependencies. This is essential for parallel execution."

### "How do you prioritise what to test with limited resources?"

> "Risk-based: impact × likelihood. P1 is anything that blocks revenue or violates compliance. P2 is customer-facing degradation. P3 is internal tooling. I document the gaps explicitly — known untested areas with rationale — rather than pretending everything is covered."

### "Tell me about a time you dealt with flaky tests in CI."

> "I have a concrete example in this project. [Walk through the flaky test story.] In production, the pattern is the same — identify root cause (usually shared state, timing, or external dependency), fix the test, add reruns as a safety net for genuine transient failures, and track rerun rate as a quality signal."

### "How do you use AI in your QA work?"

> "Three levels: (1) Code generation — AI writes the boilerplate, I review. (2) Workflow automation — custom skills for test plans, Jira cards, coverage analysis. (3) Strategic analysis — AI analyses requirements and identifies test gaps. The key is human-in-the-loop — AI accelerates, humans validate."

### "How would you onboard and mentor a junior test engineer?"

> "Start with the patterns — show them the project structure, explain why each layer exists. Pair on the first few tests. The flaky test commit history is actually my onboarding material — intentional anti-patterns, then fixes. Then graduate to writing tests independently with PR review. Skills and CLAUDE.md give them guardrails so they follow the team's patterns."

### "What's your experience with Postman?"

> "I use Postman for API exploration and debugging — it's faster than writing a test when you're investigating behavior. This project includes a Postman collection mirroring the pytest suite. In a team setting, the collection is the shared reference — anyone can import it and explore the API without setting up the test framework."

### "How do you measure test quality?"

> "Four signals: (1) Defect escape rate — bugs that reach production despite passing tests. (2) Flake rate — tests that need reruns. (3) Coverage coherency — requirements with no tests (my coherency checker). (4) Time to feedback — how fast the CI pipeline gives results. Passing tests is table stakes — these metrics tell you if the tests are actually doing their job."

---

## Demo Script (If Asked to Show Code)

1. **Run tests:** `pytest -m smoke --tb=short` (fast, shows the structure)
2. **Run coherency:** `python tools/coherency_check.py` (shows the gap analysis)
3. **Show git log:** `git log --oneline` (shows the commit narrative)
4. **Show a test:** Open `test_booking_lifecycle.py` (the CRUD lifecycle — most impressive single test)
5. **Show conftest:** Open `conftest.py` (yield fixtures, env config, `--env` flag)
6. **Show CI:** Open `.github/workflows/tests.yml` (three-stage pipeline)
