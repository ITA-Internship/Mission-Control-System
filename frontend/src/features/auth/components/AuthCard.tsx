import type { ReactNode } from "react";

interface AuthCardProps {
  children: ReactNode;
}

export function AuthCard({ children }: AuthCardProps) {
  return (
    <div
      className="w-full max-w-[440px] overflow-hidden rounded-xl border border-white/[0.08] bg-mc-card"
      style={{
        boxShadow:
          "0 0 0 1px rgba(200, 162, 74, 0.06), 0 24px 64px rgba(0, 0, 0, 0.6)",
      }}
    >
      {children}
    </div>
  );
}