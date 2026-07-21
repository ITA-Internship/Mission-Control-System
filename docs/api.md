# Mission Control System API

Documentation for Mission-Control-System

# Base URL


| URL | Description |
|-----|-------------|


# Authentication



## Security Schemes

| Name              | Type              | Description              | Scheme              | Bearer Format             |
|-------------------|-------------------|--------------------------|---------------------|---------------------------|
| basicAuth | http |  | basic |  |
| cookieAuth | apiKey |  |  |  |

# APIs

## POST /api/accounts/activate/{user_id}/{token}/

Activate user account

Validates the activation token provided via the URL parameters. If the token is valid, it sets the user's new password and creates an audit log entry.

Required permission: `AllowAny`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | True | The one-time activation token generated for the user. |
| user_id | integer | True | ID of the user activating the account. |


### Responses

#### 200


Your account has been activated. You can now log in.




#### 400


Bad Request


object






Examples





```json
{
  "detail": "Invalid or expired activation link."
}
```




```json
{
  "password": "This field is required."
}
```



#### 404


Not Found.




## GET /api/accounts/audit-log/

List audit logs

Retrieves a paginated and filtered list of audit logs. Depending on permissions, users can view all logs or only logs where they are the actor or the target.

Required permission: `PERMISSION_AUDIT_LOGS_VIEW_OWN, PERMISSION_AUDIT_LOGS_VIEW_ALL`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| action_type | string |  |  |
| actor | integer |  |  |
| end_date | string |  |  |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| result | string |  |  |
| start_date | string |  |  |
| target_user | integer |  |  |


### Responses

#### 200


Successfully retrieved the list of audit logs.


