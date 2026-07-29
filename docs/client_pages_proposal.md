# Client-Side Web Pages Proposal

Proposed web pages for the **Mission Control System** client application (planned React frontend, per [roadmap](roadmap.md)).

The backend is a REST API under `/api/`. This document maps the client pages onto existing backend apps and endpoints so the frontend can be built directly against them. Use [`schema.yml`](../schema.yml) / `/api/docs/` to generate the typed API client, and [rbac.md](rbac.md) to drive role-based UI gating.

Pages are kept deliberately broad: detail views, history timelines, and sub-actions (status changes, assignments, outcomes) are folded into their parent page as **tabs, side panels, or modals** rather than standalone routes. This keeps the client to ~13 pages.

## Prerequisites & Open Questions

- **Authentication gap.** The backend currently uses **session + CSRF only** — there is no JSON login/JWT endpoint. Before client work begins, decide between:
  1. Django session login + `X-CSRFToken` header on unsafe methods, or
  2. Adding a token/JWT auth endpoint.
  This is the primary blocker.
- **Role gating.** All pages must respect the RBAC permission matrix (6 roles: Admin, Commander, Dispatcher, Operator, Technician, Viewer). Show/hide pages and actions per the user's dotted permissions (e.g. `drones.create`, `missions.assign`).
- **UI status data.** Reuse `Drone.STATUS_UI` and the `status_label` / `status_indicator` / `status_category` fields for consistent badges and coloring.
- **Pagination & filtering.** List endpoints are paginated (`page` / `page_size`) and heavily filterable.

---

## 1. Authentication & Account

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Auth** | Single flow covering login, password reset/confirm, account activation, and the blocking force-password-change screen (routed by token/state) | `accounts`, `users/password-reset/`, `activate/...`, `users/me/change-password/` |
| **My Profile** | View/edit own profile, rank, contact, avatar; change own password | `users/me/`, `users/<id>/profile-picture/`, `users/me/change-password/` |

## 2. Drone Fleet (core)

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Drone Inventory** | Filterable/paginated fleet table with status badges. Toolbar hosts create, CSV import/export, model catalog, and drone comparison (modal/drawer) | `GET /api/drones/`, `POST drones/`, `models/`, `import/`, `export/`, `compare/` |
| **Drone Detail** | Full drone view with tabs: **Specs / edit**, **Status history**, **Spec-change history**, **Write-offs** (create + immutable history report) | `drones/<pk>/`, `.../history/`, `.../spec-changes/`, `write-offs/` |

## 3. Missions

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Missions Board** | Missions list with state-machine status filters; create/edit mission (form + lat/lng map picker) via modal | `GET /api/missions/`, `POST missions/` |
| **Mission Detail** | Overview + tabs: **Status control** (transitions), **Assignments** (drones/operators + post-mission condition), **Outcome** (result/incident notes), **Artifacts & Videos** (upload/gallery) | `missions/<pk>/`, `<pk>/status/`, `assignments/`, `<pk>/outcome/`, `artifacts/`, `media/videos/` |

## 4. Repairs & Maintenance

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Repairs Workbench** | Tabbed workspace: **Defects** (list/filter, detail, status update, event history), **Repair orders** (manage/assign/transition), **Component replacements** (log + CSV export) | `defects/`, `.../history/`, `orders/`, `replacements/`, `.../export/` |
| **Drone Repair History** | Full maintenance timeline per drone (also reachable from Drone Detail) | `drones/<drone_id>/history/` |

## 5. Media

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Media Library** | Browse/upload mission videos with status; **Audit log** tab for view/download/upload activity | `media/videos/`, `media/audit-logs/` |

## 6. Administration (Admin / Commander)

| Page | Purpose (folded-in sections) | Backend |
|------|------------------------------|---------|
| **Administration** | Tabbed admin console: **Users** (create, activate/deactivate, role assignment), **Military units** catalog, **Audit log** viewer + CSV export | `users/`, `users/<pk>/status/`, `users/<user_id>/role/`, `audit-log/`, `.../export/` |

## 7. Cross-cutting

| Page | Purpose |
|------|---------|
| **Dashboard / Home** | Role-aware KPIs: active missions, drones by status, open defects, recent audit events; surfaces `GET /api/health/` status |
| **Role-based Navigation Shell** | Layout that shows/hides features per RBAC permission matrix |

---

## Suggested Build Phases

1. **Foundation** — Auth page, navigation shell with RBAC gating, generated API client, Dashboard skeleton, My Profile.
2. **Core fleet** — Drone Inventory (incl. create/import/export/compare) + Drone Detail (specs, histories, write-offs).
3. **Missions** — Missions Board + Mission Detail (status, assignments, outcome, artifacts).
4. **Repairs & media** — Repairs Workbench, Drone Repair History, Media Library.
5. **Administration** — Administration console (users, roles, units, audit log).

## Design Briefs (Figma Make)

Per-page design briefs ready to paste into Figma Make live in [`docs/design/`](design/):

- [Auth](design/auth.md)
- [Dashboard / Home](design/dashboard.md)
- [Drone Inventory](design/drone-inventory.md)
- [Drone Detail](design/drone-detail.md)
- [Missions Board](design/missions-board.md)
- [Mission Detail](design/mission-detail.md)
- [Repairs Workbench](design/repairs-workbench.md)
- [Media Library](design/media-library.md)
- [Administration](design/administration.md)
- [My Profile](design/my-profile.md)

## References

- [API reference](api.md) — full endpoint documentation
- [RBAC](rbac.md) — role/permission matrix and auth flow
- [`schema.yml`](../schema.yml) — OpenAPI schema for client generation
- [Roadmap](roadmap.md) — planned React frontend
