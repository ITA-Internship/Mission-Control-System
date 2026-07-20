# Feature Proposals — Mission Control System

**Date:** 2026-07-20
**Status:** Proposal for planning (no application code changed by this document)
**Basis:** Capability inventory of all apps (`accounts`, `drones`, `repairs`, `missions`, `media`, `roles`, `common`, `config`) plus `docs/roadmap.md` and `docs/architecture.md`.

---

## Context

The Mission Control System (Django 5 + DRF) already covers the core drone lifecycle: inventory + specs, missions + assignments, maintenance/repairs, mission artifacts/video, and RBAC + audit logging. What it does **not** yet have are the *cross-cutting operational layers* a fleet-management platform needs to move from "system of record" to "system of action": nothing proactively tells operators when something needs attention, there is no aggregate view of fleet health, external systems cannot integrate, and there is no live/geospatial picture of missions.

This document proposes **four flagship features**, one per theme, each designed to build directly on data the system *already captures* rather than introducing parallel structures. `docs/roadmap.md` currently lists only "React components" as planned — these give it substance.

They are ordered by recommended build sequence (F1 → F4): F1 and F2 are pure backend on existing data (high value, low risk); F3 adds infrastructure; F4 is the largest lift.

### Verified baseline (from code exploration)

- Roles: ADMIN, COMMANDER, OPERATOR, TECHNICIAN, VIEWER, DISPATCHER — permissions via `ROLE_PERMISSION_MATRIX` dict in [accounts/rbac.py](accounts/rbac.py), enforced by `HasRBACPermission` in [accounts/permissions.py](accounts/permissions.py).
- Only 2 Celery tasks exist (`send_email_task`, `extract_video_duration_task`); **no Celery Beat / periodic jobs**.
- Email is the only notification channel (plain-text, via `send_email_task`); **no in-app notification model**.
- Auth is **session-only** (+ BasicAuth in DEBUG); no JWT/API-token path for external clients.
- `Mission` stores `latitude`/`longitude` as plain Decimals; **no PostGIS/GeoDjango**, no flight paths, no live status.
- **No aggregate/KPI/metrics endpoint** anywhere; aggregation exists only in the HTML drone-comparison view.
- Rich existing signal/audit surface to build on: `AuditLog`, `MissionAuditLog`, `MediaAuditLog`, `DroneStatusHistory`, `RepairEvent`, `DefectReport`, `RepairOrder`, `WriteOffRecord`.

---

## F1 — In-App Notifications & Configurable Alerts
**Theme: Notifications & Alerts** · **Effort:** M (1 sprint) · **Value:** High · **Risk:** Low (additive)

**Problem it solves.** Today the only signal to a human is one hard-coded email to a defect reporter. Commanders don't learn about critical defects, overdue repairs, firmware-outdated drones, or a drone marked LOST unless they go looking. There is no inbox and no way to tune what you're told about.

**Design — build on existing signals, don't replace email.** New app `notifications/`:

- **`Notification`** — `recipient` (FK User), `event_type` (choices: `CRITICAL_DEFECT`, `REPAIR_OVERDUE`, `FIRMWARE_OUTDATED`, `DRONE_LOST`, `MISSION_STATUS_CHANGED`, `ASSIGNMENT_CREATED`, …), `title`, `body`, `level` (info/warning/critical), generic `target_model`/`target_id` (mirror the pattern already used in `MissionAuditLog`), `is_read`, `read_at`, `created_at`. Index `(recipient, is_read, created_at)`.
- **`NotificationPreference`** — per-user, per-`event_type` channel toggles (`in_app` / `email`) with role-based defaults.
- **`AlertRule`** (admin-configurable) — `event_type`, threshold params (e.g. `repair_overdue_days`), target role(s). Lets a commander set "notify me when a repair order sits IN_PROGRESS > 7 days."

**Emission — reuse existing hooks:**
- Django signals on `DefectReport` (severity=critical), `Drone.status` → LOST/WRITTEN_OFF, `MissionAuditLog` writes.
- A **new Celery Beat periodic task** (`scan_alert_rules`, hourly) evaluating `AlertRule`s against current state: overdue `RepairOrder`s (`started_at` age vs threshold, still IN_PROGRESS), `DroneSpec.is_firmware_outdated=True` drones, drones stuck in MAINTENANCE. Requires **enabling Celery Beat** (absent today) in [config/celery.py](config/celery.py).
- A central `notify(recipients, event_type, target, ...)` service that checks `NotificationPreference`, writes `Notification` rows, and fans out email via the existing `send_email_task`. Refactor the current repairs email to call this.

