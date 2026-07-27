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
|                | Update Own          |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Reset Password Own  |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
| Drone Compare  | Specifications      |   Y   |     Y     |     Y      |    Y     |     Y      |   N    |

Users can perform Profile operations (view, update, reset password) only on their own profiles.

Only Admin users can view all audit logs. Other users can only view audit logs where they are either the actor or the target user.

## Mission-Scoped Visibility

Role-level RBAC grants the `Viewer` role read access to missions and media, but
the final decision for mission-scoped resources is constrained by object-level
visibility rules.

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

This avoids duplicated per-endpoint logic and prevents insecure nullable-field
fallbacks such as comparing two missing `unit_id` values.
