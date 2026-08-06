import { useShellContext } from "../../../shared/layout/shellContext";
import { MyProfilePage } from "./MyProfilePage";

/*
 * Route adapter for `/my-profile` inside the app shell.
 *
 * `ProtectedRoute` has already resolved the session user and hands it down via
 * outlet context, so the page is seeded with it rather than issuing a second
 * `/users/me` request on mount.
 */
export function MyProfileRoute() {
  const { user } = useShellContext();

  return <MyProfilePage initialUser={user} />;
}
