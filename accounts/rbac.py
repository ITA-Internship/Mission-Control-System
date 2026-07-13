"""Centralized RBAC permission codes and role-to-permission mappings."""

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

# Repairs
PERMISSION_REPAIRS_VIEW = "repairs.view"
PERMISSION_REPAIRS_CREATE = "repairs.create"
PERMISSION_REPAIRS_MANAGE = "repairs.manage"
PERMISSION_REPAIRS_EXPORT = "repairs.export"
PERMISSION_REPAIRS_VERIFY = "repairs.verify"

# Media
PERMISSION_MEDIA_UPLOAD = "media.upload"
PERMISSION_MEDIA_VIEW = "media.view"
PERMISSION_MEDIA_DELETE = "media.delete"
PERMISSION_MEDIA_VIEW_LOGS = "media.view_logs"

# Audit logs
PERMISSION_AUDIT_LOGS_VIEW_ALL = "audit_logs.view_all"
PERMISSION_AUDIT_LOGS_VIEW_OWN = "audit_logs.view_own"

# Profile
PERMISSION_PROFILE_VIEW_OWN = "profile.view_own"
PERMISSION_PROFILE_UPDATE_OWN = "profile.update_own"
PERMISSION_PROFILE_RESET_PASSWORD_OWN = "profile.reset_password_own"

# Drone Compare
PERMISSION_SPECIFICATIONS_COMPARE = "specifications.compare"


def profile_permissions():
    """Permissions every authenticated role has for self-service profile access."""
    return {
        PERMISSION_PROFILE_VIEW_OWN,
        PERMISSION_PROFILE_UPDATE_OWN,
        PERMISSION_PROFILE_RESET_PASSWORD_OWN,
    }


def own_audit_log_permissions():
    """Permissions for viewing audit log entries created by the current user."""
    return {PERMISSION_AUDIT_LOGS_VIEW_OWN}


def admin_permissions():
    """Full access permissions for platform administrators."""
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
        PERMISSION_MEDIA_DELETE,
        PERMISSION_MEDIA_VIEW_LOGS,
        PERMISSION_MAINTENANCE_VIEW,
        PERMISSION_MAINTENANCE_MANAGE,
        PERMISSION_SPECIFICATIONS_VIEW,
        PERMISSION_SPECIFICATIONS_MANAGE,
        PERMISSION_WRITEOFF_VIEW,
        PERMISSION_WRITEOFF_CREATE,
        PERMISSION_WRITEOFF_AUTHORIZE,
        PERMISSION_REPAIRS_VIEW,
        PERMISSION_REPAIRS_CREATE,
        PERMISSION_REPAIRS_MANAGE,
        PERMISSION_REPAIRS_EXPORT,
        PERMISSION_REPAIRS_VERIFY,
        PERMISSION_AUDIT_LOGS_VIEW_ALL,
        PERMISSION_AUDIT_LOGS_VIEW_OWN,
        PERMISSION_SPECIFICATIONS_COMPARE,
    }


def commander_permissions():
    """Permissions for command staff overseeing missions and approvals."""
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_CREATE,
            PERMISSION_DRONES_UPDATE,
            PERMISSION_DRONES_DECOMMISSION,
            PERMISSION_DRONES_VIEW,
            PERMISSION_DRONES_IMPORT_EXPORT,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_SPECIFICATIONS_COMPARE,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MISSIONS_CREATE,
            PERMISSION_MISSIONS_ASSIGN,
            PERMISSION_MISSIONS_UPDATE_STATUS,
            PERMISSION_MEDIA_VIEW,
            PERMISSION_MAINTENANCE_VIEW,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_WRITEOFF_AUTHORIZE,
            PERMISSION_REPAIRS_VIEW,
            PERMISSION_REPAIRS_EXPORT,
            PERMISSION_REPAIRS_VERIFY,
        }
    )


def dispatcher_permissions():
    """Permissions for users coordinating mission preparation and assignment."""
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_MISSIONS_CREATE,
            PERMISSION_MISSIONS_ASSIGN,
            PERMISSION_MISSIONS_RECORD_OUTCOME,
            PERMISSION_MISSIONS_RECORD_CONDITION,
            PERMISSION_MEDIA_UPLOAD,
            PERMISSION_MEDIA_VIEW,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_REPAIRS_VIEW,
            PERMISSION_SPECIFICATIONS_COMPARE,
        }
    )


def operator_permissions():
    """Permissions for users executing assigned missions in the field."""
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
            PERMISSION_REPAIRS_VIEW,
            PERMISSION_SPECIFICATIONS_COMPARE,
        }
    )


def technician_permissions():
    """Permissions for users responsible for maintenance and repair workflows."""
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
            PERMISSION_REPAIRS_VIEW,
            PERMISSION_REPAIRS_CREATE,
            PERMISSION_REPAIRS_MANAGE,
            PERMISSION_REPAIRS_EXPORT,
            PERMISSION_MEDIA_VIEW,
            PERMISSION_SPECIFICATIONS_COMPARE,
        }
    )


def viewer_permissions():
    """Read-focused permissions for users who should not modify operational data."""
    return (
        profile_permissions()
        | own_audit_log_permissions()
        | {
            PERMISSION_DRONES_VIEW,
            PERMISSION_MISSIONS_VIEW,
            PERMISSION_SPECIFICATIONS_VIEW,
            PERMISSION_MAINTENANCE_VIEW,
            PERMISSION_WRITEOFF_VIEW,
            PERMISSION_MEDIA_VIEW,
            PERMISSION_REPAIRS_VIEW,
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
