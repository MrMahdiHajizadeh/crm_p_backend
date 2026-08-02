# Phase 1: Backend API Audit Report

**Date**: 2026-07-18 | **Auditor**: AI Code Review | **Status**: Complete

---

## 1. Endpoint Inventory

### Root API Structure (`backend/crm/urls.py`)
```
/api/ → common.app_urls (aggregator)
/api/public/ → invoices.public_urls
/admin/ → Django admin
/schema/ → DRF Spectacular
/swagger-ui/ → Swagger UI
/api/schema/redoc/ → ReDoc
```

### API Route Map (via `common/app_urls/__init__.py`)

| Prefix | App | Namespace |
|--------|-----|-----------|
| `/api/` | common (auth, dashboard, activities, notifications, docs, org, settings, tags, custom-fields, teams, users, PATs) | `common_urls` |
| `/api/accounts/` | accounts | `api_accounts` |
| `/api/contacts/` | contacts | `api_contacts` |
| `/api/leads/` | leads | `api_leads` |
| `/api/opportunities/` | opportunity | `api_opportunities` |
| `/api/tasks/` | tasks | `api_tasks` |
| `/api/cases/` | cases | `api_cases` |
| `/api/time-entries/` | cases (time entries) | `api_time_entries` |
| `/api/invoices/` | invoices | `api_invoices` |
| `/api/boards/` | tasks (board URLs) | `api_boards` |
| `/api/business-hours/` | business_hours | `api_business_hours` |
| `/api/macros/` | macros | `api_macros` |
| `/api/public/csat/<token>/` | cases (public CSAT) | — |

### Per-App Endpoint Count

| App | Endpoint Count |
|-----|---------------|
| **common** | 30 |
| **accounts** | 5 |
| **contacts** | 5 |
| **leads** | ~15 |
| **opportunity** | 11 |
| **cases** | ~45 |
| **tasks** | 15 |
| **invoices** | 25 |
| **time-entries** | 4 |
| **boards** | ~5 |
| **business_hours** | 4 |
| **macros** | 3 |
| **TOTAL** | **~167** |

---

## 2. Model & Serializer Audit

### P0 — Critical / Data Loss (2 issues)

| # | File | Issue |
|---|------|-------|
| **P0-1** | `common/models.py` ~505 | `APISettings.apikey` stored in **plaintext** (not hashed). If DB compromised, all API keys exposed. Multi-tenant security-critical. |
| **P0-2** | `cases/models.py` ~410 | `CsatSurvey.RATING_CHOICES` is a **generator expression** `((i, str(i)) for i in range(1,6))`. Generator is consumed on first access and becomes empty thereafter — silently drops all rating choices in DRF serializers/forms after first use. |

### P1 — Functional Bugs (11 issues)

| # | File | Issue |
|---|------|-------|
| **P1-1** | `common/models.py` ~39 | `User.phone` is `unique=True` **globally**, not scoped per org. Two users in different orgs cannot share phone number. |
| **P1-2** | `common/models.py` ~340 | `CommentFiles.org` has `null=True, blank=True` with comment "Temporarily nullable for migration." RLS gap — comment files can exist without org assignment. |
| **P1-3** | `common/models.py` ~238 | `Profile.__str__` accesses `self.user.email` and `self.org.name`. Without `select_related`, causes N+1 queries in admin, templates, logging. |
| **P1-4** | `accounts/models.py` ~153 | `AccountEmailLog.__str__` accesses `self.email.message_subject`. `email` FK has `on_delete=SET_NULL, null=True` — AttributeError crash if parent deleted. |
| **P1-5** | `dashboard_views.py` ~49 | `ApiHomeView.get()` accesses `request.profile.org` with **no guard** for None — unhandled AttributeError (500 crash) if middleware fails. |
| **P1-6** | `dashboard_views.py` ~53 | `ApiHomeView.get()` — **No `select_related`/`prefetch_related`** on account/contact/lead/opportunity querysets. Serializer accesses cause N+1 explosion (50+ queries for dashboard). |
| **P1-7** | `dashboard_views.py` ~105 | `pipeline_by_stage` loop executes `.count()` + `.aggregate()` **per stage** — N+1 where N=number of stages (6-8). |
| **P1-8** | `dashboard_views.py` ~197 | `goal_summary` calls `g.compute_progress()` for each goal, executing its own DB query per goal. N additional queries for N goals. |
| **P1-9** | `permissions.py` ~72 | `IsSuperAdmin.has_permission()` calls `request.user.email.endswith(...)`. `email` is `null=True` — AttributeError crash (500) on any endpoint using this class if email is None. |
| **P1-10** | `invoices/models.py` ~360 | `Invoice.save()` calls `recalculate_totals()` which accesses `self.line_items.all()`. On new unsaved invoice, no line items saved yet → totals = $0.00. Second save required. |
| **P1-11** | `invoices/models.py` ~560 | `InvoiceLineItem.save()` does **NOT** trigger parent invoice recalculation. Invoice totals stale until manual invoice save. |

