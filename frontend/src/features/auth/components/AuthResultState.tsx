import {
  useId,
} from "react";
import type {
  ReactNode,
} from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";
import type {
  LucideIcon,
} from "lucide-react";

type AuthResultVariant =
  | "success"
  | "error"
  | "info";

interface AuthResultStateProps {
  variant: AuthResultVariant;
  title: string;
  description: string;
  children?: ReactNode;
}

interface ResultStyle {
  icon: LucideIcon;
  iconWrapperClass: string;
  iconClass: string;
}

const resultStyles: Record<
  AuthResultVariant,
  ResultStyle
> = {
  success: {
    icon: CheckCircle2,
    iconWrapperClass:
      "border-mc-success/30 bg-mc-success/10",
    iconClass: "text-mc-success",
  },
  error: {
    icon: AlertTriangle,
    iconWrapperClass:
      "border-mc-error/30 bg-mc-error/10",
    iconClass: "text-mc-error",
  },
  info: {
    icon: Info,
    iconWrapperClass:
      "border-mc-accent/30 bg-mc-accent/10",
    iconClass: "text-mc-accent",
  },
};

export function AuthResultState({
  variant,
  title,
  description,
  children,
}: AuthResultStateProps) {
  const titleId = useId();

  const {
    icon: Icon,
    iconWrapperClass,
    iconClass,
  } = resultStyles[variant];

  return (
    <div
      role={
        variant === "error"
          ? "alert"
          : "status"
      }
      aria-live={
        variant === "error"
          ? "assertive"
          : "polite"
      }
      aria-labelledby={titleId}
      className="flex flex-col items-center gap-5 text-center"
    >
      <div
        className={[
          "flex size-14 items-center justify-center",
          "rounded-full border",
          iconWrapperClass,
        ].join(" ")}
      >
        <Icon
          size={27}
          className={iconClass}
          aria-hidden="true"
        />
      </div>

      <div>
        <h2
          id={titleId}
          className="text-base font-semibold text-mc-text"
        >
          {title}
        </h2>

        <p className="mt-1 text-sm leading-5 text-mc-muted">
          {description}
        </p>
      </div>

      {children ? (
        <div className="w-full">
          {children}
        </div>
      ) : null}
    </div>
  );
}