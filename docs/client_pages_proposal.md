# Client-Side Web Pages Proposal

Proposed web pages for the **Mission Control System** client application (planned React frontend, per [roadmap](roadmap.md)).

The backend is a REST API under `/api/`. This document maps the client pages onto existing backend apps and endpoints so the frontend can be built directly against them. Use [`schema.yml`](../schema.yml) / `/api/docs/` to generate the typed API client, and [rbac.md](rbac.md) to drive role-based UI gating.

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

| Page | Purpose | Backend |
|------|---------|---------|
| **Login** | Session login + CSRF handshake (may require adding a login API) | `accounts` |
| **Password Reset / Reset Confirm** | Public request + token-confirm flow | `users/password-reset/`, `.../confirm/` |
| **Account Activation** | Landing page for activation token links | `activate/<user_id>/<token>/` |
| **Force Password Change** | Blocking page when `must_change_password=true` | `users/me/change-password/` |
| **My Profile** | View/edit own profile, rank, contact, avatar | `users/me/`, `users/<id>/profile-picture/` |

## 2. Drone Fleet (core)

| Page | Purpose | Backend |
|------|---------|---------|
| **Drone Inventory (list)** | Filterable/paginated fleet table with status badges | `GET /api/drones/` |
| **Drone Detail** | Full drone view: specs, current status, notes | `GET drones/<pk>/` |
| **Drone Status History** | Lifecycle transition timeline | `drones/<pk>/history/` |
| **Spec Change History** | Audit of spec edits | `drones/<pk>/spec-changes/` |
| **Create/Edit Drone** | Registration & update forms | `POST/PATCH drones/` |
| **Drone Comparison** | Side-by-side spec compare (replaces existing template) | `GET compare/` |
| **Drone Models Catalog** | Manage drone models & supported classifications | `models/` |
| **CSV Import / Export** | Bulk import + export download | `import/`, `export/` |
| **Write-Off Records & History Report** | Create write-offs, view immutable history report | `write-offs/`, `.../history/report/` |

## 3. Missions

| Page | Purpose | Backend |
|------|---------|---------|
| **Missions Board (list)** | Missions with state-machine status filters | `GET /api/missions/` |
| **Mission Detail** | Overview: commander, location/map, timeline, status | `missions/<pk>/` |
| **Create/Edit Mission** | Planning form (incl. lat/lng map picker) | `POST missions/` |
| **Mission Status Control** | Drive state transitions (Planned→Active→Completed/Aborted) | `<pk>/status/` |
| **Mission Assignments** | Assign drones + operators; post-mission condition | `<mission_pk>/assignments/` |
| **Mission Outcome** | Record result + incident notes | `<pk>/outcome/` |
| **Mission Artifacts & Videos** | Upload/view images, data files, and video gallery | `artifacts/`, `media/videos/` |

## 4. Repairs & Maintenance

| Page | Purpose | Backend |
|------|---------|---------|
| **Defect Reports (list)** | Filter by severity/status | `defects/` |
| **Defect Detail** | Defect view + status update + event history | `defects/<pk>/`, `.../history/` |
| **Repair Orders** | Manage orders, assignment, transitions | `orders/` |
| **Component Replacements** | Log hardware swaps + CSV export | `replacements/`, `.../export/` |
| **Drone Repair History** | Full maintenance timeline per drone | `drones/<drone_id>/history/` |

## 5. Media

| Page | Purpose | Backend |
|------|---------|---------|
| **Video Library** | Browse/upload mission videos with status | `media/videos/`, `videos/browser/` |
| **Media Audit Log** | Read-only view/download/upload activity | `media/audit-logs/` |

## 6. Administration (Admin / Commander)

| Page | Purpose | Backend |
|------|---------|---------|
| **User Management** | Create users, activate/deactivate | `users/`, `users/<pk>/status/` |
| **Role Assignment** | Change user roles | `users/<user_id>/role/` |
| **Military Units** | Manage unit catalog | `accounts` (admin/API) |
| **Audit Log Viewer** | System-wide immutable action log + CSV export | `audit-log/`, `.../export/` |

## 7. Cross-cutting

| Page | Purpose |
|------|---------|
| **Dashboard / Home** | Role-aware KPIs: active missions, drones by status, open defects, recent audit events |
| **Role-based Navigation Shell** | Layout that shows/hides features per RBAC permission matrix |
| **System Health / Status** | Surface `GET /api/health/` for ops |

---

## Suggested Build Phases

1. **Foundation** — Auth (login, password reset, force-change), navigation shell with RBAC gating, generated API client, Dashboard skeleton.
2. **Core fleet** — Drone inventory, detail, create/edit, status & spec history.
3. **Missions** — Board, detail, create/edit, status control, assignments, outcomes.
4. **Repairs & media** — Defects, repair orders, component replacements, video library, artifacts.
5. **Administration** — User management, role assignment, units, audit log viewer.
6. **Polish** — Drone comparison, CSV import/export, write-off reports, health/status.

## References

- [API reference](api.md) — full endpoint documentation
- [RBAC](rbac.md) — role/permission matrix and auth flow
- [`schema.yml`](../schema.yml) — OpenAPI schema for client generation
- [Roadmap](roadmap.md) — planned React frontend
