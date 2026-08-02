# Phase 2: Frontend Pages Audit Report

**Date**: 2026-07-18 | **Status**: Complete | **Pages Audited**: 24 + shared components + i18n

---

## Summary by Severity

| Severity | Count | Key Themes |
|----------|-------|------------|
| **P0 — Critical** | 4 | Typo in leads validSources (`'compaign'`), ~20 hardcoded Persian strings on login page, industry labels hardcoded in English |
| **P1 — Functional** | 18 | No loading/error/empty states, i18n system bypassed, RTL not handled, client vs server auth mismatch, missing i18n keys in en.json (~100+ placeholder values) |
| **P2 — Visual/UX/API** | 42 | Hardcoded English status labels, inconsistent i18n usage, missing kanban filter params, string/number type mismatches, token storage duality |
| **P3 — Code Quality** | 30 | Unused imports, duplicated code, JSDoc-only type annotations, dead code, inconsistent patterns |
| **TOTAL** | **94** | |

---

## Top Critical Issues (P0)

| # | Location | Issue |
|---|----------|-------|
| P0-1 | `login/+page.svelte` | ~20 hardcoded Persian strings — entire login page bypasses i18n system |
| P0-2 | `leads/+page.server.js` L198 | Typo `'compaign'` instead of `'campaign'` in validSources — campaign leads silently get null source |
| P0-3 | `accounts/+page.svelte` L54-84 | All 30 industry labels hardcoded in English — no `$_()` usage |
| P0-4 | `login/+page.svelte` L124-206 | OTP flow relies on exact string match `'Code sent'` — fragile, breaks if server changes message |

## Top Functional Issues (P1)

- **No loading indicators** on any list page (leads, contacts, accounts, opportunities, tickets, tasks, invoices) after filter/pagination
- **No error state handling** — all pages rely on SvelteKit generic error page
- **No empty state messages** — 0 results shows empty table with no explanation
- **Auth system duality**: Server stores JWT in httpOnly cookies; client `api.js` reads from localStorage — two systems that don't sync
- **en.json has ~100+ placeholder values** (e.g., `"edit_subtitle": "Edit Subtitle"`) — not real English translations
- **contacts API**: Client-side `apiRequest` reads JWT from localStorage, but Cookies-based auth is used server-side — auth will fail
- **Token refresh calls `goto('/login')`** as side effect in utility function — redirects user unexpectedly

## Top API Integration Issues (P2)

- `dashboard/+page.server.js`: `task.assigned_to.some((id) => id === userId)` assumes array of IDs but API returns objects
- `dashboard/+page.server.js`: `parseFloat(opp.amount)` returns NaN if amount is undefined, breaks revenue sums
- `leads/+page.server.js`: Kanban query params omit `assigned_to` filter
- `contacts/+page.server.js`: Contact `update` action missing `account` field
- `tickets/+page.server.js`: Watching endpoint URL doesn't support same filters as list endpoint
- `invoices/+page.server.js`: `totalAmount` defaults to string `'0.00'` instead of number — breaks `formatCurrency`

## i18n Audit Summary

- **fa.json**: Mostly complete for the audited pages
- **en.json**: Severely incomplete — missing entire `industries`, `interaction`, `followups`, `supervision` sections. ~100+ keys have placeholder English values (not real translations)
- **Hardcoded strings**: Login page (20+ Persian), accounts page (30+ English industries), tickets (6+ English statuses), tasks (6+ English statuses/priorities), invoices (7+ English statuses), opportunities (6+ English stages)

---

*Full detailed issue list with line numbers available in the subagent output.*
