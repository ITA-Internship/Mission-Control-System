import {
  createBrowserRouter,
  redirect,
} from "react-router";

import { AdministrationPage } from "../features/admin/pages/AdministrationPage";
import { RequireSessionAuth } from "../features/auth/components/RequireSessionAuth";
import { ActivateAccountPage } from "../features/auth/pages/ActivateAccountPage";
import { ForgotPasswordPage } from "../features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RequiredPasswordChangePage } from "../features/auth/pages/RequiredPasswordChangePage";
import { ResetPasswordPage } from "../features/auth/pages/ResetPasswordPage";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage";
import { MyProfilePage } from "../features/profile/pages/MyProfilePage";
import { PlaceholderPage } from "../shared/pages/PlaceholderPage";
import { ProtectedRoute } from "./ProtectedRoute";

export const router = createBrowserRouter([
  {
    path: "/",
    loader: () => redirect("/dashboard"),
  },
  {
    Component: ProtectedRoute,
    children: [
      {
        path: "/dashboard",
        Component: DashboardPage,
      },
      {
        path: "/drones",
        Component: PlaceholderPage,
      },
      {
        path: "/missions",
        Component: PlaceholderPage,
      },
      {
        path: "/repairs",
        Component: PlaceholderPage,
      },
      {
        path: "/media",
        Component: PlaceholderPage,
      },
      {
        path: "/administration",
        Component: AdministrationPage,
      },
    ],
  },
  {
    path: "/login",
    Component: LoginPage,
  },
  {
    path: "/forgot-password",
    Component: ForgotPasswordPage,
  },
  {
    path: "/reset-password/:uid/:token",
    Component: ResetPasswordPage,
  },
  {
    path: "/reset-password/*",
    Component: ResetPasswordPage,
  },
  {
    path: "/activate/:userId/:token",
    Component: ActivateAccountPage,
  },
  {
    path: "/activate/*",
    Component: ActivateAccountPage,
  },
  {
    path: "/change-password/required",
    Component: RequiredPasswordChangePage,
  },
  {
    /* Profile brings its own workspace chrome, so it guards the session itself
     * rather than rendering inside the dashboard shell. */
    path: "/my-profile",
    element: (
      <RequireSessionAuth>
        {(user) => (
          <MyProfilePage
            initialUser={user}
          />
        )}
      </RequireSessionAuth>
    ),
  },
  {
    path: "*",
    loader: () => redirect("/dashboard"),
  },
]);
