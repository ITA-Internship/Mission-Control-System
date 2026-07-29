import type { ReactNode } from "react";

import { AuthCard } from "./AuthCard";
import { AuthHeader } from "./AuthHeader";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({
  children,
}: AuthLayoutProps) {
  return (
    <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-x-hidden bg-mc-bg px-4 py-8 text-mc-text sm:py-12">
      <div
        className="auth-background"
        aria-hidden="true"
      />

      <AuthCard>
        <AuthHeader />
        {children}
      </AuthCard>

      <footer
        className="mt-6 flex w-full max-w-110 items-center justify-center gap-3 px-3"
        aria-label="Document classification"
      >
        <span className="hidden h-px flex-1 bg-white/8 sm:block" />

        <span className="text-center font-mono text-[9px] leading-4 tracking-[0.14em] text-[#2C3A4A] uppercase sm:text-[10px] sm:tracking-[0.2em]">
          Unclassified // For official use only
        </span>

        <span className="hidden h-px flex-1 bg-white/8 sm:block" />
      </footer>
    </main>
  );
}