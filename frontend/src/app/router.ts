import {
  createBrowserRouter,
  redirect,
} from "react-router";

import { ActivateAccountPage } from "../features/auth/pages/ActivateAccountPage";
import { ForgotPasswordPage } from "../features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { RequiredPasswordChangePage } from "../features/auth/pages/RequiredPasswordChangePage";
import { ResetPasswordPage } from "../features/auth/pages/ResetPasswordPage";
import { MyProfilePage } from "../features/profile/pages/MyProfilePage";

export const router = createBrowserRouter([
  {
    path: "/",
    loader: () => redirect("/login"),
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
    path: "/my-profile",
    Component: MyProfilePage,
  },
  {
    path: "*",
    loader: () => redirect("/login"),
  },
]);
