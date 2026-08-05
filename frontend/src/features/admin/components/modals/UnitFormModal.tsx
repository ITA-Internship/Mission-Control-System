import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "../Button";
import { Modal } from "../Modal";
import { ModalActions } from "../ModalActions";
import {
  FormNote,
  TextAreaField,
  TextField,
} from "../FormFields";
import {
  createUnit,
  updateUnit,
} from "../../api/adminApi";
import { isAbortError } from "../../../../shared/api/apiClient";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";
import {
  getApiFieldError,
  getFormError,
} from "../../../../shared/utils/apiErrors";
import {
  validateRequired,
  validateUnitCode,
} from "../../utils/adminValidation";

import type { MilitaryUnit } from "../../types/admin";

interface UnitFormModalProps {
  /** Omitted when creating a new unit. */
  unit?: MilitaryUnit;
  onClose: () => void;
  onSaved: (unitName: string) => void;
}

interface FieldErrors {
  name?: string;
  code?: string;
}

export function UnitFormModal({
  unit,
  onClose,
  onSaved,
}: UnitFormModalProps) {
  const isEditing = Boolean(unit);

  const [name, setName] = useState(
    unit?.name ?? "",
  );

  const [code, setCode] = useState(
    unit?.code ?? "",
  );

  const [description, setDescription] =
    useState(unit?.description ?? "");

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
      name: validateRequired(
        name,
        "Unit name",
      ),
      code: validateUnitCode(code),
    };

    setFieldErrors(errors);
    setFormError(undefined);

    if (
      Object.values(errors).some(Boolean)
    ) {
      return;
    }

    const payload = {
      name: name.trim(),
      code: code.trim(),
      description: description.trim(),
    };

    setIsSubmitting(true);

    try {
      await run((signal) =>
        unit
          ? updateUnit(
              unit.id,
              payload,
              signal,
            )
          : createUnit(payload, signal),
      );

      if (!isMounted()) {
        return;
      }

      onSaved(payload.name);
      onClose();
    } catch (error) {
      if (
        isAbortError(error) ||
        !isMounted()
      ) {
        return;
      }

      setFieldErrors({
        name: getApiFieldError(error, "name"),
        code: getApiFieldError(error, "code"),
      });

      setFormError(
        getFormError(
          error,
          isEditing
            ? "The unit could not be updated. Try again."
            : "The unit could not be created. Try again.",
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
        isEditing
          ? "Edit Military Unit"
          : "Add Military Unit"
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

        <div className="grid gap-3 sm:grid-cols-2">
          <TextField
            id="unit-form-name"
            label="Unit name"
            value={name}
            onChange={(value) => {
              setName(value);
              setFieldErrors(
                (previous) => ({
                  ...previous,
                  name: undefined,
                }),
              );
            }}
            placeholder="e.g. 5th Strike Squadron"
            error={fieldErrors.name}
            disabled={isSubmitting}
          />

          <TextField
            id="unit-form-code"
            label="Unit code"
            value={code}
            onChange={(value) => {
              setCode(value.toUpperCase());
              setFieldErrors(
                (previous) => ({
                  ...previous,
                  code: undefined,
                }),
              );
            }}
            placeholder="e.g. 5TH-STRIKE-SQN"
            hint="Unique across the catalog."
            error={fieldErrors.code}
            disabled={isSubmitting}
            isMono
          />
        </div>

        <TextAreaField
          id="unit-form-description"
          label="Description"
          value={description}
          onChange={setDescription}
          placeholder="Brief description of the unit mission…"
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
            isLoading={isSubmitting}
          >
            {isEditing
              ? "Save Changes"
              : "Add Unit"}
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