### P2 — Minor Issues (23 issues)

| # | File | Issue |
|---|------|-------|
| P2-1 | `common/models.py` ~270 | `Comment.commented_by` FK no explicit `related_name` — fragile auto-generated name. |
| P2-2 | `common/models.py` ~443 | `Document.title` is `TextField` (unbounded) instead of `CharField(max_length=...)`. |
| P2-3 | `common/models.py` ~500 | `APISettings.title` is `TextField` for a short title — should be CharField. |
| P2-4 | `common/models.py` ~104 | `Org.api_key` is `TextField` for a uuid4 key — should be `CharField(max_length=36)`. |
| P2-5 | `common/models.py` ~195 | `Tags` uses old-style `unique_together = [...]` — deprecated in Django 4.2+. |
| P2-6 | `common/models.py` ~241 | `Profile` uses old-style `unique_together` — same deprecation. |
| P2-7 | `accounts/models.py` ~70 | `Account` has two separate contact linkage mechanisms (direct M2M + Contact FK back-ref) — data ambiguity. |
| P2-8 | `accounts/models.py` ~120 | `AccountEmail.recipients` M2M has typo: `related_name="recieved_email"` (should be "received_email"). |
| P2-9 | `accounts/models.py` ~136 | `AccountEmail.__str__` returns `f"{self.message_subject}"` — returns "None" string when null. |
| P2-10 | `contacts/models.py` ~35 | `Contact` has both `organization` (CharField) and `account` (FK) for same concept — data can diverge. |
| P2-11 | `leads/models.py` ~63 | `Lead.first_name/last_name` have `null=True` but no `blank=True` — inconsistent validation. |
| P2-12 | `cases/models.py` ~210 | `Case.clean()` does `objects.only("status").get(pk=self.pk)` — raises DoesNotExist for unsaved instances. |
| P2-13 | `cases/models.py` ~220 | `Case.clean()` imports `from cases.approvals import Approval` inside method body — called on every `full_clean()`. |
| P2-14 | `cases/models.py` ~20 | `Case.name` has `max_length=64` — very short for descriptive support ticket names. |
| P2-15 | `cases/models.py` ~340 | `CaseWatcher.org` can differ from `CaseWatcher.case.org` — no validation at DB level. |
| P2-16 | `opportunity/models.py` ~355 | `OpportunityLineItem.save()` overwrites `unit_price=0` (intentionally free) with product price. |
| P2-17 | `opportunity/models.py` ~370 | `OpportunityLineItem.save()` calls `opportunity.recalculate_amount()` then `opportunity.save()` — recursive save risk if triggered during opportunity's own save. |
| P2-18 | `opportunity/models.py` ~375 | `OpportunityLineItem.delete()` recalculates but does NOT save opportunity — stale amounts after bulk deletes. |
| P2-19 | `tasks/models.py` ~370 | `Task.clean()` validates single parent entity; `BoardTask` has same FKs but no such validation. |
| P2-20 | `invoices/models.py` ~187 | `Invoice.invoice_number` is `unique=True` without org scope — theoretical cross-org collision. |
| P2-21 | `invoices/models.py` ~650 | `Payment.save()` causes second DB write to invoice after every payment save. |
| P2-22 | `business_hours/models.py` ~76 | `BusinessHoliday.org` can differ from `holiday.calendar.org` — no DB-level validation. |
| P2-23 | `base.py` ~65 | `BaseModel.save()` uses `crum.get_current_user()` (thread-local). Returns None in Celery tasks/management commands — silently loses audit trail. |

