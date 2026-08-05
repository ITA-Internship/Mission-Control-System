import type { ReactNode } from "react";

interface ModalActionsProps {
  children: ReactNode;
}

export function ModalActions({
  children,
}: ModalActionsProps) {
  return (
    <div className="flex flex-wrap justify-end gap-2 pt-1">
      {children}
    </div>
  );
}
