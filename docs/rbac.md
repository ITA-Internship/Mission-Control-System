## User Roles

The system supports role-based access control with the following roles:

| Role           | Permissions                                  |
|----------------|----------------------------------------------|
| **Admin**      | Full system access, user and role management |
| **Commander**  | Mission oversight, approvals, and operational control |
| **Dispatcher** | Mission coordination, creation, and assignment |
| **Operator**   | Mission execution and drone usage tracking   |
| **Technician** | Maintenance and repair management            |
| **Viewer**     | Read-only access to permitted system data    |

## Permission Matrix

| Module         | Operation           | Admin | Commander | Dispatcher | Operator | Technician | Viewer |
|:---------------|:--------------------|:-----:|:---------:|:----------:|:--------:|:----------:|:------:|
| Users          | Manage Roles        |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Create              |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Activate Deactivate |   Y   |     N     |     N      |    N     |     N      |   N    |
| Drones         | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Create              |   Y   |     Y     |     N      |    N     |     N      |   N    |
|                | Update              |   Y   |     Y     |     N      |    N     |     N      |   N    |
|                | Decommission        |   Y   |     Y     |     N      |    N     |     N      |   N    |
|                | Import Export       |   Y   |     Y     |     N      |    N     |     N      |   N    |
| Missions       | View                |   Y   |     Y     |     Y      |    Y     |     N      |   Y    |
|                | Create              |   Y   |     Y     |     Y      |    N     |     N      |   N    |
|                | Assign              |   Y   |     Y     |     Y      |    N     |     N      |   N    |
|                | Update Status       |   Y   |     Y     |     Y      |    Y     |     N      |   N    |
|                | Record Outcome      |   Y   |     N     |     Y      |    Y     |     N      |   N    |
|                | Record Condition    |   Y   |     N     |     Y      |    Y     |     N      |   N    |
| Maintenance    | View                |   Y   |     Y     |     N      |    N     |     Y      |   Y    |
|                | Manage              |   Y   |     N     |     N      |    N     |     Y      |   N    |
| Specifications | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Manage              |   Y   |     N     |     N      |    N     |     Y      |   N    |
| Write-offs     | View                |   Y   |     Y     |     Y      |    N     |     Y      |   Y    |
|                | Create              |   Y   |     N     |     N      |    N     |     Y      |   N    |
|                | Authorize           |   Y   |     Y     |     N      |    N     |     N      |   N    |
| Repairs        | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Create              |   Y   |     N     |     N      |    N     |     Y      |   N    |
|                | Manage              |   Y   |     N     |     N      |    N     |     Y      |   N    |
|                | Export              |   Y   |     Y     |     N      |    N     |     Y      |   N    |
|                | Verify              |   Y   |     Y     |     N      |    N     |     N      |   N    |
| Media          | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Upload              |   Y   |     N     |     Y      |    Y     |     N      |   N    |
|                | Delete              |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | View Logs           |   Y   |     N     |     N      |    N     |     N      |   N    |
| Audit Logs     | View All            |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | View Own            |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
| Profile        | View Own            |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | View Any            |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Update Own          |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Reset Password Own  |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
| Drone Compare  | Specifications      |   Y   |     Y     |     Y      |    Y     |     Y      |   N    |

Users can view and update their own profiles and reset their own passwords.

Only Admin users have the `profile.view_any` permission required to access another user's protected profile picture.
Only Admin users can view all audit logs. Other users can only view audit logs where they are either the actor or the target user.

## Mission-Scoped Visibility

Role-level RBAC and object-level scope both apply to mission-derived resources.
The permission matrix decides which role may access an endpoint category, and
the final decision is then narrowed by mission visibility rules.

### Viewer Rule

`Viewer` users may read only missions that belong to their own military unit.
This same rule applies to mission-derived media resources.

Allowed:
- Mission list/detail for missions where `mission.unit == request.user.unit`
- Mission assignment list for missions where `mission.unit == request.user.unit`
- Mission artifacts and protected media downloads for missions where
  `mission.unit == request.user.unit`
- Video metadata lists and browser results for missions where
  `mission.unit == request.user.unit`

Denied:
- Any mission-scoped resource when the viewer belongs to a different unit
- Any mission-scoped resource when the viewer has no `unit`

### Technician Rule

`Technician` users do not receive `missions.view`, so they cannot browse mission
list/detail endpoints. They do receive `media.view`, and their access to
mission-derived media is limited to missions that are part of a maintenance or
write-off workflow.

Allowed:
- Mission artifacts, protected media downloads, and video metadata for missions
  with at least one damaged or lost mission-drone assignment
- Mission artifacts, protected media downloads, and video metadata for missions
  that already have write-off records
- Mission artifacts, protected media downloads, and video metadata for missions
  linked through drone status history to a repair order or write-off

Denied:
- Mission list/detail endpoints, because `Technician` has no `missions.view`
- Media for unrelated operational missions that have no repair or write-off
  linkage

### Shared Enforcement

Mission-scoped read access is enforced through shared helpers in
`missions/permissions.py`:

- `can_user_view_mission(user, mission)`
- `restrict_missions_for_user(queryset, user)`

These helpers are the source of truth for mission visibility and are used by:

- `MissionListCreateView`
- `MissionDetailView`
- `MissionAssignmentListCreateView`
- `ArtifactListCreateView` (GET)
- `ArtifactDetailView`
- `ProtectedMediaView`
- `VideoMetadataViewSet` (list scoping plus object checks)
- `VideoMetadataBrowserView`

