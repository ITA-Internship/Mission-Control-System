import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";

export function ActivateAccountPage() {
  return (
    <AuthLayout>
      <AuthPageContent
        headingId="activate-account-heading"
        title="Activate your account"
      />
    </AuthLayout>
  );
}