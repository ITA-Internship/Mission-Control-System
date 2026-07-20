# Read Review — Mission Control System (FPV Drone Fleet Management)

**Date:** 2026-07-20
**Reviewer:** Automated read-only code review (no application files modified)
**Scope:** Full backend — `accounts`, `drones`, `repairs`, `missions`, `media`, `roles`, `common`, `config`, CI/CD, deployment, docs
**Nature of system:** Django 5 + DRF REST API tracking the operational lifecycle of FPV drones in **military units**. Because the domain is military, access-control, audit-trail integrity, and file-handling issues are treated as high-impact.

---

## 1. Executive Summary

The project is well-structured (modular monolith, service layer, RBAC, audit logging, throttling, containerized deploy with nginx hardening) and has good test density in most apps (drones 92, repairs 121, missions 76, media 65, accounts 23 test functions). However, the review found **several broken-access-control and authentication defects that are exploitable today**, plus production-hardening gaps that must be closed before this is fielded.

**Highest-priority issues (fix before any deployment):**

| # | Severity | Area | Issue |
|---|----------|------|-------|
| C1 | **CRITICAL** | media / authz | Broken object permission compares `None == None`, granting cross-unit read of all artifacts |
| C2 | **CRITICAL** | media / authz | Cross-mission IDOR: artifact list/upload not scoped to the requester's missions |
| C3 | **CRITICAL** | media / authz | Video metadata listing exposes every video in the system |
| C4 | **CRITICAL** | deploy / transport | No TLS, no `SECURE_*` cookie/HSTS settings — session cookies sent in clear |
| H1 | HIGH | accounts / auth | Account activation sets initial password with **no** strength validation |
| H2 | HIGH | accounts / auth | Password reset/change never invalidate other sessions (`invalidate_user_sessions` is dead code) |
| H3 | HIGH | accounts / audit | Audit-log IP is attacker-controlled via `X-Forwarded-For` |
| H4 | HIGH | drones / authz | Mass assignment of `status` on drone create bypasses decommission permission + audit |
| H5 | HIGH | drones,repairs / injection | CSV/formula injection in all export endpoints |
| H6 | HIGH | drones / integrity | Drone status has no state machine + no row lock (race, illegal reactivation) |
| H7 | HIGH | media / upload | File type validated by extension only; client `content_type` trusted |
| H8 | HIGH | media / DoS | Synchronous, timeout-less `ffprobe` subprocess in the request path |
| H9 | HIGH | CI/CD | No dependency/SAST/secret scanning; coverage not measured or gated |

Supporting medium findings and a remediation roadmap follow.

---

## 2. Task Definition

**Goal:** Perform a read-only review of the codebase described in the README and surface *critical* issues with concrete, actionable fixes.

**Deliverables:** This report — per-issue task definitions with severity, exact location, impact, and proposed action, followed by a prioritized remediation plan.

**Method:** Direct read of configuration/infrastructure (`config/settings.py`, `docker-compose.yml`, `Dockerfile`, `entrypoint.sh`, nginx, CI) plus four parallel deep reviews of the domain apps. Key findings were independently verified against source.

---

## 3. Critical Findings

