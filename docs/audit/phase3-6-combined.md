# Phase 3: Frontend-Backend Integration Audit

**Date**: 2026-07-18 | **Status**: Complete

---

## 1. Auth System Duality (P1)

**The most critical integration issue**: Two separate, unsynchronized auth systems.

| System | Token Storage | Token Name |
|--------|--------------|------------|
| Server-side (`api-helpers.js`) | httpOnly cookies | `jwt_access`, `jwt_refresh` |
| Client-side (`api.js`) | localStorage | `access_token`, `refresh_token` |

**Impact**: Server-side SvelteKit load functions set cookies. Client-side `apiRequest` (used in contacts page) reads from localStorage which is never populated. Any client-side API call will fail with 401.

**Files**: `frontend/src/lib/api.js` L11-14, `frontend/src/lib/api-helpers.js` L30-40

---

## 2. API Response Shape Mismatches (P1)

| Frontend Expects | Backend Returns | Files |
|-----------------|----------------|-------|
| `assigned_to` as array of IDs | Array of objects `[{id, user_details}]` | `dashboard/+page.server.js` L73 |
| `lead.company?.name` (object) | `company_name` (string) | `dashboard/+page.server.js` L38 |
| `account.id` (nested object) | Account ID (integer) | `invoices/+page.server.js` L92 |
| `total_amount` as number | String `'0.00'` | `invoices/+page.server.js` L101 |

---

## 3. Query Parameter Mismatches (P2)

| Frontend Sends | Backend Expects | Issue |
|---------------|----------------|-------|
| `issue_date_gte` | `issue_date__gte` (DRF double-underscore) | Invoices filter |
| `sort=-created_at` | `ordering=-created_at` (DRF convention) | Invoices sort |
| Array as query param | Comma-separated string | Multiple pages |

---

## 4. Missing API Integration Points (P2)

- **Kanban views missing filters**: Leads, opportunities, tickets kanban ignore `assigned_to`, `date_from`/`date_to` filters
- **Contacts update missing account**: The `update` action in contacts doesn't include the `account` field
- **Watching endpoint**: Tickets watching uses `/cases/watching/` but doesn't pass filter/pagination params

---

## 5. Token Refresh Redirection Bug (P1)

`frontend/src/lib/api.js` L90-95: `refreshAccessToken` calls `goto('/login')` as a side effect inside a utility function. During background data fetches, the user is abruptly redirected to login without warning.

---

## 6. Error Handling Gap (P2)

- Server loaders throw `error(500)` for all backend errors, masking 401/403/404
- Client ignores error responses from API in several pages
- Empty `catch {}` blocks in layout server loader silently swallow org settings failures

---

## Summary

| Severity | Count |
|----------|-------|
| P1 | 3 |
| P2 | 8 |
| **Total** | **11** |

---

# Phase 4: Mobile App Audit (Flutter)

**Date**: 2026-07-18 | **Status**: Limited (key files reviewed)

---

## 1. ApiService (Singleton Pattern)

`mobile/lib/services/api_service.dart`:

| # | Severity | Issue |
|---|----------|-------|
| M1 | **P2** | Singleton pattern with `factory ApiService()` — no dependency injection. Hard to test, hard to reset state between users |
| M2 | **P2** | `RefreshTokenCallback` wiring relies on `AuthService` calling `_refreshCallback` — if AuthService fails to register, token refresh silently breaks |
| M3 | **P3** | `_client` is `http.Client()` — not disposed anywhere. Memory leak if app recreates the service |

## 2. Architecture Observations

- 14 providers for state management (ChangeNotifier pattern)
- 12 screen modules mirroring frontend pages
- Firebase integration for push notifications
- API config likely in `lib/config/api_config.dart`

---

## Summary (Mobile)

| Severity | Count |
|----------|-------|
| P2 | 2 |
| P3 | 1 |
| **Total** | **3** |

*Note: Full mobile audit requires building/running the Flutter app. This is a code-structure-only review.*

---

# Phase 5: MCP Server Audit

**Date**: 2026-07-18 | **Status**: Complete

---

## 1. Server Architecture

