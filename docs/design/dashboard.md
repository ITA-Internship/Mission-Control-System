# Dashboard / Home — Design Brief (Figma Make)

Design brief for the **Dashboard / Home** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **role-aware operations dashboard** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, dense but scannable, data-forward. Think defense/aerospace ops software, not a consumer SaaS dashboard.

Use an **app shell layout**: a fixed left **sidebar navigation** (icons + labels), a top bar, and a main content area with a responsive grid. The dashboard is the landing page after sign-in.

### App shell (shared across all pages)
- **Left sidebar** (~240px, collapsible to icon rail): logo/wordmark at top; nav items with icons — Dashboard, Drones, Missions, Repairs, Media, Administration; each nav item can be hidden based on role. Active item highlighted with accent bar.
- **Top bar:** page title on the left; on the right a global search, a notifications bell, and a user menu (avatar, name, rank, role badge, sign out).
- Main area: 24px padding, max content width ~1440px.

### KPI stat row (top of main area)
Four to five **stat tiles** in a row (wrap on smaller screens). Each tile: large number, label, small trend/delta, and a small icon. Suggested KPIs:
- **Active Missions** (count)
- **Drones by Status** (total, with a mini breakdown)
- **Open Defects** (count, with critical highlighted red)
- **Drones in Maintenance** (count)
- **System Health** (small OK/degraded pill sourced from the health endpoint)

### Content grid (below KPIs)
A two-column responsive grid (stacks to one column on mobile):
- **Fleet Status donut/bar chart** — drones grouped by status (Active, In Mission, Damaged, Maintenance, Lost, Decommissioned…), each with its status color. Legend with counts.
- **Active & Recent Missions list** — compact rows: mission title, status pill, commander, location, started-at. "View all" link to Missions Board.
- **Open Defects panel** — rows with drone, defect type, severity pill (Low→Critical), reported date. Critical items visually prioritized.
- **Recent Activity / Audit feed** — timeline of recent audit events (actor, action, target, timestamp, result status).

### Role awareness
Panels and KPIs shown depend on the signed-in role (Admin, Commander, Dispatcher, Operator, Technician, Viewer). Design a **full Admin/Commander variant** (all panels) and note that lower roles see a reduced set (e.g. Operator sees their assigned missions and media, not the audit feed).

## Components & states to include
- Sidebar nav item: default / hover / active / collapsed
- Stat tile: default / with-trend / alert (critical)
- Status pill / badge: one per drone status and one per severity level (color-coded)
- Chart: donut and horizontal bar variants with legend
- List row: default / hover, with pill + metadata
- Empty state for each panel ("No active missions", "No open defects")
- Loading skeletons for tiles, charts, and lists

## Visual system
- **Theme:** dark mode. App background `#0B0F14`; panels/cards `#161D26` with 1px subtle border; sidebar slightly darker `#0E141B`.
- **Accent:** muted amber/gold `#C8A24A` for active nav, links, primary actions and focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`.
- **Status palette (reuse across the app):** Active `#3FB950` (green), In Mission `#4C8DFF` (blue), Maintenance `#C8A24A` (amber), Damaged `#E5484D` (red), Lost/Decommissioned `#8A94A6` (grey). Severity: Low grey → Medium amber → High orange `#F0883E` → Critical red `#E5484D`.
- **Type:** Inter or IBM Plex Sans. KPI numbers ~32px semibold; panel titles 16px semibold; body 14px; metadata 12–13px muted.
- **Radius:** 12px cards, 8px inner elements, pills fully rounded.
- **Density:** compact — this is an operator tool; favor information density over whitespace, but keep clear grouping.

## Behavior notes (annotations, not visuals)
- KPIs and panels aggregate from the drones, missions, repairs, media, and audit-log APIs.
- System Health pill sourced from `GET /api/health/`.
- Navigation and panel visibility are gated by the RBAC permission matrix.
