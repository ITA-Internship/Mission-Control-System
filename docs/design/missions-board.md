# Missions Board — Design Brief (Figma Make)

Design brief for the **Missions Board** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **missions board page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, operationally focused. Think defense/aerospace mission-planning software.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The board lives in the main content area.

### Page header
- Page title: "Missions" with a total count.
- **View toggle:** switch between a **Board (kanban)** view grouped by status and a **List (table)** view.
- Primary action: **+ New Mission** (gated by role).

### Filter bar
- Free-text search (title, location).
- Filters: **Status** (Planned / Active / Completed / Aborted), **Commander**, **Result** (Success / Failure), date range.
- Active filters as removable chips.

### Board (kanban) view
- Columns by mission status: **Planned → Active → Completed / Aborted**, each with a count.
- **Mission cards:** title, status pill, commander, location, started-at, a small drone-count/operator-count indicator, and result pill when completed. Card click opens Mission Detail.
- Column empty states.

### List (table) view
Sortable, paginated table. Columns: title, status (pill), commander, location, started-at, ended-at, result (pill), assigned drones count, row actions (View, Edit). Sticky header, hover + selected row states.

### New / Edit Mission modal (design as a frame)
Form: title, commander (select), location description, **latitude/longitude with a map picker**, planned notes. Primary "Create" + "Cancel".

## Components & states to include
- View toggle (board / list)
- Kanban column with count + mission card (default / hover); result pill
- Status pill (Planned / Active / Completed / Aborted) and result pill (Success / Failure)
- Filter dropdown + removable chip
- Data table: sortable header, row default / hover / selected
- New/Edit mission modal with inputs, select, textarea, and map-picker placeholder
- Pagination bar (list view)
- Empty states (no missions / empty column) and loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; cards/columns `#161D26` with 1px subtle border; kanban columns slightly recessed.
- **Accent:** muted amber/gold `#C8A24A` for active toggle, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`.
- **Mission status colors:** Planned `#8A94A6` (grey), Active `#3FB950` (green), Completed `#4C8DFF` (blue), Aborted `#E5484D` (red). Result: Success green, Failure red.
- **Type:** Inter or IBM Plex Sans. Page title 24px semibold, card title 15px semibold, metadata 12–13px muted.
- **Radius:** 12px cards/columns, 8px buttons/inputs, pills fully rounded.
- **Density:** compact cards; board scrolls horizontally on small screens; list rows ~44px.

## Behavior notes (annotations, not visuals)
- List from `GET /api/missions/`, paginated and filterable by status/commander/result.
- Create/edit via `POST missions/`; status is a state machine (Planned → Active → Completed/Aborted).
- New Mission and edit actions gated by the RBAC permission matrix.
- Selecting a mission navigates to the [Mission Detail](mission-detail.md) page.
