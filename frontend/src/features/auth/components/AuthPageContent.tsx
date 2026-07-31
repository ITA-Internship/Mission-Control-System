import type { ReactNode } from "react";

interface AuthPageContentProps {
  headingId: string;
  title: string;
  description?: string;
  prelude?: ReactNode;
  children?: ReactNode;
}

export function AuthPageContent({
  headingId,
  title,
  description,
  prelude,
  children,
}: AuthPageContentProps) {
  return (
    <section
      className="flex flex-col gap-5 px-6 py-7 sm:px-8"
      aria-labelledby={headingId}
    >
      {prelude}

      <div>
        <h1
          id={headingId}
          className="text-xl font-semibold tracking-tight text-mc-text"
        >
          {title}
        </h1>

        {description && (
          <p className="mt-1 text-sm leading-5 text-mc-muted">
            {description}
          </p>
        )}
      </div>

      {children}
    </section>
  );
}
