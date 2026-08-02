# Master Audit Report — BottleCRM

**Date**: 2026-07-18 | **Audit Type**: Full-Stack Code Review | **Status**: Complete

---

## Executive Summary

A comprehensive full-stack audit of the BottleCRM system covering **Django backend** (10 apps, ~167 API endpoints), **SvelteKit frontend** (24 pages), **Flutter mobile** (12 screens), **MCP server** (7 tools), and **infrastructure** (Docker, configs).

**Total Issues Found: 196**

---

## Overall Statistics

| Phase | P0 (Critical) | P1 (Functional) | P2 (Visual/API) | P3 (Code Quality) | **Total** |
|-------|:---:|:---:|:---:|:---:|---:|
| Phase 1: Backend API | 2 | 11 | 23 | 33 | **69** |
| Phase 2: Frontend Pages | 4 | 18 | 42 | 30 | **94** |
| Phase 3: Integration | 0 | 3 | 8 | 0 | **11** |
| Phase 4: Mobile App | 0 | 0 | 2 | 1 | **3** |
| Phase 5: MCP Server | 0 | 1 | 3 | 2 | **6** |
| Phase 6: Infrastructure | 0 | 1 | 7 | 4 | **12** |
| Supervision Page (prev) | 0 | 1 | 0 | 0 | **1** |
| **TOTAL** | **6** | **35** | **85** | **70** | **196** |

---

## P0 — Critical Issues (Must Fix Immediately)

| # | Area | Issue |
|---|------|-------|
| P0-1 | Backend | `CsatSurvey.RATING_CHOICES` is a generator expression — silently drops all rating choices after first use |
| P0-2 | Backend | `APISettings.apikey` stored in plaintext — all API keys exposed if DB compromised |
| P0-3 | Frontend | ~20 hardcoded Persian strings on login page — entire page bypasses i18n system |
| P0-4 | Frontend | Typo `'compaign'` instead of `'campaign'` in leads validSources — campaign leads get null source |
| P0-5 | Frontend | 30 industry labels hardcoded English on accounts page — no i18n |
| P0-6 | Frontend | OTP flow relies on exact string match `'Code sent'` — breaks if server changes message |

---

## Top P1 Issues by Impact

| # | Area | Issue | Impact |
|---|------|-------|--------|
| P1-1 | Dashboard | N+1 query explosion (50+ queries) — no `select_related` | Page load 5-10x slower |
| P1-2 | Auth | Client/server auth duality — cookies vs localStorage | Client-side API calls fail |
| P1-3 | All pages | No loading/error/empty states | Poor UX on slow connections |
| P1-4 | i18n | en.json has ~100+ placeholder values | English UI shows nonsense |
| P1-5 | Backend | `IsSuperAdmin` crashes on null email | 500 crash on admin-only endpoints |
| P1-6 | Backend | Invoice totals stale until manual save | Wrong amounts displayed |
| P1-7 | Frontend | `task.assigned_to.some(id === userId)` compares object to ID | Upcoming tasks never filter |

---

## Fix Roadmap (Recommended Order)

### Week 1 — Critical Fixes
1. Fix P0-2: Hash `APISettings.apikey`
2. Fix P0-1: Convert `CsatSurvey.RATING_CHOICES` from generator to tuple
3. Fix P0-3: i18n-ize login page (~20 strings)
4. Fix P0-4: Fix `'compaign'` typo
5. Fix P0-5: Add `$_()` to industry labels

### Week 2 — Data Integrity & Auth
6. Fix P1-1/P1-2/P1-3: Add `select_related` to dashboard
7. Fix P1-6: Fix invoice total recalculation chain
8. Fix P1-5: Fix `IsSuperAdmin` null email crash
9. Fix P1-4: Populate en.json placeholder values

### Week 3 — UX & Integration
10. Add loading/error/empty states to all pages (P1-3)
11. Fix auth system duality (P1-2)
12. Fix API response shape mismatches (Phase 3)
13. Fix dashboard `assigned_to` comparison bug (P1-7)

### Week 4 — Completeness
14. Complete en.json translations
15. Add missing kanban filters
16. Fix contacts update missing account field
17. Add health checks to Docker

---

## Report Files

| File | Contents |
|------|----------|
| `docs/audit/phase1-backend-api.md` | 69 issues — models, views, permissions, security |
| `docs/audit/phase2-frontend-pages.md` | 94 issues — pages, i18n, RTL, a11y, components |
| `docs/audit/phase3-6-combined.md` | 32 issues — integration, mobile, MCP, infrastructure |
| `docs/audit/MASTER_AUDIT_REPORT.md` | This file — summary and roadmap |

---

## Audit Scope Boundaries

- ✅ **Covered**: All code files, models, views, serializers, URLs, permissions, frontend pages, i18n files, API helpers, Docker configs, Django settings
- ⚠️ **Limited**: Mobile app (Flutter) — code-structure-only review, not built/run
- ❌ **Excluded**: Performance profiling, penetration testing, database migration audit, load testing, dependency vulnerability scanning

---

## Legend

| Severity | Meaning |
|----------|---------|
| **P0** | Critical — blocks core functionality, causes data loss, or is a security emergency |
| **P1** | Functional — breaks a feature, degrades UX significantly, or causes incorrect behavior |
| **P2** | Minor — visual/UX degradation, API contract issues, missing polish |
| **P3** | Code Quality — code smells, DRY violations, inconsistent patterns, dead code |
