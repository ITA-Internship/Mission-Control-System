# Task: Drone Defect Logging (`repairs` subsystem)

**Status:** Specification — ready for implementation
**Owner:** _unassigned_
**Target app:** new Django app `repairs`, mounted at `api/repairs/`

---

## 0. Summary (user-story format)

**User Story:**
As an operator or technician, when I detect a problem with a drone, I want to log a defect
report (type, severity, description, detection time, related drone) automatically attributed to
me as the reporter, so that drone defects are captured in one place and can later be triaged and
repaired.

**Technical tasks:**

- Create a new `repairs` Django app, register it in `INSTALLED_APPS`, and mount it at
  `api/repairs/` in [config/urls.py](../config/urls.py) (`app_name = "repairs"`).
- Implement the `DefectReport` model (table `defect_reports`): `drone` FK (`PROTECT`),
  `defect_type` and `severity` choice enums, `description` text, `detected_at` datetime,
  `reporter` FK → `AUTH_USER_MODEL` (`SET_NULL`, nullable). Add indexes + initial migration.
- Implement `POST /api/repairs/` — submit a defect report. All writes go through
  `services.create_defect_report` (`@transaction.atomic`).
- Implement `GET /api/repairs/` — paginated, filterable list (`drone`, `severity`,
  `defect_type`, `reporter`) using a slim list serializer and `select_related` to avoid N+1.
- Implement `GET /api/repairs/{id}/` — retrieve one report. No update/delete
  (`PUT`/`PATCH`/`DELETE` → `405`).
- Validate required data: `drone`, `defect_type`, `severity`, `description`, `detected_at`;
  valid enum values; non-blank/min-length description; reject `detected_at` >60s in the future.
- Integrate with auth: `reporter` is always `request.user` (read-only — ignore any client-sent
  value); every endpoint requires authentication.
- Add RBAC codes `repairs.view` / `repairs.create` in [accounts/rbac.py](../accounts/rbac.py)
  and grant them per role in `ROLE_PERMISSION_MATRIX`; enforce via a `RepairPermission` class
  (`is_staff` bypass). **Coordinate with the platform/RBAC owner** on the exact role grants (§8).
- Register `DefectReport` in the Django admin (interim entry UI — no web UI in this task).
- **Coordinate with the drones team:** auto-linking a defect to a drone-status change is
  deferred; if/when added, route status changes through `drones.services.update_drone` — never
  set `Drone.status` directly.
- Tests: `APITestCase` + `factory_boy` covering create / validation / auth / RBAC / list /
  filter / detail / `PROTECT`, plus a unit test for `create_defect_report`.

**Acceptance Criteria:**

- An authorized operator/technician can submit a defect report and receives the persisted record.
- The reporter is recorded automatically from the authenticated user and cannot be spoofed.
- Required-field and value validation rejects incomplete/malformed reports with clear errors.
- Defect reports are retrievable individually and as a filterable, paginated list for future
  reference.
- Access is role-controlled; unauthenticated requests are rejected.
- `python manage.py test repairs` passes and `makemigrations --check` reports no missing
  migrations.

---

## 1. Goal

Provide a way to **log newly detected drone defects** and retrieve them. A defect report
captures *what* is wrong with a *specific drone*, *how bad* it is, *when* it was detected, and
*who* reported it. This is the logging entry point of the broader **repairs** workflow: the
operations in scope here are **create** and **read**. The repair/resolution lifecycle
(triage → assign → fix → close) is explicitly **deferred** (see §7).

### Scope of the listed requirements

| Requirement (from the request) | How it is satisfied here |
| --- | --- |
| UI for entering defect details | **Deferred** — no web UI in this task. The "entry interface" for now is the JSON API (§5) plus the Django admin registration (§4.6). Build the web UI as a follow-up. |
| API endpoints to submit/retrieve reports | `POST` / `GET` `api/repairs/` and `GET api/repairs/{id}/` (§5). |
| Validation of required defect data | Serializer-level validation (§4.4). |
| Database schema update | New `repairs` app + `DefectReport` model + migration (§4.2). |
| Integration with user authentication | `reporter` is taken from `request.user`, never the client payload (§4.5). |
| Unit + integration tests | `APITestCase` suite + service unit test (§6). |

