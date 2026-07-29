import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";

export function LoginPage() {
  return (
    <AuthLayout>
      <AuthPageContent
        headingId="login-heading"
        title="Sign in"
      />
    </AuthLayout>
  );
}