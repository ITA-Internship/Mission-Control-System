import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";

export function ResetPasswordPage() {
  return (
    <AuthLayout>
      <AuthPageContent
        headingId="reset-password-heading"
        title="Set a new password"
      />
    </AuthLayout>
  );
}