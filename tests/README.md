# VERA tests

The test suite is a pyramid over the real code paths. Core paths use a **real Redis** rather than
mocks, so the tests exercise the same stores the app uses.

## Tiers

| Tier | Location | Run | Notes |
|---|---|---|---|
| Unit | `tests/unit/` | `make test-unit` (or `pytest tests/unit -q`) | Needs Redis on `:6379`. Covers the catalog, weighted aggregation and bootstrap, signing and the catalog digest, score bands, triage, the graph aggregate node, and API/dashboard handlers. |
| Integration | `tests/integration/` | `VERA_INTEGRATION=1 pytest tests/integration -m integration` | Needs Redis (and MinIO for artifact round-trips). |
| End-to-end | `tests/e2e/` | `VERA_E2E_OLLAMA=1 pytest tests/e2e -m "e2e and ollama"` | Optional; drives a full run against a local Ollama model. |
| Dashboard | `dashboard/` | `cd dashboard && npx playwright test` | RBAC matrix + guided-mode surfaces. |

Lint: `ruff check src tests`. Coverage gate: 80% on `vera`.

## Conventions

- No `unittest.mock` on the core evaluation and storage paths; use a real Redis.
- Collect the unit tier with `pytest tests/unit --collect-only` to see the current count.
- CI runs the unit, integration, and dashboard/Playwright tiers
  (`.github/workflows/vera-ci.yml`).

## Reproducibility checks

- `tests/unit/test_spec_swap.py` loads the alternative specification in
  `examples/specs/security_focus/` through configuration alone and checks that it stays aligned,
  carries its own digest and leaves the default specification untouched.
- `tests/unit/test_signing.py` checks that content digests are stable.
