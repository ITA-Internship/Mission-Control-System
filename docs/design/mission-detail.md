# Mission Detail — Design Brief (Figma Make)

Design brief for the **Mission Detail** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **mission detail page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, operationally focused. Think defense/aerospace mission-command software. This is the single-mission workspace, opened from the Missions Board.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The detail view lives in the main content area.

### Page header
- Breadcrumb: "Missions / {title}".
- Title row: mission **title**, a large **status pill** (Planned / Active / Completed / Aborted), and a **result pill** (Success / Failure) when completed.
- Right-side actions: **Edit**, **Advance Status** (state-machine transition), overflow. Gated by role.
- Summary strip: commander, created-by, started-at, ended-at, and a compact location readout (lat/lng).

### Overview panel
- Mission metadata card: location description + a **map preview** with the lat/lng marker, planned notes.

### Tabbed content (design each tab as a frame)

**Tab 1 — Status Control (default)**
- Visual **state-machine stepper** (Planned → Active → Completed/Aborted) showing current state and allowed next transitions as buttons.
- Transition confirm with optional note. History of transitions listed below.

**Tab 2 — Assignments**
- Table of assigned drones + operators: drone (serial/name), operator, flight timestamps, **condition after** (OK / Damaged / Lost) pill.
- **+ Assign drone/operator** action opening a form (drone select, operator select). Per-row action to record **post-mission condition**.
- Empty state when no assignments.

**Tab 3 — Outcome**
- Form to record **result** (Success / Failure) and **incident notes**; read-only once mission is completed/aborted, with a clear summary card.

**Tab 4 — Artifacts & Videos**
- Media gallery: image/data-file artifacts as thumbnails/cards (title, type, size, uploaded-by) and mission **videos** with status (uploading / ready / failed), duration, thumbnail.
- **Upload** control (dropzone) for artifacts and videos. Download action on artifacts.

## Components & states to include
- Status pill (mission) + result pill; condition-after pill (OK / Damaged / Lost)
- Tab bar: default / active / disabled
- State-machine stepper with current + available transitions; transition confirm modal
- Assignments table row with condition pill; assign form (drone/operator selects)
- Outcome form (result toggle, notes) and read-only outcome summary
- Media card (artifact) + video card with status; upload dropzone: idle / dragging / uploading / success / error
- Map preview with marker
- Action buttons: primary / secondary with hover / disabled; empty states; loading skeletons

## Visual system
- **Theme:** dark mode. Background `#0B0F14`; cards/panels `#161D26` with 1px subtle border; tab bar with accent underline on active.
- **Accent:** muted amber/gold `#C8A24A` for active tab, links, primary actions, focus.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; coordinates in IBM Plex Mono.
- **Mission status colors:** Planned `#8A94A6`, Active `#3FB950`, Completed `#4C8DFF`, Aborted `#E5484D`. Result: Success green, Failure red. Condition: OK green, Damaged amber `#C8A24A`, Lost red.
- **Type:** Inter or IBM Plex Sans. Title 24px semibold, section titles 16px, metadata 12–13px muted, values 14px.
- **Radius:** 12px cards, 8px inner elements, pills fully rounded.
- **Density:** compact tables and cards; media gallery as responsive grid.

## Behavior notes (annotations, not visuals)
- Data from `missions/<pk>/`, `<pk>/status/`, `<mission_pk>/assignments/`, `<pk>/outcome/`, `artifacts/`, and `media/videos/`.
- Status transitions follow the mission state machine; only valid next states are actionable.
- Video upload validates that the drone is assigned to the mission.
- Assign, status, outcome, condition, and upload actions are gated by the RBAC permission matrix (Dispatcher/Operator/Commander/Admin per action).
