import { useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowLeft,
  Mail,
} from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { AuthTextLink } from "../components/AuthTextLink";
import { SubmitButton } from "../components/SubmitButton";
import { TextInput } from "../components/TextInput";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="forgot-password-heading"
        title="Reset password"
        description="Enter your email and we'll send you a reset link."
      >
        <form
          className="flex flex-col gap-5"
          onSubmit={handleSubmit}
        >
          <TextInput
            id="forgot-password-email"
            name="email"
            label="Email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            placeholder="operator@squadron.mil"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            leadingIcon={
              <Mail
                size={15}
                aria-hidden="true"
              />
            }
            required
          />

          <SubmitButton>
            Send reset link
          </SubmitButton>

          <div className="flex">
            <AuthTextLink
              to="/login"
              icon={<ArrowLeft size={14} />}
            >
              Back to sign in
            </AuthTextLink>
          </div>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}