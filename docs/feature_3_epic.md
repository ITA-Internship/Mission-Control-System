# Epic — F3: External API Access (Token Auth, Webhooks & Health/Metrics)

**Date:** 2026-07-22
**Status:** Planning
**Source:** [docs/feature_proposals.md](feature_proposals.md) §F3
**Theme:** Platform & Integration · **Effort:** M–L · **Value:** High · **Risk:** Medium (new auth surface — security review required)

---

## Epic Goal

Move the Mission Control System from a session-only *system of record* to an
integratable platform. External clients, scripts, and partner systems should be
able to **authenticate without a browser session** (scoped API keys), the system
should **push domain events outbound** (signed webhooks), and orchestration /
monitoring infrastructure should be able to **probe liveness and readiness**. All
new access remains subject to the existing RBAC matrix and must not re-open the
object-scoping gaps flagged in the code review.

---

## Background & Current State

Verified from code exploration (see [docs/feature_proposals.md](feature_proposals.md) baseline):

- **Auth is session-only.** `DEFAULT_AUTHENTICATION_CLASSES` in
  [config/settings.py](../config/settings.py) is built dynamically: always
  `SessionAuthentication`, plus `BasicAuthentication` only when `DEBUG`. There is
  **no token / JWT / API-key path** for non-browser clients.
- **No outbound eventing.** The only push to a human is one hard-coded email in
  repairs. There are no webhooks and no delivery log.
- **No health/readiness endpoint** exists for a load balancer or orchestrator —
  a gap for a containerized deployment.
- **RBAC** is role-based via `HasRBACPermission`
  ([accounts/permissions.py](../accounts/permissions.py)) reading
  `ROLE_PERMISSION_MATRIX` ([accounts/rbac.py](../accounts/rbac.py)). Roles:
  ADMIN, COMMANDER, DISPATCHER, OPERATOR, TECHNICIAN, VIEWER.
- **Audit surface** exists: `AuditLog` ([accounts/models.py](../accounts/models.py))
  is immutable and written via `create_audit_log(...)` in `accounts/services.py`.
- **Celery** runs two tasks; **Celery Beat is not enabled**
  ([config/celery.py](../config/celery.py)). The retry pattern to mirror is
  `@shared_task(bind=True, max_retries=3, default_retry_delay=60)` + `self.retry(exc=exc)`
  in [accounts/tasks.py](../accounts/tasks.py).
- **Throttling** uses `ScopedRateThrottle` with env-overridable
  `DEFAULT_THROTTLE_RATES` in [config/settings.py](../config/settings.py).

---

## In Scope

1. Scoped, revocable **API-key authentication** for service/external clients.
2. **Outbound webhooks** with HMAC signing, retry/backoff, and a delivery log.
3. **Health, readiness, and (optional) metrics** endpoints.
4. RBAC additions, audit logging of key lifecycle, and rate limiting for the new surface.

## Out of Scope (Non-Goals)

- Full **OAuth2 / OpenID Connect** authorization-server behaviour (API keys +
  optional `simplejwt` only).
- **Inbound partner APIs** beyond the existing DRF surface (this epic authenticates
  external callers into existing endpoints; it does not add new business endpoints).
- **F4 telemetry ingestion** — referenced only as a *future consumer* of API keys;
  not built here.
- A UI/frontend for key or webhook management (admin CRUD + API only).

---

## Dependencies & Prerequisites

