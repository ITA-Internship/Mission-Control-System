import { useState } from "react";
import type { FormEvent } from "react";
import { Mail } from "lucide-react";

import { AuthLayout } from "../components/AuthLayout";
import { AuthPageContent } from "../components/AuthPageContent";
import { AuthTextLink } from "../components/AuthTextLink";
import { PasswordInput } from "../components/PasswordInput";
import { SubmitButton } from "../components/SubmitButton";
import { TextInput } from "../components/TextInput";

export function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
  }

  return (
    <AuthLayout>
      <AuthPageContent
        headingId="login-heading"
        title="Sign in"
      >
        <form
          className="flex flex-col gap-5"
          onSubmit={handleSubmit}
        >
          <div className="flex flex-col gap-4">
            <TextInput
              id="login-identifier"
              name="identifier"
              label="Email"
              type="text"
              inputMode="email"
              value={identifier}
              onChange={(event) =>
                setIdentifier(event.target.value)
              }
              placeholder="operator@squadron.mil"
              autoComplete="username"
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

            <div className="flex flex-col gap-1.5">
              <PasswordInput
                id="login-password"
                name="password"
                label="Password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                autoComplete="current-password"
                required
              />

              <div className="flex justify-end">
                <AuthTextLink to="/forgot-password">
                  Forgot password?
                </AuthTextLink>
              </div>
            </div>
          </div>

          <SubmitButton>
            Sign in
          </SubmitButton>

          <p className="mt-1 text-center text-xs leading-5 text-mc-subtle">
            Authorized personnel only — unauthorized
            access is prohibited.
          </p>
        </form>
      </AuthPageContent>
    </AuthLayout>
  );
}