from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts import rbac
from drones.factories import AdminUserFactory, ViewerUserFactory
from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    DISPATCHER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
    Role,
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
            rbac.PERMISSION_USERS_VIEW,
            rbac.PERMISSION_UNITS_VIEW,
            rbac.PERMISSION_UNITS_MANAGE,
            rbac.PERMISSION_ROLES_VIEW,
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


class RoleListViewTests(APITestCase):
    """Test the read-only role list endpoint."""

    def setUp(self):
        """Set up the URL and users with and without the roles view permission."""
        self.url = reverse("roles:role-list")
        self.admin_user = AdminUserFactory()
        self.viewer_user = ViewerUserFactory()

    def test_admin_can_list_roles(self):
        """Admins can retrieve the full role catalog with id, code, and name."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Role.objects.count())
        self.assertEqual(set(response.data[0].keys()), {"id", "code", "name"})

    def test_response_is_not_paginated(self):
        """The role list returns a plain list rather than a paginated envelope."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertIsInstance(response.data, list)

    def test_user_without_permission_is_forbidden(self):
        """Users without the roles view permission receive a 403 response."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_is_rejected(self):
        """Anonymous requests are not allowed to list roles."""
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