---

## 2. Conventions this task must follow

This subsystem must look like the rest of the codebase. Mirror the `drones` and `missions` apps:

- **One app per domain.** Create a new `repairs` app (registered in `INSTALLED_APPS`), with the
  standard file layout (§3). Repairs depend on `drones` and `accounts`; nothing in those apps
  may import from `repairs` (keep the dependency direction one-way, as the missions module does).
- **Service layer owns writes.** All state-changing logic goes in `services.py`, in
  keyword-only functions wrapped in `@transaction.atomic`. Views/serializers validate and
  delegate. (See [drones/services.py](../drones/services.py),
  [missions/services.py](../missions/services.py).)
- **RBAC is centralized.** Permission codes live in [accounts/rbac.py](../accounts/rbac.py) and
  are granted per role in `ROLE_PERMISSION_MATRIX`. A per-app `permissions.py` class enforces
  them, exactly like [drones/permissions.py](../drones/permissions.py). `is_staff` users bypass
  the check (matches `DronePermission._has_permission`).
- **Pagination** uses `common.pagination.StandardResultsSetPagination`.
- **Filtering** uses `django_filters` (see [drones/filters.py](../drones/filters.py)).
- **Audit-style records are append-only** where they exist (the `DefectReport` row *is* the log
  here; no separate audit table — see §7).
- **Tests** use `rest_framework.test.APITestCase` + `factory_boy` factories
  ([drones/tests.py](../drones/tests.py), [drones/factories.py](../drones/factories.py)).

---

## 3. File layout (new `repairs` app)

| File | Responsibility |
| --- | --- |
| `repairs/models.py` | `DefectReport` model + `DefectType` / `Severity` choice enums. |
| `repairs/services.py` | `create_defect_report(...)` — the single transactional write path. |
| `repairs/serializers.py` | `DefectReportSerializer` (create/detail) + `DefectReportListSerializer`. Required-field and value validation. |
| `repairs/views.py` | `DefectListCreateView`, `DefectDetailView`. Pagination, filtering, permission wiring. |
| `repairs/permissions.py` | `RepairPermission` (RBAC-backed). |
| `repairs/filters.py` | `DefectFilter`. |
| `repairs/urls.py` | Routing, `app_name = "repairs"`. |
| `repairs/admin.py` | `DefectReportAdmin` registration. |
| `repairs/factories.py` | `DefectReportFactory` (re-export user/drone factories for convenience). |
| `repairs/tests.py` | `APITestCase` suite (§6). |
| `repairs/migrations/` | Initial migration for `DefectReport`. |

Plus edits to: [accounts/rbac.py](../accounts/rbac.py) (new permission codes + matrix grants)
and [config/urls.py](../config/urls.py) (`path("api/repairs/", include("repairs.urls"))`).

---

## 4. Technical specification (brief)

### 4.1 Choice enums

```python
class DefectType(models.TextChoices):
    MOTOR = "MOTOR", "Motor"
    BATTERY = "BATTERY", "Battery"
    CAMERA = "CAMERA", "Camera"
    FRAME = "FRAME", "Frame"
    PROPELLER = "PROPELLER", "Propeller"
    FLIGHT_CONTROLLER = "FLIGHT_CONTROLLER", "Flight controller"
    VTX = "VTX", "Video transmitter"
    WIRING = "WIRING", "Wiring"
    FIRMWARE = "FIRMWARE", "Firmware"
    OTHER = "OTHER", "Other"

class Severity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"
```

### 4.2 `DefectReport` model (table `defect_reports`)

