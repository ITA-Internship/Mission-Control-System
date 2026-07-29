import { Shield } from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";

export function RequiredPasswordChangePage() {
  return (
    <AuthLayout>
      <AuthPageContent
        headingId="required-password-change-heading"
        title="Update your password to continue"
        description="For security, you must set a new password before proceeding."
        prelude={
          <div className="flex items-center gap-2 rounded-lg border border-mc-accent/15 bg-mc-accent/10 px-3 py-2">
            <Shield
              size={14}
              className="shrink-0 text-mc-accent"
              aria-hidden="true"
            />

            <span className="text-xs font-medium tracking-wider text-mc-accent uppercase">
              Security action required
            </span>
          </div>
        }
      />
    </AuthLayout>
  );
}