### P3 — Code Quality (33 issues)

Selected highlights:
- `base.py` line 2: Imports `from common.models import models` instead of `from django.db import models` — fragile import chain
- `access_decorators_mixins.py`: **Empty file** (dead code) — should be deleted
- `leads/models.py` ~358: `InteractionLog.entity_type` choices duplicate `Activity.ENTITY_TYPE_CHOICES` — DRY violation
- `invoices/models.py`: `Estimate` and `Invoice` duplicate ~30 identical fields — should use abstract base model
- `tasks/models.py` ~300: `Task` has no `is_active` soft-delete field unlike Account, Contact, Lead, Opportunity, Case
- `cases/models.py` ~280: `Case._sla_calendar()` imports inside method body — lazy import in frequently called methods
- `common/models.py` ~436: `document_path()` parameter named `self` (misleading — it's a module-level upload_to callable)
- `common/models.py` ~570: `MagicLinkToken` has no `org` FK — inconsistent with rest of multi-tenant design
- `contact/models.py` ~121: `Contact.__str__` returns only `first_name` — indistinguishable in admin dropdowns

---

## 3. View & Logic Audit

### Dashboard (ApiHomeView)

| Severity | Issue |
|----------|-------|
| P1 | No guard for `request.profile` being None → 500 crash |
| P1 | No `select_related`/`prefetch_related` → 50+ N+1 queries |
| P1 | Pipeline-by-stage loop: N+1 counts per stage |
| P1 | Goal compute_progress: N queries for N goals |
| P2 | Uses `IsAuthenticated` but not `HasOrgContext` permission |
| P2 | `is_admin` check inlined instead of permission class |
| P3 | `hot_leads` serialization manually constructs dicts — fragile |

### ActivityListView

| Severity | Issue |
|----------|-------|
| P2 | Docstring says default limit=10, code uses limit=20 — mismatch |
| P1 | (Previously fixed) `created_at__lte` → should be `created_at__date__lte` |

### Permission System

| Severity | Issue |
|----------|-------|
| P1 | `IsSuperAdmin` crashes on null email |
| P2 | `HasOrgContext` defined but inconsistently applied across views |
| P3 | `access_decorators_mixins.py` is an empty dead file |

---

## 4. Security Findings

| Severity | Finding |
|----------|---------|
| P0 | API keys stored in plaintext in DB (`APISettings.apikey`) |
| P1 | `CommentFiles.org` nullable — RLS bypass possible |
| P1 | `IsSuperAdmin` crashes on null email → potential DoS |
| P2 | `BaseModel.save()` loses audit trail in async/Celery contexts |
| P2 | `CaseWatcher.org` and `BusinessHoliday.org` can differ from parent org |
| P3 | `MagicLinkToken` has no org FK — cross-org token reuse theoretically possible |

---

## 5. Summary Statistics

| Severity | Count |
|----------|-------|
| **P0 — Critical** | 2 |
| **P1 — Functional** | 11 |
| **P2 — Minor** | 23 |
| **P3 — Code Quality** | 33 |
| **TOTAL** | **69** |

---

## 6. Top Priority Issues (Fix Roadmap)

1. **P0-2**: Fix `CsatSurvey.RATING_CHOICES` generator → tuple (immediate crash fix)
2. **P0-1**: Hash `APISettings.apikey` (security critical)
3. **P1-5**: Add null guard on `ApiHomeView` profile access
4. **P1-6/P1-7/P1-8**: Add `select_related`/`prefetch_related` to dashboard querysets (performance)
5. **P1-10/P1-11**: Fix invoice total recalculation chain
6. **P1-9**: Fix `IsSuperAdmin` null email crash
7. **P1-4**: Fix `AccountEmailLog.__str__` null crash
