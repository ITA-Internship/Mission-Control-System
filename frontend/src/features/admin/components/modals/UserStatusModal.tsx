import { useState } from "react";
import type { FormEvent } from "react";
import { TriangleAlert } from "lucide-react";

import { Button } from "../Button";
import { Modal } from "../Modal";
import { ModalActions } from "../ModalActions";
import { StatusPill } from "../StatusPill";
import {
  FormNote,
  TextAreaField,
} from "../FormFields";
import { updateUserStatus } from "../../api/adminApi";
import { isAbortError } from "../../../../shared/api/apiClient";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";
import { getFormError } from "../../../../shared/utils/apiErrors";
import { validateRequired } from "../../utils/adminValidation";

import type { AdminUser } from "../../types/admin";

interface UserStatusModalProps {
  user: AdminUser;
  onClose: () => void;
  onUpdated: (
    username: string,
    isActive: boolean,
  ) => void;
}

export function UserStatusModal({
  user,
  onClose,
  onUpdated,
}: UserStatusModalProps) {
  const isDeactivating = user.is_active;

  const [reason, setReason] = useState("");

  const [reasonError, setReasonError] =
    useState<string>();

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

    const validationError = validateRequired(
      reason,
      "A reason",
    );

    setReasonError(validationError);
    setFormError(undefined);

    if (validationError) {
      return;
    }

    setIsSubmitting(true);

    try {
      await run((signal) =>
        updateUserStatus(
          user.id,
          !user.is_active,
          reason.trim(),
          signal,
        ),
      );

      if (!isMounted()) {
        return;
      }

      onUpdated(
        user.username,
        !user.is_active,
      );

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
          "The status could not be updated. Try again.",
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
      title={
        isDeactivating
          ? "Deactivate User"
          : "Activate User"
      }
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
          <StatusPill
            isActive={user.is_active}
          />

          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-mc-text">
              {user.full_name}
            </p>

            <p className="truncate font-mono text-xs text-mc-muted">
              {user.email}
            </p>
          </div>
        </div>

        {isDeactivating ? (
          <FormNote
            tone="danger"
            icon={<TriangleAlert size={13} />}
          >
            Deactivating this user immediately
            revokes system access — they will
            not be able to sign in.
          </FormNote>
        ) : null}

        <TextAreaField
          id="user-status-reason"
          label="Reason (recorded in audit log)"
          value={reason}
          onChange={(value) => {
            setReason(value);
            setReasonError(undefined);
          }}
          placeholder="Provide a reason for this action…"
          error={reasonError}
          disabled={isSubmitting}
        />

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
            variant={
              isDeactivating
                ? "danger"
                : "success"
            }
            isLoading={isSubmitting}
          >
            {isDeactivating
              ? "Deactivate"
              : "Activate"}
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