### C1 — Broken object-level permission grants cross-unit access to all media
**Severity:** CRITICAL · **File:** [media/permissions.py:25-27](media/permissions.py#L25-L27)

```python
mission = getattr(obj, "mission", None)
if mission and getattr(mission, "unit_id", None) == request.user.unit_id:
    return True
```

The `Mission` model has **no `unit`/`unit_id` field** (verified: `grep unit missions/models.py` → 0 matches). So `getattr(mission, "unit_id", None)` is always `None`. `User.unit` is nullable ([accounts/models.py](accounts/models.py)). For any user whose `unit` is `None`, the comparison is `None == None → True`, granting read access to **every artifact of every mission**. This is the gate relied on by artifact detail retrieval and `ProtectedMediaView` download.

**Proposed action:** Remove the `unit_id` comparison entirely. Authorize on real mission membership — user is the mission's `commander`/`created_by`, an assigned operator via `MissionDrone`, or admin. Never compare two attributes that can both be `None`.

---

### C2 — Cross-mission IDOR on artifact list & upload
**Severity:** CRITICAL · **File:** [media/views.py:97-149](media/views.py#L97-L149)

`_MissionArtifactMixin.get_mission` loads `Mission.objects.all()` by `mission_pk` with no scoping to the requester. List views never invoke `has_object_permission`, so:
- **GET** — any user with `media.view` can enumerate `mission_pk` and read artifacts of any mission, bypassing `restrict_missions_for_user` used elsewhere in the missions app.
- **POST** — any user with `media.upload` can attach artifacts to any mission by choosing an arbitrary `mission_pk`.

**Proposed action:** Scope `get_mission` to the requester's authorized missions (reuse `missions.views.restrict_missions_for_user`) so unauthorized `mission_pk` returns 404, and enforce object-level authorization on both list and create.

---

### C3 — Video metadata listing exposes all videos system-wide
**Severity:** CRITICAL · **File:** [media/views.py:52-94](media/views.py#L52-L94), [media/views.py:249-266](media/views.py#L249-L266)

`VideoMetadataViewSet.get_queryset` and `VideoMetadataBrowserView` return `VideoMetadata.objects.all()` filtered only by optional query params, with no scoping to the caller's unit/missions. Any authenticated user with `media.view` can list metadata and links for every video in the system.

**Proposed action:** Filter the base queryset by the caller's authorized missions/unit before applying request-supplied filters.

---

### C4 — No transport security; session cookies not marked Secure
**Severity:** CRITICAL · **Files:** [config/settings.py](config/settings.py) (missing settings), [deploy/nginx/default.conf:6](deploy/nginx/default.conf#L6)

There is no `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, or `SESSION_COOKIE_HTTPONLY` anywhere. nginx listens only on `:80` with no TLS block and no HSTS header. With session-based auth, cookies can be transmitted and stolen over plaintext HTTP.

**Proposed action:** Terminate TLS (nginx `443` block or external LB with 80→443 redirect), add HSTS, and in production settings set `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_HTTPONLY=True`. Add a Django deployment-check step (`manage.py check --deploy`) to CI.

---

## 4. High-Severity Findings

### H1 — Account activation bypasses password-strength policy
**File:** [accounts/views.py:154-161](accounts/views.py#L154-L161). The public activation endpoint reads the raw password from `request.data` and calls `set_user_password` without `validate_password`, while change/reset flows enforce it. An operator can activate a military account with `"1"`. It also does not verify account state or set `is_active`, making it a reusable "set password by valid token" endpoint.
**Action:** Route the body through a serializer that calls `django.contrib.auth.password_validation.validate_password(value, user)`; add a state/`must_change_password` check.

### H2 — Password reset/change do not invalidate other sessions
**Files:** [accounts/views.py:374-402](accounts/views.py#L374-L402) (`invalidate_user_sessions` — **defined but never called**), reset-confirm and change-password views. An attacker who hijacked a session keeps access after the victim resets. The API docs (`api_details.py`) explicitly promise the opposite.
**Action:** Call `invalidate_user_sessions(user)` in both password-reset-confirm and change-password, re-establishing the current session via `update_session_auth_hash` for the change case.

### H3 — Audit-log IP is attacker-controllable
**File:** [accounts/services.py:220-227](accounts/services.py#L220-L227). `X-Forwarded-For` is trusted blindly (`split(",")[-1]`) with no trusted-proxy count, so clients forge the `ip_address` on every immutable `AuditLog` entry (LOGIN_FAILED, ROLE_CHANGED, …), destroying attribution. Note `TRUSTED_PROXY_COUNT` already exists in settings but is not used here.
**Action:** Derive the client IP using `TRUSTED_PROXY_COUNT` (strip exactly N trusted hops from the right) or `django-ipware`; never fall back to a raw header when no proxy is trusted.

### H4 — Mass assignment of drone `status` on create
**File:** [drones/serializers.py:225-234](drones/serializers.py#L225-L234) (`fields = "__all__"`). The create permission only requires `DRONES_CREATE`; the decommission guard lives in `has_object_permission`, which never runs on create. A user can POST a drone with `status: WRITTEN_OFF` — landing it in an inactive state with no `WriteOffRecord` and no `DroneStatusHistory`, bypassing permission and audit.
**Action:** Replace `__all__` with an explicit field list; make `status` read-only on create (force `ACTIVE`) or validate initial status.

### H5 — CSV / formula injection in exports
**Files:** [drones/services.py:228-264](drones/services.py#L228-L264), [drones/views.py:164-205](drones/views.py#L164-L205), [repairs/views.py:214-232](repairs/views.py#L214-L232), [repairs/services.py:386-410](repairs/services.py#L386-L410). User-controlled fields (drone name/notes, serials, defect descriptions) are written raw; a value like `=cmd|'/c calc'!A1` executes when opened in Excel/Sheets.
**Action:** Add a shared sanitizer that neutralizes cells starting with `= + - @`, tab, or CR (prefix `'`), applied across all writers.

### H6 — Drone status: no state machine + no row lock
**Files:** [drones/serializers.py:323-359](drones/serializers.py#L323-L359), [drones/services.py:122-212](drones/services.py#L122-L212). A `WRITTEN_OFF` drone can be transitioned back to `ACTIVE` (leaving a dangling immutable write-off record), and `update_drone` is atomic but never does `select_for_update`, so concurrent PATCHes race on status/history. (The repairs service correctly locks — see [repairs/services.py:80](repairs/services.py#L80).)
**Action:** Define an allowed-transition map for `Drone.status`; re-fetch with `select_for_update()` inside the atomic block. Apply the same lock to write-off creation ([drones/services.py:560-595](drones/services.py#L560-L595)).

### H7 — File type by extension only; client content-type trusted
**Files:** [media/models.py:59-64](media/models.py#L59-L64), [media/serializers.py:87](media/serializers.py#L87), [media/serializers.py:199-220](media/serializers.py#L199-L220). Arbitrary bytes named `x.png`/`x.csv` are accepted; video `content_type` is taken from the client. Also a **path-traversal** risk: `video_upload_path` interpolates the raw client filename ([media/models.py:51-56](media/models.py#L51-L56)), unlike the artifact path which correctly uses a UUID.
**Action:** Validate real content with libmagic/`python-magic` against the claimed extension; never trust client `content_type`; use a UUID + validated extension for the video path.

### H8 — Synchronous timeout-less ffprobe in request path (DoS)
**File:** [media/serializers.py:99-132](media/serializers.py#L99-L132). `subprocess.run([... ffprobe ...], check=True)` runs synchronously with no `timeout` in the HTTP request; a crafted file blocks the worker. The same probe is also enqueued as a Celery task, duplicating work.
**Action:** Remove the synchronous probe and rely on the existing Celery task (`media/tasks.py`, which sets `timeout=30`); if kept, add a strict timeout.

### H9 — CI has no security scanning and no coverage gate
**File:** [.github/workflows/ci.yml](.github/workflows/ci.yml). Runs flake8 + tests only. No `pip-audit`/`safety` (dependency CVEs), no `bandit` (SAST), no secret scanning, no coverage measurement/threshold.
**Action:** Add `pip-audit`, `bandit -r .`, `coverage run manage.py test && coverage report --fail-under=N`, and enable secret scanning/gitleaks. Confirm branch protection makes these required checks on `main`/`develop`.

---

## 5. Medium-Severity Findings

- **No global DRF permission default.** `REST_FRAMEWORK` sets no `DEFAULT_PERMISSION_CLASSES` ([config/settings.py:153](config/settings.py#L153)), so it falls back to `AllowAny`. Views mostly set permissions explicitly (50 declarations / 43 view classes), but any missed action is silently public. **Action:** set `DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.IsAuthenticated"]`.
- **Video metadata mass assignment:** `mission`/`drone` reassignable on PATCH, skipping `Model.clean()` assignment validation ([media/serializers.py:22-63](media/serializers.py#L22-L63)).
- **Repairs business-logic gaps:** replacements can be added to completed/cancelled orders ([repairs/views.py:310-322](repairs/views.py#L310-L322)); defect status transitions largely unrestricted ([repairs/services.py:70-108](repairs/services.py#L70-L108)); repair-history timeline fully materialized in memory before pagination ([repairs/services.py:256-383](repairs/services.py#L256-L383)).
- **N+1 on drone CSV export** — add `drone_model` to `select_related` ([drones/views.py:401](drones/views.py#L401)).
- **Login endpoint not rate-limited** at nginx (auth zone covers only activate/reset); DRF has no login throttle ([deploy/nginx/default.conf:27](deploy/nginx/default.conf#L27)) — brute-force exposure.
- **Celery serializer not pinned** — set `CELERY_ACCEPT_CONTENT=["json"]`, `CELERY_TASK_SERIALIZER="json"`; use `rediss://` in prod.
- **CSP allows `'unsafe-inline'`** for scripts/styles ([deploy/nginx/default.conf:25](deploy/nginx/default.conf#L25)).
- **`docker-compose.yml`** bind-mounts source (`.:/app`) and sets celery `DEBUG` default to `True` — dev-oriented; ensure a separate prod compose file.

---

## 6. Testing & Documentation Gaps

- **`roles/tests.py` has 0 tests** yet `roles` is the RBAC backbone (`docs/rbac.md` permission matrix). Add tests asserting each role→permission mapping.
- **`common/models.py`, `common/views.py`, `roles/views.py` are empty**; `common/utils.py` is a stub. Remove or document.
- **`docs/deployment.md` is empty** despite real TLS/secrets/Celery/storage complexity.
- Missing tests for the exact areas of H1/H2 (activation password strength, session invalidation on reset).
- `CONTRIBUTING.md` branch-naming is inconsistent and omits `pre-commit`/test prerequisites.

---

## 7. What's Already Good (no action)

- No real secrets committed; only `.env.example` tracked; settings hard-fail without `DJANGO_SECRET_KEY`; `BasicAuthentication` gated behind `DEBUG`.
- Missions app: sound object-level scoping, `select_for_update` locking, audit logging, role checks.
- Service-layer pattern binds `reporter`/`authorized_by`/`created_by` from the request user, not the payload.
- nginx baseline: `server_tokens off`, sane timeouts, 60m body cap, solid security-header set, internal-media (`X-Accel-Redirect`) gated through Django.
- `AuditLogViewSet` and `UserMeSerializer` correctly prevent IDOR / self-privilege-escalation.

---

## 8. Proposed Remediation Roadmap

**Sprint 1 — block deployment until done (auth & transport):**
1. C1, C2, C3 — rebuild media authorization around real mission membership; add regression tests for cross-unit/cross-mission access.
2. C4 — TLS + `SECURE_*`/HSTS settings; add `manage.py check --deploy` to CI.
3. H1, H2, H3 — activation password validation, session invalidation on reset/change, trusted-proxy IP resolution.

**Sprint 2 — data integrity & injection:**
4. H4, H6 — explicit field lists, drone status state machine + row locking.
5. H5 — shared CSV sanitizer.
6. H7, H8 — content-based file validation, UUID video paths, remove synchronous ffprobe.

**Sprint 3 — hardening & coverage:**
7. H9 — bandit/pip-audit/coverage in CI + branch protection.
8. Global DRF permission default; medium findings; `roles` tests; fill `docs/deployment.md`.

---

*This report is analysis only; no application source files were modified. Each finding cites exact locations for verification.*
