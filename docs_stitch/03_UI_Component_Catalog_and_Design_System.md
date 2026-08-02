# 03 - UI Component Catalog and Design System

This document outlines the visual design system, glassmorphism tokens, color palettes, typography, and reusable UI component catalog for **Emarat Connect (عمارت کانکت)**.

## 1. Visual Design Aesthetics

- **Style Theme**: Executive Dark Mode Glassmorphism with Vibrant Accent Highlights.
- **Glassmorphism Spec**:
  - Container Background: `bg-surface-raised/70 backdrop-blur-2xl dark:bg-card/40`
  - Border Styling: `border border-border/60 dark:border-border/40`
  - Ambient Glows: Soft background radial gradient glows (`bg-primary/20 blur-3xl`, `bg-amber-500/10 blur-3xl`).

---

## 2. Color Palette & Badges

| Accent Category | Tailwind Classes | Use Cases |
| :--- | :--- | :--- |
| **Primary (Orange/Amber)** | `from-primary via-orange-500 to-amber-500` | Hero text, active tab highlights, primary CTA buttons |
| **Rose / Urgent** | `bg-rose-500/10 text-rose-500 border-rose-500/20` | Overdue tasks, HOT leads, deletion alerts |
| **Emerald / Success** | `bg-emerald-500/10 text-emerald-500 border-emerald-500/20` | Won revenue, completed actions, positive conversion rates |
| **Blue / Corporate** | `bg-blue-500/10 text-blue-500 border-blue-500/20` | Accounts, company metrics, corporate client info |
| **Purple / Activity** | `bg-purple-500/10 text-purple-500 border-purple-500/20` | Follow-ups, total tasks, interactions |
| **Amber / Warning** | `bg-amber-500/10 text-amber-500 border-amber-500/20` | Champions podium 🥇, warning notifications, due today |

---

## 3. Reusable UI Component Catalog

### 1. `KPICard.svelte`
- Executive stat card with glowing ambient icon orb, metric value (`tabular-nums`), trend pill, and subtitle.

### 2. `FocusBar.svelte`
- Floating glassmorphic action center with animated pulse dots (`animate-pulse`) for urgent items.

### 3. `HotLeadsPanel.svelte`
- High-priority lead cards featuring glowing fire icons, contact info, follow-up dates, and quick actions.

### 4. `OpportunitiesTable.svelte`
- Spotlight table for active sales deals featuring probability progress bars, deal stage badges, and formatted amounts.

### 5. `ActivityFeed.svelte`
- Real-time activity timeline stream with node icons color-coded by action type (Create, Update, Delete, Assign).

### 6. `TeamPerformance.svelte`
- Interactive Leaderboard:
  - Top 3 Champions Podium (🥇 Gold, 🥈 Silver, 🥉 Bronze).
  - Cards vs Table View switcher toggle.
  - Interactive Click-to-View Detail Modal with unicode-safe initials (`Array.from(name)[0]`).

### 7. `AppSidebar.svelte`
- Main navigation bar displaying logo `static/logo.png`, single-company name `عمارت کانکت`, workspace monogram avatar, user email, and grouped navigation items.
