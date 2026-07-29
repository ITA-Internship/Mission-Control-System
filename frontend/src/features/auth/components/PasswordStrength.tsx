interface PasswordStrengthProps {
  id: string;
  password: string;
}

interface StrengthLevel {
  label: string;
  segmentClass: string;
  labelClass: string;
}

const strengthLevels: StrengthLevel[] = [
  {
    label: "Very weak",
    segmentClass: "bg-mc-error",
    labelClass: "text-mc-error",
  },
  {
    label: "Weak",
    segmentClass: "bg-orange-400",
    labelClass: "text-orange-400",
  },
  {
    label: "Fair",
    segmentClass: "bg-mc-warning",
    labelClass: "text-mc-warning",
  },
  {
    label: "Good",
    segmentClass: "bg-mc-accent",
    labelClass: "text-mc-accent",
  },
  {
    label: "Strong",
    segmentClass: "bg-mc-success",
    labelClass: "text-mc-success",
  },
];

function calculateStrength(password: string): number {
  let score = 0;

  if (password.length >= 8) {
    score += 1;
  }

  if (password.length >= 12) {
    score += 1;
  }

  if (
    /[a-z]/.test(password) &&
    /[A-Z]/.test(password)
  ) {
    score += 1;
  }

  if (/\d/.test(password)) {
    score += 1;
  }

  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1;
  }

  return Math.max(1, Math.min(score, 5));
}

export function PasswordStrength({
  id,
  password,
}: PasswordStrengthProps) {
  if (!password) {
    return null;
  }

  const score = calculateStrength(password);
  const level = strengthLevels[score - 1];

  return (
    <div
      id={id}
      className="flex flex-col gap-1.5"
      aria-live="polite"
    >
      <div
        role="meter"
        aria-label="Password strength estimate"
        aria-valuemin={1}
        aria-valuemax={5}
        aria-valuenow={score}
        aria-valuetext={`${level.label} strength estimate`}
        className="flex gap-1"
      >
        {Array.from({ length: 5 }).map(
          (_, index) => (
            <span
              key={index}
              className={[
                "h-1 flex-1 rounded-full",
                "transition-colors duration-200",
                index < score
                  ? level.segmentClass
                  : "bg-white/8",
              ].join(" ")}
            />
          ),
        )}
      </div>

      <p
        className={[
          "text-xs",
          level.labelClass,
        ].join(" ")}
      >
        Strength estimate: {level.label}
      </p>

      <p className="text-xs leading-4 text-mc-subtle">
        Password security rules will be checked
        when the form is submitted.
      </p>
    </div>
  );
}