**API (`/api/notifications/`):** list (filter `is_read`/`event_type`/`level`; paginated), `PATCH <id>/read/`, `POST mark-all-read/`, unread-count, preferences CRUD, admin-only AlertRule CRUD.

**RBAC.** New `notifications.view_own`, `notifications.manage_rules` (admin/commander) added to `ROLE_PERMISSION_MATRIX` ([accounts/rbac.py](accounts/rbac.py)) and `docs/rbac.md`.

**Files touched:** new `notifications/` app; [config/settings.py](config/settings.py) (INSTALLED_APPS + Beat schedule), [config/celery.py](config/celery.py), [repairs/services.py](repairs/services.py), [config/urls.py](config/urls.py).

---

## F2 — Fleet Analytics & Readiness Dashboard API
**Theme: Analytics & Dashboards** · **Effort:** M · **Value:** High · **Risk:** Low (read-only)

**Problem it solves.** There is no way to answer "how ready is the fleet?" — no counts by status, no repair turnaround, no defect rates, no cost. The raw data exists (`DroneStatusHistory`, `RepairEvent`, `RepairOrder`, `DefectReport`, `WriteOffRecord`, `MissionDrone`) but is never aggregated; leadership exports CSVs and computes by hand.

**Design — read-only aggregation over existing tables.** New app `analytics/` (no new domain models; pure query layer). Optionally add lightweight **cost fields** for TCO: `labor_cost`, `parts_cost` on `RepairOrder`, `unit_cost` on `ComponentReplacement` (small `repairs` migrations).

**Endpoints (`/api/analytics/`), RBAC-gated and Redis-cached:**
- `GET fleet-readiness/` — drone counts by `status` (ACTIVE vs INACTIVE), % operational, MAINTENANCE count, firmware-outdated count, per-`MilitaryUnit` breakdown.
- `GET maintenance-metrics/` — mean repair turnaround (`RepairOrder.started_at`→`completed_at`), open vs closed defects, defect rate by `defect_type`/`severity`, time-in-status from `RepairEvent`, top drones by defect count.
- `GET mission-metrics/` — missions by status/result over a date range, success rate, drone utilization (count / flight time from `MissionDrone.flight_started_at/ended_at`), loss rate.
- `GET cost-summary/` — total maintenance cost, cost-per-drone, cost by component type (needs cost fields).

Implemented with ORM aggregates (`Count`, `Avg`, `F`-expression durations, `TruncMonth` trends). Params `?unit=`, `?date_from=`/`?date_to=`, `?group_by=`. JSON shaped for charting.

**RBAC.** New `analytics.view` (ADMIN, COMMANDER, DISPATCHER); cost data behind `analytics.view_cost` (ADMIN/COMMANDER).

**Optional add-on:** async weekly **readiness digest** (PDF/XLSX) via Celery Beat + `send_email_task`, reusing F1's Beat infrastructure.

**Files touched:** new `analytics/` app; migrations in [repairs/models.py](repairs/models.py); [config/urls.py](config/urls.py); [accounts/rbac.py](accounts/rbac.py). Watch query cost — add indexes and cache.

---

## F3 — External API Access: Token Auth, Webhooks & Health/Metrics
**Theme: Platform & Integration** · **Effort:** M–L · **Value:** High · **Risk:** Medium (new auth surface — security-review required)

**Problem it solves.** Auth is session-only, so no external client, script, storage-side service, or partner system can integrate. There are no webhooks to push events out, and no health/readiness endpoint for orchestration/monitoring — a gap for a containerized deployment.