| # | Prerequisite | Type | Notes |
|---|---|---|---|
| P1 | **Shared event-type enum (F1)** | Blocking for Webhooks (Workstream B) | F1 is **not built** — no `notifications/` app exists. F3 webhooks are meant to "reuse F1's event enum". **Fallback:** define an interim `IntegrationEventType` `TextChoices` inside `integrations/` that F1 later consolidates, so Workstream B is not hard-blocked on F1. |
| P2 | **TLS + secure cookies / HSTS** | Blocking (gating) | Code review **C4**: no TLS, no `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_SSL_REDIRECT` / `SECURE_HSTS_SECONDS`; nginx on `:80` only. API keys over plaintext are trivially stealable — TLS must land **before or with** this epic. |
| P3 | **Set `DEFAULT_PERMISSION_CLASSES`** | Advisory (strongly recommended) | Review: DRF currently falls back to `AllowAny`. New endpoints must set permissions explicitly; recommend a global `IsAuthenticated` default so a missed declaration fails closed. Health/ready endpoints opt out explicitly with `AllowAny`. |
| P4 | **Celery Beat** | Optional | Only needed if a **scheduled retry sweep** for failed webhook deliveries is wanted. `/api/ready/` polling is synchronous and needs no Beat. |

---

## User Stories

Stories are grouped into three workstreams. Each has a suggested `task#NN-...`
branch slug (per `CONTRIBUTING.md`), acceptance criteria (AC), and explicit
security ties.

### Workstream A — Token Auth for Service/External Clients

**A1 — API-key model (`task#NN-integrations-apikey-model`)**
*As a* system administrator, *I want* a scoped, revocable API-key record, *so that*
external clients can be granted least-privilege programmatic access.

Acceptance Criteria:
1. New `integrations/` app (mirroring the `drones/` layout) contains an `ApiKey`
   model with: opaque key **hashed at rest** (never stored/returned in plaintext
   after issuance), `role` (FK/choice tied to an existing RBAC role), `is_active`
   / revocation flag, `last_used_at`, `created_at`, and an owning/label field.
2. The raw key is shown **exactly once** at creation; the DB stores only a hash.
3. Revoking a key immediately denies subsequent requests using it.

**A2 — DRF authentication class (`task#NN-integrations-apikey-auth`)**
*As an* external client, *I want* to authenticate with an API key header, *so that*
I can call the API without a browser session.

Acceptance Criteria:
1. A `BaseAuthentication` subclass in `integrations/authentication.py` resolves a
   valid, active key from a request header, sets the authenticated principal with
   the key's role, and updates `last_used_at`.
2. The class is added to `DEFAULT_AUTHENTICATION_CLASSES` in
   [config/settings.py](../config/settings.py) **alongside** session auth (not replacing it).
3. Requests authenticated by key remain subject to `HasRBACPermission`
   — the key's role drives `ROLE_PERMISSION_MATRIX` checks exactly as a session user's does.
4. Invalid/expired/revoked keys return `401`; insufficient role returns `403`.

**A3 — Object scoping for key-authenticated access (`task#NN-integrations-scoping`)**
*As a* security reviewer, *I want* data returned to a key to be object-scoped, *so that*
a key cannot enumerate resources outside its authorization.

Acceptance Criteria:
1. Endpoints reachable by a key that return mission/media/drone data apply
   **membership scoping at the queryset level** via `restrict_missions_for_user`
   ([missions/views.py](../missions/views.py)) — **not** `unit_id` comparisons.
2. No new code compares `mission.unit_id`/`user.unit_id` (review **C1**: `Mission`
   has no unit field and `User.unit` is nullable, so `None == None` grants cross-unit access).
3. No unscoped `.objects.all()` is exposed to key callers (review **C2/C3** IDOR).

**A4 — Admin CRUD + audit logging (`task#NN-integrations-apikey-admin`)**
*As a* system administrator, *I want* to issue and revoke keys with an audit trail, *so that*
key lifecycle is accountable.

Acceptance Criteria:
1. Admin-only CRUD for keys (Django admin + `/api/integrations/api-keys/`).
2. Issuance and revocation write an immutable `AuditLog` entry via the existing
   `create_audit_log(...)` factory (`accounts/services.py`).
3. Key-management endpoints are gated by a new `integrations.manage_keys` permission.

**A5 — Rate limiting the auth surface (`task#NN-integrations-throttle`)**
*As a* platform operator, *I want* key-authenticated and key-management traffic
throttled, *so that* the new surface can't be abused.

