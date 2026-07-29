import {
  forwardRef,
  useState,
} from "react";
import {
  Eye,
  EyeOff,
  Lock,
} from "lucide-react";

import { TextInput } from "./TextInput";
import type { TextInputProps } from "./TextInput";

export type PasswordInputProps = Omit<
  TextInputProps,
  "type" | "leadingIcon" | "trailingElement"
>;

export const PasswordInput = forwardRef<
  HTMLInputElement,
  PasswordInputProps
>(function PasswordInput(
  {
    disabled,
    placeholder = "••••••••",
    ...inputProps
  },
  ref,
) {
  const [isVisible, setIsVisible] = useState(false);

  const visibilityLabel = isVisible
    ? "Hide password"
    : "Show password";

  return (
    <TextInput
      {...inputProps}
      ref={ref}
      type={isVisible ? "text" : "password"}
      disabled={disabled}
      placeholder={placeholder}
      leadingIcon={
        <Lock
          size={15}
          aria-hidden="true"
        />
      }
      trailingElement={
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsVisible((current) => !current)}
          aria-label={visibilityLabel}
          aria-controls={inputProps.id}
          aria-pressed={isVisible}
          className="rounded p-1 text-mc-muted transition-colors hover:text-mc-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mc-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isVisible ? (
            <EyeOff
              size={15}
              aria-hidden="true"
            />
          ) : (
            <Eye
              size={15}
              aria-hidden="true"
            />
          )}
        </button>
      }
    />
  );
});