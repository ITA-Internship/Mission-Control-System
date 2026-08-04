import {
  createBrowserRouter,
  redirect,
} from "react-router";

import { ActivateAccountPage } from "../features/auth/pages/ActivateAccountPage";
import { ForgotPasswordPage } from "../features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RequiredPasswordChangePage } from "../features/auth/pages/RequiredPasswordChangePage";
import { ResetPasswordPage } from "../features/auth/pages/ResetPasswordPage";
import { InventoryPage } from "../features/fleet/pages/InventoryPage";

export const router = createBrowserRouter([
  {
    path: "/",
    loader: () => redirect("/fleet/inventory"),
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
    path: "/fleet",
    loader: () => redirect("/fleet/inventory"),
  },
  {
    path: "/fleet/inventory",
    Component: InventoryPage,
  },
  {
    path: "*",
    loader: () => redirect("/fleet/inventory"),
  },
]);
