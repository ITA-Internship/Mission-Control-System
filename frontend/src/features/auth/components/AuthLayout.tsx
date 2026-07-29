import type { ReactNode } from "react";

import { AuthCard } from "./AuthCard";
import { AuthHeader } from "./AuthHeader";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-x-hidden bg-mc-bg px-4 py-8 text-mc-text sm:py-12">
      <div className="auth-background" aria-hidden="true" />

      <AuthCard>
        <AuthHeader />
        {children}
      </AuthCard>

      <footer
        className="mt-6 flex items-center gap-3"
        aria-label="Document classification"
      >
        <span className="h-px w-12 bg-white/[0.08]" />

        <span className="font-mono text-[10px] tracking-[0.2em] text-[#2C3A4A] uppercase">
          Unclassified // For official use only
        </span>

        <span className="h-px w-12 bg-white/[0.08]" />
      </footer>
    </main>
  );
}