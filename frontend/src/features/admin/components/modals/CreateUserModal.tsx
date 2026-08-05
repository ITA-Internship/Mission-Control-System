import { useState } from "react";
import type { FormEvent } from "react";
import { MailCheck } from "lucide-react";

import { Button } from "../Button";
import { Modal } from "../Modal";
import { ModalActions } from "../ModalActions";
import {
  FormNote,
  SelectField,
  TextField,
} from "../FormFields";
import { createUser } from "../../api/adminApi";
import { isAbortError } from "../../../../shared/api/apiClient";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";
import {
  getApiFieldError,
  getFormError,
} from "../../../../shared/utils/apiErrors";
import {
  splitFullName,
  validateEmail,
  validateRequired,
  validateUsername,
} from "../../utils/adminValidation";

import type { FilterOption } from "../FilterSelect";
import type {
  MilitaryUnit,
  Role,
} from "../../types/admin";

interface CreateUserModalProps {
  roles: Role[];
  units: MilitaryUnit[];
  onClose: () => void;
  onCreated: (username: string) => void;
}

interface FieldErrors {
  fullName?: string;
  username?: string;
  email?: string;
}

function toOptions(
  items: { id: number; name: string }[],
): FilterOption[] {
  return items.map((item) => ({
    value: String(item.id),
    label: item.name,
  }));
}

export function CreateUserModal({
  roles,
  units,
  onClose,
  onCreated,
}: CreateUserModalProps) {
  const [fullName, setFullName] = useState("");
  const [rank, setRank] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState("");
  const [unitId, setUnitId] = useState("");

  const [fieldErrors, setFieldErrors] =
    useState<FieldErrors>({});

  const [formError, setFormError] =
    useState<string>();

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const { run, isMounted } =
    useAbortableRequest();

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const errors: FieldErrors = {
      fullName: validateRequired(
        fullName,
        "Full name",
      ),
      username: validateUsername(username),
      email: validateEmail(email),
    };

    setFieldErrors(errors);
    setFormError(undefined);

    if (
      Object.values(errors).some(Boolean)
    ) {
      return;
    }

    const { firstName, lastName } =
      splitFullName(fullName);

    setIsSubmitting(true);

    try {
      await run((signal) =>
        createUser(
          {
            username: username.trim(),
            email: email.trim(),
            first_name: firstName,
            last_name: lastName,
            role: roleId
              ? Number(roleId)
              : null,
            unit: unitId
              ? Number(unitId)
              : null,
            ...(rank.trim()
              ? { rank: rank.trim() }
              : {}),
          },
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      onCreated(username.trim());
      onClose();
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      setFieldErrors({
        username: getApiFieldError(
          error,
          "username",
        ),
        email: getApiFieldError(
          error,
          "email",
        ),
      });

      setFormError(
        getFormError(
          error,
          "The user could not be created. Check the form and try again.",
        ),
      );
    } finally {
      if (isMounted()) {
        setIsSubmitting(false);
      }
    }
  }

  return (
    <Modal
      title="Create New User"
      onClose={onClose}
    >
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        noValidate
        aria-busy={isSubmitting}
      >
        {formError ? (
          <FormNote
            tone="danger"
            isAlert
          >
            {formError}
          </FormNote>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <TextField
            id="create-user-full-name"
            label="Full name"
            value={fullName}
            onChange={(value) => {
              setFullName(value);
              setFieldErrors(
                (previous) => ({
                  ...previous,
                  fullName: undefined,
                }),
              );
            }}
            placeholder="Marcus Hale"
            error={fieldErrors.fullName}
            disabled={isSubmitting}
          />

          <TextField
            id="create-user-rank"
            label="Rank (optional)"
            value={rank}
            onChange={setRank}
            placeholder="Col."
            disabled={isSubmitting}
          />

          <TextField
            id="create-user-username"
            label="Username"
            value={username}
            onChange={(value) => {
              setUsername(value);
              setFieldErrors(
                (previous) => ({
                  ...previous,
                  username: undefined,
                }),
              );
            }}
            placeholder="m.hale"
            hint="Used for sign-in and audit entries."
            error={fieldErrors.username}
            disabled={isSubmitting}
            isMono
          />

          <TextField
            id="create-user-email"
            label="Email"
            type="email"
            value={email}
            onChange={(value) => {
              setEmail(value);
              setFieldErrors(
                (previous) => ({
                  ...previous,
                  email: undefined,
                }),
              );
            }}
            placeholder="user@mcs.mil"
            error={fieldErrors.email}
            disabled={isSubmitting}
          />

          <SelectField
            id="create-user-role"
            label="Role"
            value={roleId}
            onChange={setRoleId}
            options={toOptions(roles)}
            placeholder={
              roles.length === 0
                ? "No roles available"
                : "Select a role"
            }
            disabled={
              isSubmitting ||
              roles.length === 0
            }
          />

          <SelectField
            id="create-user-unit"
            label="Unit"
            value={unitId}
            onChange={setUnitId}
            options={toOptions(units)}
            placeholder={
              units.length === 0
                ? "No units available"
                : "Select a unit"
            }
            disabled={
              isSubmitting ||
              units.length === 0
            }
          />
        </div>

        <FormNote
          icon={<MailCheck size={13} />}
        >
          An activation email will be sent to
          the new user. They must set a
          password before their first sign-in.
        </FormNote>

        <ModalActions>
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            isLoading={isSubmitting}
          >
            Create &amp; Send Activation
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
