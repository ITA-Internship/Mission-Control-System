## User Roles

The system supports role-based access control with the following roles:

| Role           | Permissions                                  |
|----------------|----------------------------------------------|
| **Admin**      | Full system access, user and role management |
| **Commander**  | System oversight, reporting, decision-making |
| **Dispatcher** | Mission planning and drone allocation        |
| **Operator**   | Mission execution and drone usage tracking   |
| **Technician** | Maintenance and repair management            |
| **Viewer**     | Read-only access to system data              |

## Permission Matrix

| Module         | Operation           | Admin | Commander | Dispatcher | Operator | Technician | Viewer |
|:---------------|:--------------------|:-----:|:---------:|:----------:|:--------:|:----------:|:------:|
| Users          | Manage Roles        |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Create              |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Activate Deactivate |   Y   |     N     |     N      |    N     |     N      |   N    |
| Drones         | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Create              |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Update              |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Decommission        |   Y   |     N     |     N      |    N     |     N      |   N    |
|                | Import Export       |   Y   |     N     |     N      |    N     |     N      |   N    |
| Missions       | View                |   Y   |     Y     |     Y      |    Y     |     N      |   Y    |
|                | Create              |   Y   |     N     |     Y      |    N     |     N      |   N    |
|                | Assign              |   Y   |     Y     |     Y      |    N     |     N      |   N    |
|                | Update Status       |   Y   |     Y     |     N      |    Y     |     N      |   N    |
|                | Record Outcome      |   Y   |     N     |     N      |    Y     |     N      |   N    |
|                | Record Condition    |   Y   |     N     |     N      |    Y     |     N      |   N    |
| Maintenance    | View                |   Y   |     Y     |     N      |    N     |     Y      |   Y    |
|                | Manage              |   Y   |     N     |     N      |    N     |     Y      |   N    |
| Specifications | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Manage              |   Y   |     N     |     N      |    N     |     Y      |   N    |
| Write-offs     | View                |   Y   |     Y     |     N      |    N     |     Y      |   Y    |
|                | Create              |   Y   |     N     |     N      |    N     |     Y      |   N    |
|                | Authorize           |   Y   |     Y     |     N      |    N     |     N      |   N    |
| Repairs        | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Create              |   Y   |     N     |     N      |    Y     |     Y      |   N    |
| Media          | View                |   Y   |     Y     |     Y      |    Y     |     N      |   Y    |
|                | Upload              |   Y   |     N     |     Y      |    Y     |     N      |   N    |
|                | Delete              |   Y   |     Y     |     N      |    N     |     N      |   N    |
| Audit Logs     | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
| Profile        | View                |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Update              |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
|                | Reset Password      |   Y   |     Y     |     Y      |    Y     |     Y      |   Y    |
| Drone Compare  | Specifications      |   Y   |     N     |     Y      |    Y     |     Y      |   N    |

Users can perform Profile operations (view, update, reset password) only on their own profiles.

Only Admin users can view all audit logs. 
Other users can only view audit logs where they are either the actor or the target user.
