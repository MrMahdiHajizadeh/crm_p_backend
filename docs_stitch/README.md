# Emarat Connect (عمارت کانکت) - Comprehensive Redesign Documentation for Stitch

This documentation directory contains complete API specifications, page structures, routing maps, design system tokens, and page-by-page UI redesign instructions for **Emarat Connect (عمارت کانکت)**.

## Document Index

1. **[01_API_Endpoints_Specification.md](file:///c:/Users/mrmah/OneDrive/Desktop/CRM%20p/Django-CRM/docs_stitch/01_API_Endpoints_Specification.md)**
   - Complete reference for all active Django REST Framework API endpoints.
   - HTTP methods, authentication headers (`Authorization: Bearer <jwt>`, `org: <org_id>`), query parameters, request payloads, and JSON response structures.

2. **[02_Pages_and_Routing_Architecture.md](file:///c:/Users/mrmah/OneDrive/Desktop/CRM%20p/Django-CRM/docs_stitch/02_Pages_and_Routing_Architecture.md)**
   - Complete route tree map of the SvelteKit application (`/`, `/leads`, `/contacts`, `/accounts`, `/opportunities`, `/tickets`, `/follow-ups`, `/supervision`, `/invoices`, `/solutions`, `/support`, `/login`).
   - Server-side loaders (`+page.server.js`), API data flow, and state handling.

3. **[03_UI_Component_Catalog_and_Design_System.md](file:///c:/Users/mrmah/OneDrive/Desktop/CRM%20p/Django-CRM/docs_stitch/03_UI_Component_Catalog_and_Design_System.md)**
   - Core design tokens: dark mode color palette (HSL tailored colors), glassmorphism specs, mesh gradient background glows, typography, spacing, and micro-animations.
   - Reusable UI component catalog (`KPICard`, `FocusBar`, `HotLeadsPanel`, `OpportunitiesTable`, `ActivityFeed`, `TeamPerformance`, `CrmTable`, `PageHeader`, `InteractionDialog`, `AppSidebar`, `AppShell`).

4. **[04_Page_by_Page_Redesign_Specs.md](file:///c:/Users/mrmah/OneDrive/Desktop/CRM%20p/Django-CRM/docs_stitch/04_Page_by_Page_Redesign_Specs.md)**
   - Detailed blueprint for redesigning every page in the application.
   - Expected UI layout, required widgets, state behavior, empty states, and API mapping for Stitch design implementation.

---

## Technical Stack Overview

- **Frontend**: SvelteKit 5 + Tailwind CSS v4 + `@lucide/svelte` + `svelte-i18n` (Persian RTL & English LTR).
- **Backend**: Django 5 + Django REST Framework + SimpleJWT + SQLite (`db.sqlite3`).
- **Organization Scope**: Single dedicated organization (**عمارت کانکت / Emarat Connect**).
