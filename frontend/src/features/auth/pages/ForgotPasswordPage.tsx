import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";

export function ForgotPasswordPage() {
  return (
    <AuthLayout>
      <AuthPageContent
        headingId="forgot-password-heading"
        title="Reset password"
        description="Enter your email and we'll send you a reset link."
      />
    </AuthLayout>
  );
}