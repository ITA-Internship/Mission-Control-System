# Drone Detail — Design Brief (Figma Make)

Design brief for the **Drone Detail** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **drone detail page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, data-dense. Think defense/aerospace asset-management software. This is the deep-dive view for a single drone, opened from the Drone Inventory table.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The detail view lives in the main content area.

### Page header
- Breadcrumb: "Drones / {serial number}".
- Title row: drone **name** + **serial / inventory number** (monospace), a large **status badge** (color-coded with indicator dot), and a **classification** pill.
- Right-side action buttons: **Edit**, **Change Status**, **Write-off**, overflow menu. Actions gated by role.
- A summary strip: model (name + manufacturer), military unit, acquired date, last-updated.

### Tabbed content (design each tab as a frame)

**Tab 1 — Specs (default)**
- Grouped spec cards: hardware, firmware, range, payload, and other technical fields (label → value rows, two columns).
- An **Edit** mode variant turning the spec rows into a form with Save/Cancel.

**Tab 2 — Status History**
- Vertical **timeline** of lifecycle transitions: from-status → to-status badges, actor, timestamp, and note. Most recent first. Empty state included.

**Tab 3 — Spec Change History**
- Audit table of spec edits: field changed, old value → new value, changed-by, timestamp. Sortable, paginated.

**Tab 4 — Write-offs**
- If not written off: a **Create Write-off** panel/form (reason, authorized-by, related mission, document number, date) plus any prior records.
- Immutable **write-off record card** (read-only once created) with a link to the history report.

## Components & states to include
- Status badge (one per drone status) with indicator dot; classification pill
- Tab bar: default / active / disabled
- Spec card: read view and edit (form) view
- Timeline item: from→to badges, actor, timestamp, note
- Audit table row: field, old→new value, actor, timestamp
- Write-off form (inputs, select, date) and read-only immutable record card
- Action buttons: primary / secondary / destructive (write-off) with hover / disabled
- Change-status modal (from→to with allowed transitions + note)
- Empty states per tab and loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; cards/panels `#161D26` with 1px subtle border; tab bar with accent underline on active.
- **Accent:** muted amber/gold `#C8A24A` for active tab, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; identifiers in IBM Plex Mono.
- **Status palette (reuse app-wide):** Active `#3FB950`, In Mission `#4C8DFF`, Maintenance `#C8A24A`, Damaged `#E5484D`, Lost/Decommissioned/Sold/Transferred/Written-off `#8A94A6`.
- **Destructive:** write-off / decommission actions in red `#E5484D`.
- **Type:** Inter or IBM Plex Sans; IBM Plex Mono for identifiers. Title 24px semibold, section titles 16px, spec labels 13px muted, values 14px.
- **Radius:** 12px cards, 8px inner elements, pills/badges fully rounded.
- **Density:** compact spec rows, clear grouping, right-aligned numeric values.

## Behavior notes (annotations, not visuals)
- Data from `drones/<pk>/`, `.../history/`, `.../spec-changes/`, and `write-offs/`.
- Status badges driven by the backend `STATUS_UI` map / `status_label` / `status_indicator` / `status_category`.
- Write-off and status-history records are **immutable** once created — render read-only.
- Edit, Change Status, and Write-off actions are gated by the RBAC permission matrix.
