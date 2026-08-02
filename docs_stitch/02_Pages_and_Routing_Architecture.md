# 02 - Pages and Routing Architecture

This document describes the front-end page structure, routing system, server loaders, and state management in SvelteKit for Emarat Connect (عمارت کانکت).

## Route Architecture Map

All main application routes reside under `src/routes/(app)` wrapped inside the `AppShell` layout (`AppSidebar` & `AppHeader`).

| Route | Page File | Purpose & Data Loader |
| :--- | :--- | :--- |
| `/` | `src/routes/(app)/+page.svelte` | **Executive Dashboard**: Consolidated metrics, FocusBar, Deals Spotlight, Hot Leads, Activity Feed, Team Leaderboard. Loaded via `+page.server.js` (`GET /api/dashboard/`). |
| `/leads` | `src/routes/(app)/leads/+page.svelte` | **Leads List & Kanban Board**: Filterable table & kanban by rating (HOT, WARM, COLD) and status. |
| `/leads/[id]` | `src/routes/(app)/leads/[id]/+page.svelte` | **Lead Details View**: Contact info, interaction history, notes, follow-up scheduler. |
| `/contacts` | `src/routes/(app)/contacts/+page.svelte` | **Contacts Directory**: Individual contact list with search, tag filters, and phone/email actions. |
| `/accounts` | `src/routes/(app)/accounts/+page.svelte` | **Accounts / Companies Directory**: Corporate clients, billing info, associated contacts, and deals. |
| `/opportunities` | `src/routes/(app)/opportunities/+page.svelte` | **Sales Deals / Opportunities**: Kanban pipeline & list views of deals by stage. |
| `/tickets` | `src/routes/(app)/tickets/+page.svelte` | **Support Ticket Desk**: Ticket management table, priority tags, status filtering, and approvals. |
| `/follow-ups` | `src/routes/(app)/follow-ups/+page.svelte` | **Follow-ups Stream**: Dedicated view for upcoming and today's customer follow-up actions. |
| `/supervision` | `src/routes/(app)/supervision/+page.svelte` | **Management Supervision**: Oversight dashboard for team activities and response times. |
| `/invoices` | `src/routes/(app)/invoices/+page.svelte` | **Invoices & Financial Desk**: Invoice history, payment statuses, estimates, products, and PDF generation. |
| `/solutions` | `src/routes/(app)/solutions/+page.svelte` | **Knowledge Base / Solutions**: FAQ and solution articles repository for support agents. |
| `/support` | `src/routes/(app)/support/+page.svelte` | **Help Desk & Platform Support**: System documentation, feature requests, and contact support. |
| `/login` | `src/routes/(no-layout)/login/+page.svelte` | **Authentication Page**: Phone OTP login & password login form. |

---

## Server Loaders & Data Binding (`+page.server.js`)

Each page route connects to Django REST API via helper utilities:
- `apiRequest(endpoint, options, { cookies, org })` in `$lib/api-helpers.js`.
- Automatic JWT refresh handling on 401 response.
- Organization context passed automatically in headers (`org: <org_id>`).

## Localization & Direction (Persian RTL & English LTR)

- Powered by `svelte-i18n`.
- Translation dictionaries:
  - `src/lib/i18n/fa.json` (Persian / Farsi - Default locale `fa`)
  - `src/lib/i18n/en.json` (English - Fallback locale `en`)
- HTML element contains `dir="rtl"` when `$locale === 'fa'`, with Tailwind RTL utility classes (`text-right`, `space-x-reverse`, `mr-auto`, `pr-4`).
