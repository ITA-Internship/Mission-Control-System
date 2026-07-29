# Administration — Design Brief (Figma Make)

Design brief for the **Administration** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design an **administration console** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, orderly and authoritative. Think defense/aerospace admin/IT console. This is restricted to Admin (and partly Commander) roles.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The console lives in the main content area with a **top-level tab bar**.

### Page header
- Page title: "Administration".
- Top-level tabs: **Users**, **Military Units**, **Audit Log**.

### Tab 1 — Users (default)
- Filter bar: search (name/email), **role**, **unit**, **status** (Active / Inactive).
- Table: name, email, **role badge**, unit, status pill, created-by, last login, row actions.
- **+ Create User** action (form: email, name, role, unit; triggers activation email).
- Row actions: **activate / deactivate** toggle, **change role** (select), edit.
- **Change-role modal** and **activate/deactivate confirm** with reason note (both are audited).

### Tab 2 — Military Units
- Table: unit name, **code** (unique), description, active status, drone/user counts if available.
- **+ Add Unit** action (form: name, code, description) and edit; toggle active/inactive.

### Tab 3 — Audit Log
- System-wide immutable action log table: **action type** pill, actor, target user, **result status** (Success / Failure) pill, IP address, user agent, timestamp.
- Filter bar: action type, actor, result, date range. Sortable, paginated.
- **Export CSV** button. Rows are read-only (immutable).

## Components & states to include
- Top-level tab bar: default / active
- Role badge (one per role: Admin, Commander, Dispatcher, Operator, Technician, Viewer) and status pill (Active / Inactive)
- Data table: sortable header, row default / hover / selected; sticky header; pagination
- Create-user / add-unit forms (inputs, selects); change-role modal
- Activate/deactivate confirm modal with reason note
- Audit action-type pill and result-status pill (Success / Failure)
- Export button; filter dropdown + removable chip; empty states; loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; tables/panels `#161D26` with 1px subtle border.
- **Accent:** muted amber/gold `#C8A24A` for active tab, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; IP/user-agent in IBM Plex Mono.
- **Role badges:** Admin amber `#C8A24A`, Commander blue `#4C8DFF`, Dispatcher teal, Operator green `#3FB950`, Technician orange `#F0883E`, Viewer grey `#8A94A6` (keep restrained and consistent app-wide).
- **Status/result:** Active/Success green `#3FB950`, Inactive grey `#8A94A6`, Failure/Denied red `#E5484D`.
- **Type:** Inter or IBM Plex Sans; IBM Plex Mono for IPs. Page title 24px semibold, table cells 13–14px, header 12px uppercase tracking.
- **Radius:** 12px cards, 8px inner elements, pills/badges fully rounded.
- **Density:** compact rows (~44px), clear alignment; destructive/failure states clearly flagged.

## Behavior notes (annotations, not visuals)
- Users: `users/`, `users/<pk>/status/`, role change `users/<user_id>/role/`. Units: managed via accounts admin/API. Audit: `audit-log/`, `.../export/` (CSV).
- Creating a user triggers an activation email flow; new users may have `must_change_password` set (see [Auth](auth.md) force-password-change).
- Audit log is **immutable** (no edit/delete) — render read-only.
- The entire console is gated by the RBAC permission matrix — Admin has full access; Commander sees a reduced set; other roles do not see this page.