Acceptance Criteria:
1. New `integrations_*` scope(s) added to `DEFAULT_THROTTLE_RATES` in
   [config/settings.py](../config/settings.py), env-overridable like existing scopes.
2. Throttling verified for both key-auth request volume and key-management endpoints.

### Workstream B — Outbound Webhooks

**B1 — Webhook subscription model (`task#NN-integrations-webhook-model`)**
*As an* integrator, *I want* to register a webhook with signing and event filters, *so that*
my system receives only the events it cares about, verifiably.

Acceptance Criteria:
1. `Webhook` model: `url`, `secret` (used for HMAC-SHA256 signing), subscribed
   `event_types` (uses the event enum — F1's when available, else the interim
   `IntegrationEventType` per **P1**), `is_active`.
2. Admin/API CRUD gated by `integrations.manage_webhooks`.

**B2 — Signed delivery task (`task#NN-integrations-deliver-webhook`)**
*As an* integrator, *I want* reliable, verifiable delivery, *so that* I can trust
and de-duplicate received events.

Acceptance Criteria:
1. A `deliver_webhook` Celery task signs the payload with HMAC-SHA256 (signature in
   a header) and POSTs to the subscriber URL.
2. It retries with backoff on failure, mirroring the
   `@shared_task(bind=True, max_retries=..., ...)` + `self.retry(exc=exc)` pattern
   in [accounts/tasks.py](../accounts/tasks.py) (**recommend exponential backoff**,
   an improvement over the current fixed 60s delay).
3. Delivery fires from the **same signals** the notifications feature listens to.

**B3 — Delivery log (`task#NN-integrations-delivery-log`)**
*As an* operator, *I want* a record of each delivery attempt, *so that* I can debug
failing integrations.

Acceptance Criteria:
1. A delivery-log record captures target, event type, response status, attempt
   count, and timestamp for each attempt.
2. Log is queryable by admins via API/admin, scoped to management permission.

### Workstream C — Health & Metrics

**C1 — Liveness (`task#NN-integrations-health`)**
*As a* load balancer, *I want* `GET /api/health/`, *so that* I can detect a live process.

Acceptance Criteria:
1. `GET /api/health/` returns `200` quickly with no external dependency checks.
2. Explicitly `AllowAny` (unauthenticated), independent of the global permission default.

**C2 — Readiness (`task#NN-integrations-ready`)**
*As an* orchestrator, *I want* `GET /api/ready/`, *so that* I only route traffic to
a fully-wired instance.

Acceptance Criteria:
1. `GET /api/ready/` checks DB, Redis, and Celery broker reachability and returns
   `200` when all are reachable, `503` otherwise, with a per-dependency status body.
2. Unauthenticated (`AllowAny`); no Celery Beat required.

**C3 — Metrics (optional) (`task#NN-integrations-metrics`)**
*As a* monitoring system, *I want* `/metrics` in Prometheus format, *so that* I can
scrape platform metrics.

Acceptance Criteria:
1. Optional `/metrics` endpoint in Prometheus exposition format.
2. Protected — behind an API key with an `integrations.view_metrics` permission.

---

## Task Breakdown by Phase

**Phase 1 — Prerequisites & scaffolding**
- Land TLS / secure-cookie / HSTS settings (**P2**, gating) — coordinate with deployment.
- Set `DEFAULT_PERMISSION_CLASSES` to `IsAuthenticated` (**P3**); audit existing
  views for accidental reliance on the `AllowAny` fallback.
- Decide the event-enum path (**P1**): consume F1's enum if built, else create the
  interim `IntegrationEventType`.
- Create the `integrations/` app (mirror `drones/`: `apps.py, models.py, serializers.py,
  views.py, urls.py, admin.py, permissions.py, filters.py, services.py, api_details.py,
  factories.py, tests.py, migrations/`); add to `INSTALLED_APPS`; mount
  `path("api/integrations/", include("integrations.urls"))` in [config/urls.py](../config/urls.py).