- FastMCP-based MCP server (`bcrm_mcp/server.py`)
- Two transports: stdio (single-user) and HTTP (multi-user)
- PAT-based authentication (`bcrm_mcp/auth.py`)
- `CrmClient` wraps HTTP calls to Django API (`bcrm_mcp/client.py`)
- 7 tools: `crm_search`, `crm_get`, `crm_create`, `crm_update`, `crm_delete`, `crm_action`, `crm_list_actions`

## 2. Audit Findings

| # | Severity | Issue |
|---|----------|-------|
| MCP1 | **P2** | `crm_search` has hardcoded `MAX_LIMIT = 50` — users requesting more get silently capped. No warning in response |
| MCP2 | **P2** | `crm_delete` requires `confirm=True` (good!) but `crm_action` only requires confirm for `CONFIRM_REQUIRED_ACTIONS`. Other actions that could have side effects (e.g., `convert`) may bypass confirmation |
| MCP3 | **P2** | `resolve_path()` function not shown — entity path resolution is critical. If entity names don't match Django URL prefixes exactly, all tools break |
| MCP4 | **P3** | HTTP transport creates a fresh `CrmClient` per request (correct for multi-tenant isolation), but no connection pooling — each tool call creates a new HTTP client |
| MCP5 | **P1** | **No rate limiting**: MCP tools have no rate limiting. A malicious user could call `crm_search` in a tight loop to DDoS the Django backend |
| MCP6 | **P3** | `pyproject.toml` and `README.md` exist but no test files in `mcp_server/tests/` were reviewed |

## Summary (MCP Server)

| Severity | Count |
|----------|-------|
| P1 | 1 |
| P2 | 3 |
| P3 | 2 |
| **Total** | **6** |

---

# Phase 6: Infrastructure & DevOps Audit

**Date**: 2026-07-18 | **Status**: Complete

---

## 1. Docker Compose

| # | Severity | Issue |
|---|----------|-------|
| I1 | **P2** | PostgreSQL port 5432 exposed to host — security risk in production |
| I2 | **P2** | Redis port 6379 exposed to host — no password set |
| I3 | **P3** | Frontend mounts entire `/app` as volume — `node_modules` would be overwritten without the named volume workaround |
| I4 | **P2** | No nginx/ reverse proxy in compose — backend and frontend run on separate ports with no HTTPS |
| I5 | **P2** | `.env.docker` referenced but not checked — may contain secrets that shouldn't be committed |
| I6 | **P2** | Celery worker and beat share the same codebase — if a task has a memory leak, it affects both |
| I7 | **P3** | No health check on backend or frontend services |

## 2. Django Settings

| # | Severity | Issue |
|---|----------|-------|
| I8 | **P1** | `SECRET_KEY` defaults to `'django-insecure-dev-key-please-change-in-production'` — guard only works if `ENV_TYPE != 'dev'` |
| I9 | **P2** | `ALLOWED_HOSTS` split on comma — values may have trailing spaces causing host mismatches |
| I10 | **P2** | `DEBUG` defaults to `False` (good) but `ENV_TYPE` defaults to `'dev'` — in dev, the SECRET_KEY guard is disabled |

## 3. Testing

| # | Severity | Issue |
|---|----------|-------|
| I11 | **P3** | `coverage.xml` and `htmlcov/` committed to repo — adds noise to PRs, should be in `.gitignore` |
| I12 | **P3** | `pytest.ini` exists but test coverage not reviewed — unknown coverage percentage |

## Summary (Infrastructure)

| Severity | Count |
|----------|-------|
| P1 | 1 |
| P2 | 7 |
| P3 | 4 |
| **Total** | **12** |

---

## Combined Summary (Phases 3-6)

| Phase | P0 | P1 | P2 | P3 | Total |
|-------|----|----|----|----|-------|
| Phase 3: Integration | 0 | 3 | 8 | 0 | 11 |
| Phase 4: Mobile | 0 | 0 | 2 | 1 | 3 |
| Phase 5: MCP Server | 0 | 1 | 3 | 2 | 6 |
| Phase 6: Infrastructure | 0 | 1 | 7 | 4 | 12 |
| **Combined** | **0** | **5** | **20** | **7** | **32** |
