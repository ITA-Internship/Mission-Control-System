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
import { createReplacement } from "../../api/repairsApi";
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

interface LogReplacementModalProps {
  onClose: () => void;
  onCreated: () => void;
  defaultDroneId?: number;
}

interface FieldErrors {
  drone?: string;
  component_type?: string;
  component_name?: string;
  old_serial_number?: string;
  new_serial_number?: string;
  reason?: string;
  replaced_at?: string;
  form?: string;
}

export function LogReplacementModal({
  onClose,
  onCreated,
  defaultDroneId,
}: LogReplacementModalProps) {
  const { run } = useAbortableRequest();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [drone, setDrone] = useState(
    defaultDroneId ? String(defaultDroneId) : "",
  );
  const [componentType, setComponentType] = useState("");
  const [componentName, setComponentName] = useState("");
  const [oldSerial, setOldSerial] = useState("");
  const [newSerial, setNewSerial] = useState("");
  const [reason, setReason] = useState("");
  const [replacedAt, setReplacedAt] = useState(
    toLocalDatetimeInput(),
  );
  const [errors, setErrors] = useState<FieldErrors>({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setErrors({});

    const droneId = Number(drone);
    if (!drone.trim() || Number.isNaN(droneId)) {
      setErrors({ drone: "Enter a valid drone ID." });
      return;
    }
    if (!componentType) {
      setErrors({ component_type: "Select a component type." });
      return;
    }
    if (componentType === "OTHER" && !componentName.trim()) {
      setErrors({
        component_name: "Name is required for OTHER component types.",
      });
      return;
    }
    if (!oldSerial.trim() || !newSerial.trim()) {
      setErrors({
        old_serial_number: !oldSerial.trim()
          ? "Old serial is required."
          : undefined,
        new_serial_number: !newSerial.trim()
          ? "New serial is required."
          : undefined,
      });
      return;
    }
    if (reason.trim().length < 3) {
      setErrors({
        reason: "Reason must be at least 3 characters.",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      await run(() =>
        createReplacement({
          drone: droneId,
          component_type: componentType,
          component_name: componentName.trim() || null,
          old_serial_number: oldSerial.trim(),
          new_serial_number: newSerial.trim(),
          reason: reason.trim(),
          replaced_at: localDatetimeToIso(replacedAt),
        }),
      );
      onCreated();
      onClose();
    } catch (error) {
      if (isAbortError(error)) return;

      setErrors({
        drone: getApiFieldError(error, "drone"),
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
        form: getFormError(
          error,
          "Could not log the component replacement.",
        ),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Log Component Replacement" onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        noValidate
      >
        <TextField
          id="replacement-drone"
          label="Drone"
          type="number"
          value={drone}
          onChange={setDrone}
          error={errors.drone}
          placeholder="Drone ID"
          isMono
        />

        <SelectField
          id="replacement-component-type"
          label="Component type"
          value={componentType}
          onChange={setComponentType}
          error={errors.component_type}
          options={COMPONENT_TYPE_OPTIONS}
          placeholder="Select component type"
        />

        {componentType === "OTHER" ? (
          <TextField
            id="replacement-component-name"
            label="Component name"
            value={componentName}
            onChange={setComponentName}
            error={errors.component_name}
            placeholder="Custom component name"
          />
        ) : null}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            id="replacement-old-serial"
            label="Old serial"
            value={oldSerial}
            onChange={setOldSerial}
            error={errors.old_serial_number}
            placeholder="MCB-XXXX-X"
            isMono
          />

          <TextField
            id="replacement-new-serial"
            label="New serial"
            value={newSerial}
            onChange={setNewSerial}
            error={errors.new_serial_number}
            placeholder="MCB-XXXX-X"
            isMono
          />
        </div>

        <TextField
          id="replacement-replaced-at"
          label="Replaced at"
          type="datetime-local"
          value={replacedAt}
          onChange={setReplacedAt}
          error={errors.replaced_at}
        />

        <TextAreaField
          id="replacement-reason"
          label="Reason"
          value={reason}
          onChange={setReason}
          error={errors.reason}
          rows={3}
          placeholder="Failure mode, condition, justification..."
        />

        {errors.form ? (
          <p className="text-sm text-mc-error" role="alert">
            {errors.form}
          </p>
        ) : null}

        <ModalActions>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            icon={<Plus size={14} aria-hidden="true" />}
          >
            Log Replacement
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
