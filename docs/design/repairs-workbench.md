# Repairs Workbench — Design Brief (Figma Make)

Design brief for the **Repairs Workbench** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **repairs & maintenance workbench** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, data-dense. Think defense/aerospace maintenance-management software. This is a technician-focused workspace.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The workbench lives in the main content area with a **top-level tab bar**.

### Page header
- Page title: "Repairs & Maintenance".
- Top-level tabs: **Defects**, **Repair Orders**, **Component Replacements**.

### Tab 1 — Defects (default)
- Filter bar: search, **severity** (Low / Medium / High / Critical), **status** (Reported / In Progress / Fixed / Verified), drone.
- Table: drone (serial/name), defect type, **severity pill**, **status pill**, detected-at, reporter, row actions.
- **+ Report Defect** action (form: drone, defect type, severity, description).
- **Defect detail drawer** (opens from a row): full description, **status update** control (transition + note), and an **event history** timeline. Critical severity emphasized.

### Tab 2 — Repair Orders
- Filter bar: status (Pending / In Progress / Completed / Cancelled), assigned-to, drone.
- Table: drone, linked defect, status pill, assigned-to, created/updated timestamps, row actions.
- **+ New Order** and per-order **status transition** control.
- Order detail drawer: order info, linked defect, and a **component replacements** sub-list for that order.

### Tab 3 — Component Replacements
- Table: drone, component type, old serial → new serial, reason, replaced-at, replaced-by.
- **+ Log Replacement** action (form) and an **Export CSV** button.

## Components & states to include
- Top-level tab bar: default / active
- Severity pill (Low / Medium / High / Critical) and status pills (defect + repair-order variants)
- Filter dropdown + removable chip
- Data table: sortable header, row default / hover / selected; sticky header
- Detail drawer (defect + order): info, status-update control, event-history timeline
- Report-defect / new-order / log-replacement forms (inputs, selects, textarea)
- Status-transition modal (from→to + note)
- Export button; empty states per tab; loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; tables/panels `#161D26` with 1px subtle border; drawer as an elevated right panel.
- **Accent:** muted amber/gold `#C8A24A` for active tab, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; serials in IBM Plex Mono.
- **Severity palette:** Low `#8A94A6` (grey), Medium `#C8A24A` (amber), High `#F0883E` (orange), Critical `#E5484D` (red).
- **Defect status:** Reported grey, In Progress amber, Fixed blue `#4C8DFF`, Verified green `#3FB950`. Repair-order status: Pending grey, In Progress amber, Completed green, Cancelled red.
- **Type:** Inter or IBM Plex Sans; IBM Plex Mono for serials. Page title 24px semibold, table cells 13–14px, header 12px uppercase tracking.
- **Radius:** 12px cards, 8px inner elements, pills fully rounded.
- **Density:** compact rows (~44px), clear alignment; critical items visually prioritized.

## Behavior notes (annotations, not visuals)
- Defects: `defects/`, `.../history/`, status update endpoint. Orders: `orders/`. Replacements: `replacements/`, `.../export/` (CSV).
- Drone Repair History (full per-drone timeline) is a related view: `drones/<drone_id>/history/`.
- Report/update/verify, order management, and replacement logging are gated by the RBAC permission matrix (Technician manages maintenance; Commander verifies/exports; Viewer read-only).
