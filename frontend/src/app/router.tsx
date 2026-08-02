import {
  createBrowserRouter,
  redirect,
} from "react-router";

import { RequireSessionAuth } from "../features/auth/components/RequireSessionAuth";
import { ActivateAccountPage } from "../features/auth/pages/ActivateAccountPage";
import { ForgotPasswordPage } from "../features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "../features/auth/pages/LoginPage";
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
    loader: () => redirect("/login"),
  },
]);