**Phase 2 — Token auth (Workstream A)**
- `ApiKey` model + migration; `integrations/authentication.py`; register in
  `DEFAULT_AUTHENTICATION_CLASSES`; admin + API CRUD; audit logging via
  `create_audit_log`; queryset/membership scoping; `integrations_*` throttle scope.

**Phase 3 — Webhooks (Workstream B)**
- `Webhook` + delivery-log models + migrations; `deliver_webhook` task with
  backoff; HMAC signing; signal wiring; management API.

**Phase 4 — Health & metrics (Workstream C)**
- `/api/health/`, `/api/ready/` (DB/Redis/broker probes), optional `/metrics`.

**Phase 5 — Docs, RBAC & test hardening**
- Add permissions to `ROLE_PERMISSION_MATRIX` and the [docs/rbac.md](rbac.md) matrix.
- Tests (note `roles`/`common` currently have 0 tests — add coverage for the new
  auth path). Update [docs/api.md](api.md) / drf-spectacular schema.

---

## Parallel Team Execution Plan (8 Developers)

**Goal: no developer is ever blocked waiting on another's in-flight code.**

The natural dependencies (auth needs the key model; the delivery task needs the
webhook model; scoping needs an authenticated principal) are removed by resolving
them **once, up front, as contracts** — then every track codes against the
contract and *mocks/fakes* its collaborators. A track only depends on the merged
Sprint 7 foundation, never on another person's branch.

### Sprint 7 — Foundation & Contracts (collaborative, merged before parallel work)

A single short, mobbed/paired PR that lands **stubs and agreed interfaces**, not
behaviour. Small enough to merge in ~1 day. It contains:

