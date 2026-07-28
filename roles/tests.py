from django.test import SimpleTestCase

from accounts import rbac
from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    DISPATCHER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
)


class RolePermissionMatrixTests(SimpleTestCase):
    """
    Unit tests to verify that the rights of each role (ROLE_PERMISSION_MATRIX)
    correspond to the documented access matrix (RBAC backbone).
    """

    def test_all_roles_present_in_matrix(self):
        """Check that all 6 roles are registered in ROLE_PERMISSION_MATRIX."""

        expected_roles = {
            ADMIN_CODE,
            COMMANDER_CODE,
            DISPATCHER_CODE,
            OPERATOR_CODE,
            TECHNICIAN_CODE,
            VIEWER_CODE,
        }

        self.assertEqual(set(rbac.ROLE_PERMISSION_MATRIX.keys()), expected_roles)

    def test_admin_permissions(self):
        """Checks permissions for admin"""
        admin_perms = rbac.ROLE_PERMISSION_MATRIX[ADMIN_CODE]

        expected_permissions = {
            rbac.PERMISSION_USERS_MANAGE_ROLES,
            rbac.PERMISSION_USERS_CREATE,
            rbac.PERMISSION_USERS_ACTIVATE_DEACTIVATE,
            rbac.PERMISSION_DRONES_CREATE,
            rbac.PERMISSION_DRONES_UPDATE,
            rbac.PERMISSION_DRONES_DECOMMISSION,
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_DRONES_IMPORT_EXPORT,
            rbac.PERMISSION_MISSIONS_VIEW,
            rbac.PERMISSION_MISSIONS_CREATE,
            rbac.PERMISSION_MISSIONS_ASSIGN,
            rbac.PERMISSION_MISSIONS_UPDATE_STATUS,
            rbac.PERMISSION_MISSIONS_RECORD_OUTCOME,
            rbac.PERMISSION_MISSIONS_RECORD_CONDITION,
            rbac.PERMISSION_MEDIA_UPLOAD,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_MEDIA_DELETE,
            rbac.PERMISSION_MEDIA_VIEW_LOGS,
            rbac.PERMISSION_MAINTENANCE_VIEW,
            rbac.PERMISSION_MAINTENANCE_MANAGE,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_SPECIFICATIONS_MANAGE,
            rbac.PERMISSION_SPECIFICATIONS_COMPARE,
            rbac.PERMISSION_WRITEOFF_VIEW,
            rbac.PERMISSION_WRITEOFF_CREATE,
            rbac.PERMISSION_WRITEOFF_AUTHORIZE,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_REPAIRS_CREATE,
            rbac.PERMISSION_REPAIRS_MANAGE,
            rbac.PERMISSION_REPAIRS_EXPORT,
            rbac.PERMISSION_REPAIRS_VERIFY,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_ALL,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_ANY,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
        }

        self.assertEqual(admin_perms, expected_permissions)

    def test_commander_permissions(self):
        """Check permissions for commander"""
        commander_permissions = rbac.ROLE_PERMISSION_MATRIX[COMMANDER_CODE]

        expected_permissions = {
            rbac.PERMISSION_DRONES_CREATE,
            rbac.PERMISSION_DRONES_UPDATE,
            rbac.PERMISSION_DRONES_DECOMMISSION,
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_DRONES_IMPORT_EXPORT,
            rbac.PERMISSION_MISSIONS_VIEW,
            rbac.PERMISSION_MISSIONS_CREATE,
            rbac.PERMISSION_MISSIONS_ASSIGN,
            rbac.PERMISSION_MISSIONS_UPDATE_STATUS,
            rbac.PERMISSION_MAINTENANCE_VIEW,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_WRITEOFF_VIEW,
            rbac.PERMISSION_WRITEOFF_AUTHORIZE,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_REPAIRS_EXPORT,
            rbac.PERMISSION_REPAIRS_VERIFY,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
            rbac.PERMISSION_SPECIFICATIONS_COMPARE,
        }

        self.assertEqual(commander_permissions, expected_permissions)

    def test_dispatcher_permissions(self):
        """Check permissions for dispatcher"""
        dispatcher_perms = rbac.ROLE_PERMISSION_MATRIX[DISPATCHER_CODE]

        expected_permissions = {
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_MISSIONS_VIEW,
            rbac.PERMISSION_MISSIONS_CREATE,
            rbac.PERMISSION_MISSIONS_ASSIGN,
            rbac.PERMISSION_MISSIONS_UPDATE_STATUS,
            rbac.PERMISSION_MISSIONS_RECORD_OUTCOME,
            rbac.PERMISSION_MISSIONS_RECORD_CONDITION,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_WRITEOFF_VIEW,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_MEDIA_UPLOAD,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
            rbac.PERMISSION_SPECIFICATIONS_COMPARE,
        }

        self.assertEqual(dispatcher_perms, expected_permissions)

    def test_operator_permissions(self):
        """Check permissions for operator"""
        operator_perms = rbac.ROLE_PERMISSION_MATRIX[OPERATOR_CODE]

        expected_permissions = {
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_MISSIONS_VIEW,
            rbac.PERMISSION_MISSIONS_UPDATE_STATUS,
            rbac.PERMISSION_MISSIONS_RECORD_OUTCOME,
            rbac.PERMISSION_MISSIONS_RECORD_CONDITION,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_MEDIA_UPLOAD,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
            rbac.PERMISSION_SPECIFICATIONS_COMPARE,
        }

        self.assertEqual(operator_perms, expected_permissions)

    def test_technician_permissions(self):
        """Check permissions for technician"""
        technician_perms = rbac.ROLE_PERMISSION_MATRIX[TECHNICIAN_CODE]

        expected_permissions = {
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_MAINTENANCE_VIEW,
            rbac.PERMISSION_MAINTENANCE_MANAGE,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_SPECIFICATIONS_MANAGE,
            rbac.PERMISSION_WRITEOFF_VIEW,
            rbac.PERMISSION_WRITEOFF_CREATE,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_REPAIRS_CREATE,
            rbac.PERMISSION_REPAIRS_MANAGE,
            rbac.PERMISSION_REPAIRS_EXPORT,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
            rbac.PERMISSION_SPECIFICATIONS_COMPARE,
        }

        self.assertEqual(technician_perms, expected_permissions)

    def test_viewer_permissions(self):
        """Check permissions for viewer"""
        viewer_perms = rbac.ROLE_PERMISSION_MATRIX[VIEWER_CODE]

        expected_permissions = {
            rbac.PERMISSION_DRONES_VIEW,
            rbac.PERMISSION_MISSIONS_VIEW,
            rbac.PERMISSION_MAINTENANCE_VIEW,
            rbac.PERMISSION_SPECIFICATIONS_VIEW,
            rbac.PERMISSION_WRITEOFF_VIEW,
            rbac.PERMISSION_REPAIRS_VIEW,
            rbac.PERMISSION_MEDIA_VIEW,
            rbac.PERMISSION_AUDIT_LOGS_VIEW_OWN,
            rbac.PERMISSION_PROFILE_VIEW_OWN,
            rbac.PERMISSION_PROFILE_UPDATE_OWN,
            rbac.PERMISSION_PROFILE_RESET_PASSWORD_OWN,
        }

        self.assertEqual(viewer_perms, expected_permissions)
