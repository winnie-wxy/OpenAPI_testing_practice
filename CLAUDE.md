# CoverG — Project Instructions

## Purpose

Interview preparation project demonstrating senior/lead QA engineering capabilities. Targets the [Restful Booker API](https://restful-booker.herokuapp.com) as a stand-in for Cover Genius XCover insurance API.

## Architecture

```
src/
  api/booking_client.py    — HTTP client wrapping requests.Session (auth via cookie token)
  models/booking.py        — Pydantic models for response schema validation
  utils/data_factory.py    — Randomised test data factory (parallel-safe, no shared state)

tests/
  conftest.py              — Session-scoped fixtures (auth_token, client, unauth_client, created_booking)
  smoke/                   — Health check, auth, basic create (gate for regression)
  regression/              — Full CRUD lifecycle, negative tests, parametrized variations
  contract/                — Pydantic-based response schema validation
  nonfunctional/           — Response time, concurrency, resilience, security smoke

docs/                      — Interview prep docs, test strategy, AI-driven QA approach
postman/                   — Postman collection + environment mirroring pytest tests
```

## Test Categories and Markers

| Marker | Purpose | Run command |
|--------|---------|-------------|
| `smoke` | Quick health + basic CRUD | `pytest -m smoke` |
| `regression` | Full coverage + edge cases | `pytest -m regression` |
| `contract` | Response schema validation | `pytest -m contract` |
| `nonfunctional` | Performance, security, resilience | `pytest -m nonfunctional` |

## Running Tests

```bash
pytest                        # all tests
pytest -m smoke               # by marker
pytest -n auto                # parallel execution
pytest --lf                   # last failed only
pytest --reruns 2             # with flake retry
pytest --env=staging -m smoke # target environment
```

## Environment Configuration

- Config loaded from `.env` via `python-dotenv`
- Override with `--env` flag: `pytest --env=staging`
- Credentials: public test API (`admin` / `password123`)

## CI Pipeline

`.github/workflows/tests.yml` — Three-stage pipeline:
1. **Smoke** — gates everything, runs first
2. **Regression** — runs after smoke passes (includes contract tests)
3. **Non-functional** — runs after regression passes

Features: pip caching, parallel execution (`pytest-xdist`), flake management (`pytest-rerunfailures`), JUnit XML reports, test result PR comments via `dorny/test-reporter`.

## Coding Conventions

- **Class-based tests** — group related tests in classes with descriptive docstrings
- **Fixture injection** — no hardcoded URLs or credentials in test files
- **Data factory** — all test data via `build_booking_payload()`, never hardcoded
- **Yield fixtures** — created resources are cleaned up via teardown
- **Parametrize** — use `pytest.mark.parametrize` with `ids` for data-driven tests
- **Assertions** — one logical assertion per test, descriptive failure messages where needed

## Commit Conventions

- Imperative mood: "Add X", "Fix Y", "Update Z"
- Separate concerns: one logical change per commit

---

# Claude Code Usage Strategy

This section documents how I use Claude Code effectively — not just as a code generator, but as a configurable AI engineering tool. The patterns below are drawn from my experience managing multi-repo test platforms with 20+ skills, multiple MCP servers, and team-wide AI workflows.

## CLAUDE.md Design Philosophy

CLAUDE.md is the most important file for AI-assisted development. Every line is loaded into every session, consuming context tokens. The design principles:

**Keep it under 200 lines.** For each line, ask: "Would removing this cause Claude to make mistakes?" If not, cut it.

**Tell Claude what it can't figure out by reading code:**
- Build/test commands that aren't obvious
- Conventions that differ from language defaults
- Architectural boundaries and file ownership
- Environment-specific gotchas

**Don't tell Claude what it already knows:**
- Standard language conventions
- Self-evident code patterns
- Anything Claude can infer from existing code

**Use emphasis for critical rules:** "IMPORTANT" or "YOU MUST" improves adherence for non-negotiable rules (e.g., "IMPORTANT: Never commit .env files").

### File Hierarchy

```
~/.claude/CLAUDE.md           # Personal global — identity, preferences, tool credentials
./CLAUDE.md                    # Project root — architecture, test commands, conventions (git-tracked)
./CLAUDE.local.md              # Personal project overrides (gitignored)
./subdir/CLAUDE.md             # Subdirectory-specific — loaded when working in that directory
```

**Why this matters:** Global CLAUDE.md carries your identity and credentials across all repos. Project CLAUDE.md is shared via git so the whole team benefits. Subdirectory CLAUDE.md keeps specialised context out of the root file.

**Monorepo pattern:** In a test platform monorepo, I use subdirectory CLAUDE.md files to scope context:
- Root CLAUDE.md — shared library, architecture overview, subdirectory references
- `frontend_test/CLAUDE.md` — Playwright-specific: POM hierarchy, locator conventions, MCP setup
- `performance_tests/CLAUDE.md` — Locust-specific: TAT analysis patterns, GHA workflows

This way Claude only loads the Playwright context when I'm working in `frontend_test/`, not when I'm writing performance tests.

## Skills: On-Demand Workflows (Not Always-Loaded Context)

**The key insight:** Move specialised workflows from CLAUDE.md to Skills. Skills load on-demand when invoked — they don't consume tokens when you're doing unrelated work.

```
.claude/skills/
  generate-test-plan/SKILL.md     # Only loaded when /generate-test-plan is invoked
  generate-test-card/SKILL.md     # Only loaded when /generate-test-card is invoked
  pr-review/SKILL.md              # Only loaded when /pr-review is invoked
```

### What Belongs in CLAUDE.md vs Skills

| CLAUDE.md (always loaded) | Skill (loaded on demand) |
|---------------------------|--------------------------|
| Architecture overview | Test plan generation workflow |
| Test run commands | Jira card creation process |
| Coding conventions | PR review checklist |
| Environment setup | Performance analysis template |
| Commit conventions | Debugging playbooks |

**Anti-pattern:** Putting your entire test plan template, Jira card creation instructions, and PR review workflow in CLAUDE.md. This wastes tokens on every session where you're just writing tests.

### Skills I've Built and Use in Production

**Test engineering skills (11 across my test platform):**
- `generate-test-plan` (v2.0) — generates test plans from Jira Epics, Confluence pages, or local specs. Supports both SaMD and NMD compliance styles. Multi-step: gathers sources via AskUserQuestion → analyses requirements → generates plan with traceability.
- `generate-test-card` (v2.1) — creates/updates Jira Test cards with smart linking. Enforces mandatory human review before committing to Jira.
- `container-samd-test-plan` — IEC 62304 V&V test plans with cross-repo impact analysis and Jama SR traceability.

**Orchestration skills (13 across an OpenSpec-driven platform):**
- Artifact lifecycle: `explore`, `apply`, `verify`, `archive`, `sync`
- Mandatory query routing — all codebase questions go through a single skill to enforce consistent patterns across 22 repos
- Card generation — breaks implementation into Jira cards from design specs

**Key design principle:** Each skill has a SKILL.md metadata file. Skills accept `$ARGUMENTS` for parameterisation (e.g., `/generate-test-plan EPIC-1234`). Use `disable-model-invocation: true` for workflows with side effects that should only trigger manually.

## MCP Server Strategy: Load What You Need

MCP (Model Context Protocol) servers extend Claude's capabilities but consume context. The strategy:

### Default Behavior (Claude Code v2.1+)

Tool search is enabled by default. At session start, only tool **names** are loaded (not full schemas). Full descriptions load on-demand when Claude decides to use a tool. This means adding MCP servers has minimal idle cost.

### When to Use MCP vs CLI

| Use MCP Server | Use CLI Instead |
|----------------|-----------------|
| Playwright browser inspection (live element testing) | GitHub (`gh` CLI is more efficient) |
| Codebase-wide structural search (`codebase-memory`) | Simple file search (built-in Glob/Grep) |
| Atlassian API (Jira/Confluence read/write) | AWS operations (`aws` CLI) |
| Custom orchestration tools | Git operations (built-in) |

**What I've found works:**
- Simple API test projects (like this one) — no MCP servers needed. Built-in tools + CLI cover everything.
- Playwright E2E repos — Playwright MCP for live element inspection during test development.
- Multi-repo orchestration platforms — custom MCP servers for structural code search, plus Atlassian MCP for Jira/Confluence.
- Most repos — no MCP servers. Don't add them unless you have a clear use case.

### Configuration

```jsonc
// .mcp.json — only declare what this repo actually needs
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@0.0.64", "--cdp-endpoint", "http://localhost:9222"]
    }
  }
}
```

```jsonc
// .claude/settings.local.json — control which servers are active
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["playwright"]
}
```

## Token Efficiency Practices

### High-Impact Habits (Ranked)

1. **`/clear` between unrelated tasks.** Stale context wastes tokens on every subsequent message. This is the single easiest win.

2. **Use subagents for investigation.** When Claude reads files during research, all those files consume your main context. Subagents run in separate context and return only summaries.
   ```
   Use subagents to investigate how the auth system handles token refresh
   ```

3. **`/compact` at ~70% context, not when warned.** Always provide focus:
   ```
   /compact Focus on the API test changes and conftest.py modifications
   ```

4. **Write specific prompts.** "Add input validation to `create_booking` in `booking_client.py`" is cheaper than "improve the codebase". Vague requests trigger broad file scanning.

5. **Move specialised instructions to Skills.** If test plan templates are in CLAUDE.md, they load every session — even when you're just fixing a typo.

6. **Choose the right model.** Sonnet for straightforward tasks (test writing, small fixes). Opus for architecture decisions and complex debugging. Use `/model` to switch mid-session.

7. **Use `/btw` for quick side questions.** The answer appears in an overlay and never enters conversation history.

### Session Management

```
# Good: focused sessions with clear scope
Session 1: Write smoke tests → /clear
Session 2: Add non-functional tests → /clear
Session 3: Fix CI pipeline → /clear

# Bad: kitchen-sink session
Session 1: Write tests + fix CI + review PR + update docs (context fills up, quality degrades)
```

**After 2 failed corrections:** `/clear` and write a better initial prompt incorporating what you learned. The correction spiral is the most common source of wasted tokens.

## Permissions & Security

### Permission Strategy

```jsonc
// .claude/settings.json — project-level (git-tracked)
{
  "permissions": {
    "allow": [
      "Bash(pytest:*)",           // test execution
      "Bash(git:*)",              // version control
      "Bash(pip install:*)"       // dependency management
    ],
    "deny": [
      "Read(.env*)",              // protect secrets
      "Bash(rm -rf*)"            // prevent dangerous deletions
    ]
  }
}
```

**Scaling permissions across repos:**
- High-trust repos (your own test platform): comprehensive allow list — individually permit each tool/command
- Low-trust repos (third-party, new repos): minimal — only `gh pr view`, `gh pr diff`, read-only access
- All repos: explicit deny for `.env*` reads and destructive commands

**Principle:** Start restrictive, add permissions as needed. Per-repo settings allow different trust levels for different codebases.

## Hooks: Automated Guardrails

Hooks run shell commands in response to Claude Code events:

```jsonc
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      { "command": "./scripts/pre-prompt-check.sh" }
    ],
    "Stop": [
      { "command": "./scripts/post-session-cleanup.sh" }
    ]
  }
}
```

**Use cases:**
- Auto-cleanup git worktrees before/after prompts
- Pre-process data before Claude reads it (grep for errors in a 10K-line log → feed only matching lines, saving thousands of tokens)
- Enforce linting or formatting after code changes
- Log session activity for audit trails

## Compaction Instructions

Add to CLAUDE.md so `/compact` preserves critical context:

```markdown
# Compact instructions
When compacting, always preserve:
- List of modified files and their paths
- Test commands that were run and their results
- Jira ticket IDs and requirement traceability
- Current branch name and PR URL
```

## What This Project Demonstrates

This CLAUDE.md itself is a demonstration of the principles:
- **Concise project context** (architecture, test commands, conventions) — always loaded, no bloat
- **Specialised workflows belong in Skills** — not in always-loaded CLAUDE.md
- **AI usage strategy documented** — shows how a senior/lead QA engineer configures and optimises AI tooling for team-wide productivity
- **Patterns drawn from production** — multi-repo test platforms, 20+ custom skills, MCP server management, token-efficient workflows