- **App skeleton** — `integrations/` mirroring [drones/](../drones/) (`apps.py`,
  `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `permissions.py`,
  `services.py`, `tasks.py`, `api_details.py`, `factories.py`, `tests/`), added to
  `INSTALLED_APPS` and mounted at `api/integrations/` in [config/urls.py](../config/urls.py).
- **Model field contracts** — `ApiKey`, `Webhook`, `WebhookDelivery` classes with
  **final field names/types** and migrations. Behaviour (hashing, signing) is a stub.
- **Service signatures** — e.g. `generate_api_key()`, `hash_api_key(raw)`,
  `verify_api_key(raw)`, `sign_payload(secret, body)`, `enqueue_webhook(event, payload)`
  in `services.py`, defined and typed but raising `NotImplementedError`.
- **`IntegrationEventType` `TextChoices`** (interim enum per **P1**) — the frozen
  event vocabulary both webhook and signal code import.
- **RBAC constants** — `PERMISSION_INTEGRATIONS_MANAGE_KEYS`,
  `PERMISSION_INTEGRATIONS_MANAGE_WEBHOOKS`, `PERMISSION_INTEGRATIONS_VIEW_METRICS`
  added to [accounts/rbac.py](../accounts/rbac.py) and wired into the matrix.
- **Auth header constant** — the header name the auth class reads and clients send.
- **Serializer skeletons** and **URL routes returning `501 Not Implemented`** so
  every endpoint path exists and is importable from day 1.
- **Factories** — `ApiKeyFactory`, `WebhookFactory`, `WebhookDeliveryFactory` that
  build valid rows directly (setting hashes/secrets on the record), so any track can
  create realistic test data **without** the owning track's logic being finished.

Once this PR merges, the 8 tracks below run fully concurrently.

### The 8 parallel tracks

| Dev | Track (stories) | Owns | Stays unblocked by |
|-----|-----------------|------|--------------------|
| **D1** | **Key lifecycle service** (A1) | `services.py` key gen/hash/verify, one-time reveal, revoke, `last_used_at` update | Implements the Sprint 0 service stubs. Pure functions + model — depends on nothing downstream. |
| **D2** | **DRF auth class** (A2) | `integrations/authentication.py`; registration in `DEFAULT_AUTHENTICATION_CLASSES` | Calls `verify_api_key(...)`; in tests **mocks** it (or uses `ApiKeyFactory` rows). Doesn't wait on D1's real hashing. |
| **D3** | **Object scoping** (A3) | Scoping helper wrapping `restrict_missions_for_user` ([missions/views.py](../missions/views.py)) | Takes an authenticated principal as input; tests with any `UserFactory`. Independent of how the principal was authenticated (D2). |
| **D4** | **Key admin + CRUD + audit** (A4) | `admin.py`, key management viewset/serializers, audit via `create_audit_log` | Uses `ApiKeyFactory` + the model contract; `create_audit_log` already exists. Doesn't need D1/D2 merged. |
| **D5** | **Webhook model + management API** (B1) | `Webhook` CRUD viewset/serializers, admin | Model + enum frozen in Sprint 0. No dependency on delivery (D6) or log (D7). |
| **D6** | **Delivery task + HMAC signing** (B2) | `deliver_webhook` Celery task, `sign_payload` | Operates on a `webhook_id` + payload; **fakes** HTTP with `responses`/`httpretty` and uses `WebhookFactory`. Independent of D5's API and D7's log. |
| **D7** | **Delivery log + signal wiring** (B3) | `WebhookDelivery` writes; signals → `enqueue_webhook(...)` | Calls `enqueue_webhook` (Sprint 0 signature); **mocks** the task in tests. Doesn't wait on D6's real delivery. |
| **D8** | **Health/ready/metrics + throttling + TLS** (C1–C3, A5, P2/P3) | `/api/health/`, `/api/ready/`, optional `/metrics`; `integrations_*` throttle scopes; `SECURE_*` settings | Infra-only; touches no integration model. Fully standalone from day 1. |

### Why nothing blocks

- **Every cross-track call is a Sprint 7 signature**, so a caller codes and tests
  against the interface while the owner fills in behaviour. Example: D2 (auth) and
  D1 (key service) both reference `verify_api_key`; D2 mocks it until D1 lands.
- **Factories replace fixtures-from-other-branches.** D4 doesn't need D1's issuance
  flow to test CRUD — `ApiKeyFactory` builds valid rows.
- **Each track owns distinct files.** Shared files ([config/settings.py](../config/settings.py),
  [accounts/rbac.py](../accounts/rbac.py)) are edited **only in Sprint 0**; tracks add
  their own modules, keeping merge conflicts near zero.
- **Merge order is arbitrary.** Because tracks integrate through stubs, they can land
  in any sequence; a track merging flips its stub to real behaviour with no coordination.
- **Only two things are genuinely sequential and both are handled in Sprint 7:** the
  event enum (**P1**) and the RBAC constants. **P2 (TLS)** is a production-ship gate,
  not a dev-time blocker — developers run over HTTP locally.

>
---

## RBAC Additions

New permission constants in [accounts/rbac.py](../accounts/rbac.py) (following the
`PERMISSION_<DOMAIN>_<ACTION>` convention), wired into the relevant role builders
in `ROLE_PERMISSION_MATRIX`:

| Permission constant | Dotted code | ADMIN | COMMANDER | Others |
|---|---|:---:|:---:|:---:|
| `PERMISSION_INTEGRATIONS_MANAGE_KEYS` | `integrations.manage_keys` | Y | N | N |
| `PERMISSION_INTEGRATIONS_MANAGE_WEBHOOKS` | `integrations.manage_webhooks` | Y | Y | N |
| `PERMISSION_INTEGRATIONS_VIEW_METRICS` | `integrations.view_metrics` | Y | Y | N |

Add a corresponding **Integrations** module block (Manage Keys / Manage Webhooks /
View Metrics operations × role columns) to the permission matrix in
[docs/rbac.md](rbac.md). Enforce via `HasRBACPermission` (view sets
`required_permission`) or an app-local `BasePermission` class like
[drones/permissions.py](../drones/permissions.py).

---

## Security Considerations

This feature introduces a **new authentication surface**; the following code-review
findings ([docs/code_review_report.md](code_review_report.md)) become hard
constraints, each with a required mitigation:

- **C1 — illusory unit scoping.** Do **not** authorize on `unit_id` comparisons.
  `Mission` has no unit field and `User.unit` is nullable, so `None == None` grants
  cross-unit access. Use membership scoping (`restrict_missions_for_user`). (AC A3.2)
- **C2 / C3 — IDOR via unscoped querysets.** RBAC role checks do **not** provide
  object scoping. Every key-reachable endpoint must scope its base queryset. (AC A3.3)
- **Missing `DEFAULT_PERMISSION_CLASSES`.** DRF falls back to `AllowAny`; a missed
  declaration on a new endpoint is silently public. Set a fail-closed default (**P3**).
- **C4 — no TLS / secure cookies.** Keys sent over plaintext are stealable; TLS +
  `SECURE_*` cookie/HSTS settings must land before/with this epic (**P2**).
- **H3 — spoofable audit IP.** `create_audit_log` resolves client IP from
  `X-Forwarded-For` while `TRUSTED_PROXY_COUNT` is unused — weakens attribution for
  key issuance/revocation entries. Harden proxy-aware IP resolution as part of Phase 2.
- **Auth-endpoint throttling.** Extend `DEFAULT_THROTTLE_RATES` to cover the new
  surface (AC A5); today login/token paths lack DRF throttles.

---

## Verification / Definition of Done

**Workstream A (Token Auth)**
- Issue an API key → authenticate a request with it → assert the response respects
  the key's role via `HasRBACPermission`, and `last_used_at` updates.
- Revoke the key → assert subsequent requests return `401`.
- As a key with an unauthorized role → assert `403`.
- Attempt cross-mission/cross-media access via a scoped key → assert it is denied
  (regression guard for C1/C2/C3).

**Workstream B (Webhooks)**
- Register a webhook → trigger a subscribed event → assert a signed delivery with a
  valid HMAC-SHA256 signature and a delivery-log entry.
- Force a delivery failure → assert retry/backoff and that the log records attempts.

**Workstream C (Health & Metrics)**
- `curl /api/health/` → `200` with all services up.
- `curl /api/ready/` with a dependency down → `503` with the failing dependency named;
  with all up → `200`.
- (If built) `/metrics` requires a valid key → `401`/`403` without one.

**Cross-cutting**
- New permissions present in both `ROLE_PERMISSION_MATRIX` and [docs/rbac.md](rbac.md).
- Run `python manage.py test` and `python manage.py check --deploy` — both clean.

---

## Files Touched

- **New `integrations/` app** — `ApiKey`, `Webhook`, delivery log, `authentication.py`,
  services, tasks, serializers, views, urls, admin, permissions, tests (mirror
  [drones/](../drones/)).
- [config/settings.py](../config/settings.py) — `INSTALLED_APPS`,
  `DEFAULT_AUTHENTICATION_CLASSES`, `DEFAULT_PERMISSION_CLASSES`, `DEFAULT_THROTTLE_RATES`,
  `SECURE_*` settings.
- [config/urls.py](../config/urls.py) — mount `api/integrations/`; health/ready (and
  optional metrics) endpoints.
- [config/celery.py](../config/celery.py) — only if a scheduled retry sweep needs Beat (**P4**).
- [accounts/rbac.py](../accounts/rbac.py) — new `PERMISSION_INTEGRATIONS_*` constants + matrix wiring.
- [docs/rbac.md](rbac.md) — new Integrations module block.
- Reuse [accounts/tasks.py](../accounts/tasks.py) retry pattern and
  `create_audit_log` from `accounts/services.py`.

**Depends on F1's event enum** (with interim fallback per **P1**).
