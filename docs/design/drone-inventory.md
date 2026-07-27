# Drone Inventory — Design Brief (Figma Make)

Design brief for the **Drone Inventory** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **drone fleet inventory page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, data-dense table-driven layout. Think defense/aerospace asset-management software.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The inventory lives in the main content area.

### Page header
- Page title: "Drone Inventory" with a total count (e.g. "128 drones").
- **Toolbar** on the right with action buttons: **+ Add Drone** (primary), **Import CSV**, **Export CSV**, **Compare**, and a **Models** link (drone model catalog). Buttons collapse into an overflow menu on smaller screens.

### Filter bar
A horizontal filter/search bar above the table:
- Free-text search (serial number, inventory number, name).
- Dropdown filters: **Status** (multi-select), **Classification** (Recon / Combat / Transport / Surveillance), **Military Unit**, **Drone Model**.
- Active filters shown as removable chips. "Clear all" link.

### Data table (core)
A dense, sortable table with paginated results. Columns:
- **Serial / Inventory #** (monospace)
- **Name**
- **Model** (name + manufacturer)
- **Classification** (pill)
- **Status** (color-coded status badge with indicator dot)
- **Military Unit**
- **Acquired** (date)
- **Row actions** (kebab menu: View, Edit, Compare, Write-off)
Row click opens Drone Detail. Include hover state, selected/checkbox state (for multi-select compare/export), sortable column headers, and a sticky header.

### Pagination
Bottom bar: page-size selector, page navigation, and "showing X–Y of Z" text.

### Modals / drawers (design as separate frames)
- **Add / Edit Drone drawer** — right-side panel form: serial number, inventory number, name, model (select), classification, military unit, acquired date, notes. Primary "Save" + "Cancel".
- **Import CSV modal** — file dropzone, template download link, preview/validation summary (rows OK / rows with errors), "Import" button.
- **Compare view** — side-by-side columns of 2–4 selected drones showing spec rows aligned for comparison; differing values highlighted.

## Components & states to include
- Toolbar buttons: primary / secondary / icon, with hover + disabled
- Filter dropdown (multi-select) and filter chip (removable)
- Data table: header (sortable asc/desc), row default / hover / selected, checkbox column
- Status badge: one variant per drone status (Active, In Mission, Damaged, Maintenance, Lost, Decommissioned, Sold, Transferred, Written-off) with indicator dot
- Classification pill
- Pagination bar
- Side drawer form (add/edit) with input / select / textarea / date picker states
- Modal (import) with dropzone: idle / dragging / uploading / success / error
- Empty state ("No drones match these filters") and loading skeleton rows

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; table/panel surface `#161D26`; header row slightly lighter with 1px bottom border; zebra rows subtle (`#131A22`).
- **Accent:** muted amber/gold `#C8A24A` for primary actions, links, sort indicators, focus rings.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; serial numbers in monospace.
- **Status palette (reuse app-wide):** Active `#3FB950`, In Mission `#4C8DFF`, Maintenance `#C8A24A`, Damaged `#E5484D`, Lost/Decommissioned/Sold/Transferred/Written-off `#8A94A6` (grey, some with an icon).
- **Type:** Inter or IBM Plex Sans; IBM Plex Mono for identifiers. Table cells 13–14px; header 12px uppercase tracking; page title 24px semibold.
- **Radius:** 12px cards, 8px buttons/inputs, pills fully rounded.
- **Density:** compact table rows (~44px), clear column alignment, right-aligned dates/numbers.

## Behavior notes (annotations, not visuals)
- List is paginated (`page` / `page_size`) and filterable by status, classification, unit, model, and spec fields.
- Status badges should be driven by the backend `STATUS_UI` map / `status_label` / `status_indicator` / `status_category` fields.
- Add/Edit, Import, Export, Compare, Write-off, and Models actions are gated by the RBAC permission matrix — hide or disable per role.
