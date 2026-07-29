# Media Library — Design Brief (Figma Make)

Design brief for the **Media Library** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **media library page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast. Think defense/aerospace evidence/footage management. This houses mission videos and an activity audit log.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The library lives in the main content area with a **tab bar**.

### Page header
- Page title: "Media Library".
- Tabs: **Videos**, **Audit Log**.
- Primary action: **Upload Video** (gated by role).

### Tab 1 — Videos (default)
- Filter bar: search, **mission**, **drone**, **status** (Uploading / Ready / Failed), date range.
- **Grid of video cards:** thumbnail with a play overlay, title, status pill, duration, mission + drone tags, uploaded-by, upload date. Failed uploads clearly flagged; uploading shows a progress state.
- Card click opens a **video detail / player modal**: player, metadata (mission, drone, uploader, duration, checksum, status), and actions.
- **Upload modal** (design as a frame): dropzone, mission select, drone select (must be assigned to mission), title; states idle / dragging / uploading (progress) / success / error.

### Tab 2 — Audit Log
- Read-only table of media activity: action (View / Download / Upload / Update / Delete / Denied) as a pill, actor, target media, mission, timestamp, result.
- Filter bar: action type, actor, date range. Sortable, paginated.
- "Denied" actions visually flagged (red).

## Components & states to include
- Tab bar: default / active
- Video card: thumbnail + play overlay; states ready / uploading (progress) / failed
- Status pill (Uploading / Ready / Failed) and audit action pill (incl. Denied)
- Video player modal with metadata panel and actions
- Upload dropzone modal: idle / dragging / uploading / success / error, with mission + drone selects
- Filter dropdown + removable chip
- Audit table: sortable header, row default / hover; sticky header; pagination
- Empty states per tab and loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; cards/panels `#161D26` with 1px subtle border; video thumbnails on darker `#0E141B`.
- **Accent:** muted amber/gold `#C8A24A` for active tab, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; checksum in IBM Plex Mono.
- **Video status:** Uploading `#C8A24A` (amber), Ready `#3FB950` (green), Failed `#E5484D` (red).
- **Audit actions:** neutral grey for reads/views; Upload/Update blue `#4C8DFF`; Delete/Denied red `#E5484D`.
- **Type:** Inter or IBM Plex Sans. Page title 24px semibold, card title 14–15px, metadata 12–13px muted.
- **Radius:** 12px cards, 8px inner elements, pills fully rounded.
- **Density:** responsive video grid (3–4 columns desktop, 1–2 mobile); compact audit rows.

## Behavior notes (annotations, not visuals)
- Videos from `media/videos/` (full CRUD + browser view); audit log from `media/audit-logs/` (read-only).
- Video upload validates that the selected **drone is assigned to the mission**; status progresses uploading → ready / failed.
- Mission artifacts (images/data files) are managed within the [Mission Detail](mission-detail.md) page; this library focuses on videos + the media audit trail.
- Upload/download/delete actions and audit-log visibility are gated by the RBAC permission matrix; media access is itself audited.