| Field | Type | Notes |
| --- | --- | --- |
| `drone` | FK → `drones.Drone`, `on_delete=PROTECT`, `related_name="defects"` | Required. `PROTECT` matches how the rest of the system guards drones with dependent records. |
| `defect_type` | `CharField(30, choices=DefectType)` | Required. Indexed. |
| `severity` | `CharField(20, choices=Severity)` | Required. Indexed. |
| `description` | `TextField` | Required, non-blank; serializer enforces a trimmed min length (`DESCRIPTION_MIN_LENGTH = 10`). |
| `detected_at` | `DateTimeField` | Required. Must not be in the future (small grace window, §4.4). |
| `reporter` | FK → `settings.AUTH_USER_MODEL`, `on_delete=SET_NULL`, `null=True`, `blank=True`, `related_name="reported_defects"` | Set from `request.user`; nullable so the row survives user deletion (matches `created_by` / `changed_by` pattern). |
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `updated_at` | `DateTimeField(auto_now=True)` | |

`Meta`: `db_table = "defect_reports"`, `ordering = ("-detected_at",)`, indexes on
`(drone, "-detected_at")`, `severity`, and `defect_type`. `__str__` returns something like
`f"{self.get_severity_display()} {self.get_defect_type_display()} on {self.drone}"`.

> **No `status` field in this task.** Adding a repair lifecycle would pull in a state machine +
> audit log (the missions pattern); that is deliberately deferred (§7).

### 4.3 Service — `services.create_defect_report`

```python
@transaction.atomic
def create_defect_report(*, drone, reporter, defect_type, severity, description, detected_at):
    return DefectReport.objects.create(
        drone=drone,
        reporter=_get_authenticated_user(reporter),   # see drones/services.py helper
        defect_type=defect_type,
        severity=severity,
        description=description,
        detected_at=detected_at,
    )
```

A single insert, but keep it in the service layer for consistency and so the future lifecycle
work has a home. `reporter` is normalized through the same `_get_authenticated_user` guard used
in `drones/services.py` (returns `None` for anonymous/unauthenticated).

### 4.4 Validation (serializer)

`DefectReportSerializer` (used for `POST` and detail representation) enforces:

- `drone`, `defect_type`, `severity`, `description`, `detected_at` are **required**.
- `defect_type` / `severity` must be valid enum members (DRF `ChoiceField` handles this → 400).
- `description`: reject blank / whitespace-only; trimmed length ≥ `DESCRIPTION_MIN_LENGTH`.
- `detected_at`: reject values more than `DETECTED_AT_GRACE_PERIOD` (60s) in the **future**
  — defects are detected in the past/now. (Mirror the inverse of
  `missions.serializers` `STARTED_AT_GRACE_PERIOD`, allowing 60s for clock skew.)
- `drone` must reference an existing drone (`PrimaryKeyRelatedField`; nonexistent → 400).
- `reporter`, `id`, `created_at`, `updated_at` are **read-only** (see §4.5).

The serializer's `create()` pulls `reporter` from `self.context["request"].user` and delegates
to `services.create_defect_report`.

### 4.5 Authentication / reporter tracking

- All endpoints require `IsAuthenticated` (via the RBAC permission class, which returns `False`
  for anonymous users — same as `DronePermission`).
- `reporter` is **never** read from the request body. It is always set to `request.user` in the
  view/serializer. A client-supplied `reporter` field must be ignored (read-only), not honored.
- This is the integration point with `accounts`: the custom user model
  (`settings.AUTH_USER_MODEL`) is the FK target, and `reported_defects` is the reverse accessor
  for "defects this user reported."

### 4.6 Admin

Register `DefectReport` like the drones admin:
`list_display = ("id", "drone", "defect_type", "severity", "reporter", "detected_at", "created_at")`,
`list_filter = ("severity", "defect_type", "detected_at")`,
`search_fields = ("drone__serial_number", "drone__inventory_number", "description")`.
This doubles as the interim "entry UI" until the web interface is built.

