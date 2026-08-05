import { useState } from "react";
import type { FormEvent } from "react";
import { Plus } from "lucide-react";

import { Button } from "../../../admin/components/Button";
import { Modal } from "../../../admin/components/Modal";
import { ModalActions } from "../../../admin/components/ModalActions";
import {
  SelectField,
  TextAreaField,
  TextField,
} from "../../../admin/components/FormFields";
import { addOrderReplacement } from "../../api/repairsApi";
import { COMPONENT_TYPE_OPTIONS } from "../../constants/repairsCatalog";
import {
  localDatetimeToIso,
  toLocalDatetimeInput,
} from "../../utils/repairsFormat";
import { isAbortError } from "../../../../shared/api/apiClient";
import {
  getApiFieldError,
  getFormError,
} from "../../../../shared/utils/apiErrors";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";

import type { OrderReplacement } from "../../types";

interface AddOrderReplacementModalProps {
  orderId: number;
  droneId: number;
  onClose: () => void;
  onCreated: (replacement: OrderReplacement) => void;
}

export function AddOrderReplacementModal({
  orderId,
  droneId,
  onClose,
  onCreated,
}: AddOrderReplacementModalProps) {
  const { run, isPending } = useAbortableRequest();

  const [componentType, setComponentType] = useState("");
  const [componentName, setComponentName] = useState("");
  const [oldSerial, setOldSerial] = useState("");
  const [newSerial, setNewSerial] = useState("");
  const [reason, setReason] = useState("");
  const [replacedAt, setReplacedAt] = useState(
    toLocalDatetimeInput(),
  );
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<
    Record<string, string | undefined>
  >({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setFieldErrors({});

    try {
      const replacement = await run(() =>
        addOrderReplacement(orderId, {
          drone: droneId,
          component_type: componentType,
          component_name: componentName.trim() || null,
          old_serial_number: oldSerial.trim(),
          new_serial_number: newSerial.trim(),
          reason: reason.trim(),
          replaced_at: localDatetimeToIso(replacedAt),
        }),
      );
      onCreated(replacement);
      onClose();
    } catch (error) {
      if (isAbortError(error)) return;

      setFieldErrors({
        component_type: getApiFieldError(error, "component_type"),
        component_name: getApiFieldError(error, "component_name"),
        old_serial_number: getApiFieldError(
          error,
          "old_serial_number",
        ),
        new_serial_number: getApiFieldError(
          error,
          "new_serial_number",
        ),
        reason: getApiFieldError(error, "reason"),
        replaced_at: getApiFieldError(error, "replaced_at"),
      });
      setFormError(
        getFormError(error, "Could not add replacement."),
      );
    }
  }

  return (
    <Modal title="Add replacement" onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        noValidate
      >
        <SelectField
          id="order-replacement-type"
          label="Component type"
          value={componentType}
          onChange={(event) =>
            setComponentType(event.target.value)
          }
          error={fieldErrors.component_type}
          options={COMPONENT_TYPE_OPTIONS}
          placeholder="Select component type"
        />

        {componentType === "OTHER" ? (
          <TextField
            id="order-replacement-name"
            label="Component name"
            value={componentName}
            onChange={(event) =>
              setComponentName(event.target.value)
            }
            error={fieldErrors.component_name}
          />
        ) : null}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            id="order-replacement-old-serial"
            label="Old serial"
            value={oldSerial}
            onChange={(event) => setOldSerial(event.target.value)}
            error={fieldErrors.old_serial_number}
          />
          <TextField
            id="order-replacement-new-serial"
            label="New serial"
            value={newSerial}
            onChange={(event) => setNewSerial(event.target.value)}
            error={fieldErrors.new_serial_number}
          />
        </div>

        <TextField
          id="order-replacement-replaced-at"
          label="Replaced at"
          type="datetime-local"
          value={replacedAt}
          onChange={(event) => setReplacedAt(event.target.value)}
          error={fieldErrors.replaced_at}
        />

        <TextAreaField
          id="order-replacement-reason"
          label="Reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          error={fieldErrors.reason}
          rows={3}
        />

        {formError ? (
          <p className="text-sm text-mc-error" role="alert">
            {formError}
          </p>
        ) : null}

        <ModalActions>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isPending}>
            Add replacement
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
