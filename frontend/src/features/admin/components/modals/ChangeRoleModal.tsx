import { useState } from "react";
import type { FormEvent } from "react";
import { ShieldAlert } from "lucide-react";

import { Avatar } from "../../../../shared/components/Avatar";
import { Button } from "../Button";
import { Modal } from "../Modal";
import { ModalActions } from "../ModalActions";
import { RoleBadge } from "../RoleBadge";
import {
  FormNote,
  SelectField,
} from "../FormFields";
import { updateUserRole } from "../../api/adminApi";
import { isAbortError } from "../../../../shared/api/apiClient";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";
import { getFormError } from "../../../../shared/utils/apiErrors";

import type {
  AdminUser,
  Role,
} from "../../types/admin";

interface ChangeRoleModalProps {
  user: AdminUser;
  roles: Role[];
  onClose: () => void;
  onChanged: (username: string) => void;
}

export function ChangeRoleModal({
  user,
  roles,
  onClose,
  onChanged,
}: ChangeRoleModalProps) {
  const [roleId, setRoleId] = useState(
    user.role ? String(user.role.id) : "",
  );

  const [fieldError, setFieldError] =
    useState<string>();

  const [formError, setFormError] =
    useState<string>();

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const { run, isMounted } =
    useAbortableRequest();

  const hasRoles = roles.length > 0;

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    if (!roleId) {
      setFieldError(
        "Select the role to assign.",
      );

      return;
    }

    if (
      user.role &&
      Number(roleId) === user.role.id
    ) {
      setFieldError(
        "This is already the user's role.",
      );

      return;
    }

    setFieldError(undefined);
    setFormError(undefined);
    setIsSubmitting(true);

    try {
      await run((signal) =>
        updateUserRole(
          user.id,
          Number(roleId),
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      onChanged(user.username);
      onClose();
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      setFormError(
        getFormError(
          error,
          "The role could not be changed. Try again.",
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
      title="Change User Role"
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

        <div className="flex items-center gap-3 rounded-lg bg-white/4 p-3">
          <Avatar
            name={user.full_name}
            size="md"
          />

          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-mc-text">
              {user.full_name}
            </p>

            <p className="truncate font-mono text-xs text-mc-muted">
              {user.email}
            </p>
          </div>

          <span className="ml-auto">
            <RoleBadge role={user.role} />
          </span>
        </div>

        {hasRoles ? (
          <SelectField
            id="change-role-role"
            label="New role"
            value={roleId}
            onChange={(value) => {
              setRoleId(value);
              setFieldError(undefined);
            }}
            options={roles.map((role) => ({
              value: String(role.id),
              label: role.name,
            }))}
            placeholder="Select a role"
            error={fieldError}
            disabled={isSubmitting}
          />
        ) : (
          <FormNote tone="danger">
            The role catalog could not be
            loaded, so no role can be assigned.
            The API needs a roles endpoint for
            this action.
          </FormNote>
        )}

        <FormNote
          tone="danger"
          icon={<ShieldAlert size={13} />}
        >
          This action is written to the
          immutable audit log.
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
            disabled={!hasRoles}
          >
            Confirm Change
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