---

## 5. HTTP API

All endpoints under `api/repairs/`, authenticated, namespace `repairs:`.

| Method | Path | View | Permission code | Purpose |
| --- | --- | --- | --- | --- |
| `GET` | `/` | `DefectListCreateView` | `repairs.view` | List defect reports (paginated, filterable). |
| `POST` | `/` | `DefectListCreateView` | `repairs.create` | Submit a new defect report. |
| `GET` | `/{id}/` | `DefectDetailView` | `repairs.view` | Retrieve one defect report. |

- `DefectListCreateView` is a `ListCreateAPIView`; `DefectDetailView` is a `RetrieveAPIView`
  (no `PUT`/`PATCH`/`DELETE` in this task — restrict `http_method_names` accordingly).
- **List uses `DefectReportListSerializer`** (slim: `id`, `drone`, `defect_type`, `severity`,
  `detected_at`, `reporter`, `created_at`); POST/detail use the full `DefectReportSerializer`
  — same `get_serializer_class` switch as `DroneListCreateView`.
- **Pagination:** `StandardResultsSetPagination`.
- **Filtering** (`DefectFilter`): `drone` (exact), `severity` (exact), `defect_type` (exact),
  `reporter` (exact). **Ordering:** `detected_at`, `created_at`, `severity`.
- **Query optimization:** `get_queryset` uses `select_related("drone", "reporter")` to avoid
  N+1s in the list view.

### Create payload shape

```jsonc
POST /api/repairs/
{
  "drone": 3,
  "defect_type": "MOTOR",
  "severity": "HIGH",
  "description": "Rear-left motor stutters under load and overheats after ~2 min.",
  "detected_at": "2026-06-03T14:30:00Z"
  // "reporter" is IGNORED if sent — it is taken from the authenticated user
}
```

Success → `201` with the full report including server-assigned `id`, resolved `reporter`, and
timestamps.

---

## 6. Testing requirements

`repairs/tests.py` — `APITestCase` + `factory_boy`, following [drones/tests.py](../drones/tests.py).
Add a `DefectReportFactory` to `repairs/factories.py` and re-export the user/drone factories.

**Integration (API) coverage:**

- **Create success** — authorized role with a valid payload → `201`; row persisted; `reporter`
  equals the authenticated user; `detected_at` stored correctly.
- **Reporter is server-set** — a `reporter` value in the request body is ignored; the stored
  reporter is still `request.user`.
- **Required-field validation** — missing `drone` / `defect_type` / `severity` / `description`
  / `detected_at` each → `400` with a field error.
- **Choice validation** — invalid `defect_type` / `severity` → `400`.
- **Description rules** — blank / whitespace-only / too-short description → `400`.
- **`detected_at` in the future** (beyond grace) → `400`; now / recent past → accepted.
- **Nonexistent drone** → `400`.
- **AuthN/AuthZ** — unauthenticated → `401/403`; a role lacking `repairs.create` → `403` on
  POST but can still `GET` if it has `repairs.view`; a role lacking `repairs.view` → `403` on
  list/detail. (Drive these off the RBAC matrix, §8.)
- **List** — returns only via paginated envelope; filter by `drone` / `severity` /
  `defect_type` returns the expected subset; ordering by `detected_at` works.
- **Detail** — existing id → `200`; unknown id → `404`.
- **`drone` PROTECT** — a drone with defect reports cannot be hard-deleted (raises
  `ProtectedError`).

**Unit coverage:**

- `create_defect_report` — happy path creates the row with normalized `reporter`; an
  anonymous/None reporter is stored as `NULL`.
- **Factory integrity** — `DefectReportFactory()` produces a DB-valid row (sanity check, like
  `MissionOutcomeFactoryIntegrityTests`).

Run with: `python manage.py test repairs`.

---

## 7. Out of scope (deferred follow-ups)