The helpers must stay consistent:

- list endpoints use `restrict_missions_for_user(queryset, user)`
- object checks use `can_user_view_mission(user, mission)`

This avoids duplicated per-endpoint logic, keeps list and retrieve behavior
aligned, and prevents insecure nullable-field fallbacks such as comparing two
missing `unit_id` values.

## Authentication

The application uses Django authentication and the custom `accounts.User`
model.

Django REST Framework uses `SessionAuthentication` as the default
authentication provider. `BasicAuthentication` is enabled only when
`DEBUG=True` and is intended for local development.

Protected DRF endpoints use `IsAuthenticated` by default. A new API endpoint is
therefore protected unless it explicitly declares another permission policy.

Public endpoints must explicitly use `AllowAny`. The intentionally public
endpoints are:

* `POST /api/accounts/activate/<user_id>/<token>/`
* `POST /api/accounts/users/password-reset/`
* `POST /api/accounts/users/password-reset-confirm/<uidb64>/<token>/`
* `GET /api/schema/`
* `GET /api/docs/`
* `GET /api/redoc/`

User registration is not public. Creating a new user requires the
`users.create` permission.

## Session and CSRF Security

Protected API requests are authenticated through the Django session.

Session and CSRF cookies use the following policy:

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
```

Unsafe session-authenticated requests require a valid CSRF token. Unsafe
methods include:

* `POST`
* `PUT`
* `PATCH`
* `DELETE`

Browser clients must send the CSRF token through the `X-CSRFToken` header.

Logging out invalidates access through the current session. Inactive users
cannot create authenticated sessions. A successful password reset invalidates
the user's existing sessions.

## Authorization Flow

Access to a protected action is evaluated in this order:

1. Django resolves the authenticated user from the session.
2. The global `IsAuthenticated` policy rejects anonymous requests.
3. The endpoint applies an RBAC permission class.
4. The permission class checks a permission code against
   `ROLE_PERMISSION_MATRIX`.
5. Object-level ownership, assignment, or resource-scope rules are evaluated.
6. The request is allowed only when all required checks succeed.

The central permission constants and `ROLE_PERMISSION_MATRIX` in
`accounts/rbac.py` are the source of truth.

Views must not maintain separate hardcoded role lists or use `is_staff` as a
replacement for application RBAC.

For a single required permission, use:

```python
class ExampleView(APIView):
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_EXAMPLE_VIEW
```

When any of several permissions is accepted, use:

```python
class ExampleView(APIView):
    permission_classes = [HasAnyRBACPermission]
    required_permissions = [
        PERMISSION_EXAMPLE_VIEW_ALL,
        PERMISSION_EXAMPLE_VIEW_OWN,
    ]
```

## Assigning and Updating Roles

Only users with the `users.manage_roles` permission may assign or change roles.

Before changing role permissions:

1. review the permission matrix;
2. follow the principle of least privilege;
3. update `accounts/rbac.py`;
4. update the matrix in this document;
5. add allowed and denied access tests;
6. verify object-level restrictions where applicable.

## Access Denial

Access must be denied when:

* the endpoint is protected and the user is anonymous;
* the account is inactive;
* the user has no role when an RBAC permission is required;
* the user's role does not contain the required permission;
* ownership, assignment, or resource-scope conditions fail;
* an unsafe session-authenticated request has no valid CSRF token.

With `SessionAuthentication`, rejected anonymous requests may return
`403 Forbidden`.

A `404 Not Found` response may be used instead when queryset scoping prevents
the caller from learning that an inaccessible object exists.

## Access-Control Checklist

Complete this checklist whenever adding or changing an endpoint.

### Authentication

* [ ] Decide whether the endpoint is public or protected.
* [ ] Use explicit `AllowAny` only when anonymous access is required.
* [ ] Confirm protected endpoints reject anonymous users.
* [ ] Add throttling to public credential, activation, or recovery endpoints.
* [ ] Require CSRF protection for unsafe session-authenticated requests.

### RBAC

* [ ] Identify the business action performed by the endpoint.
* [ ] Reuse an existing permission or add a permission constant.
* [ ] Add new permissions to `ROLE_PERMISSION_MATRIX`.
* [ ] Review which roles should receive the permission.
* [ ] Use `HasRBACPermission` or `HasAnyRBACPermission`.
* [ ] Avoid hardcoded role names and `is_staff` authorization bypasses.
* [ ] Add object-level ownership, assignment, or scope checks when required.

### Tests

* [ ] Add a successful request from an authorized role.
* [ ] Add a denied request from an unauthorized role.
* [ ] Add an anonymous-access test.
* [ ] Add a no-role test when RBAC is required.
* [ ] Add an inactive-user test when authentication is involved.
* [ ] Add allowed and denied object-level tests.
* [ ] Add a missing-CSRF test for unsafe session-authenticated requests.
* [ ] Run the complete test suite.

### Documentation

* [ ] Update the permission matrix when permissions change.
* [ ] Document the permission required by the endpoint.
* [ ] Update the OpenAPI endpoint description.
* [ ] Update this checklist when authentication or RBAC behavior changes.

## Verification

Run focused tests:

```bash
python manage.py test common
python manage.py test accounts
```

Then run the complete suite and quality checks:

```bash
python manage.py test
pre-commit run --all-files
```

Authentication or RBAC changes are incomplete until both authorized and
unauthorized paths are covered by automated tests.