[PaginatedAuditLogList](#paginatedauditloglist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 3,
      "actor": 1,
      "actor_username": "user",
      "target_user": 1,
      "target_user_username": "user",
      "action_type": "LOGOUT",
      "result": "SUCCESS",
      "description": "User logged out successfully",
      "ip_address": "127.0.0.1",
      "user_agent": "Test Agent Value",
      "created_at": "2026-06-25T14:44:49.068836Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/accounts/audit-log/{id}/

Retrieve an audit log

Retrieves detailed information about specific audit log entry by its ID. Depending on permissions, users can view all logs or only logs where they are the actor or the target.

Required permission: `PERMISSION_AUDIT_LOGS_VIEW_OWN, PERMISSION_AUDIT_LOGS_VIEW_ALL`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of specific audit log. |


### Responses

#### 200


Audit log details successfully retrieved.


[AuditLog](#auditlog)






Examples





```json
{
  "id": 3,
  "actor": 1,
  "actor_username": "user",
  "target_user": 1,
  "target_user_username": "user",
  "action_type": "LOGOUT",
  "result": "SUCCESS",
  "description": "User logged out successfully",
  "ip_address": "127.0.0.1",
  "user_agent": "Test Agent Value",
  "created_at": "2026-06-25T14:44:49.068836Z"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/accounts/audit-log/export/

Export audit logs to CSV

Generates and downloads a CSV file with the filtered audit logs. Supports full filtering and sorting identical to the standard list endpoint. 

The export is limited to a maximum of 10000 records.

Required permission: `PERMISSION_AUDIT_LOGS_VIEW_OWN, PERMISSION_AUDIT_LOGS_VIEW_ALL`.




### Responses

#### 200


A CSV file containing audit logs generated successfully.




#### 403


Forbidden. User does not have permission to perform this action.




#### 429


Export rate limit exceeded.




## POST /api/accounts/users/

Register a new user

Creates a new user. Sends an activation email to the user and creates an audit log entry. 

Validation: 
- Image file size cannot exceed 5 MB. 
- Supported image file formats: .jpg, .jpeg, .png, .webp.

Required permission: `PERMISSION_USERS_CREATE`.




### Request Body

[UserRegistration](#userregistration)






Examples





```json
{
  "username": "oleksandr.koval",
  "email": "oleksandr.koval@example.com",
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000",
  "role": 1,
  "unit": 7
}
```

[UserRegistration](#userregistration)





[UserRegistration](#userregistration)







### Responses

#### 201


User account successfully created.


[UserRegistration](#userregistration)






Examples





```json
{
  "username": "oleksandr.koval",
  "email": "oleksandr.koval@example.com",
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000",
  "role": 1,
  "unit": 7
}
```



#### 400


Bad Request


[UserRegistration](#userregistration)






Examples





```json
{
  "profile_picture": "Unsupported file format. Allowed are: .jpg, .jpeg, .png, .webp."
}
```




```json
{
  "profile_picture": "Image size cannot exceed 5MB."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## PATCH /api/accounts/users/{id}/status/

Update user status

Allows system administrators to activate or deactivate a user's account, creates an audit log entry. 

Validation: 
- User cannot deactivate their own account.

Required permission: `PERMISSION_USERS_ACTIVATE_DEACTIVATE`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| pk | integer | True | The ID of the target user whose status is being updated. |


### Request Body

[PatchedUserStatusUpdate](#patcheduserstatusupdate)






Examples





```json
{
  "is_active": true
}
```

[PatchedUserStatusUpdate](#patcheduserstatusupdate)





[PatchedUserStatusUpdate](#patcheduserstatusupdate)







### Responses

#### 200


User status updated successfully.




#### 400


Bad Request




#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/accounts/users/{user_id}/profile-picture/

Retrieve a user's profile picture

Returns the profile picture image file of the specified user, served inline. In production the file is delivered through a protected `X-Accel-Redirect` internal redirect; in debug mode the file is streamed directly.

Access rules: 
- Any authenticated user may retrieve their own profile picture. 
- Only staff users may retrieve another user's profile picture. 
- Returns 404 if the target user has no profile picture, or if the stored file is missing from the server.

Required permission: `IsAuthenticated`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | integer | True | ID of the user whose profile picture is being retrieved. |


### Responses

#### 200


The profile picture image file is returned inline with the appropriate content type.


string







#### 403


Forbidden




#### 404


Not Found




## PATCH /api/accounts/users/{user_id}/role/

Update user role

Updates the role of a specific user and creates an audit log entry. 

Validation: 
- The role of an inactive user cannot be changed. 
- Admin user cannot remove their own admin role. 
- The admin role cannot be removed from the root account. 
- The admin role cannot be removed from the last admin user.

Required permission: `PERMISSION_USERS_MANAGE_ROLES`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | integer | True | ID of the user whose role is being updated. |


### Request Body

[PatchedUserRoleUpdate](#patcheduserroleupdate)






Examples





```json
{
  "role_id": 3
}
```

[PatchedUserRoleUpdate](#patcheduserroleupdate)





[PatchedUserRoleUpdate](#patcheduserroleupdate)







### Responses

#### 200


User role successfully updated.


[UserRoleUpdateResponse](#userroleupdateresponse)






Examples





```json
{
  "role_id": 3
}
```



#### 400


Bad Request


[UserRoleUpdateResponse](#userroleupdateresponse)






Examples





```json
{
  "role_id": "This field is required."
}
```




```json
{
  "role_id": "Invalid role_id"
}
```




```json
{
  "role_id": "Cannot change the role of an inactive user."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/accounts/users/me/

Retrieve current user profile

Retrieves the profile details of the currently authenticated user.

Required permission: `PERMISSION_PROFILE_VIEW_OWN`.




### Responses

#### 200


Profile details successfully retrieved.


[UserMe](#userme)






Examples





```json
{
  "id": 24,
  "username": "oleksander.koval",
  "email": "oleksander.koval@example.com",
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000",
  "profile_picture": null,
  "role": 1,
  "unit": 7,
  "is_active": true
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## PUT /api/accounts/users/me/

Update current user profile

Updates the currently authenticated user's profile information and creates an audit log entry.

Validation: 
- Image file size cannot exceed 5 MB. 
- Supported image file formats: .jpg, .jpeg, .png, .webp.

Required permission: `PERMISSION_PROFILE_UPDATE_OWN`.




### Request Body

[UserMe](#userme)






Examples





```json
{
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000"
}
```

[UserMe](#userme)





[UserMe](#userme)







### Responses

#### 200


Profile information successfully updated.


[UserMe](#userme)






Examples





```json
{
  "id": 24,
  "username": "oleksander.koval",
  "email": "oleksander.koval@example.com",
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000",
  "profile_picture": null,
  "role": 1,
  "unit": 7,
  "is_active": true
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## PATCH /api/accounts/users/me/

Update current user profile

Updates the currently authenticated user's profile information and creates an audit log entry.

Validation: 
- Image file size cannot exceed 5 MB. 
- Supported image file formats: .jpg, .jpeg, .png, .webp.

Required permission: `PERMISSION_PROFILE_UPDATE_OWN`.




### Request Body

[PatchedUserMe](#patcheduserme)






Examples





```json
{
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000"
}
```

[PatchedUserMe](#patcheduserme)





[PatchedUserMe](#patcheduserme)







### Responses

#### 200


Profile information successfully updated.


[UserMe](#userme)






Examples





```json
{
  "id": 24,
  "username": "oleksander.koval",
  "email": "oleksander.koval@example.com",
  "first_name": "Oleksandr",
  "last_name": "Koval",
  "rank": "Colonel",
  "contact": "+380000000000",
  "profile_picture": null,
  "role": 1,
  "unit": 7,
  "is_active": true
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/accounts/users/me/change-password/

Change user password

Changes the password for the currently authenticated user and creates an audit log entry. Upon a successful password change, all active sessions for this user are invalidated.

Required permission: `PERMISSION_PROFILE_RESET_PASSWORD_OWN`.




### Request Body

[ChangePassword](#changepassword)






Examples





```json
{
  "old_password": "my_old_password_123",
  "new_password": "my_new_password_123"
}
```

[ChangePassword](#changepassword)





[ChangePassword](#changepassword)







### Responses

#### 200


Password changed successfully. Active sessions have been invalidated.




#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/accounts/users/password-reset/

Initiate password reset

Accepts a user's email address and sends a password reset link containing a one-time token to that email. An audit log entry and an email are only generated if a matching user is found.

Required permission: `AllowAny`.




### Request Body

[PasswordResetRequest](#passwordresetrequest)





[PasswordResetRequest](#passwordresetrequest)





[PasswordResetRequest](#passwordresetrequest)







### Responses

#### 200


If an account with this email exists, a password reset link has been sent.


[PasswordResetRequest](#passwordresetrequest)







#### 400


Bad Request. Provided payload contains validation errors.




## POST /api/accounts/users/password-reset-confirm/{uidb64}/{token}/

Confirm password reset

Validates the link parameters sent via email. If valid, updates the user's password to the newly provided one, invalidates all current sessions for this user, sends a confirmation email, and creates an audit log entry.

Required permission: `AllowAny`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | True | The one-time password reset token generated for the user. |
| uidb64 | string | True | The Base64-encoded unique identifier of the user. |


### Request Body

[PasswordResetConfirm](#passwordresetconfirm)





[PasswordResetConfirm](#passwordresetconfirm)





[PasswordResetConfirm](#passwordresetconfirm)







### Responses

#### 200


Password has been reset successfully.




#### 400


Bad Request. Provided payload contains validation errors.




## GET /api/drones/

List drones

Retrieves a paginated and filtered list of all drones in the system.

By default list displays only drones with active statuses. Choose one of the inactive statuses during filtration to get drones with inactive status.

Required permission: `PERMISSION_DRONES_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| classification | string |  |  |
| drone_model | integer |  |  |
| drone_model__name | string |  |  |
| inventory_number | string |  |  |
| inventory_number__icontains | string |  |  |
| is_firmware_outdated | boolean |  |  |
| military_unit | string |  |  |
| military_unit__name__icontains | string |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| serial_number | string |  |  |
| serial_number__icontains | string |  |  |
| spec__max_flight_time_min | number |  |  |
| spec__max_flight_time_min__gte | number |  |  |
| spec__max_flight_time_min__lte | number |  |  |
| spec__max_range_km | number |  |  |
| spec__max_range_km__gte | number |  |  |
| spec__max_range_km__lte | number |  |  |
| spec__max_speed_kmh | number |  |  |
| spec__max_speed_kmh__gte | number |  |  |
| spec__max_speed_kmh__lte | number |  |  |
| spec__payload_capacity_g | integer |  |  |
| spec__payload_capacity_g__gte | integer |  |  |
| spec__payload_capacity_g__lte | integer |  |  |
| spec__typical_flight_time_min | number |  |  |
| spec__typical_flight_time_min__gte | number |  |  |
| spec__typical_flight_time_min__lte | number |  |  |
| spec__typical_range_km | number |  |  |
| spec__typical_range_km__gte | number |  |  |
| spec__typical_range_km__lte | number |  |  |
| status | string |  |  |


### Responses

#### 200


Successfully retrieved the list of drones.


[PaginatedDroneListList](#paginateddronelistlist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 21,
      "serial_number": "FPV-AER-24001",
      "inventory_number": "INV-AER-001",
      "name": "Falcon Eye 1",
      "drone_model": 15,
      "classification": "RECONNAISSANCE",
      "status": "ACTIVE",
      "status_label": "Active",
      "status_indicator": "success",
      "status_category": "available",
      "military_unit": 7,
      "created_at": "2026-07-02T02:21:31.174390Z"
    }
  ]
}
```




```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 29,
      "serial_number": "FPV-ATK-24009",
      "inventory_number": "INV-ATK-009",
      "name": "Lancer 1",
      "drone_model": 21,
      "classification": "COMBAT",
      "status": "WRITTEN_OFF",
      "status_label": "Written off",
      "status_indicator": "danger",
      "status_category": "written_off",
      "military_unit": 8,
      "created_at": "2026-07-02T02:21:31.218672Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/drones/

Create a new drone

Creates a new drone with its technical specification. Creates an audit log entry with all spec values written down as `new_values`. 

Validation: 
- Classification of a drone must be supported by its model.

Required permission: `PERMISSION_DRONES_CREATE`.




### Request Body

[Drone](#drone)






Examples





```json
{
  "spec": {
    "frame_type": "7-inch carbon frame",
    "motor_model": "XING2 2806.5 1300KV",
    "battery_type": "Li-Ion 6S",
    "battery_capacity_mah": 4000,
    "camera_model": "RunCam Phoenix 2",
    "vtx_model": "Rush Tank Solo",
    "flight_controller": "Matek H743",
    "firmware_version": "INAV 7.1",
    "is_firmware_outdated": false,
    "max_speed_kmh": "118.50",
    "typical_range_km": "14.60",
    "max_range_km": "18.20",
    "typical_flight_time_min": "21.00",
    "max_flight_time_min": "24.00",
    "frequency_mhz": 5800,
    "payload_capacity_g": 250
  },
  "status_label": "Active",
  "status_indicator": "success",
  "status_category": "available",
  "serial_number": "FPV-AER-24001",
  "inventory_number": "INV-AER-001",
  "name": "Falcon Eye 1",
  "classification": "RECONNAISSANCE",
  "status": "ACTIVE",
  "acquired_at": "2025-01-12",
  "notes": "Recon platform configured for stable daytime observation sorties.",
  "drone_model": 15,
  "military_unit": 7
}
```

[Drone](#drone)





[Drone](#drone)







### Responses

#### 201


Drone created successfully.


[Drone](#drone)






Examples





```json
{
  "id": 32,
  "spec": {
    "id": 32,
    "frame_type": "7-inch carbon frame",
    "motor_model": "XING2 2806.5 1300KV",
    "battery_type": "Li-Ion 6S",
    "battery_capacity_mah": 4000,
    "battery_model": "",
    "camera_model": "RunCam Phoenix 2",
    "camera_specs": {},
    "vtx_model": "Rush Tank Solo",
    "flight_controller": "Matek H743",
    "firmware_version": "INAV 7.1",
    "is_firmware_outdated": false,
    "communication_protocol": "",
    "control_channel": "",
    "telemetry_channel": "",
    "max_speed_kmh": "118.50",
    "typical_range_km": "14.60",
    "max_range_km": "18.20",
    "typical_flight_time_min": "21.00",
    "max_flight_time_min": "24.00",
    "frequency_mhz": 5800,
    "payload_capacity_g": 250,
    "additional_modules": [],
    "technical_documentation_url": "",
    "firmware_file_url": "",
    "updated_at": "2026-07-03T00:40:00.799313Z",
    "change_history": [
      {
        "id": 2,
        "changed_by": 24,
        "changed_fields": [
          "frame_type",
          "motor_model",
          "battery_type",
          "battery_capacity_mah",
          "camera_model",
          "vtx_model",
          "flight_controller",
          "firmware_version",
          "is_firmware_outdated",
          "max_speed_kmh",
          "typical_range_km",
          "max_range_km",
          "typical_flight_time_min",
          "max_flight_time_min",
          "frequency_mhz",
          "payload_capacity_g"
        ],
        "old_values": {},
        "new_values": {
          "vtx_model": "Rush Tank Solo",
          "frame_type": "7-inch carbon frame",
          "motor_model": "XING2 2806.5 1300KV",
          "battery_type": "Li-Ion 6S",
          "camera_model": "RunCam Phoenix 2",
          "max_range_km": "18.20",
          "frequency_mhz": 5800,
          "max_speed_kmh": "118.50",
          "firmware_version": "INAV 7.1",
          "typical_range_km": "14.60",
          "flight_controller": "Matek H743",
          "payload_capacity_g": 250,
          "max_flight_time_min": "24.00",
          "battery_capacity_mah": 4000,
          "is_firmware_outdated": false,
          "typical_flight_time_min": "21.00"
        },
        "created_at": "2026-07-03T00:40:00.800251Z"
      }
    ]
  },
  "writeoff_record": null,
  "status_history": [],
  "status_label": "Active",
  "status_indicator": "success",
  "status_category": "available",
  "serial_number": "FPV-AER-24001",
  "inventory_number": "INV-AER-001",
  "name": "Falcon Eye 1",
  "classification": "RECONNAISSANCE",
  "status": "ACTIVE",
  "acquired_at": "2025-01-12",
  "notes": "Recon platform configured for stable daytime observation sorties.",
  "created_at": "2026-07-03T00:40:00.798536Z",
  "updated_at": "2026-07-03T00:40:00.798549Z",
  "drone_model": 15,
  "military_unit": 7
}
```



#### 400


Bad Request


object






Examples





```json
{
  "classification": "Classification \"RECONNAISSANCE\" is not supported by drone model \"Atlas Relay 8\". Allowed: Transport, Surveillance"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/drones/{drone_pk}/write-offs/history/



Expose read-only write-off audit records.

The endpoint can return all write-off records or records scoped to a selected
drone when the URL contains a drone primary key.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| authorized_by | number |  |  |
| document_number | string |  |  |
| drone | number |  |  |
| drone_inventory_number | string |  |  |
| drone_pk | integer | True |  |
| drone_serial_number | string |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| reason | string |  |  |
| related_mission | number |  |  |
| search | string | False | A search term. |
| written_off_at_after | string |  |  |
| written_off_at_before | string |  |  |


### Responses

#### 200



[PaginatedWriteOffAuditList](#paginatedwriteoffauditlist)







## GET /api/drones/{id}/

Retrieve drone details

Retrieves detailed information about a specific drone by its ID, including technical specification and history.

Required permission: `PERMISSION_DRONES_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of specific drone. |


### Responses

#### 200


Detailed information about the drone.


[Drone](#drone)






Examples





```json
{
  "id": 21,
  "spec": {
    "id": 21,
    "frame_type": "7-inch carbon frame",
    "motor_model": "XING2 2806.5 1300KV",
    "battery_type": "Li-Ion 6S",
    "battery_capacity_mah": 4000,
    "battery_model": "",
    "camera_model": "RunCam Phoenix 2",
    "camera_specs": {},
    "vtx_model": "Rush Tank Solo",
    "flight_controller": "Matek H743",
    "firmware_version": "INAV 7.1",
    "is_firmware_outdated": false,
    "communication_protocol": "",
    "control_channel": "",
    "telemetry_channel": "",
    "max_speed_kmh": "118.50",
    "typical_range_km": "14.60",
    "max_range_km": "18.20",
    "typical_flight_time_min": "21.00",
    "max_flight_time_min": "24.00",
    "frequency_mhz": 5800,
    "payload_capacity_g": 250,
    "additional_modules": [],
    "technical_documentation_url": "",
    "firmware_file_url": "",
    "updated_at": "2026-07-02T02:21:31.177903Z",
    "change_history": []
  },
  "writeoff_record": null,
  "status_history": [],
  "status_label": "Active",
  "status_indicator": "success",
  "status_category": "available",
  "serial_number": "FPV-AER-24001",
  "inventory_number": "INV-AER-001",
  "name": "Falcon Eye 1",
  "classification": "RECONNAISSANCE",
  "status": "ACTIVE",
  "acquired_at": "2025-01-12",
  "notes": "Recon platform configured for stable daytime observation sorties.",
  "created_at": "2026-07-02T02:21:31.174390Z",
  "updated_at": "2026-07-02T02:21:31.174396Z",
  "drone_model": 15,
  "military_unit": 7
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## PATCH /api/drones/{id}/

Partially update a drone

Updates specific fields of an existing drone record.

Validation: 
- New classification of a drone must be supported by its model. 
- If a drone is being decommissioned, sold, transferred, or written off the reason must be provided.

Required permission: `PERMISSION_DRONES_UPDATE`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |


### Request Body

[PatchedDroneUpdate](#patcheddroneupdate)






Examples





```json
{
  "name": "Falcon Eye 1"
}
```

[PatchedDroneUpdate](#patcheddroneupdate)





[PatchedDroneUpdate](#patcheddroneupdate)







### Responses

#### 200


Drone updated successfully.


[Drone](#drone)






Examples





```json
{
  "id": 21,
  "spec": {
    "id": 21,
    "frame_type": "7-inch carbon frame",
    "motor_model": "XING2 2806.5 1300KV",
    "battery_type": "Li-Ion 6S",
    "battery_capacity_mah": 4000,
    "battery_model": "",
    "camera_model": "RunCam Phoenix 2",
    "camera_specs": {},
    "vtx_model": "Rush Tank Solo",
    "flight_controller": "Matek H743",
    "firmware_version": "INAV 7.1",
    "is_firmware_outdated": false,
    "communication_protocol": "",
    "control_channel": "",
    "telemetry_channel": "",
    "max_speed_kmh": "118.50",
    "typical_range_km": "14.60",
    "max_range_km": "18.20",
    "typical_flight_time_min": "21.00",
    "max_flight_time_min": "24.00",
    "frequency_mhz": 5800,
    "payload_capacity_g": 250,
    "additional_modules": [],
    "technical_documentation_url": "",
    "firmware_file_url": "",
    "updated_at": "2026-07-02T02:21:31.177903Z",
    "change_history": []
  },
  "writeoff_record": null,
  "status_history": [],
  "status_label": "Active",
  "status_indicator": "success",
  "status_category": "available",
  "serial_number": "FPV-AER-24001",
  "inventory_number": "INV-AER-001",
  "name": "Falcon Eye 1",
  "classification": "RECONNAISSANCE",
  "status": "ACTIVE",
  "acquired_at": "2025-01-12",
  "notes": "Recon platform configured for stable daytime observation sorties.",
  "created_at": "2026-07-02T02:21:31.174390Z",
  "updated_at": "2026-07-02T02:21:31.174396Z",
  "drone_model": 15,
  "military_unit": 7
}
```



#### 400


Bad Request


object






Examples





```json
{
  "writeoff_reason": "This field is required when drone is decommissioned, sold, transferred, or written off."
}
```




```json
{
  "classification": "Classification \"RECONNAISSANCE\" is not supported by drone model \"Atlas Relay 8\". Allowed: Transport, Surveillance"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/drones/{id}/history/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200



[PaginatedDroneStatusHistoryList](#paginateddronestatushistorylist)







## GET /api/drones/{id}/spec-changes/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200



[PaginatedDroneSpecChangeLogList](#paginateddronespecchangeloglist)







## GET /api/drones/export/

Export drones data to CSV

Generates and downloads a CSV file with the filtered list of drones. Supports full filtering and sorting identical to the standard list endpoint. 

The export is limited to a maximum of 10000 records.

Required permission: `PERMISSION_DRONES_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| classification | string |  |  |
| drone_model | integer |  |  |
| drone_model__name | string |  |  |
| inventory_number | string |  |  |
| inventory_number__icontains | string |  |  |
| is_firmware_outdated | boolean |  |  |
| military_unit | string |  |  |
| military_unit__name__icontains | string |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| serial_number | string |  |  |
| serial_number__icontains | string |  |  |
| spec__max_flight_time_min | number |  |  |
| spec__max_flight_time_min__gte | number |  |  |
| spec__max_flight_time_min__lte | number |  |  |
| spec__max_range_km | number |  |  |
| spec__max_range_km__gte | number |  |  |
| spec__max_range_km__lte | number |  |  |
| spec__max_speed_kmh | number |  |  |
| spec__max_speed_kmh__gte | number |  |  |
| spec__max_speed_kmh__lte | number |  |  |
| spec__payload_capacity_g | integer |  |  |
| spec__payload_capacity_g__gte | integer |  |  |
| spec__payload_capacity_g__lte | integer |  |  |
| spec__typical_flight_time_min | number |  |  |
| spec__typical_flight_time_min__gte | number |  |  |
| spec__typical_flight_time_min__lte | number |  |  |
| spec__typical_range_km | number |  |  |
| spec__typical_range_km__gte | number |  |  |
| spec__typical_range_km__lte | number |  |  |
| status | string |  |  |


### Responses

#### 200


A CSV file containing drone data generated successfully.




#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/drones/import/

Import drones data via CSV

Uploads a CSV file to batch-import drone data. Processes the file record row by row, validates data and return error logs if any. Rows with existing `Serial Number`s will be skipped and reported in the API error summary.

Validation: 
- In uploaded .csv file following headers must be present: Serial Number, Inventory Number, Name, Model, Military Unit, Acquired At. 
- `Military Unit` must exactly match the name of an existing unit in the database.

Required permission: `PERMISSION_DRONES_CREATE`.




### Request Body

[DroneImport](#droneimport)





[DroneImport](#droneimport)





[DroneImport](#droneimport)







### Responses

#### 200


Import processing completed.




#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/drones/models/

List drone models

Retrieves a list of all drone models.

Required permission: `PERMISSION_DRONES_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200


Successfully retrieved the list of drone models.


[PaginatedDroneModelList](#paginateddronemodellist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 18,
      "name": "Atlas Relay 8",
      "manufacturer": "Quantum Systems",
      "description": "Long-endurance signal relay and perimeter monitoring platform.",
      "supported_classifications": [
        "TRANSPORT",
        "SURVEILLANCE"
      ],
      "is_active": true,
      "created_at": "2026-07-02T02:21:31.163658Z",
      "updated_at": "2026-07-02T02:21:31.163664Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/drones/models/

Create a new drone model

Creates a new drone model in the system. 

Validation: 
- Drone model must have at least one valid supported classification.

Required permission: `PERMISSION_DRONES_CREATE`.




### Request Body

[DroneModel](#dronemodel)






Examples





```json
{
  "name": "Atlas Relay 8",
  "manufacturer": "Quantum Systems",
  "description": "Long-endurance signal relay and perimeter monitoring platform.",
  "supported_classifications": [
    "TRANSPORT",
    "SURVEILLANCE"
  ]
}
```

[DroneModel](#dronemodel)





[DroneModel](#dronemodel)







### Responses

#### 200


Drone model created successfully.


[DroneModel](#dronemodel)






Examples





```json
{
  "id": 18,
  "name": "Atlas Relay 8",
  "manufacturer": "Quantum Systems",
  "description": "Long-endurance signal relay and perimeter monitoring platform.",
  "supported_classifications": [
    "TRANSPORT",
    "SURVEILLANCE"
  ],
  "is_active": true,
  "created_at": "2026-07-02T02:21:31.163658Z",
  "updated_at": "2026-07-02T02:21:31.163664Z"
}
```



#### 400


Bad Request


object






Examples





```json
{
  "supported_classifications": "A drone model must support at least one classification."
}
```




```json
{
  "supported_classifications": "Value ['Example classification'] are not valid classifications. Valid classifications: RECONNAISSANCE, COMBAT, TRANSPORT, SURVEILLANCE"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/drones/write-offs/



List existing write-offs or create a new immutable write-off record.




### Responses

#### 200



array







## POST /api/drones/write-offs/



List existing write-offs or create a new immutable write-off record.




### Request Body

[WriteOffRecordCreate](#writeoffrecordcreate)





[WriteOffRecordCreate](#writeoffrecordcreate)





[WriteOffRecordCreate](#writeoffrecordcreate)







### Responses

#### 201



[WriteOffRecordCreate](#writeoffrecordcreate)







## GET /api/drones/write-offs/history/



Expose read-only write-off audit records.

The endpoint can return all write-off records or records scoped to a selected
drone when the URL contains a drone primary key.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| authorized_by | number |  |  |
| document_number | string |  |  |
| drone | number |  |  |
| drone_inventory_number | string |  |  |
| drone_serial_number | string |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| reason | string |  |  |
| related_mission | number |  |  |
| search | string | False | A search term. |
| written_off_at_after | string |  |  |
| written_off_at_before | string |  |  |


### Responses

#### 200



[PaginatedWriteOffAuditList](#paginatedwriteoffauditlist)







## GET /api/media/audit-logs/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| action | string |  |  |
| artifact | integer |  |  |
| end_date | string |  |  |
| mission | integer |  |  |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| start_date | string |  |  |
| user | integer |  |  |


### Responses

#### 200



[PaginatedMediaAuditLogList](#paginatedmediaauditloglist)







## GET /api/media/audit-logs/{id}/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | A unique integer value identifying this media audit log. |


### Responses

#### 200



[MediaAuditLog](#mediaauditlog)







## GET /api/media/videos/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200



[PaginatedVideoMetadataList](#paginatedvideometadatalist)







## POST /api/media/videos/







### Request Body

[VideoUpload](#videoupload)





[VideoUpload](#videoupload)





[VideoUpload](#videoupload)







### Responses

#### 201



[VideoUpload](#videoupload)







## GET /api/media/videos/{id}/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | A unique integer value identifying this video metadata. |


### Responses

#### 200



[VideoMetadata](#videometadata)







## PUT /api/media/videos/{id}/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | A unique integer value identifying this video metadata. |


### Request Body

[VideoMetadata](#videometadata)





[VideoMetadata](#videometadata)





[VideoMetadata](#videometadata)







### Responses

#### 200



[VideoMetadata](#videometadata)







## PATCH /api/media/videos/{id}/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | A unique integer value identifying this video metadata. |


### Request Body

[PatchedVideoMetadata](#patchedvideometadata)





[PatchedVideoMetadata](#patchedvideometadata)





[PatchedVideoMetadata](#patchedvideometadata)







### Responses

#### 200



[VideoMetadata](#videometadata)







## DELETE /api/media/videos/{id}/





### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | A unique integer value identifying this video metadata. |


### Responses

#### 204


No response body




## GET /api/missions/

List missions

Retrieves a paginated and filtered by status list of missions, assigned to the currently authenticated user.

Required permission: `PERMISSION_MISSIONS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| assigned_to | string |  | Filter to only show missions where the currently authenticated user is assigned to. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| status | string |  | Filter missions by their current state. |


### Responses

#### 200


Successfully retrieved the filtered list of missions.


[PaginatedMissionList](#paginatedmissionlist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 31,
      "title": "Fallback Route Mapping",
      "commander": {
        "id": 27,
        "username": "commander.south",
        "email": "commander.south@example.com"
      },
      "status": "planned",
      "result": null,
      "location_description": "Secondary fallback route south-west of artillery support line.",
      "latitude": "48.619700",
      "longitude": "22.287900",
      "started_at": "2026-07-09T01:17:37.650595Z",
      "ended_at": "2026-07-09T01:49:37.650595Z",
      "notes": "Objective: capture updated terrain references and route obstacles.",
      "incident_notes": "",
      "created_by": {
        "id": 24,
        "username": "oleksander.koval",
        "email": "oleksander.koval@example.com"
      },
      "created_at": "2026-07-02T02:21:31.151234Z",
      "updated_at": "2026-07-03T01:17:37.651465Z",
      "drones": []
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/missions/

Create a new mission

Creates a new mission. The logged-in user is automatically assigned as the creator (`created_by`).

Validation: 
- Title of the mission must be at least 3 character long. 
- User assigned as a commander must have a Commander role. 
- Either location or latitude and longitude must be provided. 
- Assigned drones and operators cannot already be assigned to another mission.

Required permission: `PERMISSION_MISSIONS_CREATE`.




### Request Body

[Mission](#mission)






Examples





```json
{
  "title": "Fallback Route Mapping",
  "status": "planned",
  "location_description": "Secondary fallback route south-west of artillery support line.",
  "latitude": "48.619700",
  "longitude": "22.287900",
  "started_at": "2026-07-09T01:17:37.650595Z",
  "ended_at": "2026-07-09T01:49:37.650595Z",
  "notes": "Objective: capture updated terrain references."
}
```

[Mission](#mission)





[Mission](#mission)







### Responses

#### 200


Mission successfully created.


[Mission](#mission)






Examples





```json
{
  "id": 33,
  "title": "Fallback Route Mapping",
  "commander": null,
  "status": "planned",
  "result": null,
  "location_description": "Secondary fallback route south-west of artillery support line.",
  "latitude": "48.619700",
  "longitude": "22.287900",
  "started_at": "2026-07-09T01:17:37.650595Z",
  "ended_at": "2026-07-09T01:49:37.650595Z",
  "notes": "Objective: capture updated terrain references.",
  "incident_notes": "",
  "created_by": {
    "id": 24,
    "username": "oleksander.koval",
    "email": "oleksander.koval@example.com"
  },
  "created_at": "2026-07-03T01:24:28.367298Z",
  "updated_at": "2026-07-03T01:24:28.367301Z",
  "drones": []
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/missions/{mission_pk}/artifacts/

List all artifacts for a specific mission

Retrieves a paginated list of artifacts associated with a given mission.

Required permission: `PERMISSION_MEDIA_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| mission_pk | integer | True | ID of the mission. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200


Successfully retrieved the list of mission artifacts.


[PaginatedMissionArtifactList](#paginatedmissionartifactlist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 1,
      "mission": 11,
      "uploaded_by": {
        "id": 24,
        "username": "oleksandr.koval",
        "email": "oleksandr.koval@example.com"
      },
      "title": "Example Title",
      "description": null,
      "file": "http://localhost:8000/media/artifacts/mission_11/d4ab2e.png",
      "file_type": "image",
      "original_filename": "test_drone_photo.png",
      "file_size": 982936,
      "storage_backend": "local",
      "captured_at": "2026-06-02T02:28:43.353809Z",
      "uploaded_at": "2026-07-02T02:28:43.353809Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## POST /api/missions/{mission_pk}/artifacts/

Upload a new artifact to a mission

Uploads a media file or document as an artifact for a specific mission. 

Validation: 
- File must have one of the following formats:
	- image: .jpg, .jpeg, .png
	- data: .csv, .json
- File size cannot be empty or exceed 50MB.

Required permission: `PERMISSION_MEDIA_UPLOAD`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| mission_pk | integer | True | ID of the mission. |


### Request Body

[MissionArtifactUpload](#missionartifactupload)





[MissionArtifactUpload](#missionartifactupload)







### Responses

#### 201


Artifact successfully uploaded.


[MissionArtifact](#missionartifact)






Examples





```json
{
  "id": 1,
  "mission": 11,
  "uploaded_by": {
    "id": 24,
    "username": "oleksandr.koval",
    "email": "oleksandr.koval@example.com"
  },
  "title": "Example Title",
  "description": null,
  "file": "http://localhost:8000/media/artifacts/mission_11/d4ab2e.png",
  "file_type": "image",
  "original_filename": "test_drone_photo.png",
  "file_size": 982936,
  "storage_backend": "local",
  "captured_at": "2026-06-02T02:28:43.353809Z",
  "uploaded_at": "2026-07-02T02:28:43.353809Z"
}
```



#### 400


Bad Request


object






Examples





```json
{
  "title": "Title is required."
}
```




```json
{
  "file": "File is empty or its size cannot be determined."
}
```




```json
{
  "file": "Unsupported file type '.md'. Allowed: .csv, .jpeg, .jpg, .json, .png."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/missions/{mission_pk}/artifacts/{artifact_pk}/

Retrieve specific artifact details

Retrieves detailed information for a single mission artifact by its ID.

Required permission: `PERMISSION_MEDIA_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| artifact_pk | integer | True | ID of the artifact. |
| mission_pk | integer | True | ID of the mission. |


### Responses

#### 200


Artifact detailed profile.


[MissionArtifact](#missionartifact)






Examples





```json
{
  "id": 1,
  "mission": 11,
  "uploaded_by": {
    "id": 24,
    "username": "oleksandr.koval",
    "email": "oleksandr.koval@example.com"
  },
  "title": "Example Title",
  "description": null,
  "file": "http://localhost:8000/media/artifacts/mission_11/d4ab2e.png",
  "file_type": "image",
  "original_filename": "test_drone_photo.png",
  "file_size": 982936,
  "storage_backend": "local",
  "captured_at": "2026-06-02T02:28:43.353809Z",
  "uploaded_at": "2026-07-02T02:28:43.353809Z"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## DELETE /api/missions/{mission_pk}/artifacts/{artifact_pk}/

Delete a mission artifact

Deletes the specified artifact from the mission and creates an audit log entry.

Required permission: `PERMISSION_MEDIA_DELETE`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| artifact_pk | integer | True | ID of the artifact. |
| mission_pk | integer | True | ID of the mission. |


### Responses

#### 204


Artifact successfully deleted. No content returned.




#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/missions/{mission_pk}/artifacts/{artifact_pk}/download/

Download a protected artifact file

Streams or internally redirects to the stored artifact file after object-level media access checks pass.

Required permission: `PERMISSION_MEDIA_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| artifact_pk | integer | True | ID of the artifact to download. |
| mission_pk | integer | True |  |


### Responses

#### 200


Artifact file returned successfully.


string







#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/missions/{mission_pk}/assignments/

List drone assignments for a mission

Retrieves a list of all drones and their designated operators assigned to a specific mission.

Required permission: `PERMISSION_MISSIONS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| mission_pk | integer | True | ID of the mission. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200


Successfully retrieved the list of mission drone and operator assignments.


[PaginatedMissionDroneList](#paginatedmissiondronelist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 1,
      "mission": 34,
      "drone": 21,
      "drone_details": {
        "id": 21,
        "name": "Falcon Eye 1",
        "serial_number": "FPV-AER-24001",
        "drone_model": 15,
        "status": "ACTIVE"
      },
      "operator": 28,
      "operator_details": {
        "id": 28,
        "username": "operator.alpha",
        "email": "operator.alpha@example.com"
      },
      "condition_after": null,
      "condition_description": null,
      "flight_started_at": null,
      "flight_ended_at": null,
      "created_at": "2026-07-06T02:19:18.140785Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## POST /api/missions/{mission_pk}/assignments/

Assign a drone and operator to a mission

Deploys a specific drone and maps an operator to the given mission. Validation: 
- User selected as a operator must have an Operator role. 
- Assignments can only be added to planned missions. 
- Mission must have a start time before assigning drones or operators. 
- All assigned drones must be active. 
- Operators and drones cannot be assigned to overlapping missions.

Required permission: `PERMISSION_MISSIONS_ASSIGN`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| mission_pk | integer | True | ID of the target mission. |


### Request Body

[MissionDrone](#missiondrone)






Examples





```json
{
  "id": 1,
  "mission": 34,
  "drone": 21,
  "drone_details": {
    "id": 21,
    "name": "Falcon Eye 1",
    "serial_number": "FPV-AER-24001",
    "drone_model": 15,
    "status": "ACTIVE"
  },
  "operator": 28,
  "operator_details": {
    "id": 28,
    "username": "operator.alpha",
    "email": "operator.alpha@example.com"
  },
  "condition_after": null,
  "condition_description": null,
  "flight_started_at": null,
  "flight_ended_at": null,
  "created_at": "2026-07-06T02:19:18.140785Z"
}
```

[MissionDrone](#missiondrone)





[MissionDrone](#missiondrone)







### Responses

#### 201


Drone and operator successfully assigned to the mission.


[MissionDrone](#missiondrone)






Examples





```json
{
  "id": 1,
  "mission": 34,
  "drone": 21,
  "drone_details": {
    "id": 21,
    "name": "Falcon Eye 1",
    "serial_number": "FPV-AER-24001",
    "drone_model": 15,
    "status": "ACTIVE"
  },
  "operator": 28,
  "operator_details": {
    "id": 28,
    "username": "operator.alpha",
    "email": "operator.alpha@example.com"
  },
  "condition_after": null,
  "condition_description": null,
  "flight_started_at": null,
  "flight_ended_at": null,
  "created_at": "2026-07-06T02:19:18.140785Z"
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## DELETE /api/missions/{mission_pk}/assignments/{id}/

Remove a drone assignment from a mission

Deletes a specific drone assignment and creates an audit log entry. 

Validation: 
- Cannot delete assignment unless mission is planned.

Required permission: `PERMISSION_MISSIONS_ASSIGN`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| mission_pk | integer | True | ID of the parent mission. |
| pk | integer | True | ID of the specific drone assignment to be removed. |


### Responses

#### 204


Assignment successfully deleted. No content is returned.




#### 400


Cannot delete assignment unless mission is planned.




#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/missions/{id}/

Retrieve mission details

Retrieves detailed information about a single mission by its ID.

Required permission: `PERMISSION_MISSIONS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of the mission. |


### Responses

#### 200


Detailed mission profile.


[Mission](#mission)






Examples





```json
{
  "id": 31,
  "title": "Fallback Route Mapping",
  "commander": {
    "id": 27,
    "username": "commander.south",
    "email": "commander.south@example.com"
  },
  "status": "planned",
  "result": null,
  "location_description": "Secondary fallback route south-west of artillery support line.",
  "latitude": "48.619700",
  "longitude": "22.287900",
  "started_at": "2026-07-09T01:17:37.650595Z",
  "ended_at": "2026-07-09T01:49:37.650595Z",
  "notes": "Objective: capture updated terrain references and route obstacles.",
  "incident_notes": "",
  "created_by": {
    "id": 24,
    "username": "oleksander.koval",
    "email": "oleksander.koval@example.com"
  },
  "created_at": "2026-07-02T02:21:31.151234Z",
  "updated_at": "2026-07-03T01:17:37.651465Z",
  "drones": []
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## PATCH /api/missions/{id}/assignments/{assignment_id}/condition/

Update drone post-mission condition

Updates the condition of a specific drone assigned to a mission and creates an audit log entry. 

Validation: 
- Drone condition can only be recorded for missions with status `completed` or `aborted`. 
- Condition `lost` cannot be overwritten.

Required permission: `PERMISSION_MISSIONS_RECORD_CONDITION, IsAssignedOperatorOrAdmin`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| assignment_id | integer | True | ID of the specific drone-to-mission assignment. |
| id | integer | True |  |
| pk | integer | True | ID of the parent mission. |


### Request Body

[PatchedMissionDroneCondition](#patchedmissiondronecondition)






Examples





```json
{
  "condition_after": "ok"
}
```

[PatchedMissionDroneCondition](#patchedmissiondronecondition)





[PatchedMissionDroneCondition](#patchedmissiondronecondition)







### Responses

#### 200


Drone condition successfully updated.


[MissionDroneCondition](#missiondronecondition)






Examples





```json
{
  "id": 1,
  "condition_after": "ok",
  "condition_description": null
}
```



#### 400


Bad Request


object






Examples





```json
{
  "mission": "Drone condition can only be recorded for missions with status 'completed' or 'aborted'."
}
```




```json
{
  "condition_after": "Cannot reverse a 'lost' condition: a writeoff record has been created and requires a manual reversal process."
}
```




```json
{
  "condition_after": "Drone is already written off; cannot record 'lost' condition again."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## PATCH /api/missions/{id}/outcome/

Record mission outcome

Partially updates the mission record to record status, result and incident notes for the mission. Creates an audit log entry. 

Validation: 
- Status can only be recorded for completed or aborted mission. 
- Already recorded outcome cannot be overwritten. 
- If result of a mission is a failure, incident notes must be provided.

Required permission: `PERMISSION_MISSIONS_RECORD_OUTCOME, IsAssignedOperatorOrAdmin`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of the mission. |


### Request Body

[PatchedMissionOutcome](#patchedmissionoutcome)






Examples





```json
{
  "result": "success"
}
```

[PatchedMissionOutcome](#patchedmissionoutcome)





[PatchedMissionOutcome](#patchedmissionoutcome)







### Responses

#### 200


Mission outcome recorded successfully.


[MissionOutcome](#missionoutcome)






Examples





```json
{
  "id": 35,
  "status": "completed",
  "result": "success",
  "notes": "The mission was completed successfully.",
  "incident_notes": ""
}
```



#### 400


Bad Request.


object






Examples





```json
{
  "status": "Outcome can only be recorded for missions with status 'completed' or 'aborted'."
}
```




```json
{
  "result": "Outcome has already been recorded for this mission and cannot be overwritten."
}
```




```json
{
  "incident_notes": "Incident notes are required when result is 'failure'."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/missions/{id}/status/

Retrieve mission status

Retrieves the current status of a mission.

Required permission: `PERMISSION_MISSIONS_UPDATE_STATUS, IsAssignedToMissionOrAdmin`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of the mission. |


### Responses

#### 200


Current mission status successfully retrieved.


[MissionStatusUpdate](#missionstatusupdate)






Examples





```json
{
  "status": "planned"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## PUT /api/missions/{id}/status/

Update mission status

Updates the mission status and creates an audit log entry. 

Validation: 
- Status validation restrictions: 
	- status `PLANNED` can be updated to `ACTIVE` or `ABORTED`; 
	- status `ACTIVE` can be updated to `COMPLETED` or `ABORTED`; 
	- statuses `COMPLETED` or `ABORTED` cannot be updated. 
- Mission cannot be updated to status `ACTIVE` if it has assigned inactive drones.

Required permission: `PERMISSION_MISSIONS_UPDATE_STATUS, IsAssignedToMissionOrAdmin`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of the mission. |


### Request Body

[MissionStatusUpdate](#missionstatusupdate)






Examples





```json
{
  "status": "completed"
}
```

[MissionStatusUpdate](#missionstatusupdate)





[MissionStatusUpdate](#missionstatusupdate)







### Responses

#### 200


Mission status updated successfully.


[MissionStatusUpdate](#missionstatusupdate)






Examples





```json
{
  "status": "completed"
}
```



#### 400


Bad Request


object






Examples





```json
{
  "status": "Cannot change status from 'completed' to 'planned'."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## PATCH /api/missions/{id}/status/

Update mission status

Updates the mission status and creates an audit log entry. 

Validation: 
- Status validation restrictions: 
	- status `PLANNED` can be updated to `ACTIVE` or `ABORTED`; 
	- status `ACTIVE` can be updated to `COMPLETED` or `ABORTED`; 
	- statuses `COMPLETED` or `ABORTED` cannot be updated. 
- Mission cannot be updated to status `ACTIVE` if it has assigned inactive drones.

Required permission: `PERMISSION_MISSIONS_UPDATE_STATUS, IsAssignedToMissionOrAdmin`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of the mission. |


### Request Body

[PatchedMissionStatusUpdate](#patchedmissionstatusupdate)






Examples





```json
{
  "status": "completed"
}
```

[PatchedMissionStatusUpdate](#patchedmissionstatusupdate)





[PatchedMissionStatusUpdate](#patchedmissionstatusupdate)







### Responses

#### 200


Mission status updated successfully.


[MissionStatusUpdate](#missionstatusupdate)






Examples





```json
{
  "status": "completed"
}
```



#### 400


Bad Request


object






Examples





```json
{
  "status": "Cannot change status from 'completed' to 'planned'."
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/repairs/defects/

List defect reports

Retrieves a paginated and filtered list of all recorded drone defect reports.

Required permission: `PERMISSION_REPAIRS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| defect_type | string |  |  |
| drone | integer |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| reporter | integer |  |  |
| severity | string |  |  |


### Responses

#### 200


Successfully retrieved the list of defect reports.


[PaginatedDefectReportListList](#paginateddefectreportlistlist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 4,
      "drone": 21,
      "defect_type": "CAMERA",
      "severity": "MEDIUM",
      "detected_at": "2026-05-19T16:05:00Z",
      "reporter": 28,
      "created_at": "2026-07-02T02:21:31.254932Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/repairs/defects/

Create a new defect report

Creates a new defect report. 

Validation: 
- Description must be at least 10 character long.

Required permission: `PERMISSION_REPAIRS_CREATE`.




### Request Body

[DefectReport](#defectreport)






Examples





```json
{
  "drone": 21,
  "defect_type": "CAMERA",
  "severity": "MEDIUM",
  "description": "Camera feed intermittently flickers during high-speed turns.",
  "detected_at": "2026-07-02"
}
```

[DefectReport](#defectreport)





[DefectReport](#defectreport)







### Responses

#### 201


Defect report successfully created.


[DefectReport](#defectreport)






Examples





```json
{
  "id": 5,
  "drone": 21,
  "defect_type": "CAMERA",
  "severity": "MEDIUM",
  "description": "Camera feed intermittently flickers during high-speed turns.",
  "detected_at": "2026-07-02T00:00:00Z",
  "reporter": 24,
  "created_at": "2026-07-03T05:03:12.266745Z",
  "updated_at": "2026-07-03T05:03:12.266754Z"
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/repairs/defects/{id}/

Retrieve specific defect report details

Retrieves detailed information about specific defect report by its ID.

Required permission: `PERMISSION_REPAIRS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of specific defect report. |


### Responses

#### 200


Detailed information about the drone defect report.


[DefectReport](#defectreport)






Examples





```json
{
  "id": 4,
  "drone": 21,
  "defect_type": "CAMERA",
  "severity": "MEDIUM",
  "description": "Camera feed intermittently flickers during high-speed turns.",
  "detected_at": "2026-05-19T16:05:00Z",
  "reporter": 28,
  "created_at": "2026-07-02T02:21:31.254932Z",
  "updated_at": "2026-07-03T01:17:37.754142Z"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/repairs/defects/{id}/history/



List the audit history of state changes for a specific defect report.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |


### Responses

#### 200



[PaginatedRepairEventList](#paginatedrepaireventlist)







## POST /api/repairs/defects/{id}/update-status/

Update defect report status

Transitions a defect report to a new status and records a repair event.

Required permission: `PERMISSION_REPAIRS_CREATE`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |
| pk | integer | True | ID of the defect report to update. |


### Request Body

[DefectStatusUpdate](#defectstatusupdate)





[DefectStatusUpdate](#defectstatusupdate)





[DefectStatusUpdate](#defectstatusupdate)







### Responses

#### 200


Defect status updated successfully.


[RepairEvent](#repairevent)







#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/repairs/drones/{drone_id}/history/



Fetch, validate, and paginate the unified drone history timeline.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| drone_id | integer | True |  |


### Responses

#### 200



[RepairHistoryTimeline](#repairhistorytimeline)







## GET /api/repairs/drones/{drone_id}/history/export/

Export drone repair history to CSV

Exports the aggregated repair timeline for a specific drone as a CSV file.

Required permission: `PERMISSION_REPAIRS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| drone_id | integer | True | ID of the drone whose repair history is exported. |


### Responses

#### 200


CSV file generated successfully.


string







#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/repairs/orders/



List existing repair orders or create a new one.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| assigned_to | integer |  |  |
| created_at__gte | string |  |  |
| created_at__lte | string |  |  |
| defect_report | integer |  |  |
| drone | integer |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| status | string |  |  |


### Responses

#### 200



[PaginatedRepairOrderListList](#paginatedrepairorderlistlist)







## POST /api/repairs/orders/



List existing repair orders or create a new one.




### Request Body

[RepairOrderCreate](#repairordercreate)





[RepairOrderCreate](#repairordercreate)





[RepairOrderCreate](#repairordercreate)







### Responses

#### 201



[RepairOrderCreate](#repairordercreate)







## GET /api/repairs/orders/{id}/



Retrieve or transition a specific repair order.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |


### Responses

#### 200



[RepairOrder](#repairorder)







## PATCH /api/repairs/orders/{id}/



Delegate state transitions to the dedicated service method.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |


### Request Body

[PatchedRepairOrderStatusUpdate](#patchedrepairorderstatusupdate)





[PatchedRepairOrderStatusUpdate](#patchedrepairorderstatusupdate)





[PatchedRepairOrderStatusUpdate](#patchedrepairorderstatusupdate)







### Responses

#### 200



[RepairOrderStatusUpdate](#repairorderstatusupdate)







## POST /api/repairs/orders/{id}/replacements/



Attach a new component replacement to an existing repair order.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True |  |


### Request Body

[RepairOrderReplacement](#repairorderreplacement)





[RepairOrderReplacement](#repairorderreplacement)





[RepairOrderReplacement](#repairorderreplacement)







### Responses

#### 201



[RepairOrderReplacement](#repairorderreplacement)







## GET /api/repairs/replacements/

List component replacements

Retrieves a paginated and filtered list of all recorded component replacements performed on drones.

Required permission: `PERMISSION_REPAIRS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| component_type | string |  |  |
| drone | integer |  |  |
| end_date | string |  |  |
| ordering | string | False | Which field to use when ordering the results. |
| page | integer | False | A page number within the paginated result set. |
| page_size | integer | False | Number of results to return per page. |
| replaced_by | integer |  |  |
| start_date | string |  |  |


### Responses

#### 200


Successfully retrieved the list of component replacements.


[PaginatedComponentReplacementListList](#paginatedcomponentreplacementlistlist)






Examples





```json
{
  "count": 123,
  "next": "http://api.example.org/accounts/?page=4",
  "previous": "http://api.example.org/accounts/?page=2",
  "results": [
    {
      "id": 1,
      "drone": 24,
      "component_type": "MOTOR",
      "component_name": null,
      "new_serial_number": "TM-F60PV-24004-B",
      "replaced_at": "2026-05-09T09:30:00Z",
      "replaced_by": 31,
      "created_at": "2026-07-02T02:21:31.258041Z"
    }
  ]
}
```



#### 403


Forbidden. User does not have permission to perform this action.




## POST /api/repairs/replacements/

Record a component replacement

Creates a new component replacement report. 

Validation: 
- If component type is `OTHER`, component name must be provided.

Required permission: `PERMISSION_REPAIRS_CREATE`.




### Request Body

[ComponentReplacement](#componentreplacement)






Examples





```json
{
  "drone": 25,
  "component_type": "FRAME",
  "component_name": null,
  "old_serial_number": "FRAME-SPEAR1-OLD",
  "new_serial_number": "FRAME-SPEAR1-NEW",
  "reason": "Frame section replaced after structural damage from forced landing.",
  "replaced_at": "2026-07-03"
}
```

[ComponentReplacement](#componentreplacement)





[ComponentReplacement](#componentreplacement)







### Responses

#### 201


Component replacement report successfully created.


[ComponentReplacement](#componentreplacement)






Examples





```json
{
  "id": 5,
  "drone": 25,
  "component_type": "FRAME",
  "component_name": null,
  "old_serial_number": "FRAME-SPEAR1-OLD",
  "new_serial_number": "FRAME-SPEAR1-NEW",
  "reason": "Frame section replaced after structural damage from forced landing.",
  "replaced_at": "2026-07-03T00:00:00Z",
  "replaced_by": 24,
  "created_at": "2026-07-03T05:09:09.903830Z",
  "updated_at": "2026-07-03T05:09:09.903879Z"
}
```



#### 400


Bad Request. Provided payload contains validation errors.




#### 403


Forbidden. User does not have permission to perform this action.




## GET /api/repairs/replacements/{id}/

Retrieve specific component replacement details

Retrieves detailed information about specific component replacement report by its ID.

Required permission: `PERMISSION_REPAIRS_VIEW`.


### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | True | ID of specific component replacement report. |


### Responses

#### 200


Detailed information about the component replacement record.


[ComponentReplacement](#componentreplacement)






Examples





```json
{
  "id": 1,
  "drone": 24,
  "component_type": "MOTOR",
  "component_name": null,
  "old_serial_number": "TM-F60PV-24004-A",
  "new_serial_number": "TM-F60PV-24004-B",
  "reason": "Motor replaced after abnormal vibration was confirmed in inspection.",
  "replaced_at": "2026-05-09T09:30:00Z",
  "replaced_by": 31,
  "created_at": "2026-07-02T02:21:31.258041Z",
  "updated_at": "2026-07-03T01:17:37.756512Z"
}
```



#### 403


Forbidden. User does not have permission to perform this action.




#### 404


Not Found.




## GET /api/repairs/replacements/export/

Export component replacement data to CSV

Generates and downloads a CSV file with the filtered component replacement history.Supports full filtering identical to the standard list endpoint. 

The export is limited to a maximum of 10000 records.

Required permission: `PERMISSION_REPAIRS_VIEW`.




### Responses

#### 200


A CSV file generated successfully.




#### 403


Forbidden. User does not have permission to perform this action.




# Components



## ActionEnum





## ActionTypeEnum





## AuditLog


Serialize audit log entries for read-only API responses.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| actor | integer | User performing the action (can be Null for system actions) |
| actor_username | string |  |
| target_user | integer | User on whom the action was taken |
| target_user_username | string |  |
| action_type |  |  |
| result |  |  |
| description | string |  |
| ip_address | string |  |
| user_agent | string |  |
| created_at | string |  |


## AuditLogResultEnum





## BlankEnum





## ChangePassword


Serialize requests to change the user's password.


| Field | Type | Description |
|-------|------|-------------|
| old_password | string |  |
| new_password | string |  |


## ClassificationEnum





## ComponentReplacement


Serialize standalone hardware replacements.

Validates physical consistency (e.g., specific names for the OTHER category)
and delegates creation to the service layer.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| component_type |  |  |
| component_name | string |  |
| old_serial_number | string |  |
| new_serial_number | string |  |
| reason | string |  |
| replaced_at | string |  |
| replaced_by | integer |  |
| created_at | string |  |
| updated_at | string |  |


## ComponentReplacementList


Read-only summary of a component replacement for list views.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| component_type |  |  |
| component_name | string |  |
| new_serial_number | string |  |
| replaced_at | string |  |
| replaced_by | integer |  |
| created_at | string |  |


## ConditionAfterEnum





## DefectReport


Serialize a defect report for creation and detailed view.

The reporter field is strictly read-only because it must be securely
bound to the authenticated user making the request via the service
layer, rather than accepting it from the payload.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| defect_type |  |  |
| severity |  |  |
| description | string |  |
| detected_at | string |  |
| reporter | integer |  |
| created_at | string |  |
| updated_at | string |  |


## DefectReportList


Read-only summary of a defect report for list views.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| defect_type |  |  |
| severity |  |  |
| detected_at | string |  |
| reporter | integer |  |
| created_at | string |  |


## DefectStatusUpdate


Validate payloads for transitioning a DefectReport's status.


| Field | Type | Description |
|-------|------|-------------|
| status |  |  |
| action_taken | string |  |


## DefectType





## Drone


Serialize drone create/detail data with nested technical specification.

Creation is delegated to the service layer so the drone, DroneSpec, and
initial DroneSpecChangeLog are created consistently in one workflow.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| spec |  |  |
| writeoff_record |  |  |
| status_label | string |  |
| status_indicator | string |  |
| status_category | string |  |
| serial_number | string |  |
| inventory_number | string |  |
| name | string |  |
| classification |  |  |
| status |  |  |
| acquired_at | string |  |
| notes | string |  |
| created_at | string |  |
| updated_at | string |  |
| drone_model | integer | Drone Model |
| military_unit | integer |  |


## DroneBrief


Read-only summary of a drone, embedded in mission/assignment responses.

Output-only: all fields are read-only, so it never creates or updates.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| name | string |  |
| serial_number | string |  |
| drone_model | integer | Drone Model |
| status |  |  |


## DroneImport


Validate uploaded files for drone CSV import.


| Field | Type | Description |
|-------|------|-------------|
| file | string | CSV file with drone inventory data. |


## DroneList


Serialize compact drone fields for list responses.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| serial_number | string |  |
| inventory_number | string |  |
| name | string |  |
| drone_model | integer | Drone Model |
| classification |  |  |
| status |  |  |
| status_label | string |  |
| status_indicator | string |  |
| status_category | string |  |
| military_unit | integer |  |
| created_at | string |  |


## DroneModel


Serialize drone model catalog entries and supported classifications.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| name | string |  |
| manufacturer | string |  |
| description | string |  |
| supported_classifications |  | List of supported classifications |
| is_active | boolean |  |
| created_at | string |  |
| updated_at | string |  |


## DroneSpecChangeLog


Serialize specification audit entries for read-only API responses.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| changed_by | integer |  |
| changed_fields |  |  |
| old_values |  |  |
| new_values |  |  |
| created_at | string |  |


## DroneSpecDetail


Serialize technical specifications included in drone detail responses.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| frame_type | string |  |
| motor_model | string |  |
| battery_type | string |  |
| battery_capacity_mah | integer |  |
| battery_model | string |  |
| camera_model | string |  |
| camera_specs |  |  |
| vtx_model | string |  |
| flight_controller | string |  |
| firmware_version | string |  |
| is_firmware_outdated | boolean | Indicates if the firmware or communication parameters are unsupported. |
| communication_protocol | string |  |
| control_channel | string |  |
| telemetry_channel | string |  |
| max_speed_kmh | string |  |
| typical_range_km | string |  |
| max_range_km | string |  |
| typical_flight_time_min | string |  |
| max_flight_time_min | string |  |
| frequency_mhz | integer |  |
| payload_capacity_g | integer |  |
| additional_modules |  |  |
| technical_documentation_url |  |  |
| firmware_file_url |  |  |
| updated_at | string |  |


## DroneSpecUpdate


Serialize partial updates to a drone technical specification.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| frame_type | string |  |
| motor_model | string |  |
| battery_type | string |  |
| battery_capacity_mah | integer |  |
| battery_model | string |  |
| camera_model | string |  |
| camera_specs |  |  |
| vtx_model | string |  |
| flight_controller | string |  |
| firmware_version | string |  |
| is_firmware_outdated | boolean | Indicates if the firmware or communication parameters are unsupported. |
| communication_protocol | string |  |
| control_channel | string |  |
| telemetry_channel | string |  |
| max_speed_kmh | string |  |
| typical_range_km | string |  |
| max_range_km | string |  |
| typical_flight_time_min | string |  |
| max_flight_time_min | string |  |
| frequency_mhz | integer |  |
| payload_capacity_g | integer |  |
| additional_modules |  |  |
| technical_documentation_url |  |  |
| firmware_file_url |  |  |
| updated_at | string |  |


## DroneStatus





## DroneStatusHistory


Serialize drone lifecycle status history with display metadata.

Adds a readable user label and event type so clients can distinguish status
changes caused by missions, repairs, write-offs, or manual updates.


| Field | Type | Description |
|-------|------|-------------|
| id | string |  |
| from_status | string |  |
| to_status | string |  |
| changed_by | integer |  |
| changed_by_display | string | Return a readable name for the user who changed the status. |
| reason | string |  |
| event_type | string | Return the domain event type that caused this status history entry. |
| related_mission_id | integer |  |
| related_repair_order | integer |  |
| related_writeoff | integer |  |
| created_at | string |  |


## EventTypeEnum





## FileTypeEnum





## MediaAuditLog



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| action |  |  |
| artifact | integer | Null after the referenced artifact is deleted. |
| mission | integer |  |
| user |  |  |
| changes |  |  |
| ip_address | string |  |
| created_at | string |  |


## Mission


Serialize a mission, including its nested drone assignments.

Handles both create and update. Assignments may only be set at creation
time; on update the nested ``drones`` field is forced read-only (see
``__init__``) so they are managed through the dedicated assignment endpoints
instead.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| title | string |  |
| commander |  |  |
| commander_id | integer |  |
| status |  |  |
| result |  |  |
| location_description | string |  |
| latitude | string |  |
| longitude | string |  |
| started_at | string |  |
| ended_at | string |  |
| notes | string |  |
| incident_notes | string |  |
| created_by |  |  |
| created_at | string |  |
| updated_at | string |  |
| drones | array |  |


## MissionArtifact



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| mission | integer |  |
| uploaded_by |  |  |
| title | string |  |
| description | string |  |
| file | string |  |
| file_type |  |  |
| original_filename | string |  |
| file_size | integer | File size in bytes |
| storage_backend | string |  |
| captured_at | string |  |
| uploaded_at | string |  |


## MissionArtifactUpload



| Field | Type | Description |
|-------|------|-------------|
| file | string |  |
| title | string |  |
| description | string |  |
| captured_at | string |  |


## MissionDrone


Serialize a mission-drone assignment with drone and operator details.

Used to list assignments and to create new ones; ``create`` delegates to
the service layer so locking and auditing stay consistent.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| mission | integer |  |
| drone | integer |  |
| drone_details |  |  |
| operator | integer |  |
| operator_details |  |  |
| condition_after |  |  |
| condition_description | string |  |
| flight_started_at | string |  |
| flight_ended_at | string |  |
| created_at | string |  |


## MissionDroneCondition


Record a drone's condition after a mission for a single assignment.

Update-only; ``update`` delegates persistence and drone-status propagation
to the service layer.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| condition_after |  |  |
| condition_description | string |  |


## MissionDroneInput


Nested write serializer for assigning a drone/operator on mission create.

Exposes ``drone_id`` (required) and ``operator_id`` (optional, nullable),
mapped to the ``drone`` and ``operator`` relations of :class:`MissionDrone`.


| Field | Type | Description |
|-------|------|-------------|
| drone_id | integer |  |
| operator_id | integer |  |


## MissionOutcome


Record the result and notes of a completed/aborted mission.

Update-only; ``update`` delegates persistence to the service layer.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| status |  |  |
| result |  |  |
| notes | string |  |
| incident_notes | string |  |


## MissionResult





## MissionStatus





## MissionStatusUpdate


Drive a mission through its lifecycle and propagate drone statuses.

Exposes only ``status``; ``update`` applies the change transactionally and
cascades the assigned drones' statuses.


| Field | Type | Description |
|-------|------|-------------|
| status |  |  |


## NullEnum





## PaginatedAuditLogList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedComponentReplacementListList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedDefectReportListList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedDroneListList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedDroneModelList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedDroneSpecChangeLogList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedDroneStatusHistoryList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedMediaAuditLogList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedMissionArtifactList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedMissionDroneList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedMissionList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedRepairEventList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedRepairOrderListList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedVideoMetadataList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PaginatedWriteOffAuditList



| Field | Type | Description |
|-------|------|-------------|
| count | integer |  |
| next | string |  |
| previous | string |  |
| results | array |  |


## PasswordResetConfirm


Serialize requests to confirm a password reset with a new password.


| Field | Type | Description |
|-------|------|-------------|
| new_password | string |  |


## PasswordResetRequest


Serialize requests to initiate a password reset.


| Field | Type | Description |
|-------|------|-------------|
| email | string |  |


## PatchedDroneUpdate


Serialize partial drone updates and inactive lifecycle transitions.

Inactive transitions require write-off metadata so the service layer can
create an immutable WriteOffRecord and link it to DroneStatusHistory.


| Field | Type | Description |
|-------|------|-------------|
| serial_number | string |  |
| inventory_number | string |  |
| name | string |  |
| drone_model | integer | Drone Model |
| classification |  |  |
| status |  |  |
| military_unit | integer |  |
| acquired_at | string |  |
| notes | string |  |
| spec |  |  |
| writeoff_reason |  |  |
| writeoff_reason_description | string |  |
| status_change_reason | string |  |
| document_number | string |  |
| written_off_at | string |  |
| related_mission_id | integer |  |


## PatchedMissionDroneCondition


Record a drone's condition after a mission for a single assignment.

Update-only; ``update`` delegates persistence and drone-status propagation
to the service layer.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| condition_after |  |  |
| condition_description | string |  |


## PatchedMissionOutcome


Record the result and notes of a completed/aborted mission.

Update-only; ``update`` delegates persistence to the service layer.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| status |  |  |
| result |  |  |
| notes | string |  |
| incident_notes | string |  |


## PatchedMissionStatusUpdate


Drive a mission through its lifecycle and propagate drone statuses.

Exposes only ``status``; ``update`` applies the change transactionally and
cascades the assigned drones' statuses.


| Field | Type | Description |
|-------|------|-------------|
| status |  |  |


## PatchedRepairOrderStatusUpdate


Drive a repair order through its state machine.


| Field | Type | Description |
|-------|------|-------------|
| status |  |  |
| notes | string |  |


## PatchedUserMe


Serialize the authenticated user's data along with their profile information.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| username | string | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| email | string |  |
| first_name | string |  |
| last_name | string |  |
| rank | string |  |
| contact | string |  |
| profile_picture | string |  |
| role | integer |  |
| unit | integer |  |
| is_active | boolean | Designates whether this user should be treated as active. Unselect this instead of deleting accounts. |
| must_change_password | boolean |  |


## PatchedUserRoleUpdate


Serialize user role update requests.


| Field | Type | Description |
|-------|------|-------------|
| role_id | integer |  |


## PatchedUserStatusUpdate


Serialize user status update requests.


| Field | Type | Description |
|-------|------|-------------|
| is_active | boolean |  |
| reason | string |  |


## PatchedVideoMetadata



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| mission | integer | Mission associated with this video |
| drone | integer | Drone used to capture this video |
| uploader | integer | User who uploaded the file |
| uploader_username | string |  |
| file | string |  |
| file_name | string |  |
| file_size | integer | File size in bytes |
| content_type | string |  |
| status |  |  |
| checksum | string | Optional SHA-256 checksum of the file |
| duration_seconds | integer |  |
| recorded_at | string | Video recording timestamp from drone metadata |
| created_at | string |  |
| updated_at | string |  |
| url | string |  |


## RepairEvent


Read-only view of a repair state transition event.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| from_status |  |  |
| to_status |  |  |
| action_taken | string |  |
| technician | integer |  |
| created_at | string |  |


## RepairHistoryTimeline


Shape heterogeneous repair events into a uniform timeline response.


| Field | Type | Description |
|-------|------|-------------|
| event_type |  |  |
| timestamp | string |  |
| summary | string |  |
| details | object |  |


## RepairOrder


Serialize a repair order for detailed views.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| defect_report | integer |  |
| status |  |  |
| description | string |  |
| assigned_to | integer |  |
| started_at | string |  |
| completed_at | string |  |
| notes | string |  |
| created_by | integer |  |
| created_at | string |  |
| updated_at | string |  |


## RepairOrderCreate


Validate payloads for creating a new repair order.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| defect_report | integer |  |
| description | string |  |
| assigned_to | integer |  |


## RepairOrderList


Read-only summary of a repair order for list views.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| defect_report | integer |  |
| status |  |  |
| assigned_to | integer |  |
| created_by | integer |  |
| created_at | string |  |


## RepairOrderReplacement


Serialize hardware replacements explicitly linked to a repair order.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| component_type |  |  |
| component_name | string |  |
| old_serial_number | string |  |
| new_serial_number | string |  |
| reason | string |  |
| replaced_at | string |  |
| replaced_by | integer |  |
| created_at | string |  |
| updated_at | string |  |


## RepairOrderStatusUpdate


Drive a repair order through its state machine.


| Field | Type | Description |
|-------|------|-------------|
| status |  |  |
| notes | string |  |


## SeverityEnum





## StatusFccEnum





## ToStatusEnum





## UserBrief



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| username | string | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| email | string |  |


## UserMe


Serialize the authenticated user's data along with their profile information.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| username | string | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| email | string |  |
| first_name | string |  |
| last_name | string |  |
| rank | string |  |
| contact | string |  |
| profile_picture | string |  |
| role | integer |  |
| unit | integer |  |
| is_active | boolean | Designates whether this user should be treated as active. Unselect this instead of deleting accounts. |
| must_change_password | boolean |  |


## UserRegistration


Provide serialization and validation for user registration requests.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| username | string | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| email | string |  |
| first_name | string |  |
| last_name | string |  |
| role | integer |  |
| unit | integer |  |
| rank | string |  |
| contact | string |  |
| profile_picture | string |  |


## UserRoleUpdateResponse


Serialize user role update responses.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| username | string | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| email | string |  |
| role | object | Return the role details of the user. |


## VideoMetadata



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| mission | integer | Mission associated with this video |
| drone | integer | Drone used to capture this video |
| uploader | integer | User who uploaded the file |
| uploader_username | string |  |
| file | string |  |
| file_name | string |  |
| file_size | integer | File size in bytes |
| content_type | string |  |
| status |  |  |
| checksum | string | Optional SHA-256 checksum of the file |
| duration_seconds | integer |  |
| recorded_at | string | Video recording timestamp from drone metadata |
| created_at | string |  |
| updated_at | string |  |
| url | string |  |


## VideoMetadataStatusEnum





## VideoUpload



| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| mission | integer | Mission associated with this video |
| drone | integer | Drone used to capture this video |
| file | string |  |
| recorded_at | string | Video recording timestamp from drone metadata |
| checksum | string | Optional SHA-256 checksum of the file |


## WriteOffAudit


Serialize write-off records for audit and history endpoints.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone_id | integer |  |
| drone_name | string |  |
| drone_serial_number | string |  |
| drone_inventory_number | string |  |
| reason |  | Canonical reason for writing off the drone. |
| reason_description | string | Free-form details about the write-off. Required when the reason is 'Other'. |
| authorized_by | integer |  |
| authorized_by_username | string |  |
| related_mission | integer |  |
| related_mission_id | integer |  |
| document_number | string |  |
| written_off_at | string |  |
| created_at | string |  |


## WriteOffReason





## WriteOffRecord


Serialize immutable write-off data attached to a drone.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| reason |  | Canonical reason for writing off the drone. |
| reason_label | string |  |
| reason_description | string | Free-form details about the write-off. Required when the reason is 'Other'. |
| authorized_by | integer |  |
| related_mission_id | integer |  |
| document_number | string |  |
| written_off_at | string |  |
| created_at | string |  |


## WriteOffRecordCreate


Validate and create immutable drone write-off records.

A drone can be written off only once, cannot already be inactive, and when a
mission is supplied it must be the latest mission assigned to that drone.


| Field | Type | Description |
|-------|------|-------------|
| id | integer |  |
| drone | integer |  |
| reason |  | Canonical reason for writing off the drone. |
| reason_description | string | Free-form details about the write-off. Required when the reason is 'Other'. |
| related_mission | integer |  |
| document_number | string |  |
| written_off_at | string |  |
| created_at | string |  |
