from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    DISPATCHER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
)

# Users
PERMISSION_USERS_MANAGE_ROLES = "users.manage_roles"
PERMISSION_USERS_CREATE = "users.create"
PERMISSION_USERS_ACTIVATE_DEACTIVATE = "users.activate_deactivate"

# Drones
PERMISSION_DRONES_CREATE = "drones.create"
PERMISSION_DRONES_UPDATE = "drones.update"
PERMISSION_DRONES_DECOMMISSION = "drones.decommission"
PERMISSION_DRONES_VIEW = "drones.view"
PERMISSION_DRONES_IMPORT_EXPORT = "drones.import_export"

# Missions
PERMISSION_MISSIONS_VIEW = "missions.view"
PERMISSION_MISSIONS_CREATE = "missions.create"
PERMISSION_MISSIONS_ASSIGN = "missions.assign"
PERMISSION_MISSIONS_UPDATE_STATUS = "missions.update_status"
PERMISSION_MISSIONS_RECORD_OUTCOME = "missions.record_outcome"
PERMISSION_MISSIONS_RECORD_CONDITION = "missions.record_condition"

# Maintenance
PERMISSION_MAINTENANCE_VIEW = "maintenance.view"
PERMISSION_MAINTENANCE_MANAGE = "maintenance.manage"

# Specifications
PERMISSION_SPECIFICATIONS_VIEW = "specifications.view"
PERMISSION_SPECIFICATIONS_MANAGE = "specifications.manage"

# Write-off
PERMISSION_WRITEOFF_VIEW = "writeoff.view"
PERMISSION_WRITEOFF_CREATE = "writeoff.create"
PERMISSION_WRITEOFF_AUTHORIZE = "writeoff.authorize"

# Media
PERMISSION_MEDIA_UPLOAD = "media.upload"
PERMISSION_MEDIA_VIEW = "media.view"

# Audit logs
PERMISSION_AUDIT_LOGS_VIEW_ALL = "audit_logs.view_all"
PERMISSION_AUDIT_LOGS_VIEW_OWN = "audit_logs.view_own"

# Profile
PERMISSION_PROFILE_VIEW_OWN = "profile.view_own"
PERMISSION_PROFILE_UPDATE_OWN = "profile.update_own"
PERMISSION_PROFILE_RESET_PASSWORD_OWN = "profile.reset_password_own"


def profile_permissions():
    return {
        PERMISSION_PROFILE_VIEW_OWN,
        PERMISSION_PROFILE_UPDATE_OWN,
        PERMISSION_PROFILE_RESET_PASSWORD_OWN,
    }


def own_audit_log_permissions():
    return {PERMISSION_AUDIT_LOGS_VIEW_OWN}


def admin_permissions():
    return profile_permissions() | {
        PERMISSION_USERS_MANAGE_ROLES,
        PERMISSION_USERS_CREATE,
        PERMISSION_USERS_ACTIVATE_DEACTIVATE,
        PERMISSION_DRONES_CREATE,
        PERMISSION_DRONES_UPDATE,
        PERMISSION_DRONES_DECOMMISSION,
        PERMISSION_DRONES_VIEW,
        PERMISSION_DRONES_IMPORT_EXPORT,
        PERMISSION_MISSIONS_VIEW,
        PERMISSION_MISSIONS_CREATE,
        PERMISSION_MISSIONS_ASSIGN,
        PERMISSION_MISSIONS_UPDATE_STATUS,
        PERMISSION_MISSIONS_RECORD_OUTCOME,
        PERMISSION_MISSIONS_RECORD_CONDITION,
        PERMISSION_MEDIA_UPLOAD,
        PERMISSION_MEDIA_VIEW,
        PERMISSION_MAINTENANCE_VIEW,
        PERMISSION_MAINTENANCE_MANAGE,
        PERMISSION_SPECIFICATIONS_VIEW,
        PERMISSION_SPECIFICATIONS_MANAGE,
        PERMISSION_WRITEOFF_VIEW,
        PERMISSION_WRITEOFF_CREATE,
        PERMISSION_WRITEOFF_AUTHORIZE,
        PERMISSION_AUDIT_LOGS_VIEW_ALL,
    }


def commander_permissions():
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MISSIONS_ASSIGN,
            PERMISSION_MISSIONS_UPDATE_STATUS,
            PERMISSION_MEDIA_VIEW,
            PERMISSION_MAINTENANCE_VIEW,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_WRITEOFF_AUTHORIZE,
        }
    )


def dispatcher_permissions():
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MISSIONS_CREATE,
            PERMISSION_MISSIONS_ASSIGN,
            PERMISSION_MEDIA_VIEW,
        }
    )


def operator_permissions():
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MISSIONS_UPDATE_STATUS,
            PERMISSION_MISSIONS_RECORD_OUTCOME,
            PERMISSION_MISSIONS_RECORD_CONDITION,
            PERMISSION_MEDIA_UPLOAD,
            PERMISSION_MEDIA_VIEW,
        }
    )


def technician_permissions():
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_SPECIFICATIONS_MANAGE,
            PERMISSION_MAINTENANCE_VIEW,
            PERMISSION_MAINTENANCE_MANAGE,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_WRITEOFF_CREATE,
        }
    )


def viewer_permissions():
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MAINTENANCE_VIEW,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_MEDIA_VIEW,
        }
    )


ROLE_PERMISSION_MATRIX = {
    ADMIN_CODE: admin_permissions(),
    COMMANDER_CODE: commander_permissions(),
    DISPATCHER_CODE: dispatcher_permissions(),
    OPERATOR_CODE: operator_permissions(),
    TECHNICIAN_CODE: technician_permissions(),
    VIEWER_CODE: viewer_permissions(),
}
