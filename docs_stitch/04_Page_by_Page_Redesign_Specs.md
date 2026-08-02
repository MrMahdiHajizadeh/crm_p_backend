# 04 - Page-by-Page Redesign Specifications

This document provides detailed design and structural requirements for redesigning every page in Emarat Connect (عمارت کانکت) via Stitch.

---

## 1. Executive Dashboard (`src/routes/(app)/+page.svelte`)

- **Target Audience**: Business Executives, Sales Managers, and CRM Administrators.
- **Layout Structure**:
  1. **Hero Executive Banner**:
     - Modern glass card with mesh background glows (`from-primary/10 via-surface-raised/80 to-primary/5`).
     - Animated pulse dot, today's Persian/English date, company welcome text (`Welcome to Emarat Connect`).
     - Quick revenue summary pill (`Total Revenue Won`).
  2. **Focus Bar (Urgent Action Center)**:
     - Stat cards for **Today's Follow-ups** and **Hot Leads**.
     - Direct arrow hover animations (`ArrowUpRight`).
  3. **Executive KPI Metric Grid (4 Cards)**:
     - **Total Leads** (Orange icon, active prospects count).
     - **Active Deals** (Violet icon, open opportunities count).
     - **Accounts** (Blue icon, corporate clients count).
     - **Contacts** (Emerald icon, individual people count).
  4. **Operational Hub (2-Column Grid)**:
     - **Left Column**: `OpportunitiesTable` (Deals Spotlight with probability progress meters).
     - **Right Column**: `HotLeadsPanel` (HOT leads with follow-up dates & quick contact actions).
  5. **Live Activity Stream (`ActivityFeed`)**:
     - Action node icons, user avatar, entity type badges, relative time tags.
  6. **Team Leaderboard (`TeamPerformance`)**:
     - Visual Podium for Top 3 Champions (🥇, 🥈, 🥉).
     - View switch toggle button (Grid Cards vs Detailed Table).
     - Clickable cards opening an interactive Member Activity Detail Modal.

---

## 2. Leads Management (`src/routes/(app)/leads/+page.svelte`)

- **Core Goal**: Efficient lead tracking, rating filter, status updates, and fast creation.
- **Design Blueprint**:
  - Top Action Header: Search input, Rating filter pills (All, HOT, WARM, COLD), Status filter dropdown, "Create Lead" primary button.
  - Dual View Toggle: **List Table View** vs **Kanban Board View** (columns: New, Assigned, In Process, Converted, Closed).
  - Row Card Specs: Lead name, company badge, rating flame badge, phone/email quick icons, last contacted date.

---

## 3. Lead Detail View (`src/routes/(app)/leads/[id]/+page.svelte`)

- **Core Goal**: 360-degree customer profile view and interaction logging.
- **Design Blueprint**:
  - Left Panel: Profile summary card, contact details, rating badge, status converter button ("Convert to Deal / Account").
  - Right Panel: Interaction timeline tabs (Notes, Calls, Emails, Follow-up Scheduler).

---

## 4. Contacts & Accounts Directory (`/contacts` & `/accounts`)

- **Design Blueprint**:
  - Glassmorphic data table with bulk selection, column visibility toggles, quick search, export options, and contact card modals.

---

## 5. Opportunities & Deals Pipeline (`/opportunities`)

- **Design Blueprint**:
  - Visual Kanban Pipeline with stage columns (`PROSPECTING`, `QUALIFICATION`, `PROPOSAL`, `NEGOTIATION`, `CLOSED_WON`, `CLOSED_LOST`).
  - Stage totals & deal value summary header pills.

---

## 6. Tickets & Support Desk (`/tickets`)

- **Design Blueprint**:
  - Ticket queue cards with priority tags (Urgent, High, Normal, Low), SLA resolution timer, assigned agent avatars, and status pills.

---

## 7. Follow-ups Stream (`/follow-ups`)

- **Design Blueprint**:
  - Dedicated action list sorted by due date, featuring quick-complete checkboxes, phone call triggers, and note attachments.

---

## 8. Supervision & Team Oversight (`/supervision`)

- **Design Blueprint**:
  - Administrative oversight dashboard displaying team activity heatmaps, response time averages, and member workload cards.

---

## 9. Invoices & Financial Desk (`/invoices`)

- **Design Blueprint**:
  - Invoice history table, PDF preview modal, status badges (Paid, Pending, Overdue, Draft), and total revenue totals.

---

## 10. Login & Authentication (`src/routes/(no-layout)/login/+page.svelte`)

- **Design Blueprint**:
  - Glassmorphic login card centered with mesh background glows.
  - App Logo (`static/logo.png`) & company name **عمارت کانکت**.
  - Tab Switcher: **OTP Login** (Phone number + 6-digit code) vs **Password Login**.