**Design.**
1. **Token auth for service/external clients.** Add a scoped **`ApiKey`** model (per-client key, hashed at rest, tied to a role, revocable, `last_used_at`) + a custom DRF authentication class, added to `DEFAULT_AUTHENTICATION_CLASSES` in [config/settings.py](config/settings.py) **alongside** session auth. (Alternative: `rest_framework_simplejwt`.) Admin CRUD for keys; issuance/revocation audit-logged via existing `AuditLog`. API keys carry a role and remain subject to `HasRBACPermission`.
2. **Outbound webhooks.** **`Webhook`** model — `url`, `secret` (HMAC-SHA256 signing), subscribed `event_types` (reuse F1's event enum), `is_active`. A `deliver_webhook` Celery task with retry/backoff (mirrors `send_email_task`) fires on the same signals F1 listens to. Delivery log for observability.
3. **Health & metrics.** `GET /api/health/` (liveness) and `GET /api/ready/` (DB + Redis + Celery broker reachability), unauthenticated for the load balancer. Optional `/metrics` (Prometheus) behind a key.

**Security tie-in.** Must respect the RBAC matrix and the unit-scoping fixes flagged in the code review. Rate-limit token endpoints by extending the existing throttle scopes in [config/settings.py](config/settings.py).

**Files touched:** new `integrations/` app (ApiKey, Webhook, auth class, tasks); [config/settings.py](config/settings.py); [config/urls.py](config/urls.py); reuse [accounts/tasks.py](accounts/tasks.py) retry pattern. **Depends on F1's event enum.**

---

## F4 — Live Mission Tracking & Geospatial Support
**Theme: Real-time & Geospatial** · **Effort:** L (multi-sprint epic) · **Value:** High but specialized · **Risk:** High (infra changes)

**Problem it solves.** Missions store a single lat/long and status changes only via manual PATCH. There is no live picture, no flight path, no map. Largest lift — proposed last as a phased epic.

**Phase A — Geospatial data model (backend only).**
- Add **GeoDjango/PostGIS** — requires the PostGIS extension; update [docker-compose.yml](docker-compose.yml) DB image to `postgis/postgis`.
- **`TelemetryPoint`** / **`MissionRoute`** — timestamped `PointField` (`LineStringField` for planned routes) linked to `Mission`/`MissionDrone`, plus altitude, battery %, speed. Migrate existing `Mission.latitude/longitude` into a `PointField` (keep decimals during transition).
- Telemetry ingestion `POST /api/missions/<id>/telemetry/` (batched points; authenticated via F3 API keys for field devices). Geospatial queries: proximity, flight-path GeoJSON export for maps.

**Phase B — Real-time status via WebSockets.**
- Add **Django Channels** + ASGI ([config/asgi.py](config/asgi.py) exists but the app runs WSGI/gunicorn; add an ASGI server + Redis channel layer — Redis already deployed).
- `ws/missions/<id>/` group pushes mission status changes, new telemetry, and F1 notifications live to connected commanders, emitted from the same service hooks that write `MissionAuditLog`.

**Phase C — Video enrichment (complements media app).**
- Extend `extract_video_duration_task` in [media/tasks.py](media/tasks.py) to also generate **thumbnails/poster frames** (ffmpeg is already in the Docker image) and extract resolution/codec/fps into `VideoMetadata`. Populate the existing-but-unused `checksum` field. Optional HLS transcoding for in-browser streaming.

**RBAC.** Telemetry write behind `missions.telemetry_write` (operators + service keys); live view behind `missions.view`.

**Files touched:** [docker-compose.yml](docker-compose.yml), [config/settings.py](config/settings.py), [config/asgi.py](config/asgi.py), new consumers, [missions/models.py](missions/models.py) + migrations, [media/tasks.py](media/tasks.py). Run as its own initiative after F1–F3.

---

## Recommended sequence & rationale

1. **F1 Notifications** — unlocks Celery Beat + an event enum that F2 (digests) and F3 (webhooks) reuse. Pure additive backend.
2. **F2 Analytics** — highest leadership value, read-only, low risk, uses data already present.
3. **F3 Integration** — enables external clients; depends on F1's event model; needs a security review.
4. **F4 Real-time/Geo** — largest lift and infra change; its own phased epic.

## Cross-cutting prerequisites (shared by F1–F3)
- **Enable Celery Beat** in [config/celery.py](config/celery.py) + [config/settings.py](config/settings.py) (`django-celery-beat` or a static `beat_schedule`). No periodic tasks exist today — a one-time enabler F1, the F2 digest, and F3 all build on.
- **Shared event-type enum** introduced in F1, reused by F2/F3 to avoid divergence.
- Add every new permission to `ROLE_PERMISSION_MATRIX` ([accounts/rbac.py](accounts/rbac.py)) **and** `docs/rbac.md`, with tests (note: `roles`/`common` currently have 0 tests).

## Verification (per feature, when built)
- **F1:** unit tests for `notify()` preference filtering + dedup; trigger a critical `DefectReport` → assert a `Notification` row + queued email; run `scan_alert_rules` against a seeded overdue `RepairOrder` → assert an alert; hit the API as each role → assert RBAC.
- **F2:** seed known data via `seed_db`, call each endpoint, assert aggregates match hand-computed values; verify cost endpoints 403 for non-privileged roles; verify Redis cache hit on repeat.
- **F3:** issue an API key, authenticate with it, assert RBAC enforced + `last_used_at` updates; register a webhook, trigger an event, assert signed delivery + retry on failure; curl `/api/health/` and `/api/ready/` with services up/down.
- **F4:** POST a telemetry batch, fetch GeoJSON flight path; open a WS connection, assert a status change pushes a message; upload a video, assert thumbnail + resolution populated.
- Run `python manage.py test` and `python manage.py check --deploy` after each feature.