- **Web interface** for entering defects — API + admin only for now.
- **Repair / resolution lifecycle** (status field, transitions, assignment to a technician,
  closing a defect). When added, follow the missions state-machine pattern: a `RepairStatus`
  enum + transition table, service functions under locks, and an **append-only audit log** (see
  `MissionAuditLog` / `DroneStatusHistory`). Do **not** mutate state outside the service layer.
- **Auto-linking defects to drone status** (e.g. a `CRITICAL` defect flipping the drone to
  `DAMAGED`). If introduced, route the drone-status change through
  `drones.services.update_drone` — never assign `Drone.status` directly (the missions README
  §11 calls this out explicitly).
- **Media attachments** (photos of the defect) — there is a `media.upload` permission code
  reserved already; wire in when the media subsystem exists.
- **Linking a defect to the mission during which it was detected** (a nullable
  `related_mission` FK, as `WriteOffRecord`/`DroneStatusHistory` have).

---

## 8. RBAC grants (proposed)

Add to [accounts/rbac.py](../accounts/rbac.py):

```python
# Repairs
PERMISSION_REPAIRS_VIEW = "repairs.view"
PERMISSION_REPAIRS_CREATE = "repairs.create"
```

Proposed grants in `ROLE_PERMISSION_MATRIX` (confirm with product/RBAC owner before finalizing):

| Role | `repairs.view` | `repairs.create` |
| --- | --- | --- |
| Admin | ✅ | ✅ |
| Commander | ✅ | — |
| Dispatcher | ✅ | — |
| Operator | ✅ | ✅ (detects defects in the field) |
| Technician | ✅ | ✅ (detects defects during maintenance) |
| Viewer | ✅ | — |

> Operators and Technicians are the field/bench roles that actually find defects, so they get
> `create`; everyone can `view`. Adjust if product wants Commanders/Dispatchers to log too.

---

## 9. Acceptance criteria

The task is **done** when all of the following hold:

**Schema & app**
- [ ] A `repairs` app exists, is in `INSTALLED_APPS`, and is mounted at `api/repairs/` in
      [config/urls.py](../config/urls.py) with `app_name = "repairs"`.
- [ ] `DefectReport` is implemented per §4.2 (`db_table = "defect_reports"`, `PROTECT` on
      `drone`, `SET_NULL` + nullable on `reporter`, declared indexes, choice enums).
- [ ] An initial migration is committed and `python manage.py makemigrations --check` reports no
      missing migrations.

**API**
- [ ] `POST /api/repairs/` creates a report and returns `201` with the full representation.
- [ ] `GET /api/repairs/` returns a paginated list (slim serializer) and supports filtering by
      `drone`, `severity`, `defect_type`, `reporter` and ordering by `detected_at`.
- [ ] `GET /api/repairs/{id}/` returns `200` for an existing report and `404` otherwise.
- [ ] No update/delete endpoints are exposed (`PUT`/`PATCH`/`DELETE` → `405`).

**Validation**
- [ ] Missing any required field → `400` with a per-field error.
- [ ] Invalid `defect_type` / `severity` → `400`.
- [ ] Blank/whitespace-only or too-short `description` → `400`.
- [ ] `detected_at` more than 60s in the future → `400`; current/past time → accepted.

**Auth integration**
- [ ] All endpoints reject unauthenticated requests.
- [ ] `reporter` is always the authenticated user and a client-supplied `reporter` is ignored.
- [ ] Permissions are enforced via a `RepairPermission` class backed by the new RBAC codes;
      `is_staff` bypasses the check; the role→permission grants in §8 are applied.

**Testing & quality**
- [ ] `python manage.py test repairs` passes, covering every case in §6.
- [ ] All writes go through `services.create_defect_report` (no model `.create()` in the view).
- [ ] List view uses `select_related("drone", "reporter")` (no N+1).
- [ ] `DefectReport` is registered in the Django admin per §4.6.
- [ ] Code passes the repo's `flake8` / `pre-commit` config.
```
